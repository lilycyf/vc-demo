from __future__ import annotations

import argparse
import json
import math
import random
import shutil
from copy import deepcopy
from pathlib import Path

from vc_demo.train import load_config, train


def uct_score(node: dict, parent_visits: int, exploration: float) -> float:
    visits = max(int(node.get("visits", 0)), 1)
    value = float(node.get("value", 0.0))
    return value / visits + exploration * math.sqrt(math.log(max(parent_visits, 2)) / visits)


def propose_child_config(parent_config: dict, child_index: int, rng: random.Random) -> dict:
    child = deepcopy(parent_config)
    child["node_name"] = f"{parent_config.get('node_name', 'node')}_child_{child_index}"
    child.setdefault("model", {})
    child.setdefault("training", {})

    mutation = rng.choice(["hidden_dim", "dropout", "depth", "lr", "weight_decay"])
    if mutation == "hidden_dim":
        child["model"]["hidden_dim"] = rng.choice([128, 192, 256, 384, 512])
    elif mutation == "dropout":
        child["model"]["dropout"] = rng.choice([0.0, 0.05, 0.1, 0.2, 0.35])
    elif mutation == "depth":
        child["model"]["depth"] = rng.choice([1, 2, 3, 4])
    elif mutation == "lr":
        child["training"]["lr"] = rng.choice([1e-4, 2e-4, 3e-4, 5e-4, 8e-4])
    elif mutation == "weight_decay":
        child["training"]["weight_decay"] = rng.choice([0.0, 1e-5, 1e-4, 5e-4, 1e-3])
    child["proposal_note"] = f"mutated {mutation} from parent {parent_config.get('node_name', 'node')}"
    return child


def load_tree(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"root": "root_mlp", "nodes": {}}


def metrics_path(run_dir: Path, node_name: str) -> Path:
    return run_dir / "nodes" / node_name / "metrics.json"


def node_output_dir(run_dir: Path, node_name: str) -> Path:
    return run_dir / "nodes" / node_name


def reward_from_metrics(metrics: dict) -> float:
    return float(metrics["best_val_macro_f1"])


