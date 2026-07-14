from __future__ import annotations

import argparse
import json
import random
import traceback
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_acquisition import resolve_item, source_map
from vc_demo.harness.artifact_registry import audit_registry, load_registry, requirements_for_blueprint, summarize_missing_requirements
from vc_demo.harness.executor import run_node
from vc_demo.harness.implementation_agent import implement_pending
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


def refresh_node_artifact_contract(proposal: dict[str, Any], registry_audit: dict[str, Any]) -> None:
    contract_path = Path(str(proposal.get("artifact_contract_path") or ""))
    if not contract_path.exists():
        return
    contract = read_json(contract_path)
    strategy = str(proposal.get("strategy") or contract.get("blueprint") or "")
    rows = requirements_for_blueprint(registry_audit, strategy) if strategy else []
    contract["artifact_rows"] = rows
    contract["required_artifacts"] = [str(row.get("id")) for row in rows]
    contract["present_required_artifacts"] = [str(row.get("id")) for row in rows if row.get("present")]
    contract["missing_required_artifacts"] = [str(row.get("id")) for row in rows if not row.get("present")]
    contract["refreshed_after_realtime_acquisition"] = True
    write_json(contract_path, contract)


def attempt_realtime_artifact_acquisition(
    run_dir: Path,
    args: argparse.Namespace,
    child_name: str,
    proposal: dict[str, Any],
    missing_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Try source-backed acquisition before a selected rollout is blocked.

    The strict policy is: missing artifact -> run deterministic resolver or create
    a research task -> re-audit -> only block when the artifact is still missing
    because source/provenance/tensor contract cannot be verified yet.
    """
    output_dir = run_dir / "artifact_acquisition"
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path = args.artifact_registry or Path("configs/artifacts/k562_registry.json")
    registry = load_registry(registry_path, "K562")
    sources_path = Path("configs/artifacts/acquisition_sources.json")
    if args.artifact_registry:
        sibling_sources = Path(args.artifact_registry).parent / "acquisition_sources.json"
        if sibling_sources.exists():
            sources_path = sibling_sources
    sources = source_map(sources_path)
    missing_ids = list(missing_summary.get("missing_required_artifacts", []) or [])
    missing_paths = list(missing_summary.get("missing_required_artifact_paths", []) or [])
    missing_sources = list(missing_summary.get("missing_required_artifact_sources", []) or [])
    results: list[dict[str, Any]] = []
    for idx, artifact_id in enumerate(missing_ids):
        item = {
            "node": child_name,
            "strategy": proposal.get("strategy"),
            "artifact_id": artifact_id,
            "expected_path": missing_paths[idx] if idx < len(missing_paths) else "",
            "source": missing_sources[idx] if idx < len(missing_sources) else "",
        }
        results.append(resolve_item(item, sources, registry, output_dir, execute_known=True))
    report = {
        "node": child_name,
        "strategy": proposal.get("strategy"),
        "policy": "realtime_source_backed_acquisition_before_block",
        "items": results,
    }
    existing_path = output_dir / "realtime_acquisition_results.jsonl"
    with existing_path.open("a") as f:
        import json as _json

        f.write(_json.dumps(report) + "\n")
    refreshed_audit = audit_registry(load_registry(registry_path, "K562"))
    return results, refreshed_audit


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


def add_candidate_queued_node(
    tree: dict[str, Any],
    name: str,
    config_path: Path,
    parent: str,
    iteration: int,
    proposal: dict[str, Any],
    rank: int,
    cheap_score: dict[str, Any],
) -> None:
    node = {
        "config": str(config_path),
        "parent": parent,
        "children": [],
        "status": "candidate_queued",
        "iteration": iteration,
        "visits": 0,
        "value": 0.0,
        "Q_v": 0.0,
        "Exploitation": 0.0,
        "stage": "global_proposal_queue",
        "queue_reason": "queued for global proposal selection before rollout training",
        "candidate_rank": rank,
        "cheap_screen_score": cheap_score,
        "global_priority": float(cheap_score.get("score", 0.0) or 0.0),
    }
    enrich_node_from_proposal(node, proposal, config_path, name)
    tree["nodes"][name] = node
    link_child(tree, parent, name)


def queued_candidates(tree: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, node in tree.get("nodes", {}).items():
        if node.get("status") != "candidate_queued":
            continue
        score = node.get("global_priority")
        if score is None:
            score = float((node.get("cheap_screen_score") or {}).get("score", 0.0) or 0.0)
        rows.append({"name": name, "node": node, "score": float(score)})
    return sorted(rows, key=lambda row: row["score"], reverse=True)


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


def present_artifact_ids(registry_audit: dict[str, Any]) -> set[str]:
    return {
        str(item.get("id"))
        for item in registry_audit.get("artifacts", [])
        if item.get("present") or item.get("resolved_status") == "present"
    }


def reactivate_resolved_artifact_blockers(
    run_dir: Path,
    tree: dict[str, Any],
    failures: list[dict[str, Any]],
    registry_audit: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    present = present_artifact_ids(registry_audit)
    reactivated: list[dict[str, Any]] = []
    reactivated_nodes: set[str] = set()
    for name, node in tree.get("nodes", {}).items():
        if node.get("status") not in {"requires_artifact_acquisition", "blocked_missing_artifact"}:
            continue
        required = [str(x) for x in node.get("artifact_requirements", []) or [] if x]
        missing = [str(x) for x in node.get("missing_required_artifacts", []) or [] if x]
        needed = required or missing
        if not needed:
            continue
        still_missing = sorted(x for x in needed if x not in present)
        if still_missing:
            node["missing_required_artifacts"] = still_missing
            continue
        node.update({
            "status": "candidate_queued",
            "missing_required_artifacts": [],
            "missing_required_artifact_paths": [],
            "reactivated_after_artifact_acquisition": True,
            "reactivation_policy": "artifact_audit_now_present_requeue_for_global_selection",
            "requires_implementation": bool(node.get("requires_implementation")),
        })
        reactivated_nodes.add(name)
        row = {
            "node": name,
            "strategy": node.get("strategy"),
            "artifact_requirements": needed,
            "policy": "artifact_audit_now_present_requeue_for_global_selection",
        }
        reactivated.append(row)
        append_mcts_trace(run_dir, {"event": "artifact_blocker_reactivated", **row})
    if reactivated_nodes:
        filtered_failures = []
        for failure in failures:
            if failure.get("node") in reactivated_nodes and failure.get("error") == "requires_artifact_acquisition":
                continue
            filtered_failures.append(failure)
        failures = filtered_failures
    return tree, failures, reactivated



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
    tree["artifact_registry"] = registry_audit
    if resume:
        tree, failures, reactivated = reactivate_resolved_artifact_blockers(run_dir, tree, failures, registry_audit)
        if reactivated:
            tree.setdefault("events", []).append({"event": "resolved_artifact_blockers_reactivated", "items": reactivated})
            write_json(run_dir / "resolved_artifact_blockers.json", {"items": reactivated})
    memory = rebuild_memory_from_tree(run_dir, tree, failures)

    if not resume:
        root_configs = [Path(path) for path in args.root_configs]
        train_roots(root_configs, run_dir, tree, args.max_epochs)
    trained_values = [node["best_val_macro_f1"] for node in tree["nodes"].values() if node.get("status") == "trained"]
    best_val = max(trained_values) if trained_values else -1.0
    no_improve = 0
    pending_count = len(implementation_queue(tree))
    stop_reason = "proposal budget exhausted"
    proposal_statuses = {
        "trained",
        "pruned_not_selected",
        "candidate_queued",
        "selected_for_training",
        "needs_implementation",
        "implementation_skipped",
        "requires_artifact_acquisition",
        "blocked_missing_artifact",
        "failed",
    }
    generated_proposals = sum(
        1
        for node in tree.get("nodes", {}).values()
        if node.get("parent") and node.get("status") in proposal_statuses
    )
    trained_rollouts = sum(
        1
        for node in tree.get("nodes", {}).values()
        if node.get("parent") and node.get("status") == "trained"
    )
    proposal_budget = int(args.budget_proposals if args.budget_proposals is not None else args.budget_nodes * max(args.candidate_pool_size, 1))
    trained_node_budget = args.budget_trained_nodes
    if args.proposal_selection_mode == "global_queue":
        max_iterations = max(1, proposal_budget + (trained_node_budget or proposal_budget) + 10)
    else:
        max_iterations = max(1, (proposal_budget + max(args.candidate_pool_size, 1) - 1) // max(args.candidate_pool_size, 1))
    write_tree_and_failures(run_dir, tree, failures)

    start_iteration = max([0, *[int(node.get("iteration", 0)) for node in tree["nodes"].values()]]) + 1
    end_iteration = start_iteration + max_iterations - 1
    for iteration in range(start_iteration, end_iteration + 1):
        queue = queued_candidates(tree)
        if generated_proposals >= proposal_budget and not queue:
            stop_reason = f"proposal budget exhausted ({generated_proposals}/{proposal_budget})"
            break
        if trained_node_budget is not None and trained_rollouts >= trained_node_budget:
            stop_reason = f"trained-node budget exhausted ({trained_rollouts}/{trained_node_budget})"
            break
        child_config = None
        proposal = None
        child_name = ""
        duplicate_skips: list[dict[str, Any]] = []
        proposal_candidates: list[dict[str, Any]] = []
        parent_name = ""
        scored: list[dict[str, Any]] = []
        parent_node: dict[str, Any] | None = None
        parent_config: dict[str, Any] | None = None

        should_generate_pool = args.proposal_selection_mode != "global_queue" or generated_proposals < proposal_budget
        if should_generate_pool:
            parent_name, scored = select_parent(tree, args.exploration, args.max_children, policy=args.selection_policy)
            append_mcts_trace(run_dir, {"event": "selection", "iteration": iteration, "policy": args.selection_policy, "exploration": args.exploration, "selected_parent": parent_name, "candidate_list": compact_candidates(scored), "selected_components": compact_candidates(scored, 1)[0] if scored else {}})
            parent_node = tree["nodes"][parent_name]
            parent_config = read_json(Path(parent_node["config"]))
        pool_attempts = max(args.max_duplicate_proposal_attempts, args.candidate_pool_size)
        for duplicate_attempt in range(1, pool_attempts + 1):
            if not should_generate_pool or parent_node is None or parent_config is None:
                break
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
            append_mcts_trace(run_dir, {"event": "proposal_pool_generated", "iteration": iteration, "selected_parent": parent_name, "candidate_count": len(proposal_candidates), "generated_proposals": generated_proposals, "proposal_budget": proposal_budget, "proposal_selection_mode": args.proposal_selection_mode})
            proposal_candidates.sort(key=lambda item: float(item["score"].get("score", 0.0)), reverse=True)
            selected_index = 0
            selected = None
            if args.proposal_selection_mode != "global_queue":
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
                cand_proposal["candidate_pool_selected"] = args.proposal_selection_mode != "global_queue" and selected is not None and rank == selected_index + 1
                cand_proposal["candidate_pool_policy"] = "global_queue_generate_many_train_best_available" if args.proposal_selection_mode == "global_queue" else "generate_many_prune_before_training"
                write_json(cand_config_path, cand_config)
                write_json(cand_proposal_path, cand_proposal)
                if args.proposal_selection_mode == "global_queue":
                    if item["duplicate"] and not args.force_blueprint:
                        reason = f"duplicate proposal pruned before global queue: {item['duplicate_reason']}"
                        add_pruned_node(tree, cand_name, cand_config_path, parent_name, iteration, cand_proposal, reason, rank, item["score"])
                        append_mcts_trace(run_dir, {"event": "proposal_pruned", "iteration": iteration, "selected_parent": parent_name, "child": cand_name, "chosen_blueprint": cand_proposal.get("strategy"), "candidate_rank": rank, "cheap_screen_score": item["score"], "reason": reason, "proposal_selection_mode": args.proposal_selection_mode})
                    else:
                        add_candidate_queued_node(tree, cand_name, cand_config_path, parent_name, iteration, cand_proposal, rank, item["score"])
                        append_mcts_trace(run_dir, {"event": "proposal_queued", "iteration": iteration, "selected_parent": parent_name, "child": cand_name, "chosen_blueprint": cand_proposal.get("strategy"), "candidate_rank": rank, "cheap_screen_score": item["score"], "proposal_selection_mode": args.proposal_selection_mode})
                elif selected is None or rank != selected_index + 1:
                    reason = "lower cheap-screen rank; not selected for rollout training"
                    if item["duplicate"]:
                        reason = f"duplicate proposal pruned before training: {item['duplicate_reason']}"
                    add_pruned_node(tree, cand_name, cand_config_path, parent_name, iteration, cand_proposal, reason, rank, item["score"])
                    append_mcts_trace(run_dir, {"event": "proposal_pruned", "iteration": iteration, "selected_parent": parent_name, "child": cand_name, "chosen_blueprint": cand_proposal.get("strategy"), "candidate_rank": rank, "cheap_screen_score": item["score"], "reason": reason})

        if args.proposal_selection_mode == "global_queue":
            queue = queued_candidates(tree)
            if queue:
                selected_row = queue[0]
                child_name = selected_row["name"]
                queued_node = selected_row["node"]
                parent_name = str(queued_node.get("parent", ""))
                child_config_path = Path(queued_node["config"])
                proposal_path = proposal_dir / f"{child_name}.proposal.json"
                child_config = read_json(child_config_path)
                proposal = read_json(proposal_path)
                proposal["candidate_pool_selected"] = True
                proposal["global_queue_selected"] = True
                proposal["global_queue_priority"] = selected_row["score"]
                proposal["candidate_pool_policy"] = "global_queue_generate_many_train_best_available"
                write_json(proposal_path, proposal)
                append_mcts_trace(run_dir, {"event": "global_queue_selected", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "global_queue_priority": selected_row["score"], "queued_candidates": len(queue)})
            else:
                child_config = None
                proposal = None

        if child_config is None or proposal is None:
            tree["events"].append({"iteration": iteration, "selected_parent": parent_name, "event": "no_candidate_selected_after_proposal_screen", "skips": duplicate_skips})
            no_improve += 1
            write_tree_and_failures(run_dir, tree, failures)
            continue
        child_name = str(child_config["node_name"])
        if args.proposal_selection_mode != "global_queue":
            child_config_path = proposal_dir / f"{child_name}.json"
            proposal_path = proposal_dir / f"{child_name}.proposal.json"
        else:
            child_config_path = Path(tree["nodes"][child_name]["config"])
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
            acquisition_results: list[dict[str, Any]] = []
            if args.enable_acquisition_loop:
                acquisition_results, registry_audit = attempt_realtime_artifact_acquisition(run_dir, args, child_name, proposal, missing_summary)
                refreshed_missing = summarize_missing_requirements(registry_audit, str(proposal.get("strategy", "")))
                proposal["realtime_acquisition_results"] = acquisition_results
                proposal["missing_required_artifacts"] = refreshed_missing.get("missing_required_artifacts", [])
                proposal["missing_required_artifact_paths"] = refreshed_missing.get("missing_required_artifact_paths", [])
                proposal["missing_required_artifact_sources"] = refreshed_missing.get("missing_required_artifact_sources", [])
                refresh_node_artifact_contract(proposal, registry_audit)
                write_json(child_config_path, child_config)
                write_json(proposal_path, proposal)
                append_mcts_trace(run_dir, {
                    "event": "realtime_artifact_acquisition_attempt",
                    "iteration": iteration,
                    "selected_parent": parent_name,
                    "child": child_name,
                    "chosen_blueprint": proposal.get("strategy"),
                    "items": acquisition_results,
                    "remaining_missing_required_artifacts": proposal["missing_required_artifacts"],
                })
                missing_summary = refreshed_missing
            if proposal["missing_required_artifacts"]:
                add_blocked_missing_artifact_node(tree, child_name, child_config_path, parent_name, iteration, proposal, missing_summary)
                failures.append({
                    "node": child_name,
                    "parent": parent_name,
                    "error": "requires_artifact_acquisition",
                    "strategy": proposal.get("strategy"),
                    "missing_required_artifacts": proposal["missing_required_artifacts"],
                    "missing_required_artifact_paths": proposal["missing_required_artifact_paths"],
                    "acquisition_results": acquisition_results,
                })
                no_improve += 1
                memory = rebuild_memory_from_tree(run_dir, tree, failures)
                append_mcts_trace(run_dir, {
                    "event": "artifact_acquisition_block_continued",
                    "iteration": iteration,
                    "selected_parent": parent_name,
                    "child": child_name,
                    "chosen_blueprint": proposal.get("strategy"),
                    "missing_required_artifacts": proposal["missing_required_artifacts"],
                    "policy": "block_only_after_realtime_acquisition_or_verified_unavailable_source",
                })
                write_tree_and_failures(run_dir, tree, failures)
                if proposal_budget is not None and generated_proposals >= proposal_budget and not queued_candidates(tree):
                    stop_reason = f"proposal budget exhausted ({generated_proposals}/{proposal_budget})"
                    break
                continue
            append_mcts_trace(run_dir, {
                "event": "artifact_acquisition_resolved_selected_rollout",
                "iteration": iteration,
                "selected_parent": parent_name,
                "child": child_name,
                "chosen_blueprint": proposal.get("strategy"),
                "policy": "resolver_succeeded_continue_to_implementation_or_training",
            })

        if proposal.get("requires_implementation"):
            add_pending_node(tree, child_name, child_config_path, parent_name, iteration, proposal)
            pending_count += 1
            append_mcts_trace(run_dir, {"event": "pending_implementation", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "scientific_selection": proposal.get("scientific_selection", {}), "structural_relation": proposal.get("structural_relation", ""), "implementation_request_path": proposal.get("implementation_request_path"), "artifact_contract_path": proposal.get("artifact_contract_path"), "smoke_contract_path": proposal.get("smoke_contract_path"), "parent_summary_path": proposal.get("parent_summary_path"), "auto_loop_enabled": bool(args.enable_implementation_loop)})
            write_tree_and_failures(run_dir, tree, failures)
            if args.enable_implementation_loop:
                append_mcts_trace(run_dir, {"event": "implementation_loop_start", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "repair_attempts": args.implementation_repair_attempts})
                implementation_report = implement_pending(run_dir, max_nodes=1, train=True, max_epochs=args.max_epochs, repair_attempts=args.implementation_repair_attempts, allow_skip=args.allow_implementation_skip)
                tree = read_json(run_dir / "tree.json")
                failures = read_json(run_dir / "failures.json").get("failures", []) if (run_dir / "failures.json").exists() else []
                memory = rebuild_memory_from_tree(run_dir, tree, failures)
                pending_count = len(implementation_queue(tree))
                item = (implementation_report.get("items") or [{}])[0]
                append_mcts_trace(run_dir, {"event": "implementation_loop_result", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "status": item.get("status"), "training": item.get("training"), "attempt_count": len(item.get("attempts", [])), "repair_log": implementation_report.get("repair_log"), "agent_decision_trace": implementation_report.get("agent_decision_trace")})
                if item.get("status") == "trained":
                    trained_rollouts += 1
                    val = float((item.get("training") or {}).get("best_val_macro_f1", -1.0) or -1.0)
                    if val > best_val + args.min_delta:
                        best_val = val
                        no_improve = 0
                    else:
                        no_improve += 1
                    write_tree_and_failures(run_dir, tree, failures)
                    if trained_node_budget is not None and trained_rollouts >= trained_node_budget:
                        stop_reason = f"trained-node budget exhausted ({trained_rollouts}/{trained_node_budget})"
                        break
                    continue
                if item.get("status") == "failed":
                    no_improve += 1
                    write_tree_and_failures(run_dir, tree, failures)
                    continue
                if item.get("status") == "requires_realtime_implementation":
                    stop_reason = f"realtime implementation required for selected node {child_name}"
                    append_mcts_trace(run_dir, {"event": "realtime_implementation_required", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "task_path": item.get("task_path"), "reason": item.get("reason"), "policy": "current_codex_must_implement_node_local_model_then_resume"})
                    write_tree_and_failures(run_dir, tree, failures)
                    break
                if item.get("status") == "implementation_skipped":
                    no_improve += 1
                    append_mcts_trace(run_dir, {"event": "implementation_skipped_continued", "iteration": iteration, "selected_parent": parent_name, "child": child_name, "chosen_blueprint": proposal.get("strategy"), "task_path": item.get("task_path"), "skip_reason": item.get("skip_reason"), "policy": "skip_unimplemented_candidate_and_continue_global_queue_without_fallback"})
                    write_tree_and_failures(run_dir, tree, failures)
                    if args.proposal_selection_mode == "global_queue":
                        continue
                write_tree_and_failures(run_dir, tree, failures)
            if pending_count >= args.max_pending_implementations and args.proposal_selection_mode != "global_queue":
                stop_reason = f"pending implementation limit reached ({pending_count})"
                break
            if args.proposal_selection_mode == "global_queue":
                continue
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

    if args.proposal_selection_mode == "global_queue" and trained_node_budget is not None and trained_rollouts == 0:
        if str(stop_reason).startswith("proposal budget exhausted"):
            stop_reason = "framework_failed_no_generated_child_trained: proposal budget exhausted before any generated rollout trained"
    memory = rebuild_memory_from_tree(run_dir, tree, failures)
    write_tree_and_failures(run_dir, tree, failures)
    write_summary(tree, args.summary, failures, stop_reason)
    run_manifest_path = write_run_manifest(run_dir, args, tree, failures, stop_reason, registry_audit)
    result = {"tree": str(run_dir / "tree.json"), "summary": str(args.summary), "mcts_trace": str(run_dir / "mcts_trace.jsonl"), "implementation_queue": str(run_dir / "implementation_queue.json"), "acquisition_queue": str(run_dir / "acquisition_queue.json"), "artifact_acquisition_command": f"python -m vc_demo.harness.artifact_acquisition --queue {run_dir / 'acquisition_queue.json'} --registry {args.artifact_registry or Path('configs/artifacts/k562_registry.json')} --sources configs/artifacts/acquisition_sources.json --cell-line K562 --output-dir {run_dir / 'artifact_acquisition'} --execute-known", "run_manifest": str(run_manifest_path), "search_memory": str(run_dir / "search_memory.json"), "stop_reason": stop_reason, "failures": len(failures), "pending_implementations": pending_count, "generated_proposals": generated_proposals, "proposal_budget": proposal_budget, "trained_rollouts_this_invocation": trained_rollouts, "trained_node_budget": trained_node_budget, "candidate_pool_size": args.candidate_pool_size, "proposal_selection_mode": args.proposal_selection_mode, "queued_candidates": len(queued_candidates(tree))}
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
    parser.add_argument("--enable-implementation-loop", action="store_true", help="Automatically materialize selected planned nodes, run native smoke, train_pending, and repair-log failures before returning to MCTS.")
    parser.add_argument("--enable-acquisition-loop", action=argparse.BooleanOptionalAction, default=True, help="Before blocking a selected rollout for missing artifacts, run source-backed acquisition resolvers, re-audit, and continue if resolved. Disable only for negative smoke tests.")
    parser.add_argument("--allow-implementation-skip", action="store_true", help="Loop/self-test only: allow missing node-local templates to become implementation_skipped. Formal full runs should leave this disabled so the active Codex must implement selected artifact-present nodes before resume.")
    parser.add_argument("--implementation-repair-attempts", type=int, default=3, help="Maximum compile/native-smoke/train repair attempts for the automatic implementation loop.")
    parser.add_argument("--force-blueprint", default=None)
    parser.add_argument("--artifact-registry", type=Path, default=None)
    parser.add_argument("--artifact-aware-blueprint-policy", action=argparse.BooleanOptionalAction, default=True, help="Prefer executable blueprints whose required artifacts are already present before blueprints that would trigger acquisition.")
    parser.add_argument("--allow-missing-artifact-fallbacks", action="store_true", help="Allow planned artifact blueprints to train explicit fallback models when required artifacts are missing. Default is strict: block and stop.")
    parser.add_argument("--official-blueprint-space", action="store_true", help="Restrict child proposals to official K562 paper-level blueprints.")
    parser.add_argument("--max-blueprint-repeats", type=int, default=2, help="Global repeat limit per blueprint; -1 disables the global duplicate guard.")
    parser.add_argument("--allow-parent-duplicate-blueprints", action="store_true", help="Allow the same parent to generate the same blueprint more than once.")
    parser.add_argument("--max-duplicate-proposal-attempts", type=int, default=8, help="How many candidate blueprints to try before skipping an iteration as duplicate-only.")
    parser.add_argument("--candidate-pool-size", type=int, default=4, help="Paper-aligned default: generate multiple proposal candidates per selected parent.")
    parser.add_argument("--proposal-selection-mode", choices=["local_top1", "global_queue"], default="local_top1", help="local_top1 trains the best candidate from the current parent pool; global_queue queues feasible candidates from all parent pools and trains the globally highest-priority next rollout.")
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
