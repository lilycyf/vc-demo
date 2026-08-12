from __future__ import annotations

import argparse
import copy
import json
import math
import random
import shutil
import time
from pathlib import Path
from typing import Any

from vc_demo.train import train

SEARCH_TRANSFORMS = [
    {"id": "backbone_residual", "priority": 0.90, "cost": "medium"},
    {"id": "backbone_gated", "priority": 0.88, "cost": "medium"},
    {"id": "low_rank_head", "priority": 0.76, "cost": "cheap"},
    {"id": "mixture_of_experts", "priority": 0.82, "cost": "medium"},
    {"id": "film_residual", "priority": 0.80, "cost": "medium"},
    {"id": "temperature_calibration", "priority": 0.70, "cost": "cheap"},
    {"id": "feature_dropout", "priority": 0.72, "cost": "cheap"},
    {"id": "capacity_wide", "priority": 0.68, "cost": "medium"},
    {"id": "capacity_deep", "priority": 0.64, "cost": "medium"},
    {"id": "optimizer_low_lr", "priority": 0.58, "cost": "cheap"},
    {"id": "optimizer_high_lr", "priority": 0.56, "cost": "cheap"},
    {"id": "dropout_low", "priority": 0.60, "cost": "cheap"},
    {"id": "dropout_high", "priority": 0.52, "cost": "cheap"},
    {"id": "weighted_ce", "priority": 0.66, "cost": "cheap"},
    {"id": "focal_loss", "priority": 0.62, "cost": "cheap"},
]

