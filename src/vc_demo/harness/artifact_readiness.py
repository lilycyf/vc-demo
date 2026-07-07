from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import audit_registry, load_registry
from vc_demo.harness.state import read_json, write_json


def _source_map(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return {str(item.get("id")): item for item in payload.get("artifacts", [])}


def readiness(registry: Path, sources: Path, cell_line: str = "K562") -> dict[str, Any]:
    audit = audit_registry(load_registry(registry, cell_line))
    source_by_id = _source_map(sources)
    rows: list[dict[str, Any]] = []
    for artifact in audit.get("artifacts", []):
        artifact_id = str(artifact.get("id"))
        source = source_by_id.get(artifact_id, {})
        present = bool(artifact.get("present"))
        auto = bool(source.get("can_execute_automatically"))
        if present:
            action = "use_existing"
        elif auto:
            action = "run_known_resolver"
        elif source.get("resolver") == "definition_required_before_acquisition":
            action = "define_artifact_contract_before_search"
        else:
            action = "codex_search_official_source"
        rows.append({
            "artifact_id": artifact_id,
            "provider": artifact.get("provider"),
            "family": artifact.get("family"),
            "present": present,
            "expected_path": artifact.get("path"),
            "resolver": source.get("resolver", "unconfigured"),
            "can_execute_automatically": auto,
            "action": action,
            "source": artifact.get("source") or source.get("source"),
            "required_for_blueprints": artifact.get("required_for_blueprints", []),
        })
    return {
        "format": "vc_demo_artifact_readiness.v1",
        "registry": str(registry),
        "sources": str(sources),
        "present_artifacts": audit.get("present_artifacts", []),
        "missing_artifacts": audit.get("missing_artifacts", []),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an artifact readiness/action matrix for a formal run.")
    parser.add_argument("--registry", type=Path, default=Path("configs/artifacts/k562_registry.json"))
    parser.add_argument("--sources", type=Path, default=Path("configs/artifacts/acquisition_sources.json"))
    parser.add_argument("--cell-line", default="K562")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    payload = readiness(args.registry, args.sources, args.cell_line)
    if args.output:
        write_json(args.output, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
