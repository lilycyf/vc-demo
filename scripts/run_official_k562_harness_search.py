from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vc_demo.harness.official_k562_backend import OfficialK562BackendSpec, validate_official_k562_backend, write_backend_report
from vc_demo.harness.program_run import run_search
from scripts.build_official_k562_static_tree import build_tree, write_catalog
from scripts.write_official_k562_artifact_alignment import build_matrix, write_md
from scripts.audit_official_k562_paper_scale_search_space import build_audit as build_search_space_audit, write_md as write_search_space_audit_md


def main() -> None:
    parser = argparse.ArgumentParser(description="Run vc_demo MCTS/program search on the official K562 TSV task backend.")
    parser.add_argument("--experiment", default="official_k562_harness_backend_smoke")
    parser.add_argument("--run-dir", type=Path, default=Path("experiments/official_k562_harness_backend_smoke"))
    parser.add_argument("--root-configs", nargs="+", type=Path, default=list(OfficialK562BackendSpec.root_configs))
    parser.add_argument("--registry", type=Path, default=OfficialK562BackendSpec.registry_path)
    parser.add_argument("--data-dir", type=Path, default=OfficialK562BackendSpec.data_dir)
    parser.add_argument("--budget-nodes", type=int, default=2, help="Legacy rollout-iteration budget. Prefer --budget-proposals and --budget-trained-nodes for paper-aligned runs.")
    parser.add_argument("--budget-proposals", type=int, default=None, help="Maximum generated proposal candidates, including pruned/blocked/pending/trained candidates.")
    parser.add_argument("--budget-trained-nodes", type=int, default=None, help="Maximum rollout candidates allowed to finish training and backpropagate reward.")
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--max-children", type=int, default=2)
    parser.add_argument("--stop-no-improve", type=int, default=2)
    parser.add_argument("--min-family-coverage-before-stop", type=int, default=5, help="Official-mode guard: no-improvement early stop waits until this many blueprint families are covered.")
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--force-blueprint", default=None, help="Optional: force one blueprint for smoke tests. Default None lets MCTS sample the configured blueprint space.")
    parser.add_argument("--allow-planned-blueprints", action="store_true")
    parser.add_argument("--max-pending-implementations", type=int, default=1)
    parser.add_argument("--selection-policy", choices=["uct", "puct"], default="uct")
    parser.add_argument("--max-blueprint-repeats", type=int, default=2)
    parser.add_argument("--allow-parent-duplicate-blueprints", action="store_true")
    parser.add_argument("--max-duplicate-proposal-attempts", type=int, default=8)
    parser.add_argument("--candidate-pool-size", type=int, default=4, help="Paper-aligned default: generate multiple proposal candidates per selected parent.")
    parser.add_argument("--proposal-selection-mode", choices=["local_top1", "global_queue"], default="local_top1", help="local_top1 trains current-pool top1; global_queue trains the best queued proposal across all generated candidates.")
    parser.add_argument("--exploration", type=float, default=1.4142135623730951)
    parser.add_argument("--official-blueprint-space", action="store_true", default=False)
    parser.add_argument("--strict-artifacts", action="store_true", default=True)
    parser.add_argument("--enable-repair-loop", action="store_true", help="Compatibility alias for --enable-implementation-loop.")
    parser.add_argument("--enable-implementation-loop", action="store_true", help="Automatically materialize selected planned nodes, run native smoke, train_pending, and repair-log failures.")
    parser.add_argument("--allow-implementation-skip", action="store_true", help="Loop/self-test only: allow missing node-local templates to become implementation_skipped. Formal full runs should leave this disabled.")
    parser.add_argument("--implementation-repair-attempts", type=int, default=3, help="Maximum attempts for compile/native-smoke/train repair in the automatic implementation loop.")
    parser.add_argument("--enable-acquisition-loop", action="store_true", help="Accepted for paper-level runbooks; missing artifacts are recorded in acquisition_queue.json.")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    if args.candidate_pool_size < 1:
        raise SystemExit("--candidate-pool-size must be >= 1")
    if args.official_blueprint_space and args.candidate_pool_size < 2:
        raise SystemExit("official paper-aligned search requires --candidate-pool-size >= 2; proposal pruning is not optional in official mode")

    backend_spec = OfficialK562BackendSpec(data_dir=args.data_dir, registry_path=args.registry, root_configs=tuple(args.root_configs))
    audit = validate_official_k562_backend(backend_spec, strict=True)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    audit_json = args.run_dir / "official_k562_backend_audit.json"
    audit_md = args.run_dir / "official_k562_backend_audit.md"
    audit_json.write_text(json.dumps(audit, indent=2) + "\n")
    write_backend_report(audit_md, audit)

    alignment_dir = args.run_dir / "alignment"
    static_tree = build_tree(Path("/workspace/_external/VCHarness/K562_cls/static"), "node2-1-1-1-1-1")
    (alignment_dir / "official_k562_static_tree.json").parent.mkdir(parents=True, exist_ok=True)
    (alignment_dir / "official_k562_static_tree.json").write_text(json.dumps(static_tree, indent=2) + "\n")
    (alignment_dir / "official_k562_family_mapping.json").write_text(json.dumps(static_tree.get("family_mapping", {}), indent=2) + "\n")
    write_catalog(static_tree, alignment_dir / "official_k562_node_catalog.md")
    best = {"best_path": static_tree.get("best_path"), "best_lineage": static_tree.get("best_lineage", []), "nodes": [static_tree["nodes"][n] for n in static_tree.get("best_lineage", [])]}
    (alignment_dir / "official_k562_best_path.json").write_text(json.dumps(best, indent=2) + "\n")
    matrix = build_matrix(args.registry, "K562")
    (alignment_dir / "official_k562_artifact_alignment_matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
    write_md(matrix, alignment_dir / "official_k562_artifact_alignment_matrix.md")
    search_space_audit = build_search_space_audit(Path("configs/official_k562_paper_scale_search_space.json"))
    (alignment_dir / "official_k562_paper_scale_search_space_audit.json").write_text(json.dumps(search_space_audit, indent=2) + "\n")
    write_search_space_audit_md(search_space_audit, alignment_dir / "official_k562_paper_scale_search_space_audit.md")

    ns = argparse.Namespace(
        experiment=args.experiment,
        root_configs=[str(p) for p in args.root_configs],
        run_dir=args.run_dir,
        summary=args.run_dir / "search_summary.md",
        budget_nodes=args.budget_nodes,
        budget_proposals=args.budget_proposals,
        budget_trained_nodes=args.budget_trained_nodes,
        max_epochs=args.max_epochs,
        max_children=args.max_children,
        exploration=args.exploration,
        selection_policy=args.selection_policy,
        stop_no_improve=args.stop_no_improve,
        min_family_coverage_before_stop=args.min_family_coverage_before_stop,
        min_delta=1e-4,
        seed=args.seed,
        allow_planned_blueprints=args.allow_planned_blueprints,
        max_pending_implementations=args.max_pending_implementations,
        enable_implementation_loop=bool(args.enable_implementation_loop or args.enable_repair_loop),
        implementation_repair_attempts=args.implementation_repair_attempts,
        allow_implementation_skip=args.allow_implementation_skip,
        force_blueprint=args.force_blueprint or None,
        artifact_registry=args.registry,
        artifact_aware_blueprint_policy=False,
        allow_missing_artifact_fallbacks=False,
        official_blueprint_space=args.official_blueprint_space,
        max_blueprint_repeats=args.max_blueprint_repeats,
        allow_parent_duplicate_blueprints=args.allow_parent_duplicate_blueprints,
        max_duplicate_proposal_attempts=args.max_duplicate_proposal_attempts,
        candidate_pool_size=args.candidate_pool_size,
        proposal_selection_mode=args.proposal_selection_mode,
        reset=args.reset,
    )
    result = run_search(ns)
    print(json.dumps({"backend_audit": str(audit_json), **result}, indent=2))


if __name__ == "__main__":
    main()
