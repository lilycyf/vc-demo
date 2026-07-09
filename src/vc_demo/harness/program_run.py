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
    node["artifact_contract_path"] = proposal.get("artifact_contract_path", "")
    node["smoke_contract_path"] = proposal.get("smoke_contract_path", "")
    node["parent_summary_path"] = proposal.get("parent_summary_path", "")
    node["pipeline_kind"] = proposal.get("pipeline_kind", "")
    node["artifact_requirements"] = proposal.get("artifact_requirements", [])
    node["artifact_usage_claims"] = proposal.get("artifact_usage_claims", [])
    node["requires_implementation"] = bool(proposal.get("requires_implementation"))
    node["scientific_selection"] = proposal.get("scientific_selection", {})
    node["structural_signature"] = proposal.get("structural_signature", "")
    node["parent_structural_signature"] = proposal.get("parent_structural_signature", "")
    node["structural_relation"] = proposal.get("structural_relation", "")


def link_child(tree: dict[str, Any], parent: str, child: str) -> None:
    if not parent:
        roots = tree.setdefault("root_nodes", [])
        if child not in roots:
            roots.append(child)
        return
    children = tree["nodes"][parent].setdefault("children", [])
    if child not in children:
        children.append(child)


def add_selected_for_training_node(tree: dict[str, Any], name: str, config_path: Path, parent: str, iteration: int, proposal: dict[str, Any]) -> None:
    node = {
        "config": str(config_path),
        "parent": parent,
        "children": [],
        "status": "selected_for_training",
        "iteration": iteration,
        "visits": 0,
        "value": 0.0,
        "Q_v": 0.0,
        "Exploitation": 0.0,
        "stage": "rollout_selected",
        "selection_reason": "selected by proposal pool cheap-screen for rollout training",
    }
    enrich_node_from_proposal(node, proposal, config_path, name)
    tree["nodes"][name] = node
    link_child(tree, parent, name)


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
        "execution_mode": metrics.get("execution_mode"),
        "test_metric_source": metrics.get("test_metric_source"),
        "validation_metric_source": metrics.get("validation_metric_source"),
    }
    if proposal:
        enrich_node_from_proposal(node, proposal, config_path, name)
    tree["nodes"][name] = node
    link_child(tree, parent, name)


def add_pending_node(tree: dict[str, Any], name: str, config_path: Path, parent: str, iteration: int, proposal: dict[str, Any]) -> None:
    node = {"config": str(config_path), "parent": parent, "children": [], "status": "needs_implementation", "iteration": iteration, "visits": 0, "value": 0.0, "Q_v": 0.0, "Exploitation": 0.0, "stage": "improve"}
    enrich_node_from_proposal(node, proposal, config_path, name)
    tree["nodes"][name] = node
    link_child(tree, parent, name)


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
    link_child(tree, parent, name)


def add_pruned_node(
    tree: dict[str, Any],
    name: str,
    config_path: Path,
    parent: str,
    iteration: int,
    proposal: dict[str, Any],
    reason: str,
    rank: int,
    cheap_score: dict[str, Any],
) -> None:
    node = {
        "config": str(config_path),
        "parent": parent,
        "children": [],
        "status": "pruned_not_selected",
        "iteration": iteration,
        "visits": 0,
        "value": 0.0,
        "Q_v": 0.0,
        "Exploitation": 0.0,
        "stage": "proposal_screen",
        "pruned_reason": reason,
        "candidate_rank": rank,
        "cheap_screen_score": cheap_score,
    }
    enrich_node_from_proposal(node, proposal, config_path, name)
    tree["nodes"][name] = node
    link_child(tree, parent, name)


