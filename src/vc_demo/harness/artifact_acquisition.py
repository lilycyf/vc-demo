from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import artifact_by_id_or_alias, audit_registry, load_registry


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
    mapping: dict[str, dict[str, Any]] = {}
    for item in payload.get("artifacts", []):
        ids = [str(item["id"]), *[str(alias) for alias in item.get("aliases", [])]]
        for artifact_id in ids:
            mapping[artifact_id] = item
    return mapping


def registry_entry(registry: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    for artifact in registry.get("artifacts", []):
        ids = {str(artifact.get("id", "")), *[str(alias) for alias in artifact.get("aliases", [])]}
        if artifact_id in ids:
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



def derive_class_distribution(expected_path: Path, registry_path: Path) -> dict[str, Any]:
    command = [
        "python",
        "scripts/build_k562_class_distribution.py",
        "--data-dir",
        "data/cell_lines/official_k562_cls",
        "--output",
        str(expected_path),
        "--registry",
        str(registry_path),
        "--update-registry",
    ]
    proc = subprocess.run(command, text=True, capture_output=True)
    return {
        "command": " ".join(shlex.quote(part) for part in command),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-12000:],
        "stderr": proc.stderr[-12000:],
    }

def resolve_item(item: dict[str, Any], sources: dict[str, dict[str, Any]], registry: dict[str, Any], output_dir: Path, execute_known: bool) -> dict[str, Any]:
    artifact_id = str(item.get("artifact_id", ""))
    src = sources.get(artifact_id, {})
    reg = registry_entry(registry, artifact_id)
    expected_path = Path(str(item.get("expected_path") or src.get("expected_path") or reg.get("path") or ""))
    file_exists_before = bool(str(expected_path)) and expected_path.exists()
    audited = artifact_by_id_or_alias(audit_registry(registry), artifact_id)
    present_before = file_exists_before and bool(audited.get("present", False))
    result: dict[str, Any] = {
        "artifact_id": artifact_id,
        "node": item.get("node"),
        "strategy": item.get("strategy"),
        "expected_path": str(expected_path),
        "resolver": src.get("resolver", "unconfigured"),
        "can_execute_automatically": bool(src.get("can_execute_automatically")),
        "file_exists_before": file_exists_before,
        "present_before": present_before,
        "audited_status_before": audited.get("resolved_status"),
        "audit_issue_before": audited.get("shape_issue") or audited.get("pathway_membership_read_error"),
        "action": "none",
    }
    if present_before:
        result["action"] = "verified_existing_file"
        result["present_after"] = True
        result["status"] = "already_present"
        return result

    command = src.get("command")
    if execute_known and src.get("can_execute_automatically") and src.get("resolver") == "derive_from_official_train_labels":
        result["action"] = "executed_train_only_class_distribution_resolver"
        if not str(expected_path):
            expected_path = Path("experiments/official_k562_scientific_policy_run_50/artifacts/class_distribution.json")
            result["expected_path"] = str(expected_path)
        command_result = derive_class_distribution(expected_path, Path(str(registry.get("registry_path", "configs/artifacts/k562_registry.json"))))
        result["command_result"] = command_result
        audited_after = artifact_by_id_or_alias(audit_registry(load_registry(registry.get("registry_path", "configs/artifacts/k562_registry.json"))), artifact_id)
        result["file_exists_after"] = bool(str(expected_path)) and expected_path.exists()
        result["present_after"] = result["file_exists_after"] and bool(audited_after.get("present", False))
        result["audited_status_after"] = audited_after.get("resolved_status")
        result["audit_issue_after"] = audited_after.get("class_distribution_issue")
        result["status"] = "acquired" if command_result["returncode"] == 0 and result["present_after"] else "resolver_failed_or_output_invalid"
        return result
    if execute_known and src.get("can_execute_automatically") and command:
        result["action"] = "executed_known_resolver"
        command_result = run_command(str(command))
        result["command_result"] = command_result
        audited_after = artifact_by_id_or_alias(audit_registry(registry), artifact_id)
        result["file_exists_after"] = bool(str(expected_path)) and expected_path.exists()
        result["present_after"] = result["file_exists_after"] and bool(audited_after.get("present", False))
        result["audited_status_after"] = audited_after.get("resolved_status")
        result["audit_issue_after"] = audited_after.get("shape_issue") or audited_after.get("pathway_membership_read_error")
        result["status"] = "acquired" if command_result["returncode"] == 0 and result["present_after"] else "resolver_failed_or_output_invalid"
        return result

    task_path = render_task(item, src, reg, output_dir)
    result["action"] = "generated_codex_research_task"
    result["task_path"] = str(task_path)
    result["present_after"] = False
    result["status"] = "requires_codex_research_download_or_build"
    return result



