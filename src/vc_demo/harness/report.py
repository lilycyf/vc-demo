from __future__ import annotations

from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import artifact_usage_from_config
from vc_demo.harness.state import read_json


def _config_for(node: dict[str, Any]) -> dict[str, Any]:
    return read_json(Path(node["config"]))


def _pipeline_summary(node: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    if node.get("execution_backend") == "external_static_node" or cfg.get("execution", {}).get("backend") == "external_static_node":
        artifact_usage = node.get("artifact_usage") or cfg.get("execution", {}).get("artifact_usage", {})
        return {
            "pipeline_kind": "program_node",
            "loss_type": "external_static_node",
            "uses_real_artifact": bool(artifact_usage),
            "artifact_sides": ["external_public_best_node"],
            "artifact_manifest_path": str(node.get("external_script") or cfg.get("execution", {}).get("script_path", "")),
            "missing_required_artifacts": [],
            "required_artifacts": list(artifact_usage.keys()) if isinstance(artifact_usage, dict) else [],
        }
    pipeline = node.get("pipeline") or cfg.get("pipeline", {}) or {}
    if pipeline:
        return {
            "pipeline_kind": pipeline.get("pipeline_kind") or pipeline.get("kind", node.get("pipeline_kind", "model_only")),
            "loss_type": pipeline.get("loss_type", cfg.get("training", {}).get("loss_type", "cross_entropy")),
            "uses_real_artifact": bool(pipeline.get("uses_real_artifact")),
            "artifact_sides": pipeline.get("artifact_sides", []),
            "artifact_manifest_path": pipeline.get("artifact_manifest_path", ""),
            "missing_required_artifacts": pipeline.get("missing_required_artifacts", []),
            "required_artifacts": pipeline.get("required_artifacts", []),
        }
    usage = artifact_usage_from_config(cfg, {"strategy": node.get("strategy", "")})
    return {
        "pipeline_kind": node.get("pipeline_kind", "model_only"),
        "loss_type": usage.get("loss_type", cfg.get("training", {}).get("loss_type", "cross_entropy")),
        "uses_real_artifact": bool(usage.get("uses_real_artifact")),
        "artifact_sides": usage.get("artifact_sides", []),
        "artifact_manifest_path": usage.get("artifact_manifest_path", ""),
        "missing_required_artifacts": [],
        "required_artifacts": [],
    }


def trained_rows(tree: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, node in tree.get("nodes", {}).items():
        if node.get("status") != "trained":
            continue
        cfg = _config_for(node)
        data_cfg = cfg.get("data", {})
        model_cfg = cfg.get("model", {})
        training_cfg = cfg.get("training", {})
        pipeline_summary = _pipeline_summary(node, cfg)
        rows.append(
            {
                "iteration": int(node.get("iteration", 0)),
                "node": name,
                "parent": node.get("parent", ""),
                "agent_type": node.get("agent_type", "root"),
                "strategy": node.get("strategy", "root"),
                "node_kind": node.get("node_kind", "config_node" if node.get("parent") else "root"),
                "program_model_path": node.get("program_model_path", model_cfg.get("custom_model_path", "")),
                "pipeline_manifest_path": node.get("pipeline_manifest_path", cfg.get("pipeline_manifest_path", "")),
                "pipeline_kind": pipeline_summary.get("pipeline_kind", "model_only"),
                "loss_type": pipeline_summary.get("loss_type", "cross_entropy"),
                "uses_real_artifact": pipeline_summary.get("uses_real_artifact", False),
                "artifact_sides": ",".join(pipeline_summary.get("artifact_sides", [])),
                "artifact_manifest_path": pipeline_summary.get("artifact_manifest_path", ""),
                "missing_required_artifacts": ",".join(pipeline_summary.get("missing_required_artifacts", [])),
                "required_artifacts": ",".join(pipeline_summary.get("required_artifacts", [])),
                "duration_seconds": node.get("duration_seconds"),
                "test_metric_source": node.get("test_metric_source", ""),
                "execution_backend": node.get("execution_backend", cfg.get("execution", {}).get("backend", "native_train")),
                "data_dir": data_cfg.get("data_dir", "synthetic"),
                "model_type": model_cfg.get("model_type", "mlp"),
                "hidden_dim": model_cfg.get("hidden_dim"),
                "depth": model_cfg.get("depth"),
                "dropout": model_cfg.get("dropout"),
                "low_rank_dim": model_cfg.get("low_rank_dim", ""),
                "lr": training_cfg.get("lr"),
                "weight_decay": training_cfg.get("weight_decay"),
                "val": float(node["best_val_macro_f1"]),
                "test": float(node["test_macro_f1"]),
                "note": cfg.get("proposal_note", "root"),
            }
        )
    return sorted(rows, key=lambda row: (row["iteration"], row["node"]))


def write_summary(tree: dict[str, Any], summary_path: Path, failures: list[dict[str, Any]], stop_reason: str) -> None:
    rows = trained_rows(tree)
    roots = [row for row in rows if row["iteration"] == 0]
    best = max(rows, key=lambda row: row["val"]) if rows else None
    best_root = max(roots, key=lambda row: row["val"]) if roots else None

    lines = [
        "# VCHarness-Style K562 Search Summary",
        "",
        "This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.",
        "The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.",
        "",
        f"- Stop reason: {stop_reason}",
        f"- Trained nodes: {len(rows)}",
        f"- Failed nodes: {len(failures)}",
    ]
    if best:
        lines.append(f"- Best node: `{best['node']}` val={best['val']:.4f} test={best['test']:.4f}")
    if best and best_root:
        lines.append(f"- Best root: `{best_root['node']}` val={best_root['val']:.4f} test={best_root['test']:.4f}")
        lines.append(f"- Improvement over best root: {best['val'] - best_root['val']:.4f} validation Macro-F1")

    lines.extend(["", "## Root Baselines", "", "| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |", "|---|---|---|---:|---:|"])
    for row in roots:
        lines.append(f"| `{row['node']}` | `{row['data_dir']}` | {row['model_type']} | {row['val']:.4f} | {row['test']:.4f} |")

    lines.extend([
        "",
        "## All Trained Nodes",
        "",
        "| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |",
        "|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|",
    ])
    for row in rows:
        sec = "" if row["duration_seconds"] is None else f"{float(row['duration_seconds']):.1f}"
        missing = row["missing_required_artifacts"] or ""
        sides = row["artifact_sides"] or "none"
        lines.append(
            f"| {row['iteration']} | `{row['node']}` | `{row['parent']}` | {row['node_kind']} | {row['strategy']} | {row['execution_backend']} | {row['pipeline_kind']} | {row['loss_type']} | {sides} | {missing} | {sec} | {row['model_type']} | {row['val']:.4f} | {row['test']:.4f} |"
        )

    lines.extend(["", "## Artifact And Pipeline Audit", "", "| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |", "|---|---:|---|---|---|---|---|---|"])
    for row in rows:
        manifest = row["artifact_manifest_path"] or ""
        lines.append(f"| `{row['node']}` | {str(row['uses_real_artifact']).lower()} | {row['artifact_sides'] or 'none'} | {row['required_artifacts']} | {row['missing_required_artifacts']} | `{manifest}` | {row['loss_type']} | {row['test_metric_source']} |")

    lines.extend(["", "## Best-So-Far Curve", "", "| Iter | Best val Macro-F1 |", "|---:|---:|"])
    best_so_far = -1.0
    for row in rows:
        best_so_far = max(best_so_far, row["val"])
        lines.append(f"| {row['iteration']} | {best_so_far:.4f} |")

    lines.extend(["", "## Tree", ""])

    def append_tree(name: str, depth: int) -> None:
        node = tree["nodes"][name]
        label = f"{'  ' * depth}- `{name}` status={node.get('status')} visits={node.get('visits')}"
        if node.get("status") == "trained":
            label += f" val={node['best_val_macro_f1']:.4f} test={node['test_macro_f1']:.4f}"
        if node.get("strategy"):
            label += f" strategy={node['strategy']}"
        if node.get("program_model_path"):
            label += f" program={node['program_model_path']}"
        if node.get("execution_backend"):
            label += f" backend={node['execution_backend']}"
        if node.get("pipeline_kind"):
            label += f" pipeline={node['pipeline_kind']}"
        if node.get("pipeline", {}).get("artifact_sides"):
            label += f" artifacts={','.join(node['pipeline']['artifact_sides'])}"
        lines.append(label)
        for child in node.get("children", []):
            append_tree(child, depth + 1)

    for root in tree.get("root_nodes", []):
        append_tree(root, 0)

    if failures:
        lines.extend(["", "## Failures", "", "| Node | Parent | Error |", "|---|---|---|"])
        for failure in failures:
            err = str(failure.get("error", "")).replace("|", " ").splitlines()[-1]
            lines.append(f"| `{failure.get('node')}` | `{failure.get('parent')}` | {err} |")

    lines.extend([
        "",
        "## Reproducibility Notes",
        "",
        "- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.",
        "- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.",
        "- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.",
        "- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.",
        "- The proposal agent decides how to modify that parent into one executable child config or node-local model program.",
        "- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.",
    ])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
