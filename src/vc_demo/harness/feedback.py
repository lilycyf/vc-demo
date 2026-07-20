from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _nodes(tree: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = tree.get("nodes", {})
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items() if isinstance(v, dict)}
    if isinstance(raw, list):
        out: dict[str, dict[str, Any]] = {}
        for i, node in enumerate(raw):
            if isinstance(node, dict):
                out[str(node.get("name") or node.get("id") or i)] = node
        return out
    return {}


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return 0.0 if values else None
    m = sum(values) / len(values)
    return math.sqrt(sum((value - m) ** 2 for value in values) / (len(values) - 1))


def _strategy_family(strategy: str) -> str:
    if strategy in {"root", ""}:
        return "root"
    if "target" in strategy:
        return "target_aware"
    if "string" in strategy or "graph" in strategy or "laplacian" in strategy:
        return "graph_prior"
    if "pathway" in strategy or "reactome" in strategy:
        return "pathway_prior"
    if "focal" in strategy or "weighted" in strategy or "class_imbalance" in strategy:
        return "imbalance_training"
    if "temperature" in strategy or "calibr" in strategy:
        return "calibration"
    if "dropout" in strategy or "swa" in strategy or "ensemble" in strategy:
        return "stability_regularization"
    if "fusion" in strategy or "moe" in strategy or "mixture" in strategy:
        return "fusion"
    if "aido" in strategy:
        return "foundation_model"
    return strategy


def _empty_policy() -> dict[str, Any]:
    return {
        "ranking_boosts": {},
        "ranking_penalties": {},
        "implementation_guidance": [],
        "validation_recommendations": [],
        "suppressed_families": [],
    }