def cheap_screen_score(proposal: dict[str, Any], missing_summary: dict[str, Any], duplicate_reason: str = "") -> dict[str, Any]:
    scientific = proposal.get("scientific_selection", {}) or {}
    blueprint = proposal.get("blueprint", {}) or {}
    cost_class = str(blueprint.get("cost_class", "medium"))
    cost_bonus = {"cheap": 0.08, "medium": 0.0, "expensive": -0.08}.get(cost_class, 0.0)
    missing = list(missing_summary.get("missing_required_artifacts", []) or [])
    missing_penalty = 1.25 if missing else 0.0
    duplicate_penalty = 0.75 if duplicate_reason else 0.0
    implementation_penalty = 0.06 if proposal.get("requires_implementation") else 0.0
    structural_bonus = 0.05 if proposal.get("structural_relation") == "structural_variant" else -0.05
    base = float(scientific.get("score", 0.0) or 0.0)
    score = base + cost_bonus + structural_bonus - missing_penalty - duplicate_penalty - implementation_penalty
    return {
        "score": score,
        "scientific_score": base,
        "cost_class": cost_class,
        "cost_bonus": cost_bonus,
        "structural_bonus": structural_bonus,
        "missing_penalty": missing_penalty,
        "duplicate_penalty": duplicate_penalty,
        "implementation_penalty": implementation_penalty,
        "missing_required_artifacts": missing,
        "duplicate_reason": duplicate_reason,
        "policy": "proposal_pool_scientific_rank_then_feasibility_screen",
    }


def train_roots(root_configs: list[Path], run_dir: Path, tree: dict[str, Any], max_epochs: int | None) -> None:
    for root_config in root_configs:
        config = read_json(root_config)
        name = str(config.get("node_name", root_config.stem))
        metrics = run_node(config, run_dir, proposal=None, max_epochs=max_epochs)
        add_trained_node(tree, name, root_config, parent="", iteration=0, metrics=metrics)


def implementation_queue(tree: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"node": name, "program_dir": node.get("program_dir"), "implementation_request_path": node.get("implementation_request_path"), "program_model_path": node.get("program_model_path"), "pipeline_manifest_path": node.get("pipeline_manifest_path"), "artifact_contract_path": node.get("artifact_contract_path"), "smoke_contract_path": node.get("smoke_contract_path"), "parent_summary_path": node.get("parent_summary_path"), "strategy": node.get("strategy"), "artifact_requirements": node.get("artifact_requirements", []), "scientific_selection": node.get("scientific_selection", {}), "structural_relation": node.get("structural_relation", "")}
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


def lineage(tree: dict[str, Any], node_name: str) -> list[str]:
    path: list[str] = []
    current = node_name
    while current:
        path.append(current)
        current = tree.get("nodes", {}).get(current, {}).get("parent", "")
    return path


def append_mcts_trace(run_dir: Path, event: dict[str, Any]) -> None:
    path = run_dir / "mcts_trace.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def compact_candidates(scored: list[dict[str, Any]], limit: int = 16) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in scored[:limit]:
        rows.append({
            "node": row.get("node"),
            "score": row.get("score"),
            "uct": row.get("uct"),
            "puct": row.get("puct"),
            "q": row.get("q"),
            "Q_v": row.get("Q_v"),
            "exploitation": row.get("exploitation"),
            "exploration": row.get("exploration"),
            "prior": row.get("prior"),
            "visits": row.get("visits"),
            "children": row.get("children"),
            "best_val_macro_f1": row.get("best_val_macro_f1"),
        })
    return rows


