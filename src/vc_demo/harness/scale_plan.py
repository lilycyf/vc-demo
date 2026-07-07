from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from vc_demo.harness.state import write_json


PROFILES = {
    "smoke": {"budget_nodes": 3, "max_epochs": 1, "max_cycles": 2, "stop_no_improve": 3, "purpose": "validate wiring only"},
    "demo": {"budget_nodes": 16, "max_epochs": 3, "max_cycles": 4, "stop_no_improve": 6, "purpose": "small end-to-end demo"},
    "single_cellline_small": {"budget_nodes": 50, "max_epochs": 4, "max_cycles": 8, "stop_no_improve": 10, "purpose": "small paper-style single-cell-line search"},
    "single_cellline_medium": {"budget_nodes": 100, "max_epochs": 6, "max_cycles": 12, "stop_no_improve": 16, "purpose": "more credible single-cell-line search"},
    "paper_scale_single_cellline": {"budget_nodes": 200, "max_epochs": 8, "max_cycles": 20, "stop_no_improve": 24, "purpose": "large single-cell-line approximation; still below 600+ multi-task paper scale"},
}


def build_plan(profile: str, run_dir: str, experiment: str, root_configs: list[str]) -> dict[str, Any]:
    if profile not in PROFILES:
        raise KeyError(f"unknown profile {profile}; choose from {sorted(PROFILES)}")
    p = dict(PROFILES[profile])
    command = [
        "python -m vc_demo.harness.autonomous_run",
        f"--experiment {experiment}",
        "--root-configs " + " ".join(root_configs),
        f"--run-dir {run_dir}",
        f"--budget-nodes {p['budget_nodes']}",
        f"--max-epochs {p['max_epochs']}",
        "--max-children 3",
        f"--stop-no-improve {p['stop_no_improve']}",
        "--exploration 1.4142135623730951",
        "--selection-policy uct",
        "--artifact-registry configs/artifacts/k562_registry.json",
        "--seed 53",
        "--allow-planned-blueprints",
        "--auto-implement-pending",
        "--auto-acquire-known",
        "--max-auto-implement-nodes 1",
        "--repair-attempts 2",
        f"--max-cycles {p['max_cycles']}",
        "--reset",
    ]
    return {
        "format": "vc_demo_scale_plan.v1",
        "profile": profile,
        "profile_settings": p,
        "experiment": experiment,
        "run_dir": run_dir,
        "root_configs": root_configs,
        "command": " \\\n  ".join(command),
        "records_to_preserve": ["preflight.json", "benchmark_audit.json", "artifact_readiness.json", "tree.json", "search_memory.json", "run_manifest.json", "search_summary.md", "final_analysis.md", "final_conclusion.md"],
        "scale_note": "The original paper reports 600+ models across a broader system. This profile scopes a single-cell-line approximation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a scale/budget plan for formal single-cell-line searches.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--root-configs", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plan = build_plan(args.profile, args.run_dir, args.experiment, args.root_configs)
    write_json(args.output, plan)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
