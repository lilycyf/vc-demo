from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import audit_registry, load_registry


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def load_queue(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    if isinstance(payload, dict):
        return list(payload.get("items", []))
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported acquisition queue shape in {path}")


def source_map(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    return {str(item["id"]): item for item in payload.get("artifacts", [])}


def registry_entry(registry: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    for artifact in registry.get("artifacts", []):
        if artifact.get("id") == artifact_id:
            return artifact
    return {}


def run_command(command: str) -> dict[str, Any]:
    proc = subprocess.run(shlex.split(command), text=True, capture_output=True)
    return {
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-12000:],
        "stderr": proc.stderr[-12000:],
    }


def render_task(queue_item: dict[str, Any], source: dict[str, Any], registry_item: dict[str, Any], output_dir: Path) -> Path:
    artifact_id = queue_item.get("artifact_id")
    expected_path = queue_item.get("expected_path") or source.get("expected_path") or registry_item.get("path") or ""
    task_path = output_dir / f"ACQUIRE_{artifact_id}.md"
    research_questions = source.get("research_questions", []) or []
    required_outputs = source.get("required_outputs", []) or []
    lines = [
        f"# Acquire Artifact: `{artifact_id}`",
        "",
        "You are the Codex artifact acquisition agent for a strict VCHarness-style run.",
        "Do not train fallback models and do not fabricate data.",
        "",
        "## Trigger",
        f"- Node: `{queue_item.get('node', '')}`",
        f"- Strategy/blueprint: `{queue_item.get('strategy', '')}`",
        f"- Missing artifact: `{artifact_id}`",
        f"- Expected path: `{expected_path}`",
        f"- Registry source hint: `{registry_item.get('source') or source.get('source') or queue_item.get('source', '')}`",
        f"- Resolver: `{source.get('resolver', 'unconfigured')}`",
        "",
        "## Required Workflow",
        "1. Search official or primary sources for the real artifact or a reproducible way to build it.",
        "2. Prefer exact public artifacts from the paper authors, official model/project repositories, HuggingFace datasets, STRING/Reactome/GO/MSigDB official releases, or documented checkpoints.",
        "3. Download/build only source-backed artifacts. Record URL, version/date, checksum or file size, filtering rules, and coverage.",
        "4. Write the artifact to the expected path or update the registry path if a better audited layout is necessary.",
        "5. Update `configs/artifacts/k562_registry.json` with source-backed metadata only.",
        "6. Run `python -m vc_demo.harness.artifact_registry --cell-line K562` and save the audit JSON/summary.",
        "7. Resume the strict search without `--allow-missing-artifact-fallbacks`.",
        "",
        "## Research Questions",
    ]
    lines += [f"- {q}" for q in research_questions] if research_questions else ["- Identify and document the official source and exact alignment procedure."]
    lines += ["", "## Required Outputs"]
    lines += [f"- {item}" for item in required_outputs] if required_outputs else ["- Artifact files", "- Source/coverage summary", "- Registry update"]
    lines += [
        "",
        "## Forbidden",
        "- No random embeddings, random graphs, synthetic pathway memberships, or randomly initialized checkpoints marked as real artifacts.",
        "- No fallback training in formal search.",
        "- No registry `present` claim unless the expected file exists and provenance is recorded.",
        "",
        "## Handoff Back To Search",
        "After acquisition and audit, rerun the strict `program_run` command for the same run directory. If a new artifact is missing, repeat acquisition.",
    ]
    task_path.write_text("\n".join(lines) + "\n")
    return task_path


def resolve_item(item: dict[str, Any], sources: dict[str, dict[str, Any]], registry: dict[str, Any], output_dir: Path, execute_known: bool) -> dict[str, Any]:
    artifact_id = str(item.get("artifact_id", ""))
    src = sources.get(artifact_id, {})
    reg = registry_entry(registry, artifact_id)
    expected_path = Path(str(item.get("expected_path") or src.get("expected_path") or reg.get("path") or ""))
    present_before = bool(str(expected_path)) and expected_path.exists()
    result: dict[str, Any] = {
        "artifact_id": artifact_id,
        "node": item.get("node"),
        "strategy": item.get("strategy"),
        "expected_path": str(expected_path),
        "resolver": src.get("resolver", "unconfigured"),
        "can_execute_automatically": bool(src.get("can_execute_automatically")),
        "present_before": present_before,
        "action": "none",
    }
    if present_before:
        result["action"] = "verified_existing_file"
        result["present_after"] = True
        result["status"] = "already_present"
        return result

    command = src.get("command")
    if execute_known and src.get("can_execute_automatically") and command:
        result["action"] = "executed_known_resolver"
        command_result = run_command(str(command))
        result["command_result"] = command_result
        result["present_after"] = bool(str(expected_path)) and expected_path.exists()
        result["status"] = "acquired" if command_result["returncode"] == 0 and result["present_after"] else "resolver_failed_or_output_missing"
        return result

    task_path = render_task(item, src, reg, output_dir)
    result["action"] = "generated_codex_research_task"
    result["task_path"] = str(task_path)
    result["present_after"] = False
    result["status"] = "requires_codex_research_download_or_build"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve or prepare source-backed acquisition for missing VCHarness artifacts.")
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=Path("configs/artifacts/k562_registry.json"))
    parser.add_argument("--sources", type=Path, default=Path("configs/artifacts/acquisition_sources.json"))
    parser.add_argument("--cell-line", default="K562")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute-known", action="store_true", help="Run configured deterministic resolver commands for known source-backed artifacts.")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    queue = load_queue(args.queue)
    registry = load_registry(args.registry, args.cell_line)
    sources = source_map(args.sources)
    results = [resolve_item(item, sources, registry, args.output_dir, args.execute_known) for item in queue]
    audit = audit_registry(load_registry(args.registry, args.cell_line))
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "queue": str(args.queue),
        "registry": str(args.registry),
        "sources": str(args.sources),
        "execute_known": args.execute_known,
        "items": results,
        "registry_audit_after": audit,
        "next_action": "resume strict search if all queued artifacts are present; otherwise complete generated Codex acquisition tasks",
    }
    report_path = args.output_dir / "artifact_acquisition_report.json"
    write_json(report_path, report)
    print(json.dumps({"report": str(report_path), "items": results}, indent=2))


if __name__ == "__main__":
    main()