def write_tree_and_failures(run_dir: Path, tree: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    write_json(run_dir / "tree.json", tree)
    write_json(run_dir / "failures.json", {"failures": failures})
    write_json(run_dir / "implementation_queue.json", {"items": implementation_queue(tree)})
    write_json(run_dir / "acquisition_queue.json", {"items": acquisition_queue(tree)})


def family_coverage(tree: dict[str, Any]) -> int:
    families: set[str] = set()
    for node in tree.get("nodes", {}).values():
        strategy = str(node.get("strategy") or "")
        if not strategy or strategy == "root":
            continue
        scientific = node.get("scientific_selection", {}) or {}
        family = str(scientific.get("family") or strategy)
        families.add(family)
    return len(families)


def structural_variant_count(tree: dict[str, Any]) -> int:
    return sum(1 for node in tree.get("nodes", {}).values() if node.get("structural_relation") == "structural_variant")


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
    stop_reason = "proposal budget exhausted"
    generated_proposals = 0
    trained_rollouts = 0
    proposal_budget = int(args.budget_proposals if args.budget_proposals is not None else args.budget_nodes * max(args.candidate_pool_size, 1))
    trained_node_budget = args.budget_trained_nodes
    max_iterations = max(1, (proposal_budget + max(args.candidate_pool_size, 1) - 1) // max(args.candidate_pool_size, 1))
    write_tree_and_failures(run_dir, tree, failures)

    start_iteration = max([0, *[int(node.get("iteration", 0)) for node in tree["nodes"].values()]]) + 1
    end_iteration = start_iteration + max_iterations - 1
    for iteration in range(start_iteration, end_iteration + 1):
        if generated_proposals >= proposal_budget:
            stop_reason = f"proposal budget exhausted ({generated_proposals}/{proposal_budget})"
            break
        if trained_node_budget is not None and trained_rollouts >= trained_node_budget:
            stop_reason = f"trained-node budget exhausted ({trained_rollouts}/{trained_node_budget})"
            break
        parent_name, scored = select_parent(tree, args.exploration, args.max_children, policy=args.selection_policy)
        append_mcts_trace(run_dir, {"event": "selection", "iteration": iteration, "policy": args.selection_policy, "exploration": args.exploration, "selected_parent": parent_name, "candidate_list": compact_candidates(scored), "selected_components": compact_candidates(scored, 1)[0] if scored else {}})
        parent_node = tree["nodes"][parent_name]
        parent_config = read_json(Path(parent_node["config"]))
        child_config = None
        proposal = None
        child_name = ""
        duplicate_skips: list[dict[str, Any]] = []
        proposal_candidates: list[dict[str, Any]] = []
        pool_attempts = max(args.max_duplicate_proposal_attempts, args.candidate_pool_size)
        for duplicate_attempt in range(1, pool_attempts + 1):
            child_index = len(parent_node.get("children", [])) + duplicate_attempt
            candidate_config, candidate_proposal = propose_program_child(parent_config, {**parent_node, "name": parent_name}, child_index, rng, program_root, include_planned=args.allow_planned_blueprints, force_blueprint=args.force_blueprint, registry_audit=registry_audit, artifact_aware=args.artifact_aware_blueprint_policy, official_k562_only=args.official_blueprint_space, search_memory=memory)
            strategy = str(candidate_proposal.get("strategy", ""))
            duplicate, reason = is_duplicate_proposal(memory, parent_name, strategy, args.max_blueprint_repeats, allow_parent_duplicate=args.allow_parent_duplicate_blueprints)
            missing_summary = summarize_missing_requirements(registry_audit, strategy)
            candidate_proposal["strict_artifact_mode"] = not args.allow_missing_artifact_fallbacks
            candidate_proposal["missing_required_artifacts"] = missing_summary.get("missing_required_artifacts", [])
            candidate_proposal["missing_required_artifact_paths"] = missing_summary.get("missing_required_artifact_paths", [])
            candidate_proposal["candidate_pool_iteration"] = iteration
            candidate_proposal["candidate_pool_parent"] = parent_name
            candidate_proposal["duplicate_screen"] = {"is_duplicate": duplicate, "reason": reason}
            candidate_proposal["cheap_screen_score"] = cheap_screen_score(candidate_proposal, missing_summary, reason if duplicate else "")
            proposal_candidates.append({
                "config": candidate_config,
                "proposal": candidate_proposal,
                "missing_summary": missing_summary,
                "duplicate": duplicate,
                "duplicate_reason": reason,
                "score": candidate_proposal["cheap_screen_score"],
            })
            if duplicate and not args.force_blueprint:
                duplicate_skips.append({"child": candidate_config.get("node_name"), "strategy": strategy, "reason": reason})
                record_event(run_dir, "duplicate_proposal_screened", {"iteration": iteration, "parent": parent_name, **duplicate_skips[-1]})
            if len(proposal_candidates) >= args.candidate_pool_size and (args.candidate_pool_size > 1 or not duplicate or args.force_blueprint):
                break

        if proposal_candidates:
            generated_proposals += len(proposal_candidates)
            append_mcts_trace(run_dir, {"event": "proposal_pool_generated", "iteration": iteration, "selected_parent": parent_name, "candidate_count": len(proposal_candidates), "generated_proposals": generated_proposals, "proposal_budget": proposal_budget})
            proposal_candidates.sort(key=lambda item: float(item["score"].get("score", 0.0)), reverse=True)
            selected_index = 0
            if not args.force_blueprint:
                for idx, item in enumerate(proposal_candidates):
                    if not item["duplicate"]:
                        selected_index = idx
                        break
            if not args.force_blueprint and all(item["duplicate"] for item in proposal_candidates):
                selected = None
            else:
                selected = proposal_candidates[selected_index]
            if selected is not None:
                child_config = selected["config"]
                proposal = selected["proposal"]
                proposal["candidate_pool_selected"] = True
                proposal["candidate_pool_rank"] = selected_index + 1
                proposal["candidate_pool_size"] = len(proposal_candidates)
                proposal["candidate_pool_policy"] = "generate_many_prune_before_training"
                proposal["candidate_pool_summary"] = [
                {
                    "rank": rank,
                    "node": item["config"].get("node_name"),
                    "strategy": item["proposal"].get("strategy"),
                    "score": item["score"],
                    "selected": rank == selected_index + 1,
                }
                for rank, item in enumerate(proposal_candidates, start=1)
                ]

            for rank, item in enumerate(proposal_candidates, start=1):
                cand_config = item["config"]
                cand_proposal = item["proposal"]
                cand_name = str(cand_config["node_name"])
                cand_config_path = proposal_dir / f"{cand_name}.json"
                cand_proposal_path = proposal_dir / f"{cand_name}.proposal.json"
                cand_proposal["mcts_selected_parent"] = parent_name
                cand_proposal["mcts_selection_policy"] = args.selection_policy
                cand_proposal["mcts_candidates"] = scored[: min(8, len(scored))]
                cand_proposal["candidate_pool_rank"] = rank
                cand_proposal["candidate_pool_size"] = len(proposal_candidates)
                cand_proposal["candidate_pool_selected"] = selected is not None and rank == selected_index + 1
                cand_proposal["candidate_pool_policy"] = "generate_many_prune_before_training"
                write_json(cand_config_path, cand_config)
                write_json(cand_proposal_path, cand_proposal)
                if selected is None or rank != selected_index + 1:
                    reason = "lower cheap-screen rank; not selected for rollout training"
                    if item["duplicate"]:
                        reason = f"duplicate proposal pruned before training: {item['duplicate_reason']}"
                    add_pruned_node(tree, cand_name, cand_config_path, parent_name, iteration, cand_proposal, reason, rank, item["score"])
                    append_mcts_trace(run_dir, {"event": "proposal_pruned", "iteration": iteration, "selected_parent": parent_name, "child": cand_name, "chosen_blueprint": cand_proposal.get("strategy"), "candidate_rank": rank, "cheap_screen_score": item["score"], "reason": reason})

        if child_config is None or proposal is None:
            tree["events"].append({"iteration": iteration, "selected_parent": parent_name, "event": "no_candidate_selected_after_proposal_screen", "skips": duplicate_skips})
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
        tree["events"].append({"iteration": iteration, "selected_parent": parent_name, "child": child_name, "strategy": proposal["strategy"], "node_kind": "program_node", "requires_implementation": proposal.get("requires_implementation", False), "missing_required_artifacts": proposal.get("missing_required_artifacts", []), "scientific_selection": proposal.get("scientific_selection", {}), "structural_relation": proposal.get("structural_relation", "")})
        append_mcts_trace(run_dir, {"event": "expansion", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "candidate_list": compact_candidates(scored), "requires_implementation": proposal.get("requires_implementation", False), "missing_required_artifacts": proposal.get("missing_required_artifacts", []), "scientific_selection": proposal.get("scientific_selection", {}), "structural_relation": proposal.get("structural_relation", ""), "duplicate_skips": duplicate_skips, "depth": len(lineage(tree, parent_name))})

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
            append_mcts_trace(run_dir, {"event": "artifact_acquisition_block", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "missing_required_artifacts": proposal["missing_required_artifacts"], "stop_reason": stop_reason})
            write_tree_and_failures(run_dir, tree, failures)
            break

        if proposal.get("requires_implementation"):
            add_pending_node(tree, child_name, child_config_path, parent_name, iteration, proposal)
            pending_count += 1
            append_mcts_trace(run_dir, {"event": "pending_implementation", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "scientific_selection": proposal.get("scientific_selection", {}), "structural_relation": proposal.get("structural_relation", ""), "implementation_request_path": proposal.get("implementation_request_path"), "artifact_contract_path": proposal.get("artifact_contract_path"), "smoke_contract_path": proposal.get("smoke_contract_path"), "parent_summary_path": proposal.get("parent_summary_path")})
            write_tree_and_failures(run_dir, tree, failures)
            if pending_count >= args.max_pending_implementations:
                stop_reason = f"pending implementation limit reached ({pending_count})"
                break
            continue

        add_selected_for_training_node(tree, child_name, child_config_path, parent_name, iteration, proposal)
        append_mcts_trace(run_dir, {"event": "selected_for_training", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "candidate_rank": proposal.get("candidate_pool_rank"), "candidate_pool_size": proposal.get("candidate_pool_size"), "cheap_screen_score": proposal.get("cheap_screen_score")})
        write_tree_and_failures(run_dir, tree, failures)

        try:
            metrics = run_node(child_config, run_dir, proposal=proposal, max_epochs=args.max_epochs)
            add_trained_node(tree, child_name, child_config_path, parent_name, iteration, metrics, proposal)
            rollout_reward = reward(metrics)
            backpropagate(tree, child_name, rollout_reward)
            append_mcts_trace(run_dir, {"event": "backpropagation", "iteration": iteration, "leaf": child_name, "reward": rollout_reward, "backprop_path": tree.get("mcts", {}).get("last_backpropagation", {}).get("path", []), "best_val_macro_f1": metrics.get("best_val_macro_f1"), "test_macro_f1": metrics.get("test_macro_f1")})
            trained_rollouts += 1
            val = rollout_reward
            if val > best_val + args.min_delta:
                best_val = val
                no_improve = 0
            else:
                no_improve += 1
        except Exception as exc:
            error = "".join(traceback.format_exception_only(type(exc), exc)).strip()
            link_child(tree, parent_name, child_name)
            tree["nodes"][child_name] = {"config": str(child_config_path), "parent": parent_name, "children": [], "status": "failed", "iteration": iteration, "agent_type": proposal.get("agent_type"), "node_kind": proposal.get("node_kind"), "strategy": proposal.get("strategy"), "program_dir": proposal.get("program_dir"), "program_model_path": proposal.get("program_model_path"), "pipeline_manifest_path": proposal.get("pipeline_manifest_path"), "pipeline_kind": proposal.get("pipeline_kind"), "artifact_requirements": proposal.get("artifact_requirements", []), "artifact_usage_claims": proposal.get("artifact_usage_claims", []), "scientific_selection": proposal.get("scientific_selection", {}), "structural_signature": proposal.get("structural_signature", ""), "parent_structural_signature": proposal.get("parent_structural_signature", ""), "structural_relation": proposal.get("structural_relation", ""), "error": error, "visits": 0, "value": 0.0, "Q_v": 0.0, "Exploitation": 0.0, "stage": "improve"}
            failures.append({"node": child_name, "parent": parent_name, "error": error, "strategy": proposal.get("strategy")})
            append_mcts_trace(run_dir, {"event": "failure", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "error": error})
            no_improve += 1

        memory = rebuild_memory_from_tree(run_dir, tree, failures)
        write_tree_and_failures(run_dir, tree, failures)
        if trained_node_budget is not None and trained_rollouts >= trained_node_budget:
            stop_reason = f"trained-node budget exhausted ({trained_rollouts}/{trained_node_budget})"
            break
        if args.stop_no_improve and no_improve >= args.stop_no_improve:
            coverage = family_coverage(tree)
            if coverage >= args.min_family_coverage_before_stop:
                stop_reason = f"no improvement for {no_improve} nodes"
                break
            append_mcts_trace(run_dir, {"event": "early_stop_suppressed_for_family_coverage", "iteration": iteration, "no_improve": no_improve, "family_coverage": coverage, "min_family_coverage_before_stop": args.min_family_coverage_before_stop})

    memory = rebuild_memory_from_tree(run_dir, tree, failures)
    write_tree_and_failures(run_dir, tree, failures)
    write_summary(tree, args.summary, failures, stop_reason)
    run_manifest_path = write_run_manifest(run_dir, args, tree, failures, stop_reason, registry_audit)
    result = {"tree": str(run_dir / "tree.json"), "summary": str(args.summary), "mcts_trace": str(run_dir / "mcts_trace.jsonl"), "implementation_queue": str(run_dir / "implementation_queue.json"), "acquisition_queue": str(run_dir / "acquisition_queue.json"), "artifact_acquisition_command": f"python -m vc_demo.harness.artifact_acquisition --queue {run_dir / 'acquisition_queue.json'} --registry {args.artifact_registry or Path('configs/artifacts/k562_registry.json')} --sources configs/artifacts/acquisition_sources.json --cell-line K562 --output-dir {run_dir / 'artifact_acquisition'} --execute-known", "run_manifest": str(run_manifest_path), "search_memory": str(run_dir / "search_memory.json"), "stop_reason": stop_reason, "failures": len(failures), "pending_implementations": pending_count, "generated_proposals": generated_proposals, "proposal_budget": proposal_budget, "trained_rollouts_this_invocation": trained_rollouts, "trained_node_budget": trained_node_budget, "candidate_pool_size": args.candidate_pool_size}
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a VCHarness-style search where each child is a generated or on-demand model program.")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--root-configs", nargs="+", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--budget-nodes", type=int, default=12, help="Legacy rollout-iteration budget. In paper-aligned mode prefer --budget-proposals and --budget-trained-nodes.")
    parser.add_argument("--budget-proposals", type=int, default=None, help="Maximum generated proposal candidates, including pruned/blocked/pending/trained candidates.")
    parser.add_argument("--budget-trained-nodes", type=int, default=None, help="Maximum rollout candidates allowed to finish training and backpropagate reward.")
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--max-children", type=int, default=3)
    parser.add_argument("--exploration", type=float, default=1.4142135623730951)
    parser.add_argument("--selection-policy", choices=["uct", "puct"], default="uct")
    parser.add_argument("--stop-no-improve", type=int, default=6)
    parser.add_argument("--min-family-coverage-before-stop", type=int, default=0, help="Do not stop for no-improvement until this many non-root blueprint families have been exercised.")
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
    parser.add_argument("--candidate-pool-size", type=int, default=4, help="Paper-aligned default: generate multiple proposal candidates per selected parent, cheap-screen them, and train only the selected rollout candidate. Values >1 create pruned_not_selected nodes for untrained proposals.")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if args.summary is None:
        args.summary = args.run_dir / "search_summary.md"
    if args.candidate_pool_size < 1:
        raise SystemExit("--candidate-pool-size must be >= 1")
    if args.official_blueprint_space and args.candidate_pool_size < 2:
        raise SystemExit("official paper-aligned search requires --candidate-pool-size >= 2; proposal pruning is not optional in official mode")
    run_search(args)


if __name__ == "__main__":
    main()
