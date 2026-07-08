from __future__ import annotations

import argparse
import json
from pathlib import Path

from vc_demo.harness.official_k562_backend import OfficialK562BackendSpec, validate_official_k562_backend, write_backend_report
from vc_demo.harness.program_run import run_search


def main() -> None:
    parser = argparse.ArgumentParser(description="Run vc_demo MCTS/program search on the official K562 TSV task backend.")
    parser.add_argument("--experiment", default="official_k562_harness_backend_smoke")
    parser.add_argument("--run-dir", type=Path, default=Path("experiments/official_k562_harness_backend_smoke"))
    parser.add_argument("--root-configs", nargs="+", type=Path, default=list(OfficialK562BackendSpec.root_configs))
    parser.add_argument("--registry", type=Path, default=OfficialK562BackendSpec.registry_path)
    parser.add_argument("--data-dir", type=Path, default=OfficialK562BackendSpec.data_dir)
    parser.add_argument("--budget-nodes", type=int, default=2)
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--max-children", type=int, default=2)
    parser.add_argument("--stop-no-improve", type=int, default=2)
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--force-blueprint", default="dual_path_gated_low_rank", help="Default smoke uses an implemented architecture blueprint to avoid planned-node handoff.")
    parser.add_argument("--allow-planned-blueprints", action="store_true")
    parser.add_argument("--max-pending-implementations", type=int, default=1)
    parser.add_argument("--selection-policy", choices=["uct", "puct"], default="uct")
    parser.add_argument("--exploration", type=float, default=1.4142135623730951)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    backend_spec = OfficialK562BackendSpec(data_dir=args.data_dir, registry_path=args.registry, root_configs=tuple(args.root_configs))
    audit = validate_official_k562_backend(backend_spec, strict=True)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    audit_json = args.run_dir / "official_k562_backend_audit.json"
    audit_md = args.run_dir / "official_k562_backend_audit.md"
    audit_json.write_text(json.dumps(audit, indent=2) + "\n")
    write_backend_report(audit_md, audit)

    ns = argparse.Namespace(
        experiment=args.experiment,
        root_configs=[str(p) for p in args.root_configs],
        run_dir=args.run_dir,
        summary=args.run_dir / "search_summary.md",
        budget_nodes=args.budget_nodes,
        max_epochs=args.max_epochs,
        max_children=args.max_children,
        exploration=args.exploration,
        selection_policy=args.selection_policy,
        stop_no_improve=args.stop_no_improve,
        min_delta=1e-4,
        seed=args.seed,
        allow_planned_blueprints=args.allow_planned_blueprints,
        max_pending_implementations=args.max_pending_implementations,
        force_blueprint=args.force_blueprint or None,
        artifact_registry=args.registry,
        artifact_aware_blueprint_policy=True,
        allow_missing_artifact_fallbacks=False,
        max_blueprint_repeats=2,
        allow_parent_duplicate_blueprints=False,
        max_duplicate_proposal_attempts=8,
        reset=args.reset,
    )
    result = run_search(ns)
    print(json.dumps({"backend_audit": str(audit_json), **result}, indent=2))


if __name__ == "__main__":
    main()
