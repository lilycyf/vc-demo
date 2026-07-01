from __future__ import annotations

import argparse
import json
import random
import traceback
from pathlib import Path

from vc_demo.mcts import propose_child_config, uct_score
from vc_demo.train import load_config, train


def metrics_path(run_dir: Path, node_name: str) -> Path:
    return run_dir / "nodes" / node_name / "metrics.json"


def node_output_dir(run_dir: Path, node_name: str) -> Path:
    return run_dir / "nodes" / node_name


def read_metrics(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def reward(metrics: dict) -> float:
    return float(metrics["best_val_macro_f1"])


def train_node(config_path: Path, output_dir: Path, max_epochs: int | None) -> dict:
    metrics = read_metrics(output_dir / "metrics.json")
    if metrics is not None:
        return metrics
    return train(load_config(config_path), output_dir, max_epochs=max_epochs)


def init_roots(root_configs: list[Path], run_dir: Path, max_epochs: int | None) -> dict:
    tree = {"root_nodes": [], "nodes": {}}
    for cfg_path in root_configs:
        cfg = load_config(cfg_path)
        name = str(cfg.get("node_name", cfg_path.stem))
        metrics = train_node(cfg_path, node_output_dir(run_dir, name), max_epochs=max_epochs)
        tree["root_nodes"].append(name)
        tree["nodes"][name] = {
            "config": str(cfg_path),
            "parent": "",
            "children": [],
            "status": "trained",
            "iteration": 0,
            "metrics": str(metrics_path(run_dir, name)),
            "best_val_macro_f1": metrics["best_val_macro_f1"],
            "test_macro_f1": metrics["test_macro_f1"],
            "visits": 1,
            "value": reward(metrics),
        }
    return tree


def candidate_parents(tree: dict, max_children: int) -> list[str]:
    names = []
    for name, node in tree["nodes"].items():
        if node.get("status") != "trained":
            continue
        if len(node.get("children", [])) < max_children:
            names.append(name)
    if names:
        return names
    return [name for name, node in tree["nodes"].items() if node.get("status") == "trained"]


def select_parent(tree: dict, exploration: float, max_children: int) -> str:
    candidates = candidate_parents(tree, max_children)
    total_visits = sum(int(node.get("visits", 0)) for node in tree["nodes"].values()) + 1
    return max(candidates, key=lambda name: uct_score(tree["nodes"][name], total_visits, exploration))


def update_ancestors(tree: dict, node_name: str, value: float) -> None:
    current = node_name
    while current:
        node = tree["nodes"][current]
        node["visits"] = int(node.get("visits", 0)) + 1
        node["value"] = float(node.get("value", 0.0)) + value
        current = node.get("parent", "")


def rows_for_summary(tree: dict) -> list[dict]:
    rows = []
    for name, node in tree["nodes"].items():
        if node.get("status") != "trained":
            continue
        cfg = load_config(Path(node["config"]))
        data_cfg = cfg.get("data", {})
        model_cfg = cfg.get("model", {})
        training_cfg = cfg.get("training", {})
        rows.append(
            {
                "iteration": int(node.get("iteration", 0)),
                "node": name,
                "parent": node.get("parent", ""),
                "data_dir": data_cfg.get("data_dir", "synthetic"),
                "hidden_dim": model_cfg.get("hidden_dim"),
                "depth": model_cfg.get("depth"),
                "dropout": model_cfg.get("dropout"),
                "lr": training_cfg.get("lr"),
                "weight_decay": training_cfg.get("weight_decay"),
                "val": float(node["best_val_macro_f1"]),
                "test": float(node["test_macro_f1"]),
            }
        )
    return sorted(rows, key=lambda row: (row["iteration"], row["node"]))


def write_summary(tree: dict, summary_path: Path, failures: list[dict], stop_reason: str) -> None:
    rows = rows_for_summary(tree)
    best = max(rows, key=lambda row: row["val"]) if rows else None
    roots = [row for row in rows if row["iteration"] == 0]
    best_root = max(roots, key=lambda row: row["val"]) if roots else None
    best_so_far = -1.0
    curve = []
    for row in rows:
        best_so_far = max(best_so_far, row["val"])
        curve.append((row["iteration"], best_so_far))

    lines = [
        "# K562 Multi-Feature Search Summary",
        "",
        "This search trains multiple real-data K562 root configs, then expands candidate child nodes with an MCTS-style UCT policy.",
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
    lines.extend(["", "## Root Baselines", "", "| Node | Data dir | Val Macro-F1 | Test Macro-F1 |", "|---|---|---:|---:|"])
    for row in roots:
        lines.append(f"| `{row['node']}` | `{row['data_dir']}` | {row['val']:.4f} | {row['test']:.4f} |")

    lines.extend(["", "## All Trained Nodes", "", "| Iter | Node | Parent | Data dir | Hidden | Depth | Dropout | LR | Weight decay | Val | Test |", "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|"])
    for row in rows:
        lines.append(
            f"| {row['iteration']} | `{row['node']}` | `{row['parent']}` | `{row['data_dir']}` | {row['hidden_dim']} | {row['depth']} | {row['dropout']} | {row['lr']} | {row['weight_decay']} | {row['val']:.4f} | {row['test']:.4f} |"
        )

    lines.extend(["", "## Best-So-Far Curve", "", "| Iter | Best val Macro-F1 |", "|---:|---:|"])
    for iteration, value in curve:
        lines.append(f"| {iteration} | {value:.4f} |")

    lines.extend(["", "## Tree", ""])
    def append_tree(name: str, depth: int) -> None:
        node = tree["nodes"][name]
        label = f"{'  ' * depth}- `{name}` status={node.get('status')} visits={node.get('visits')}"
        if node.get("status") == "trained":
            label += f" val={node['best_val_macro_f1']:.4f} test={node['test_macro_f1']:.4f}"
        lines.append(label)
        for child in node.get("children", []):
            append_tree(child, depth + 1)
    for root in tree.get("root_nodes", []):
        append_tree(root, 0)

    if failures:
        lines.extend(["", "## Failures", "", "| Node | Parent | Error |", "|---|---|---|"])
        for failure in failures:
            err = failure["error"].replace("|", " ").splitlines()[-1]
            lines.append(f"| `{failure['node']}` | `{failure['parent']}` | {err} |")

    lines.extend([
        "",
        "## Limitations",
        "",
        "This is a single-cell-line K562 search. It is not the paper's four-cell-line benchmark, and current child generation is rule-based rather than an AI coding agent that edits model code.",
    ])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_search(args: argparse.Namespace) -> dict:
    run_dir = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    proposal_dir = run_dir / "proposals"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    tree_path = run_dir / "tree.json"
    if args.reset and tree_path.exists():
        tree_path.unlink()
    if args.reset:
        import shutil
        shutil.rmtree(run_dir / "nodes", ignore_errors=True)
        shutil.rmtree(proposal_dir, ignore_errors=True)
        proposal_dir.mkdir(parents=True, exist_ok=True)

    root_configs = [Path(path) for path in args.root_configs]
    tree = init_roots(root_configs, run_dir, args.max_epochs)
    rng = random.Random(args.seed)
    failures: list[dict] = []
    best_val = max(node["best_val_macro_f1"] for node in tree["nodes"].values())
    no_improve = 0
    stop_reason = "budget exhausted"

    for iteration in range(1, args.budget_nodes + 1):
        parent_name = select_parent(tree, args.exploration, args.max_children)
        parent = tree["nodes"][parent_name]
        parent_config = load_config(Path(parent["config"]))
        child_config = propose_child_config(parent_config, len(parent.get("children", [])) + 1, rng)
        child_name = child_config["node_name"]
        child_path = proposal_dir / f"{child_name}.json"
        child_path.write_text(json.dumps(child_config, indent=2), encoding="utf-8")
        parent.setdefault("children", []).append(child_name)
        tree["nodes"][child_name] = {"config": str(child_path), "parent": parent_name, "children": [], "status": "training", "iteration": iteration, "visits": 0, "value": 0.0}
        try:
            metrics = train(child_config, node_output_dir(run_dir, child_name), max_epochs=args.max_epochs)
            val = reward(metrics)
            tree["nodes"][child_name].update({"status": "trained", "metrics": str(metrics_path(run_dir, child_name)), "best_val_macro_f1": metrics["best_val_macro_f1"], "test_macro_f1": metrics["test_macro_f1"], "visits": 1, "value": val})
            update_ancestors(tree, parent_name, val)
            if val > best_val + args.min_delta:
                best_val = val
                no_improve = 0
            else:
                no_improve += 1
        except Exception as exc:
            error = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            tree["nodes"][child_name].update({"status": "failed", "error": error})
            failures.append({"node": child_name, "parent": parent_name, "error": error})
            no_improve += 1
        tree_path.write_text(json.dumps(tree, indent=2), encoding="utf-8")
        if args.stop_no_improve and no_improve >= args.stop_no_improve:
            stop_reason = f"no improvement for {no_improve} nodes"
            break

    tree_path.write_text(json.dumps(tree, indent=2), encoding="utf-8")
    write_summary(tree, args.summary, failures, stop_reason)
    result = {"tree": str(tree_path), "summary": str(args.summary), "stop_reason": stop_reason, "failures": len(failures)}
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a multi-root K562 real-data search.")
    parser.add_argument("--root-configs", nargs="+", required=True)
    parser.add_argument("--run-dir", type=Path, default=Path("experiments/k562_real_features"))
    parser.add_argument("--summary", type=Path, default=Path("experiments/k562_real_features/search_summary.md"))
    parser.add_argument("--budget-nodes", type=int, default=20)
    parser.add_argument("--max-epochs", type=int, default=2)
    parser.add_argument("--max-children", type=int, default=3)
    parser.add_argument("--exploration", type=float, default=1.2)
    parser.add_argument("--stop-no-improve", type=int, default=6)
    parser.add_argument("--min-delta", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    run_search(args)


if __name__ == "__main__":
    main()
