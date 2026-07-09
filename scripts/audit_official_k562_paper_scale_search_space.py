from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_model_blueprints() -> list[dict[str, Any]]:
    from vc_demo.harness.model_blueprints import MODEL_BLUEPRINTS

    return [bp for bp in MODEL_BLUEPRINTS if bp.get("official_k562")]


def estimate_candidate_count(config: dict[str, Any], blueprints: list[dict[str, Any]]) -> int:
    dimensions = config.get("search_dimensions", [])
    product = 1
    for dim in dimensions:
        product *= max(len(dim.get("options", [])), 1)
    # The manifest space is blueprint families plus constrained cross-product variants.
    # Cap is not applied: this is a search-space capacity estimate, not a run budget.
    return max(product, len(blueprints))


def normalize_blueprint(bp: dict[str, Any]) -> dict[str, Any]:
    output_shape = "[batch, 6640, 3]"
    return {
        "id": bp.get("id"),
        "family": bp.get("paper_family") or bp.get("category"),
        "status": bp.get("status"),
        "required_artifacts": bp.get("requires", []),
        "input_contract": bp.get("input_contract", "official K562 TSV/h5ad feature batch plus declared artifacts"),
        "output_contract": bp.get("output_contract", output_shape),
        "codex_action": bp.get("implementation_mode", "run immediately" if bp.get("status") == "implemented" else "implement node-local model.py/config patch on selection"),
        "allowed_changes": ["node-local model.py", "node-local pipeline metadata", "approved helpers under src/vc_demo/official_k562"],
        "forbidden_changes": ["official split", "labels", "target gene order", "metric semantics", "artifact provenance", "silent fallback", "compact/proxy/simplified stand-ins"],
        "smoke_command": "PYTHONPATH=src python -m vc_demo.harness.native_program_smoke --config <child-config>",
        "cost_class": bp.get("cost_class", "unknown"),
        "paper_alignment_claim": bp.get("role", "official K562 paper-space candidate"),
    }


def build_audit(config_path: Path) -> dict[str, Any]:
    config = load_json(config_path)
    blueprints = load_model_blueprints()
    official_selectable = [normalize_blueprint(bp) for bp in blueprints]
    status_counts: dict[str, int] = {}
    for bp in official_selectable:
        status_counts[bp["status"]] = status_counts.get(bp["status"], 0) + 1
    required_fields = config.get("blueprint_entry_required_fields", [])
    missing_fields = {
        bp["id"]: [field for field in required_fields if field not in bp or bp.get(field) in (None, "")]
        for bp in official_selectable
    }
    missing_fields = {k: v for k, v in missing_fields.items() if v}
    estimated = estimate_candidate_count(config, blueprints)
    paper_contract = config.get("paper_scale_contract", {})
    proxy_forbidden = paper_contract.get("compact_native_or_proxy_allowed_in_official_mode") is False
    fallback_forbidden = paper_contract.get("fallback_allowed_in_official_mode") is False
    hard_policy_passed = bool(proxy_forbidden and fallback_forbidden)
    return {
        "format": "official_k562_paper_scale_search_space_audit.v1",
        "config": str(config_path),
        "official_selectable_blueprints": len(official_selectable),
        "status_counts": status_counts,
        "search_dimensions": config.get("search_dimensions", []),
        "estimated_combinatorial_candidate_count": estimated,
        "reaches_600_plus": estimated >= 600,
        "minimum_required_for_paper_scale": paper_contract.get("minimum_budget_nodes_for_paper_scale_single_cellline", 600),
        "formal_proxy_policy": "forbidden" if proxy_forbidden else "not_forbidden",
        "formal_fallback_policy": "forbidden" if fallback_forbidden else "not_forbidden",
        "hard_policy_passed": hard_policy_passed,
        "missing_required_blueprint_fields": missing_fields,
        "blueprints": official_selectable,
    }


def write_md(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# Official K562 Paper-Scale Search Space Audit",
        "",
        f"- Official selectable blueprints: {audit['official_selectable_blueprints']}",
        f"- Estimated combinatorial candidate count: {audit['estimated_combinatorial_candidate_count']}",
        f"- Reaches 600+ search-space target: {str(audit['reaches_600_plus']).lower()}",
        f"- Status counts: `{json.dumps(audit['status_counts'], sort_keys=True)}`",
        f"- Formal proxy policy: `{audit.get('formal_proxy_policy')}`",
        f"- Formal fallback policy: `{audit.get('formal_fallback_policy')}`",
        f"- Hard policy passed: {str(audit.get('hard_policy_passed')).lower()}",
        "",
        "## Dimensions",
        "",
    ]
    for dim in audit.get("search_dimensions", []):
        lines.append(f"- {dim['dimension']}: {', '.join(dim.get('options', []))}")
    lines.extend(["", "## Blueprint Contract", "", "| Blueprint | Status | Family | Cost | Required artifacts |", "|---|---|---|---|---|"])
    for bp in audit.get("blueprints", []):
        lines.append(f"| `{bp['id']}` | {bp['status']} | {bp['family']} | {bp['cost_class']} | {', '.join(bp['required_artifacts']) or 'none'} |")
    if audit.get("missing_required_blueprint_fields"):
        lines.extend(["", "## Missing Required Fields", "", "```json", json.dumps(audit["missing_required_blueprint_fields"], indent=2), "```"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the official K562 paper-scale manifest and blueprint contract.")
    parser.add_argument("--config", type=Path, default=Path("configs/official_k562_paper_scale_search_space.json"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/official_k562_alignment/official_k562_paper_scale_search_space_audit.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/official_k562_alignment/official_k562_paper_scale_search_space_audit.md"))
    args = parser.parse_args()
    audit = build_audit(args.config)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    write_md(audit, args.output_md)
    print(json.dumps({"audit": str(args.output_json), "md": str(args.output_md), "estimated": audit["estimated_combinatorial_candidate_count"], "reaches_600_plus": audit["reaches_600_plus"], "hard_policy_passed": audit["hard_policy_passed"]}, indent=2))


if __name__ == "__main__":
    main()
