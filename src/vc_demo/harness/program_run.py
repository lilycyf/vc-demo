from __future__ import annotations

import argparse
import json
import random
import traceback
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import audit_registry, load_registry, summarize_missing_requirements
from vc_demo.harness.executor import run_node
from vc_demo.harness.mcts import backpropagate, select_parent
from vc_demo.harness.program_agent import propose_program_child
from vc_demo.harness.report import write_summary
from vc_demo.harness.run_manifest import write_run_manifest
from vc_demo.harness.search_memory import is_duplicate_proposal, rebuild_memory_from_tree, record_event
from vc_demo.harness.state import empty_tree, read_json, reset_run_dir, write_json


def reward(metrics: dict[str, Any]) -> float:
    return float(metrics["best_val_macro_f1"])


def enrich_node_from_proposal(node: dict[str, Any], proposal: dict[str, Any], config_path: Path, name: str) -> None:
    node["agent_type"] = proposal.get("agent_type")
    node["node_kind"] = proposal.get("node_kind")
    node["strategy"] = proposal.get("strategy")
    node["proposal"] = str(config_path.parent / f"{name}.proposal.json")
    node["program_dir"] = proposal.get("program_dir")
    node["program_model_path"] = proposal.get("program_model_path")
    node["implementation_request_path"] = proposal.get("implementation_request_path", "")
    node["pipeline_manifest_path"] = proposal.get("pipeline_manifest_path", "")
    node["pipeline_kind"] = proposal.get("pipeline_kind", "")
    node["artifact_requirements"] = proposal.get("artifact_requirements", [])
    node["artifact_usage_claims"] = proposal.get("artifact_usage_claims", [])
    node["requires_implementation"] = bool(proposal.get("requires_implementation"))


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
        "visits": 1 if not parent else 0,
        "value": reward(metrics) if not parent else 0.0,
        "Q_v": reward(metrics) if not parent else 0.0,
        "squared_value": reward(metrics) * reward(metrics) if not parent else 0.0,
        "mean_reward": reward(metrics) if not parent else 0.0,
        "Exploitation": reward(metrics) if not parent else 0.0,
        "stage": "draft" if not parent else "improve",
        "best_reward": reward(metrics) if not parent else 0.0,
        "duration_seconds": metrics.get("duration_seconds"),
        "pipeline": metrics.get("pipeline", {}),
        "execution_backend": metrics.get("execution_backend") or "native_train",
        "external_script": metrics.get("external_script"),
        "artifact_usage": metrics.get("artifact_usage", {}),
    }
    if proposal:
        enrich_node_from_proposal(node, proposal, config_path, name)
    tree["nodes"][name] = node
    if parent:
        tree["nodes"][parent].setdefault("children", []).append(name)
    else:
        tree.setdefault("root_nodes", []).append(name)


def add_pending_node(tree: dict[str, Any], name: str, config_path: Path, parent: str, iteration: int, proposal: dict[str, Any]) -> None:
    node = {"config": str(config_path), "parent": parent, "children": [], "status": "needs_implementation", "iteration": iteration, "visits": 0, "value": 0.0, "Q_v": 0.0, "Exploitation": 0.0, "stage": "improve"}
    enrich_node_from_proposal(node, proposal, config_path, name)
    tree["nodes"][name] = node
    tree["nodes"][parent].setdefault("children", []).append(name)


def add_blocked_missing_artifact_node(
    tree: dict[str, Any],
    name: str,
    config_path: Path,
    parent: str,
    iteration: int,
    proposal: dict[str, Any],
    missing_summary: dict[str, Any],
) -> None:
    node = {
        "config": str(config_path),
        "parent": parent,
        "children": [],
        "status": "requires_artifact_acquisition",
        "iteration": iteration,
        "visits": 0,
        "value": 0.0,
        "Q_v": 0.0,
        "Exploitation": 0.0,
        "stage": "blocked",
        "blocked_reason": "required artifact missing; strict artifact mode requires artifact acquisition before training",
        "missing_required_artifacts": missing_summary.get("missing_required_artifacts", []),
        "missing_required_artifact_paths": missing_summary.get("missing_required_artifact_paths", []),
        "missing_required_artifact_sources": missing_summary.get("missing_required_artifact_sources", []),
    }
    enrich_node_from_proposal(node, proposal, config_path, name)
    tree["nodes"][name] = node
    tree["nodes"][parent].setdefault("children", []).append(name)


