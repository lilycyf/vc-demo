from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from vc_demo.harness.implementation_agent import implement_pending
from vc_demo.harness.program_run import run_search
from vc_demo.harness.state import read_json, write_json




def run_known_acquisition(run_dir: Path, registry: Path | None) -> dict[str, Any]:
    output_dir = run_dir / "artifact_acquisition"
    cmd = [
        sys.executable,
        "-m",
        "vc_demo.harness.artifact_acquisition",
        "--queue",
        str(run_dir / "acquisition_queue.json"),
        "--registry",
        str(registry or Path("configs/artifacts/k562_registry.json")),
        "--sources",
        "configs/artifacts/acquisition_sources.json",
        "--cell-line",
        "K562",
        "--output-dir",
        str(output_dir),
        "--execute-known",
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    report_path = output_dir / "artifact_acquisition_report.json"
    report = read_json(report_path) if report_path.exists() else {}
    return {"command": " ".join(cmd), "returncode": proc.returncode, "stdout": proc.stdout[-12000:], "stderr": proc.stderr[-12000:], "report": report}


def acquisition_complete(acquisition_result: dict[str, Any]) -> bool:
    items = acquisition_result.get("report", {}).get("items", [])
    return bool(items) and all(bool(item.get("present_after")) for item in items)

def _queue_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return list(read_json(path).get("items", []))


def autonomous_loop(args: argparse.Namespace) -> dict[str, Any]:
    cycles: list[dict[str, Any]] = []
    for cycle in range(1, args.max_cycles + 1):
        result = run_search(args)
        run_dir = args.run_dir
        impl = _queue_items(run_dir / "implementation_queue.json")
        acq = _queue_items(run_dir / "acquisition_queue.json")
        cycle_row: dict[str, Any] = {"cycle": cycle, "search": result, "implementation_items": len(impl), "acquisition_items": len(acq)}
        if acq:
            if args.auto_acquire_known:
                acquisition_result = run_known_acquisition(run_dir, args.artifact_registry)
                cycle_row["artifact_acquisition"] = acquisition_result
                if acquisition_result.get("returncode") == 0 and acquisition_complete(acquisition_result):
                    cycle_row["status"] = "known_artifacts_acquired_resume_search"
                    cycles.append(cycle_row)
                    args.reset = False
                    continue
            cycle_row["status"] = "requires_artifact_acquisition"
            cycle_row["next_command"] = result.get("artifact_acquisition_command")
            cycles.append(cycle_row)
            break
        if impl and args.auto_implement_pending:
            impl_report = implement_pending(run_dir, max_nodes=args.max_auto_implement_nodes, train=True, max_epochs=args.max_epochs, repair_attempts=args.repair_attempts)
            cycle_row["implementation_agent"] = impl_report
            statuses = {str(item.get("status")) for item in impl_report.get("items", [])}
            if any(status != "implemented" for status in statuses):
                cycle_row["status"] = "implementation_skipped"
                cycles.append(cycle_row)
                break
            cycles.append(cycle_row)
            args.reset = False
            continue
        if impl:
            cycle_row["status"] = "implementation_skipped"
            cycles.append(cycle_row)
            break
        cycle_row["status"] = "complete_or_budget_exhausted"
        cycles.append(cycle_row)
        break
    report = {"format": "vc_demo_autonomous_loop.v1", "cycles": cycles}
    write_json(args.run_dir / "autonomous_loop_report.json", report)
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run search plus implementation-agent handoffs as a bounded autonomous loop.")
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
    parser.add_argument("--artifact-aware-blueprint-policy", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--allow-missing-artifact-fallbacks", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--max-blueprint-repeats", type=int, default=2)
    parser.add_argument("--allow-parent-duplicate-blueprints", action="store_true")
    parser.add_argument("--max-duplicate-proposal-attempts", type=int, default=8)
    parser.add_argument("--auto-implement-pending", action="store_true")
    parser.add_argument("--max-auto-implement-nodes", type=int, default=1)
    parser.add_argument("--repair-attempts", type=int, default=1)
    parser.add_argument("--max-cycles", type=int, default=4)
    parser.add_argument("--auto-acquire-known", action="store_true", help="Automatically run source-backed acquisition resolver for known artifacts and resume if all queued artifacts become present.")
    args = parser.parse_args()
    if args.summary is None:
        args.summary = args.run_dir / "search_summary.md"
    autonomous_loop(args)


if __name__ == "__main__":
    main()
