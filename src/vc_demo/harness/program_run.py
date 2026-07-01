from __future__ import annotations

import argparse
import json
import random
import traceback
from pathlib import Path
from typing import Any

from vc_demo.harness.executor import run_node
from vc_demo.harness.mcts import backpropagate, select_parent
from vc_demo.harness.program_agent import propose_program_child
from vc_demo.harness.report import write_summary
from vc_demo.harness.state import empty_tree, read_json, reset_run_dir, write_json


def reward(metrics: dict[str, Any]) -> float:
    return float(metrics["best_val_macro_f1"])


def add_trained_node(tree: dict[str, Any], name: str, config_path: Path, parent: str, iteration: int, metrics: dict[str, Any], proposal: dict[str, Any] | None = None) -> None:
    node = {
        "config": str(config_path),
        "parent": parent,
        "children": [],
        "status": "trained",
        "iteration": iteration,
        "metrics": str(config_path.parent.parent / "nodes" / name / "metrics.json") if "proposals" in config_path.parts else "",
        "best_val_macro_f1": metrics["best_val_macro_f1"],
        "test_macro_f1": metrics["test_macro_f1"],
        "visits": 1,
        "value": reward(metrics),
    }
    if proposal:
        node["agent_type"] = proposal.get("agent_type")
        node["node_kind"] = proposal.get("node_kind")
        node["strategy"] = proposal.get("strategy")
        node["proposal"] = str(config_path.parent / f"{name}.proposal.json")
        node["program_dir"] = proposal.get("program_dir")
        node["program_model_path"] = proposal.get("program_model_path")
    tree["nodes"][name] = node
    if parent:
        tree["nodes"][parent].setdefault("children", []).append(name)
    else:
        tree.setdefault("root_nodes", []).append(name)


def train_roots(root_configs: list[Path], run_dir: Path, tree: dict[str, Any], max_epochs: int | None) -> None:
    for root_config in root_configs:
        config = read_json(root_config)
        name = str(config.get("node_name", root_config.stem))
        metrics = run_node(config, run_dir, proposal=None, max_epochs=max_epochs)
        add_trained_node(tree, name, root_config, parent="", iteration=0, metrics=metrics)


def write_tree_and_failures(run_dir: Path, tree: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    write_json(run_dir / "tree.json", tree)
    write_json(run_dir / "failures.json", {"failures": failures})


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.reset:
        reset_run_dir(run_dir)
    program_root = run_dir / "programs"
    program_root.mkdir(parents=True, exist_ok=True)

    tree = empty_tree(args.experiment)
    failures: list[dict[str, Any]] = []
    rng = random.Random(args.seed)
    proposal_dir = run_dir / "proposals"
    proposal_dir.mkdir(parents=True, exist_ok=True)

    root_configs = [Path(path) for path in args.root_configs]
    train_roots(root_configs, run_dir, tree, args.max_epochs)
    best_val = max(node["best_val_macro_f1"] for node in tree["nodes"].values())
    no_improve = 0
    stop_reason = "budget exhausted"
    write_tree_and_failures(run_dir, tree, failures)

    for iteration in range(1, args.budget_nodes + 1):
        parent_name, scored = select_parent(tree, args.exploration, args.max_children)
        parent_node = tree["nodes"][parent_name]
        parent_config = read_json(Path(parent_node["config"]))
        child_index = len(parent_node.get("children", [])) + 1
        child_config, proposal = propose_program_child(parent_config, {**parent_node, "name": parent_name}, child_index, rng, program_root)
        child_name = str(child_config["node_name"])
        child_config_path = proposal_dir / f"{child_name}.json"
        proposal_path = proposal_dir / f"{child_name}.proposal.json"
        proposal["mcts_selected_parent"] = parent_name
        proposal["mcts_candidates"] = scored[: min(8, len(scored))]
        write_json(child_config_path, child_config)
        write_json(proposal_path, proposal)

        tree["events"].append({"iteration": iteration, "selected_parent": parent_name, "child": child_name, "strategy": proposal["strategy"], "node_kind": "program_node"})
        try:
            metrics = run_node(child_config, run_dir, proposal=proposal, max_epochs=args.max_epochs)
            add_trained_node(tree, child_name, child_config_path, parent_name, iteration, metrics, proposal)
            backpropagate(tree, child_name, reward(metrics))
            val = reward(metrics)
            if val > best_val + args.min_delta:
                best_val = val
                no_improve = 0
            else:
                no_improve += 1
        except Exception as exc:
            error = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            tree["nodes"][parent_name].setdefault("children", []).append(child_name)
            tree["nodes"][child_name] = {
                "config": str(child_config_path),
                "parent": parent_name,
                "children": [],
                "status": "failed",
                "iteration": iteration,
                "agent_type": proposal.get("agent_type"),
                "node_kind": proposal.get("node_kind"),
                "strategy": proposal.get("strategy"),
                "program_dir": proposal.get("program_dir"),
                "program_model_path": proposal.get("program_model_path"),
                "error": error,
                "visits": 0,
                "value": 0.0,
            }
            failures.append({"node": child_name, "parent": parent_name, "error": error, "strategy": proposal.get("strategy")})
            no_improve += 1

        write_tree_and_failures(run_dir, tree, failures)
        if args.stop_no_improve and no_improve >= args.stop_no_improve:
            stop_reason = f"no improvement for {no_improve} nodes"
            break

    write_tree_and_failures(run_dir, tree, failures)
    write_summary(tree, args.summary, failures, stop_reason)
    result = {"tree": str(run_dir / "tree.json"), "summary": str(args.summary), "stop_reason": stop_reason, "failures": len(failures)}
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a VCHarness-style search where each child is a generated model program.")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--root-configs", nargs="+", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--budget-nodes", type=int, default=12)
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--max-children", type=int, default=3)
    parser.add_argument("--exploration", type=float, default=0.7)
    parser.add_argument("--stop-no-improve", type=int, default=6)
    parser.add_argument("--min-delta", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if args.summary is None:
        args.summary = args.run_dir / "search_summary.md"
    run_search(args)


if __name__ == "__main__":
    main()