def read_metrics(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def ensure_root_trained(nodes: dict, run_dir: Path, max_epochs: int | None) -> dict:
    root_name = "root_mlp"
    root_cfg_path = Path("configs/root_mlp.json")
    root = nodes.setdefault(
        root_name,
        {"config": str(root_cfg_path), "visits": 0, "value": 0.0, "children": [], "status": "pending"},
    )
    metrics = read_metrics(metrics_path(run_dir, root_name))
    if metrics is None:
        metrics = train(load_config(Path(root["config"])), node_output_dir(run_dir, root_name), max_epochs=max_epochs)
    reward = reward_from_metrics(metrics)
    root.update(
        {
            "status": "trained",
            "metrics": str(metrics_path(run_dir, root_name)),
            "best_val_macro_f1": metrics["best_val_macro_f1"],
            "test_macro_f1": metrics["test_macro_f1"],
            "visits": max(int(root.get("visits", 0)), 1),
            "value": max(float(root.get("value", 0.0)), reward),
        }
    )
    return metrics


def select_path(tree: dict, exploration: float) -> list[str]:
    nodes = tree["nodes"]
    path = [tree["root"]]
    while True:
        current = nodes[path[-1]]
        trained_children = [
            child
            for child in current.get("children", [])
            if nodes.get(child, {}).get("status") == "trained" and int(nodes[child].get("visits", 0)) > 0
        ]
        if not trained_children:
            return path

        parent_visits = max(int(current.get("visits", 1)), 1)
        best_child = max(trained_children, key=lambda name: uct_score(nodes[name], parent_visits, exploration))
        best_score = uct_score(nodes[best_child], parent_visits, exploration)
        current_score = float(current.get("value", 0.0)) / max(int(current.get("visits", 1)), 1)

        # Expand below a strong child; otherwise keep exploring the current node.
        if best_score <= current_score:
            return path
        path.append(best_child)


def backpropagate(tree: dict, path: list[str], reward: float) -> None:
    for name in path:
        node = tree["nodes"][name]
        node["visits"] = int(node.get("visits", 0)) + 1
        node["value"] = float(node.get("value", 0.0)) + reward


def write_summary(tree: dict, summary_path: Path) -> None:
    rows: list[dict] = []
    for name, node in tree["nodes"].items():
        metrics = read_metrics(Path(node["metrics"])) if node.get("metrics") else None
        if metrics is None:
            continue
        cfg = json.loads(Path(node["config"]).read_text())
        rows.append(
            {
                "iteration": node.get("iteration", 0),
                "node": name,
                "parent": node.get("parent", ""),
                "hidden_dim": cfg.get("model", {}).get("hidden_dim"),
                "depth": cfg.get("model", {}).get("depth"),
                "dropout": cfg.get("model", {}).get("dropout"),
                "lr": cfg.get("training", {}).get("lr"),
                "weight_decay": cfg.get("training", {}).get("weight_decay"),
                "val": metrics["best_val_macro_f1"],
                "test": metrics["test_macro_f1"],
                "note": cfg.get("proposal_note", "root"),
            }
        )
    rows.sort(key=lambda row: (row["iteration"], row["node"]))

    best = -1.0
    curve: list[str] = []
    for row in rows:
        best = max(best, row["val"])
        curve.append(f"{row['iteration']}:{best:.4f}")

    lines = [
        "# Synthetic MCTS Demo Summary",
        "",
        "This run uses only the deterministic synthetic perturbation dataset. Each MCTS iteration selects a trained node, generates one child config, trains that child, reads its metrics, and backpropagates validation Macro-F1 through the tree.",
        "",
        f"- Trained nodes: {len(rows)}",
        f"- Best validation Macro-F1: {max((row['val'] for row in rows), default=0.0):.4f}",
        f"- Best-so-far curve: `{', '.join(curve)}`",
        "",
        "| Iter | Node | Parent | Hidden | Depth | Dropout | LR | Weight decay | Val Macro-F1 | Test Macro-F1 | Note |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {iteration} | `{node}` | `{parent}` | {hidden_dim} | {depth} | {dropout} | {lr} | {weight_decay} | {val:.4f} | {test:.4f} | {note} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Best-So-Far Curve",
            "",
            "| Iter | Best val Macro-F1 |",
            "|---:|---:|",
        ]
    )
    best = -1.0
    for row in rows:
        best = max(best, row["val"])
        lines.append(f"| {row['iteration']} | {best:.4f} |")

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a cheap synthetic MCTS train/evaluate loop.")
    parser.add_argument("--tree", type=Path, default=Path("experiments/tree.json"))
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--exploration", type=float, default=1.2)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--summary", type=Path, default=Path("experiments/synthetic_mcts_summary.md"))
    parser.add_argument("--reset", action="store_true", help="Start from a clean synthetic demo tree and node outputs.")
    args = parser.parse_args()

    if args.reset:
        shutil.rmtree(args.tree.parent / "nodes", ignore_errors=True)
        shutil.rmtree(args.tree.parent / "proposals", ignore_errors=True)
        args.tree.unlink(missing_ok=True)
        args.summary.unlink(missing_ok=True)

    rng = random.Random(args.seed)
    tree = load_tree(args.tree)
    run_dir = args.tree.parent
    proposal_dir = run_dir / "proposals"
    proposal_dir.mkdir(parents=True, exist_ok=True)

    root_cfg_path = Path("configs/root_mlp.json")
    nodes = tree.setdefault("nodes", {})
    nodes.setdefault("root_mlp", {"config": str(root_cfg_path), "visits": 0, "value": 0.0, "children": []})
    tree["root"] = "root_mlp"
    ensure_root_trained(nodes, run_dir, args.max_epochs)

    created: list[str] = []
    for step in range(1, args.steps + 1):
        path = select_path(tree, args.exploration)
        parent_name = path[-1]
        parent = nodes[parent_name]
        parent_config = json.loads(Path(parent["config"]).read_text())
        child_config = propose_child_config(parent_config, len(parent.get("children", [])) + 1, rng)
        child_name = child_config["node_name"]
        child_path = proposal_dir / f"{child_name}.json"
        child_path.write_text(json.dumps(child_config, indent=2), encoding="utf-8")

        parent.setdefault("children", []).append(child_name)
        nodes[child_name] = {
            "config": str(child_path),
            "parent": parent_name,
            "visits": 0,
            "value": 0.0,
            "children": [],
            "status": "training",
            "iteration": step,
        }
        metrics = train(child_config, node_output_dir(run_dir, child_name), max_epochs=args.max_epochs)
        reward = reward_from_metrics(metrics)
        nodes[child_name].update(
            {
                "status": "trained",
                "metrics": str(metrics_path(run_dir, child_name)),
                "best_val_macro_f1": metrics["best_val_macro_f1"],
                "test_macro_f1": metrics["test_macro_f1"],
                "visits": 1,
                "value": reward,
            }
        )
        backpropagate(tree, path, reward)
        created.append(str(child_path))

    args.tree.write_text(json.dumps(tree, indent=2), encoding="utf-8")
    write_summary(tree, args.summary)
    print(json.dumps({"tree": str(args.tree), "created": created, "summary": str(args.summary)}, indent=2))


if __name__ == "__main__":
    main()
