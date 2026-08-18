from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_path(row: dict[str, Any]) -> Path | None:
    value = row.get("path") or row.get("expected_path")
    return Path(str(value)) if value else None


def artifact_present(row: dict[str, Any]) -> bool:
    path = artifact_path(row)
    if path is None or not path.exists():
        return False
    if path.is_dir():
        return any(child.is_file() and child.stat().st_size > 0 for child in path.rglob("*"))
    return path.is_file() and path.stat().st_size > 0


def artifact_registry(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    return {str(item.get("id")): item for item in payload.get("artifacts", [])}


def audit(search_space: Path, registry_path: Path) -> dict[str, Any]:
    space = read_json(search_space)
    registry = artifact_registry(registry_path)
    artifact_status = {
        artifact_id: {
            "present": artifact_present(row),
            "expected_path": str(artifact_path(row) or ""),
            "status": row.get("status"),
            "acquisition_policy": row.get("acquisition_policy"),
        }
        for artifact_id, row in registry.items()
    }
    rows = []
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for family in space.get("foundation_families", []):
        family_id = str(family.get("family") or family.get("id") or "unknown")
        for bp in family.get("blueprints", []):
            required = [str(x) for x in bp.get("required_artifacts", [])]
            missing = [x for x in required if not artifact_status.get(x, {}).get("present")]
            row = {
                "family": family_id,
                "id": str(bp.get("id")),
                "implementation_status": bp.get("implementation_status", "unspecified"),
                "search_space_status": bp.get("search_space_status", "selectable"),
                "required_artifacts": required,
                "present_artifacts": [x for x in required if x not in missing],
                "missing_artifacts": missing,
                "executable_now": not missing and str(bp.get("implementation_status", "")).startswith("implemented"),
                "acquirable_or_buildable": "acquirable" in str(bp.get("implementation_status", "")) or "buildable" in str(bp.get("implementation_status", "")),
                "artifact_usefulness_control_required": bool(bp.get("artifact_usefulness_control_required")),
            }
            rows.append(row)
            by_family[family_id].append(row)
    status_counts = Counter(row["implementation_status"] for row in rows)
    family_summary = {}
    for family_id, family_rows in by_family.items():
        family_summary[family_id] = {
            "blueprints": len(family_rows),
            "executable_now": sum(1 for row in family_rows if row["executable_now"]),
            "missing_artifact_blueprints": sum(1 for row in family_rows if row["missing_artifacts"]),
            "implementation_status_counts": dict(Counter(row["implementation_status"] for row in family_rows)),
        }
    dims = space.get("search_dimensions", {}) or {}
    combinatorial_count = 1
    dimension_sizes = {}
    for key, values in dims.items():
        size = len(values) if isinstance(values, list) else 0
        dimension_sizes[key] = size
        if size:
            combinatorial_count *= size
    return {
        "format": "vc_demo_search_space_audit.v1",
        "search_space": str(search_space),
        "artifact_registry": str(registry_path),
        "search_space_id": space.get("id"),
        "schema_version": space.get("schema_version"),
        "foundation_blueprint_count": len(rows),
        "implementation_status_counts": dict(status_counts),
        "executable_now_count": sum(1 for row in rows if row["executable_now"]),
        "artifact_present_blueprint_count": sum(1 for row in rows if row["required_artifacts"] and not row["missing_artifacts"]),
        "artifact_missing_blueprint_count": sum(1 for row in rows if row["missing_artifacts"]),
        "artifact_usefulness_control_required_count": sum(1 for row in rows if row["artifact_usefulness_control_required"]),
        "estimated_candidate_count_lower_bound": space.get("estimated_candidate_count_lower_bound"),
        "dimension_sizes": dimension_sizes,
        "combinatorial_dimension_product": combinatorial_count,
        "artifact_status": artifact_status,
        "family_summary": family_summary,
        "blueprints": rows,
    }


def write_md(report: dict[str, Any], output: Path) -> None:
    lines = [
        "# HELF Perturbation Search Space Audit",
        "",
        f"- Search space: `{report['search_space']}`",
        f"- Registry: `{report['artifact_registry']}`",
        f"- Search space id: `{report.get('search_space_id')}`",
        f"- Foundation blueprint count: `{report['foundation_blueprint_count']}`",
        f"- Executable now: `{report['executable_now_count']}`",
        f"- Artifact-present blueprints: `{report['artifact_present_blueprint_count']}`",
        f"- Artifact-missing blueprints: `{report['artifact_missing_blueprint_count']}`",
        f"- Estimated candidate lower bound: `{report.get('estimated_candidate_count_lower_bound')}`",
        f"- Combinatorial dimension product: `{report.get('combinatorial_dimension_product')}`",
        "",
        "## Implementation Status",
        "",
    ]
    for key, value in sorted(report.get("implementation_status_counts", {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Family Summary", "", "| Family | Blueprints | Executable now | Missing artifact blueprints |", "|---|---:|---:|---:|"]
    for family, row in sorted(report.get("family_summary", {}).items()):
        lines.append(f"| `{family}` | {row['blueprints']} | {row['executable_now']} | {row['missing_artifact_blueprints']} |")
    lines += ["", "## Blueprint Table", "", "| Family | Blueprint | Status | Required artifacts | Missing artifacts | Executable now |", "|---|---|---|---|---|---:|"]
    for row in report.get("blueprints", []):
        lines.append(
            f"| `{row['family']}` | `{row['id']}` | `{row['implementation_status']}` | "
            f"{', '.join(row['required_artifacts']) or 'none'} | {', '.join(row['missing_artifacts']) or 'none'} | {row['executable_now']} |"
        )
    lines += ["", "## Interpretation", "", "This audit distinguishes the declared model universe from the currently executable subset. Fast runs usually train the executable subset only; paper-scale runs require acquiring/building the missing checkpoint or embedding artifacts and increasing rollout/epoch budgets."]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit HELF perturbation search-space coverage and artifact readiness.")
    parser.add_argument("--search-space", type=Path, default=Path("configs/helf_perturb_search_space.json"))
    parser.add_argument("--artifact-registry", type=Path, default=Path("configs/artifacts/helf_perturb_registry.json"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/aivc_search_space_manifest_audit/helf_perturb_search_space_audit.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/aivc_search_space_manifest_audit/helf_perturb_search_space_audit.md"))
    args = parser.parse_args()
    report = audit(args.search_space, args.artifact_registry)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_md(report, args.output_md)
    print(json.dumps({
        "foundation_blueprint_count": report["foundation_blueprint_count"],
        "executable_now_count": report["executable_now_count"],
        "artifact_present_blueprint_count": report["artifact_present_blueprint_count"],
        "artifact_missing_blueprint_count": report["artifact_missing_blueprint_count"],
        "estimated_candidate_count_lower_bound": report.get("estimated_candidate_count_lower_bound"),
        "combinatorial_dimension_product": report.get("combinatorial_dimension_product"),
        "output_json": str(args.output_json),
        "output_md": str(args.output_md),
    }, indent=2))


if __name__ == "__main__":
    main()