def train_roots(root_configs: list[Path], run_dir: Path, tree: dict[str, Any], max_epochs: int | None) -> None:
    for root_config in root_configs:
        config = read_json(root_config)
        name = str(config.get("node_name", root_config.stem))
        metrics = run_node(config, run_dir, proposal=None, max_epochs=max_epochs)
        add_trained_node(tree, name, root_config, parent="", iteration=0, metrics=metrics)


def implementation_queue(tree: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"node": name, "program_dir": node.get("program_dir"), "implementation_request_path": node.get("implementation_request_path"), "program_model_path": node.get("program_model_path"), "pipeline_manifest_path": node.get("pipeline_manifest_path"), "strategy": node.get("strategy"), "artifact_requirements": node.get("artifact_requirements", [])}
        for name, node in tree.get("nodes", {}).items()
        if node.get("status") == "needs_implementation"
    ]


def acquisition_queue(tree: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for name, node in tree.get("nodes", {}).items():
        if node.get("status") not in {"requires_artifact_acquisition", "blocked_missing_artifact"}:
            continue
        missing = node.get("missing_required_artifacts", []) or []
        paths = node.get("missing_required_artifact_paths", []) or []
        sources = node.get("missing_required_artifact_sources", []) or []
        for idx, artifact_id in enumerate(missing):
            items.append({
                "node": name,
                "strategy": node.get("strategy"),
                "artifact_id": artifact_id,
                "expected_path": paths[idx] if idx < len(paths) else "",
                "source": sources[idx] if idx < len(sources) else "",
                "action": "search_download_or_build_real_artifact",
                "resume_after": "update registry, rerun artifact audit, then resume search without fallback",
            })
    return items


def write_tree_and_failures(run_dir: Path, tree: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    write_json(run_dir / "tree.json", tree)
    write_json(run_dir / "failures.json", {"failures": failures})
    write_json(run_dir / "implementation_queue.json", {"items": implementation_queue(tree)})
    write_json(run_dir / "acquisition_queue.json", {"items": acquisition_queue(tree)})


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.reset:
        reset_run_dir(run_dir)
    program_root = run_dir / "programs"
    program_root.mkdir(parents=True, exist_ok=True)

    tree_path = run_dir / "tree.json"
    failures_path = run_dir / "failures.json"
    resume = (not args.reset) and tree_path.exists()
    if resume:
        tree = read_json(tree_path)
        failures = read_json(failures_path).get("failures", []) if failures_path.exists() else []
    else:
        tree = empty_tree(args.experiment)
        failures: list[dict[str, Any]] = []
    rng = random.Random(args.seed + len(tree.get("events", [])))
    proposal_dir = run_dir / "proposals"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    registry_audit = audit_registry(load_registry(args.artifact_registry, "K562"))
    write_json(run_dir / "artifact_registry_audit.json", registry_audit)
    tree.setdefault("artifact_registry", registry_audit)
    memory = rebuild_memory_from_tree(run_dir, tree, failures)

    if not resume:
        root_configs = [Path(path) for path in args.root_configs]
        train_roots(root_configs, run_dir, tree, args.max_epochs)
    trained_values = [node["best_val_macro_f1"] for node in tree["nodes"].values() if node.get("status") == "trained"]
    best_val = max(trained_values) if trained_values else -1.0
    no_improve = 0
    pending_count = len(implementation_queue(tree))
    stop_reason = "budget exhausted"
    write_tree_and_failures(run_dir, tree, failures)

    start_iteration = max([0, *[int(node.get("iteration", 0)) for node in tree["nodes"].values()]]) + 1
    end_iteration = start_iteration + args.budget_nodes - 1
    for iteration in range(start_iteration, end_iteration + 1):
        parent_name, scored = select_parent(tree, args.exploration, args.max_children, policy=args.selection_policy)
        parent_node = tree["nodes"][parent_name]
        parent_config = read_json(Path(parent_node["config"]))
        child_config = None
        proposal = None
        child_name = ""
        duplicate_skips: list[dict[str, Any]] = []
        for duplicate_attempt in range(1, args.max_duplicate_proposal_attempts + 1):
            child_index = len(parent_node.get("children", [])) + duplicate_attempt
            candidate_config, candidate_proposal = propose_program_child(parent_config, {**parent_node, "name": parent_name}, child_index, rng, program_root, include_planned=args.allow_planned_blueprints, force_blueprint=args.force_blueprint, registry_audit=registry_audit, artifact_aware=args.artifact_aware_blueprint_policy, official_k562_only=args.official_blueprint_space)
            duplicate, reason = is_duplicate_proposal(memory, parent_name, str(candidate_proposal.get("strategy", "")), args.max_blueprint_repeats, allow_parent_duplicate=args.allow_parent_duplicate_blueprints)
            if duplicate and not args.force_blueprint:
                duplicate_skips.append({"child": candidate_config.get("node_name"), "strategy": candidate_proposal.get("strategy"), "reason": reason})
                record_event(run_dir, "duplicate_proposal_skipped", {"iteration": iteration, "parent": parent_name, **duplicate_skips[-1]})
                continue
            child_config, proposal = candidate_config, candidate_proposal
            break
        if child_config is None or proposal is None:
            tree["events"].append({"iteration": iteration, "selected_parent": parent_name, "event": "all_candidate_blueprints_duplicate", "skips": duplicate_skips})
            no_improve += 1
            write_tree_and_failures(run_dir, tree, failures)
            continue
        child_name = str(child_config["node_name"])
        child_config_path = proposal_dir / f"{child_name}.json"
        proposal_path = proposal_dir / f"{child_name}.proposal.json"
        proposal["mcts_selected_parent"] = parent_name
        proposal["mcts_selection_policy"] = args.selection_policy
        proposal["mcts_candidates"] = scored[: min(8, len(scored))]
        missing_summary = summarize_missing_requirements(registry_audit, str(proposal.get("strategy", "")))
        proposal["strict_artifact_mode"] = not args.allow_missing_artifact_fallbacks
        proposal["missing_required_artifacts"] = missing_summary.get("missing_required_artifacts", [])
        proposal["missing_required_artifact_paths"] = missing_summary.get("missing_required_artifact_paths", [])
        write_json(child_config_path, child_config)
        write_json(proposal_path, proposal)
        tree["events"].append({"iteration": iteration, "selected_parent": parent_name, "child": child_name, "strategy": proposal["strategy"], "node_kind": "program_node", "requires_implementation": proposal.get("requires_implementation", False), "missing_required_artifacts": proposal.get("missing_required_artifacts", [])})

        if proposal["missing_required_artifacts"] and not args.allow_missing_artifact_fallbacks:
            add_blocked_missing_artifact_node(tree, child_name, child_config_path, parent_name, iteration, proposal, missing_summary)
            failures.append({
                "node": child_name,
                "parent": parent_name,
                "error": "requires_artifact_acquisition",
                "strategy": proposal.get("strategy"),
                "missing_required_artifacts": proposal["missing_required_artifacts"],
                "missing_required_artifact_paths": proposal["missing_required_artifact_paths"],
            })
            stop_reason = f"requires artifact acquisition for {proposal.get('strategy')}: {', '.join(proposal['missing_required_artifacts'])}"
            write_tree_and_failures(run_dir, tree, failures)
            break

        if proposal.get("requires_implementation"):
            add_pending_node(tree, child_name, child_config_path, parent_name, iteration, proposal)
            pending_count += 1
            write_tree_and_failures(run_dir, tree, failures)
            if pending_count >= args.max_pending_implementations:
                stop_reason = f"pending implementation limit reached ({pending_count})"
                break
            continue

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
            tree["nodes"][child_name] = {"config": str(child_config_path), "parent": parent_name, "children": [], "status": "failed", "iteration": iteration, "agent_type": proposal.get("agent_type"), "node_kind": proposal.get("node_kind"), "strategy": proposal.get("strategy"), "program_dir": proposal.get("program_dir"), "program_model_path": proposal.get("program_model_path"), "pipeline_manifest_path": proposal.get("pipeline_manifest_path"), "pipeline_kind": proposal.get("pipeline_kind"), "artifact_requirements": proposal.get("artifact_requirements", []), "artifact_usage_claims": proposal.get("artifact_usage_claims", []), "error": error, "visits": 0, "value": 0.0, "Q_v": 0.0, "Exploitation": 0.0, "stage": "improve"}
            failures.append({"node": child_name, "parent": parent_name, "error": error, "strategy": proposal.get("strategy")})
            no_improve += 1

        memory = rebuild_memory_from_tree(run_dir, tree, failures)
        write_tree_and_failures(run_dir, tree, failures)
        if args.stop_no_improve and no_improve >= args.stop_no_improve:
            stop_reason = f"no improvement for {no_improve} nodes"
            break

    memory = rebuild_memory_from_tree(run_dir, tree, failures)
    write_tree_and_failures(run_dir, tree, failures)
    write_summary(tree, args.summary, failures, stop_reason)
    run_manifest_path = write_run_manifest(run_dir, args, tree, failures, stop_reason, registry_audit)
    result = {"tree": str(run_dir / "tree.json"), "summary": str(args.summary), "implementation_queue": str(run_dir / "implementation_queue.json"), "acquisition_queue": str(run_dir / "acquisition_queue.json"), "artifact_acquisition_command": f"python -m vc_demo.harness.artifact_acquisition --queue {run_dir / 'acquisition_queue.json'} --registry {args.artifact_registry or Path('configs/artifacts/k562_registry.json')} --sources configs/artifacts/acquisition_sources.json --cell-line K562 --output-dir {run_dir / 'artifact_acquisition'} --execute-known", "run_manifest": str(run_manifest_path), "search_memory": str(run_dir / "search_memory.json"), "stop_reason": stop_reason, "failures": len(failures), "pending_implementations": pending_count}
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a VCHarness-style search where each child is a generated or on-demand model program.")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--root-configs", nargs="+", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--budget-nodes", type=int, default=12)
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--max-children", type=int, default=3)
    parser.add_argument("--exploration", type=float, default=1.4142135623730951)
    parser.add_argument("--selection-policy", choices=["uct", "puct"], default="uct")
    parser.add_argument("--stop-no-improve", type=int, default=6)
    parser.add_argument("--min-delta", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--allow-planned-blueprints", action="store_true")
    parser.add_argument("--max-pending-implementations", type=int, default=1)
    parser.add_argument("--force-blueprint", default=None)
    parser.add_argument("--artifact-registry", type=Path, default=None)
    parser.add_argument("--artifact-aware-blueprint-policy", action=argparse.BooleanOptionalAction, default=True, help="Prefer executable blueprints whose required artifacts are already present before blueprints that would trigger acquisition.")
    parser.add_argument("--allow-missing-artifact-fallbacks", action="store_true", help="Allow planned artifact blueprints to train explicit fallback models when required artifacts are missing. Default is strict: block and stop.")
    parser.add_argument("--official-blueprint-space", action="store_true", help="Restrict child proposals to official K562 paper-level blueprints.")
    parser.add_argument("--max-blueprint-repeats", type=int, default=2, help="Global repeat limit per blueprint; -1 disables the global duplicate guard.")
    parser.add_argument("--allow-parent-duplicate-blueprints", action="store_true", help="Allow the same parent to generate the same blueprint more than once.")
    parser.add_argument("--max-duplicate-proposal-attempts", type=int, default=8, help="How many candidate blueprints to try before skipping an iteration as duplicate-only.")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if args.summary is None:
        args.summary = args.run_dir / "search_summary.md"
    run_search(args)


if __name__ == "__main__":
    main()
