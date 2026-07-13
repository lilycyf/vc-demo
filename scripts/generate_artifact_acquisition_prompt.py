from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> object:
    with path.open() as handle:
        return json.load(handle)


def queue_items(path: Path) -> list[dict[str, object]]:
    payload = read_json(path)
    if isinstance(payload, dict):
        return list(payload.get("items", []))
    if isinstance(payload, list):
        return list(payload)
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a short Codex prompt for source-backed artifact acquisition.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--branch", default="k562-generic-transfer-64x16-test")
    parser.add_argument("--cell-line", default="K562")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--artifact-id", action="append", default=[], help="Missing artifact id to include when the run queue is unavailable.")
    args = parser.parse_args()

    run_dir = args.run_dir
    queue_path = run_dir / "acquisition_queue.json"
    report_path = run_dir / "artifact_acquisition" / "artifact_acquisition_report.json"
    items = queue_items(queue_path) if queue_path.exists() else []
    task_paths: list[str] = []
    if report_path.exists():
        report = read_json(report_path)
        if isinstance(report, dict):
            for item in report.get("items", []):
                if isinstance(item, dict) and item.get("task_path"):
                    task_paths.append(str(item["task_path"]))
    for item in items:
        artifact_id = str(item.get("artifact_id", ""))
        candidate = run_dir / "artifact_acquisition" / f"ACQUIRE_{artifact_id}.md"
        if candidate.exists() and str(candidate) not in task_paths:
            task_paths.append(str(candidate))

    artifact_ids = {str(item.get("artifact_id")) for item in items if item.get("artifact_id")}
    artifact_ids.update(args.artifact_id)
    artifacts = ", ".join(sorted(artifact_ids)) or "<missing-artifact>"
    for artifact_id in args.artifact_id:
        candidate = run_dir / "artifact_acquisition" / f"ACQUIRE_{artifact_id}.md"
        if str(candidate) not in task_paths:
            task_paths.append(str(candidate))
    task_block = "\n".join(f"- `{path}`" for path in task_paths) or "- `<run>/artifact_acquisition/ACQUIRE_<artifact>.md`"
    prompt = f"""Run source-backed artifact acquisition on RunPod `/workspace/vc-demo`.

Branch: `{args.branch}`
CELL_LINE_ID: `{args.cell_line}`
RUN_DIR: `{run_dir}`
MISSING_ARTIFACTS: `{artifacts}`

Use repo instructions:
- `docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md`
- `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md`

Read acquisition task(s):
{task_block}

Goal:
Search official/primary public sources and either acquire/build the exact source-backed artifact(s), or write a blocker report proving why they are unavailable/non-equivalent.

Rules:
- do not fabricate artifacts
- do not use fallback/proxy substitutes
- do not mark registry `present` unless expected files exist and provenance is recorded
- if acquired, update registry/provenance and resume the same run with `scripts/run_generic_cellline_transfer_test.py --cell-line {args.cell_line} --level transfer_64x16 --resume --execute`
- if not acquired, keep the run blocked and report the checked sources and reason

Push results to the same run branch.
"""
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(prompt, encoding="utf-8")
    print(prompt)


if __name__ == "__main__":
    main()