def build_framework_feedback(run_dir: Path, tree: dict[str, Any] | None = None, memory: dict[str, Any] | None = None, target_val_macro_f1: float | None = None) -> dict[str, Any]:
    """Infer framework-level policy feedback from completed rollouts.

    This turns task outcomes into search/implementation guidance. It is not a
    K562 model tweak: the output is generic ranking boosts, penalties, and
    Codex implementation guidance for the next run.
    """
    tree_path = run_dir / "tree.json"
    if tree is None and tree_path.exists():
        tree = json.loads(tree_path.read_text(encoding="utf-8"))
    tree = tree or {"nodes": {}}
    nodes = _nodes(tree)
    trained = {name: node for name, node in nodes.items() if node.get("status") == "trained"}
    roots = {name: node for name, node in trained.items() if not node.get("parent")}
    children = {name: node for name, node in trained.items() if node.get("parent")}
    best_root = max(roots.items(), key=lambda item: _as_float(item[1].get("best_val_macro_f1"), -1.0) or -1.0, default=("", {}))
    best_child = max(children.items(), key=lambda item: _as_float(item[1].get("best_val_macro_f1"), -1.0) or -1.0, default=("", {}))
    best_root_val = _as_float(best_root[1].get("best_val_macro_f1"))
    best_child_val = _as_float(best_child[1].get("best_val_macro_f1"))
    best_root_test = _as_float(best_root[1].get("test_macro_f1"))
    best_child_test = _as_float(best_child[1].get("test_macro_f1"))

    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for name, node in children.items():
        strategy = str(node.get("strategy") or "unknown")
        val = _as_float(node.get("best_val_macro_f1"))
        test = _as_float(node.get("test_macro_f1"))
        parent = nodes.get(str(node.get("parent") or ""), {})
        parent_val = _as_float(parent.get("best_val_macro_f1"), best_root_val)
        row = {
            "node": name,
            "strategy": strategy,
            "family": _strategy_family(strategy),
            "val": val,
            "test": test,
            "parent": node.get("parent"),
            "parent_val": parent_val,
            "delta_vs_parent": (val - parent_val) if val is not None and parent_val is not None else None,
            "delta_vs_best_root": (val - best_root_val) if val is not None and best_root_val is not None else None,
        }
        by_strategy[strategy].append(row)
        by_family[row["family"]].append(row)

    strategy_stats: dict[str, dict[str, Any]] = {}
    for strategy, rows in by_strategy.items():
        vals = [float(row["val"]) for row in rows if row.get("val") is not None]
        tests = [float(row["test"]) for row in rows if row.get("test") is not None]
        deltas = [float(row["delta_vs_parent"]) for row in rows if row.get("delta_vs_parent") is not None]
        wins = sum(1 for value in deltas if value > 0.0)
        strategy_stats[strategy] = {
            "n": len(rows),
            "family": rows[0]["family"],
            "mean_val": _mean(vals),
            "std_val": _std(vals),
            "mean_test": _mean(tests),
            "std_test": _std(tests),
            "mean_delta_vs_parent": _mean(deltas),
            "std_delta_vs_parent": _std(deltas),
            "win_rate_vs_parent": wins / len(deltas) if deltas else None,
            "best_node": max(rows, key=lambda row: row.get("val") if row.get("val") is not None else -1)["node"],
        }

    family_stats: dict[str, dict[str, Any]] = {}
    for family, rows in by_family.items():
        vals = [float(row["val"]) for row in rows if row.get("val") is not None]
        deltas = [float(row["delta_vs_parent"]) for row in rows if row.get("delta_vs_parent") is not None]
        wins = sum(1 for value in deltas if value > 0.0)
        family_stats[family] = {
            "n": len(rows),
            "mean_val": _mean(vals),
            "std_val": _std(vals),
            "mean_delta_vs_parent": _mean(deltas),
            "std_delta_vs_parent": _std(deltas),
            "win_rate_vs_parent": wins / len(deltas) if deltas else None,
        }

    policy = _empty_policy()
    findings: list[str] = []
    if best_root_val is not None and best_child_val is not None:
        delta = best_child_val - best_root_val
        if delta <= 0:
            findings.append("root_dominance: best generated child did not beat best root")
            policy["ranking_boosts"].update({
                "official_target_gene_head": 0.10,
                "official_target_low_rank_head": 0.08,
                "official_target_bilinear_head": 0.08,
                "official_aido_string_fusion": 0.08,
                "official_gene_dropout_augmentation": 0.06,
                "official_temperature_calibrated_head": 0.05,
            })
            policy["implementation_guidance"].append("Root-dominance observed: preserve the best parent dense branch and add the selected module as a residual/gated delta, not as a replacement.")
        else:
            findings.append(f"best_child_lift: best generated child beats best root by {delta:.4f} validation Macro-F1")
            policy["implementation_guidance"].append("A child beat the root: reuse its structural motif as a parent-preserving motif before broadening the search.")

    if best_root_test is not None and best_child_test is not None and best_child_val is not None and best_root_val is not None:
        val_lift = best_child_val - best_root_val
        test_lift = best_child_test - best_root_test
        if val_lift > 0 and test_lift < -0.005:
            findings.append("validation_test_divergence: best child improves validation but loses held-out test Macro-F1")
            policy["ranking_boosts"].update({
                "official_gene_dropout_augmentation": max(policy["ranking_boosts"].get("official_gene_dropout_augmentation", 0.0), 0.10),
                "official_temperature_calibrated_head": max(policy["ranking_boosts"].get("official_temperature_calibrated_head", 0.0), 0.08),
                "official_swa_or_checkpoint_ensemble": 0.08,
                "official_weighted_ce_training": 0.04,
            })
            policy["implementation_guidance"].append("Validation/test divergence observed: prioritize regularized residual gates, calibration, and seed checks; avoid unconstrained replacement heads.")

    for family, stats in family_stats.items():
        n = int(stats.get("n") or 0)
        mean_delta = stats.get("mean_delta_vs_parent")
        std_delta = stats.get("std_delta_vs_parent")
        win_rate = stats.get("win_rate_vs_parent")
        if n >= 3 and mean_delta is not None and std_delta is not None:
            if mean_delta > 0 and (std_delta > max(abs(mean_delta) * 1.5, 0.006) or (win_rate is not None and win_rate < 0.75)):
                findings.append(f"unstable_positive_family:{family}: mean_delta={mean_delta:.4f}, std={std_delta:.4f}, win_rate={win_rate}")
                policy["validation_recommendations"].append(f"Run multi-seed validation before promoting `{family}` motifs; positive average lift is not yet stable.")
                policy["ranking_boosts"].update({
                    "official_gene_dropout_augmentation": max(policy["ranking_boosts"].get("official_gene_dropout_augmentation", 0.0), 0.08),
                    "official_temperature_calibrated_head": max(policy["ranking_boosts"].get("official_temperature_calibrated_head", 0.0), 0.06),
                    "official_swa_or_checkpoint_ensemble": max(policy["ranking_boosts"].get("official_swa_or_checkpoint_ensemble", 0.0), 0.06),
                })
            if mean_delta < -0.005 and n >= 3:
                policy["ranking_penalties"][family] = max(policy["ranking_penalties"].get(family, 0.0), 0.08)
                findings.append(f"discouraged_family:{family}: repeated negative delta")

    if target_val_macro_f1 is not None and best_child_val is not None and best_child_val < target_val_macro_f1:
        gap = target_val_macro_f1 - best_child_val
        findings.append(f"target_gap: best child is {gap:.4f} below target validation Macro-F1")
        policy["implementation_guidance"].append("Target gap remains: favor competitive compositions that retain root performance and test one clear additional mechanism per rollout.")

    return {
        "format": "vc_demo_framework_feedback.v1",
        "created_at": _now(),
        "run_dir": str(run_dir),
        "target_val_macro_f1": target_val_macro_f1,
        "best_root": {"node": best_root[0], "val": best_root_val, "test": best_root_test},
        "best_child": {"node": best_child[0], "val": best_child_val, "test": best_child_test},
        "strategy_stats": strategy_stats,
        "family_stats": family_stats,
        "findings": findings,
        "policy": policy,
    }


def write_framework_feedback(run_dir: Path, feedback: dict[str, Any]) -> Path:
    path = run_dir / "framework_feedback.json"
    path.write_text(json.dumps(feedback, indent=2), encoding="utf-8")
    lines = [
        "# Framework Feedback",
        "",
        f"- Run dir: `{run_dir}`",
        f"- Best root: `{feedback.get('best_root', {}).get('node')}` val={feedback.get('best_root', {}).get('val')}",
        f"- Best child: `{feedback.get('best_child', {}).get('node')}` val={feedback.get('best_child', {}).get('val')}",
        "",
        "## Findings",
        "",
    ]
    for item in feedback.get("findings", []) or ["none"]:
        lines.append(f"- {item}")
    lines += ["", "## Policy", "", "### Ranking Boosts", ""]
    for key, value in sorted((feedback.get("policy", {}).get("ranking_boosts", {}) or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "### Ranking Penalties", ""]
    for key, value in sorted((feedback.get("policy", {}).get("ranking_penalties", {}) or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "### Implementation Guidance", ""]
    for item in feedback.get("policy", {}).get("implementation_guidance", []) or ["none"]:
        lines.append(f"- {item}")
    lines += ["", "### Validation Recommendations", ""]
    for item in feedback.get("policy", {}).get("validation_recommendations", []) or ["none"]:
        lines.append(f"- {item}")
    md_path = run_dir / "framework_feedback.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