def write_run_queues(run_dir: Path, tree: dict[str, Any]) -> None:
    implementation_items: list[dict[str, Any]] = []
    acquisition_items: list[dict[str, Any]] = []
    for name, node in tree.get("nodes", {}).items():
        if node.get("status") == "needs_implementation":
            implementation_items.append({
                "node": name,
                "program_dir": node.get("program_dir"),
                "implementation_request_path": node.get("implementation_request_path"),
                "program_model_path": node.get("program_model_path"),
                "pipeline_manifest_path": node.get("pipeline_manifest_path"),
                "artifact_contract_path": node.get("artifact_contract_path"),
                "smoke_contract_path": node.get("smoke_contract_path"),
                "parent_summary_path": node.get("parent_summary_path"),
                "strategy": node.get("strategy"),
                "artifact_requirements": node.get("artifact_requirements", []),
                "scientific_selection": node.get("scientific_selection", {}),
                "structural_relation": node.get("structural_relation", ""),
            })
        if node.get("status") in {"requires_artifact_acquisition", "blocked_missing_artifact"}:
            missing = node.get("missing_required_artifacts", []) or []
            paths = node.get("missing_required_artifact_paths", []) or []
            sources = node.get("missing_required_artifact_sources", []) or []
            for idx, artifact_id in enumerate(missing):
                acquisition_items.append({
                    "node": name,
                    "strategy": node.get("strategy"),
                    "artifact_id": artifact_id,
                    "expected_path": paths[idx] if idx < len(paths) else "",
                    "source": sources[idx] if idx < len(sources) else "",
                    "action": "search_download_or_build_real_artifact",
                    "resume_after": "update registry, rerun artifact audit, then resume search without fallback",
                })
    write_json(run_dir / "implementation_queue.json", {"items": implementation_items})
    write_json(run_dir / "acquisition_queue.json", {"items": acquisition_items})


def refresh_artifact_contract(path: Path, audit: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "updated": False, "reason": "missing_contract"}
    contract = read_json(path)
    required = list(contract.get("required_artifacts", []))
    present: list[str] = []
    missing: list[str] = []
    rows: list[dict[str, Any]] = []
    for artifact_id in required:
        row = artifact_by_id_or_alias(audit, str(artifact_id))
        rows.append(row)
        if row.get("present"):
            present.append(str(artifact_id))
        else:
            missing.append(str(artifact_id))
    contract["present_required_artifacts"] = present
    contract["missing_required_artifacts"] = missing
    contract["artifact_rows"] = rows
    write_json(path, contract)
    return {"path": str(path), "updated": True, "missing_required_artifacts": missing}


def unblock_acquired_artifacts(run_dir: Path, registry: dict[str, Any]) -> dict[str, Any]:
    tree_path = run_dir / "tree.json"
    failures_path = run_dir / "failures.json"
    if not tree_path.exists():
        return {"run_dir": str(run_dir), "updated": 0, "reason": "missing_tree"}
    tree = read_json(tree_path)
    failures_payload = read_json(failures_path) if failures_path.exists() else {"failures": []}
    failures = list(failures_payload.get("failures", []))
    audit = audit_registry(registry)
    unblocked: list[dict[str, Any]] = []
    still_blocked: list[dict[str, Any]] = []
    for name, node in tree.get("nodes", {}).items():
        if node.get("status") not in {"requires_artifact_acquisition", "blocked_missing_artifact"}:
            continue
        missing_ids = [str(x) for x in node.get("missing_required_artifacts", []) or []]
        unresolved = [artifact_id for artifact_id in missing_ids if not artifact_by_id_or_alias(audit, artifact_id).get("present")]
        contract_result = refresh_artifact_contract(Path(str(node.get("artifact_contract_path", ""))), audit) if node.get("artifact_contract_path") else {}
        if unresolved:
            node["missing_required_artifacts"] = unresolved
            still_blocked.append({"node": name, "missing_required_artifacts": unresolved, "artifact_contract": contract_result})
            continue
        node["status"] = "needs_implementation"
        node["stage"] = "improve"
        node["blocked_reason"] = "resolved_by_artifact_acquisition"
        node["missing_required_artifacts"] = []
        node["missing_required_artifact_paths"] = []
        node["missing_required_artifact_sources"] = []
        unblocked.append({"node": name, "status": node["status"], "artifact_contract": contract_result})
    resolved_nodes = {row["node"] for row in unblocked}
    failures = [row for row in failures if not (row.get("node") in resolved_nodes and row.get("error") == "requires_artifact_acquisition")]
    write_json(tree_path, tree)
    write_json(failures_path, {"failures": failures})
    write_run_queues(run_dir, tree)
    return {"run_dir": str(run_dir), "updated": len(unblocked), "unblocked": unblocked, "still_blocked": still_blocked}

def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve or prepare source-backed acquisition for missing VCHarness artifacts.")
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=Path("configs/artifacts/k562_registry.json"))
    parser.add_argument("--sources", type=Path, default=Path("configs/artifacts/acquisition_sources.json"))
    parser.add_argument("--cell-line", default="K562")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None, help="Optional run directory whose acquisition-blocked nodes should be unblocked after artifacts become present.")
    parser.add_argument("--execute-known", action="store_true", help="Run configured deterministic resolver commands for known source-backed artifacts.")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    queue = load_queue(args.queue)
    registry = load_registry(args.registry, args.cell_line)
    sources = source_map(args.sources)
    results = [resolve_item(item, sources, registry, args.output_dir, args.execute_known) for item in queue]
    audit = audit_registry(load_registry(args.registry, args.cell_line))
    unblock_result = unblock_acquired_artifacts(args.run_dir, load_registry(args.registry, args.cell_line)) if args.run_dir else None
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "queue": str(args.queue),
        "registry": str(args.registry),
        "sources": str(args.sources),
        "execute_known": args.execute_known,
        "items": results,
        "registry_audit_after": audit,
        "unblock_result": unblock_result,
        "next_action": "resume strict search if all queued artifacts are present; otherwise complete generated Codex acquisition tasks",
    }
    report_path = args.output_dir / "artifact_acquisition_report.json"
    write_json(report_path, report)
    print(json.dumps({"report": str(report_path), "items": results}, indent=2))


if __name__ == "__main__":
    main()
