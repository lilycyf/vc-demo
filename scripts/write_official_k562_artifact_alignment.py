from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import audit_registry, load_registry


def sha256_file(path: Path, limit_bytes: int = 256 * 1024 * 1024) -> str:
    if not path.is_file() or path.stat().st_size > limit_bytes:
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def provenance_status(row: dict[str, Any]) -> str:
    if not row.get("present"):
        return "missing"
    artifact_id = str(row.get("id", ""))
    family = str(row.get("family", ""))
    source = str(row.get("source", "")).lower()
    if artifact_id == "official_string_gnn_model_dir":
        return "reconstructed_compatibility"
    if "huggingface" in source or "vcharness" in source or "reactome" in source or "string" in source:
        return "original_public"
    if family in {"artifact_manifest", "pathway_membership"}:
        return "derived"
    return "derived"


def equivalence_claim(row: dict[str, Any], status: str) -> str:
    if status == "missing":
        return "unavailable; strict official mode must acquire or block"
    if row.get("id") == "official_string_gnn_model_dir":
        return "compatibility reconstruction; do not claim numerical equivalence to unpublished original checkpoint"
    if status == "original_public":
        return "public artifact available locally; equivalent to the cited public source subject to checksum/source metadata"
    return "derived local artifact; usable only with explicit provenance"


def build_matrix(registry_path: Path, cell_line: str) -> dict[str, Any]:
    audit = audit_registry(load_registry(registry_path, cell_line))
    rows: list[dict[str, Any]] = []
    for artifact in audit.get("artifacts", []):
        path = Path(str(artifact.get("path", "")))
        size = path.stat().st_size if path.exists() and path.is_file() else 0
        status = provenance_status(artifact)
        rows.append({
            "id": artifact.get("id"),
            "provider": artifact.get("provider", ""),
            "family": artifact.get("family", ""),
            "path": str(path),
            "present": bool(artifact.get("present")),
            "size_bytes": size,
            "sha256": sha256_file(path),
            "source": artifact.get("source", ""),
            "source_url": artifact.get("source_url", ""),
            "status": status,
            "required_by_blueprints": artifact.get("required_for_blueprints", []),
            "equivalence_claim": equivalence_claim(artifact, status),
        })
    return {"format": "official_k562_artifact_alignment.v1", "registry_path": str(registry_path), "cell_line": cell_line, "artifacts": rows, "present": [r["id"] for r in rows if r["present"]], "missing": [r["id"] for r in rows if not r["present"]], "reconstructed_compatibility": [r["id"] for r in rows if r["status"] == "reconstructed_compatibility"]}


def write_md(matrix: dict[str, Any], path: Path) -> None:
    lines = ["# Official K562 Artifact Alignment Matrix", "", f"- Registry: `{matrix['registry_path']}`", f"- Present artifacts: {len(matrix['present'])}", f"- Missing artifacts: {len(matrix['missing'])}", f"- Reconstructed compatibility artifacts: {', '.join(matrix['reconstructed_compatibility']) or 'none'}", "", "| Artifact | Provider | Status | Present | Size | Equivalence claim |", "|---|---|---|---:|---:|---|"]
    for row in matrix["artifacts"]:
        claim = str(row["equivalence_claim"]).replace("|", "/")
        lines.append(f"| `{row['id']}` | {row['provider']} | {row['status']} | {str(row['present']).lower()} | {row['size_bytes']} | {claim} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write official K562 artifact provenance matrix.")
    parser.add_argument("--registry", type=Path, default=Path("configs/artifacts/k562_registry.json"))
    parser.add_argument("--cell-line", default="K562")
    parser.add_argument("--output-json", type=Path, default=Path("experiments/official_k562_alignment/official_k562_artifact_alignment_matrix.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/official_k562_alignment/official_k562_artifact_alignment_matrix.md"))
    args = parser.parse_args()
    matrix = build_matrix(args.registry, args.cell_line)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    write_md(matrix, args.output_md)
    print(json.dumps({"json": str(args.output_json), "md": str(args.output_md), "missing": matrix["missing"], "reconstructed_compatibility": matrix["reconstructed_compatibility"]}, indent=2))


if __name__ == "__main__":
    main()