MODEL_FOR_TRANSFORM = {
    "backbone_residual": "residual_mlp",
    "backbone_gated": "gated_mlp",
    "low_rank_head": "low_rank_mlp",
    "mixture_of_experts": "mixture_of_experts_mlp",
    "film_residual": "film_residual_mlp",
    "temperature_calibration": "temperature_calibrated_mlp",
    "feature_dropout": "feature_dropout_mlp",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_config(config: dict[str, Any], run_dir: Path, max_epochs: int) -> dict[str, Any]:
    out = run_dir / "nodes" / str(config["node_name"])
    started = time.time()
    metrics = train(config, out, max_epochs=max_epochs)
    metrics["duration_seconds"] = time.time() - started
    metrics["metrics_path"] = str(out / "metrics.json")
    return metrics


def add_node(tree: dict[str, Any], name: str, config_path: Path, parent: str, status: str, metrics: dict[str, Any] | None = None, proposal: dict[str, Any] | None = None) -> None:
    row = {"config": str(config_path), "parent": parent, "children": [], "status": status, "visits": 0, "value": 0.0}
    if metrics:
        row.update({"best_val_macro_f1": metrics["best_val_macro_f1"], "test_macro_f1": metrics["test_macro_f1"], "metrics": metrics.get("metrics_path", ""), "visits": 1, "value": float(metrics["best_val_macro_f1"])})
    if proposal:
        row.update({"strategy": proposal["strategy"], "proposal": str(config_path.parent / f"{name}.proposal.json"), "cheap_screen_score": proposal.get("cheap_screen_score", {})})
    tree["nodes"][name] = row
    if parent:
        tree["nodes"][parent].setdefault("children", []).append(name)
    else:
        tree.setdefault("root_nodes", []).append(name)


def backprop(tree: dict[str, Any], node: str, reward: float) -> None:
    path = []
    cur = node
    while cur:
        path.append(cur)
        row = tree["nodes"][cur]
        row["visits"] = int(row.get("visits", 0)) + 1
        row["value"] = float(row.get("value", 0.0)) + reward
        cur = str(row.get("parent") or "")
    tree["last_backprop_path"] = path


def uct_select_parent(tree: dict[str, Any], max_children: int, exploration: float) -> str:
    candidates = []
    total = sum(max(1, int(n.get("visits", 0))) for n in tree["nodes"].values() if n.get("status") == "trained")
    for name, node in tree["nodes"].items():
        if node.get("status") != "trained":
            continue
        if len(node.get("children", [])) >= max_children:
            continue
        visits = max(1, int(node.get("visits", 1)))
        q = float(node.get("value", 0.0)) / visits
        score = q + exploration * math.sqrt(math.log(total + 1.0) / visits)
        candidates.append((score, name))
    if not candidates:
        raise RuntimeError("no expandable trained parent remains")
    return sorted(candidates, reverse=True)[0][1]


def apply_transform(parent: dict[str, Any], transform_id: str, child_name: str) -> dict[str, Any]:
    cfg = copy.deepcopy(parent)
    cfg["node_name"] = child_name
    model = cfg.setdefault("model", {})
    training = cfg.setdefault("training", {})
    if transform_id in MODEL_FOR_TRANSFORM:
        model["model_type"] = MODEL_FOR_TRANSFORM[transform_id]
    if transform_id == "capacity_wide":
        model["hidden_dim"] = min(max(int(model.get("hidden_dim", 256)) * 2, 256), 1024)
    if transform_id == "capacity_deep":
        model["depth"] = min(int(model.get("depth", 2)) + 1, 5)
    if transform_id == "dropout_low":
        model["dropout"] = max(0.0, float(model.get("dropout", 0.1)) - 0.1)
    if transform_id == "dropout_high":
        model["dropout"] = min(0.5, float(model.get("dropout", 0.1)) + 0.15)
    if transform_id == "optimizer_low_lr":
        training["lr"] = max(5e-5, float(training.get("lr", 3e-4)) * 0.5)
    if transform_id == "optimizer_high_lr":
        training["lr"] = min(1e-3, float(training.get("lr", 3e-4)) * 1.7)
    if transform_id == "weighted_ce":
        training["loss_type"] = "weighted_cross_entropy"
        n_classes = model.get("n_classes", 12)
        n_classes = 12 if n_classes == "auto" else int(n_classes)
        training["class_weights"] = [1.0] * n_classes
    if transform_id == "focal_loss":
        training["loss_type"] = "focal_loss"
        training["focal_gamma"] = 2.0
    if transform_id == "low_rank_head":
        model["low_rank_dim"] = min(max(int(model.get("low_rank_dim", 32)), 8), 64)
    return cfg


def cheap_score(transform: dict[str, Any], parent_val: float, seen_strategy_count: int) -> dict[str, Any]:
    cost_bonus = {"cheap": 0.04, "medium": 0.0, "expensive": -0.05}.get(transform.get("cost"), 0.0)
    novelty = 0.08 if seen_strategy_count == 0 else -0.04 * seen_strategy_count
    score = parent_val + float(transform["priority"]) * 0.1 + cost_bonus + novelty
    return {"score": score, "parent_val": parent_val, "priority": transform["priority"], "cost_bonus": cost_bonus, "novelty": novelty}


def best_rows(tree: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    trained = [(name, n) for name, n in tree["nodes"].items() if n.get("status") == "trained"]
    best_root = max(((name, n) for name, n in trained if not n.get("parent")), key=lambda x: x[1].get("best_val_macro_f1", -1))[1]
    children = [(name, n) for name, n in trained if n.get("parent")]
    best_child = max(children, key=lambda x: x[1].get("best_val_macro_f1", -1))[1] if children else None
    return best_root, best_child


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small VCHarness-style HELF drug identity demo.")
    parser.add_argument("--root-configs", nargs="+", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--experiment", default="helf_drug_harness_demo")
    parser.add_argument("--budget-proposals", type=int, default=48)
    parser.add_argument("--budget-trained-nodes", type=int, default=16)
    parser.add_argument("--candidate-pool-size", type=int, default=4)
    parser.add_argument("--max-children", type=int, default=6)
    parser.add_argument("--max-epochs", type=int, default=6)
    parser.add_argument("--exploration", type=float, default=1.2)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.reset and args.run_dir.exists():
        shutil.rmtree(args.run_dir)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    proposal_dir = args.run_dir / "proposals"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    tree = {"experiment": args.experiment, "task_id": "HELF_DRUG", "nodes": {}, "root_nodes": [], "events": []}
    rng = random.Random(args.seed)

    for root in args.root_configs:
        cfg_path = Path(root)
        cfg = read_json(cfg_path)
        metrics = run_config(cfg, args.run_dir, args.max_epochs)
        add_node(tree, cfg["node_name"], cfg_path, "", "trained", metrics)
    generated = trained_children = failed = 0
    strategy_counts: dict[str, int] = {}
    queued: list[tuple[float, str]] = []
    stop_reason = "budget exhausted"

    while generated < args.budget_proposals or queued:
        if trained_children >= args.budget_trained_nodes:
            stop_reason = f"trained-node budget exhausted ({trained_children}/{args.budget_trained_nodes})"
            break
        if generated < args.budget_proposals:
            parent = uct_select_parent(tree, args.max_children, args.exploration)
            parent_cfg = read_json(Path(tree["nodes"][parent]["config"]))
            parent_val = float(tree["nodes"][parent].get("best_val_macro_f1", 0.0))
            transforms = SEARCH_TRANSFORMS[:]
            rng.shuffle(transforms)
            transforms = sorted(transforms, key=lambda t: cheap_score(t, parent_val, strategy_counts.get(t["id"], 0))["score"], reverse=True)
            for rank, transform in enumerate(transforms[: args.candidate_pool_size], start=1):
                if generated >= args.budget_proposals:
                    break
                generated += 1
                child = f"{parent}_p{generated}_{transform['id']}"
                cfg = apply_transform(parent_cfg, transform["id"], child)
                proposal = {"strategy": transform["id"], "parent": parent, "child": child, "candidate_rank": rank, "candidate_pool_size": args.candidate_pool_size, "cheap_screen_score": cheap_score(transform, parent_val, strategy_counts.get(transform["id"], 0)), "hypothesis": f"Test {transform['id']} for HELF drug identity prediction."}
                cfg_path = proposal_dir / f"{child}.json"
                prop_path = proposal_dir / f"{child}.proposal.json"
                write_json(cfg_path, cfg)
                write_json(prop_path, proposal)
                add_node(tree, child, cfg_path, parent, "candidate_queued", proposal=proposal)
                queued.append((proposal["cheap_screen_score"]["score"], child))
            write_json(args.run_dir / "tree.json", tree)
        if not queued:
            stop_reason = f"proposal budget exhausted ({generated}/{args.budget_proposals})"
            break
        queued.sort(reverse=True)
        _, selected = queued.pop(0)
        node = tree["nodes"][selected]
        proposal = read_json(Path(node["proposal"]))
        node["status"] = "selected_for_training"
        try:
            metrics = run_config(read_json(Path(node["config"])), args.run_dir, args.max_epochs)
            node.update({"status": "trained", "best_val_macro_f1": metrics["best_val_macro_f1"], "test_macro_f1": metrics["test_macro_f1"], "metrics": metrics.get("metrics_path", str(args.run_dir / "nodes" / selected / "metrics.json")), "visits": 1, "value": float(metrics["best_val_macro_f1"])})
            strategy_counts[proposal["strategy"]] = strategy_counts.get(proposal["strategy"], 0) + 1
            backprop(tree, selected, float(metrics["best_val_macro_f1"]))
            trained_children += 1
        except Exception as exc:
            node.update({"status": "failed", "error": repr(exc)})
            failed += 1
        write_json(args.run_dir / "tree.json", tree)

    for _, name in queued:
        if tree["nodes"].get(name, {}).get("status") == "candidate_queued":
            tree["nodes"][name]["status"] = "pruned_not_selected"
            tree["nodes"][name]["pruned_reason"] = "not selected before trained-node budget/stop condition"
    best_root, best_child = best_rows(tree)
    summary = {
        "experiment": args.experiment,
        "run_dir": str(args.run_dir),
        "stop_reason": stop_reason,
        "generated_proposals": generated,
        "trained_selected_rollouts": trained_children,
        "pruned_not_selected": sum(1 for n in tree["nodes"].values() if n.get("status") == "pruned_not_selected"),
        "failed": failed,
        "best_root": best_root,
        "best_generated_child": best_child,
        "fallback_count": 0,
        "artifact_blockers": 0,
    }
    write_json(args.run_dir / "tree.json", tree)
    write_json(args.run_dir / "run_manifest.json", summary)
    lines = ["# HELF Drug Harness Demo Report", "", f"- Stop reason: `{stop_reason}`", f"- Generated proposals: `{generated}`", f"- Trained selected rollouts: `{trained_children}`", f"- Pruned not selected: `{summary['pruned_not_selected']}`", f"- Failed: `{failed}`", "", "## Best Root", "", f"- Val Macro-F1: `{best_root.get('best_val_macro_f1')}`", f"- Test Macro-F1: `{best_root.get('test_macro_f1')}`", "", "## Best Generated Child", ""]
    if best_child:
        lines += [f"- Strategy: `{best_child.get('strategy')}`", f"- Val Macro-F1: `{best_child.get('best_val_macro_f1')}`", f"- Test Macro-F1: `{best_child.get('test_macro_f1')}`"]
    else:
        lines.append("No generated child was trained.")
    (args.run_dir / "final_report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
