from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ARTIFACT_ID_ALIASES: dict[str, str] = {
    # Historical blueprint names kept for backward compatibility.
    "pathway_memberships": "pathway_membership_matrix",
    "pathway_membership": "pathway_membership_matrix",
    "pathway_membership_targets": "pathway_membership_matrix",
}


def canonical_artifact_id(artifact_id: str) -> str:
    return ARTIFACT_ID_ALIASES.get(str(artifact_id), str(artifact_id))


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def default_registry_path(cell_line: str | None = None) -> Path:
    if (cell_line or "").upper() == "K562":
        return Path("configs/artifacts/k562_registry.json")
    return Path("configs/artifacts/k562_registry.json")


def load_registry(path: str | Path | None = None, cell_line: str | None = None) -> dict[str, Any]:
    registry_path = Path(path) if path else default_registry_path(cell_line)
    registry = read_json(registry_path)
    registry["registry_path"] = str(registry_path)
    return registry


def _artifact_manifest_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        manifest = read_json(path)
    except Exception as exc:
        return {"manifest_read_error": str(exc)}
    target = manifest.get("target_gene_embeddings", {})
    return {
        "artifact_name": manifest.get("artifact_name"),
        "artifact_family": manifest.get("artifact_family"),
        "target_gene_coverage": target.get("coverage"),
        "n_target_genes": target.get("n_target_genes"),
        "target_embedding_dim": target.get("embedding_dim"),
        "missing_target_genes_count": len(target.get("missing_target_genes", []) or []),
    }


def _path_has_substantive_content(path: Path) -> tuple[bool, dict[str, Any]]:
    if not path.exists():
        return False, {"present_check": "path_missing"}
    if path.is_file():
        return path.stat().st_size > 0, {"present_check": "file_exists", "bytes": path.stat().st_size}
    if not path.is_dir():
        return True, {"present_check": "special_path_exists"}
    substantive_files: list[str] = []
    ignored_files: list[str] = []
    for child in path.rglob("*"):
        if not child.is_file():
            continue
        rel = child.relative_to(path)
        parts = rel.parts
        if any(part.startswith(".") for part in parts) or any(part in {"cache", "__pycache__"} for part in parts):
            ignored_files.append(str(rel))
            continue
        if child.stat().st_size > 0:
            substantive_files.append(str(rel))
    return bool(substantive_files), {
        "present_check": "directory_substantive_files",
        "substantive_file_count": len(substantive_files),
        "sample_substantive_files": substantive_files[:8],
        "ignored_file_count": len(ignored_files),
    }


def audit_registry(registry: dict[str, Any]) -> dict[str, Any]:
    audited: list[dict[str, Any]] = []
    for artifact in registry.get("artifacts", []):
        row = dict(artifact)
        path = Path(str(row.get("path", "")))
        present, present_details = _path_has_substantive_content(path)
        row["present"] = present
        row["present_details"] = present_details
        row["resolved_status"] = "present" if row["present"] else "missing"
        if row.get("family") == "artifact_manifest":
            row.update(_artifact_manifest_summary(path))
        audited.append(row)
    return {
        "registry_version": registry.get("registry_version"),
        "registry_path": registry.get("registry_path"),
        "cell_line": registry.get("cell_line"),
        "artifacts": audited,
        "present_artifacts": [item["id"] for item in audited if item.get("present")],
        "missing_artifacts": [item["id"] for item in audited if not item.get("present")],
    }


def requirements_for_blueprint(registry_audit: dict[str, Any], blueprint_id: str) -> list[dict[str, Any]]:
    artifacts = list(registry_audit.get("artifacts", []))
    by_id = {canonical_artifact_id(str(artifact.get("id"))): artifact for artifact in artifacts}
    required_ids: list[str] = []
    for artifact in artifacts:
        if blueprint_id in artifact.get("required_for_blueprints", []):
            artifact_id = canonical_artifact_id(str(artifact.get("id")))
            if artifact_id not in required_ids:
                required_ids.append(artifact_id)
    try:
        from vc_demo.harness.model_blueprints import blueprint_by_id

        for artifact_id in blueprint_by_id(blueprint_id).get("requires", []) or []:
            artifact_id = canonical_artifact_id(str(artifact_id))
            if artifact_id not in required_ids:
                required_ids.append(artifact_id)
    except Exception:
        pass

    rows: list[dict[str, Any]] = []
    for artifact_id in required_ids:
        row = dict(by_id.get(artifact_id, {"id": artifact_id, "present": False, "resolved_status": "missing", "path": "", "source": "not listed in artifact registry"}))
        row.setdefault("present", False)
        row.setdefault("resolved_status", "present" if row.get("present") else "missing")
        rows.append(row)
    return rows


def missing_requirements_for_blueprint(registry_audit: dict[str, Any], blueprint_id: str) -> list[dict[str, Any]]:
    return [artifact for artifact in requirements_for_blueprint(registry_audit, blueprint_id) if not artifact.get("present")]

def summarize_missing_requirements(registry_audit: dict[str, Any], blueprint_id: str) -> dict[str, Any]:
    missing = missing_requirements_for_blueprint(registry_audit, blueprint_id)
    return {
        "strategy": blueprint_id,
        "missing_required_artifacts": [item.get("id") for item in missing],
        "missing_required_artifact_paths": [item.get("path") for item in missing],
        "missing_required_artifact_sources": [item.get("source") for item in missing],
    }


def artifact_usage_from_config(config: dict[str, Any], proposal: dict[str, Any] | None = None) -> dict[str, Any]:
    data_cfg = config.get("data", {})
    model_cfg = config.get("model", {})
    training_cfg = config.get("training", {})
    pipeline = config.get("pipeline", {})
    data_dir = Path(str(data_cfg.get("data_dir", "")))
    artifact_manifest = model_cfg.get("artifact_manifest_path") or pipeline.get("artifact_manifest_path")
    if artifact_manifest == "auto":
        artifact_manifest = str(data_dir / "artifact_manifest.json")
    uses_target_manifest = bool(artifact_manifest and Path(str(artifact_manifest)).exists())
    model_type = str(model_cfg.get("model_type", ""))
    strategy = str((proposal or {}).get("strategy") or model_cfg.get("program_blueprint", ""))
    data_name = str(data_dir)
    embedding_paths = []
    if data_cfg.get("embedding_h5ad"):
        embedding_paths.append(str(data_cfg.get("embedding_h5ad")))
    embedding_paths.extend(str(path) for path in data_cfg.get("embedding_h5ads", []) or [])
    uses_official_k562_embeddings = data_cfg.get("dataset_type") == "official_k562_tsv" and bool(embedding_paths)
    uses_perturbation_embedding = (
        "gene_embedding" in data_name
        or uses_official_k562_embeddings
        or model_type in {"target_aware_bilinear"}
        or strategy in {"esm2_gene_projection", "target_gene_embedding_bilinear"}
    )
    sides: list[str] = []
    if uses_perturbation_embedding:
        sides.append("perturbation_gene_or_context")
    if uses_target_manifest or model_type == "target_aware_bilinear" or strategy == "target_gene_embedding_bilinear":
        sides.append("target_gene")
    if strategy in {"ppi_graph_message_passing", "string_gnn_perturbation_propagator", "official_string_gnn_attention", "official_aido_string_fusion", "official_native_public_best_reimplementation"}:
        sides.append("gene_graph")
    if strategy in {"official_aido_lora_adapter", "official_aido_string_fusion", "official_native_public_best_reimplementation"}:
        sides.append("AIDO.Cell-100M")
    if strategy == "pathway_pooling_encoder":
        sides.append("pathway_membership")
    if strategy == "scfoundation_cell_encoder":
        sides.append("cell_state")
    return {
        "uses_real_artifact": bool(sides),
        "artifact_sides": sorted(set(sides)),
        "artifact_manifest_path": str(artifact_manifest or ""),
        "model_type": model_type,
        "strategy": strategy,
        "loss_type": training_cfg.get("loss_type", "cross_entropy"),
        "pipeline_kind": pipeline.get("kind", "model_only"),
    }


def audit_for_config(config: dict[str, Any], proposal: dict[str, Any] | None = None, registry_path: str | Path | None = None) -> dict[str, Any]:
    registry = load_registry(registry_path, config.get("data", {}).get("cell_line"))
    audit = audit_registry(registry)
    usage = artifact_usage_from_config(config, proposal)
    strategy = usage.get("strategy", "")
    requirements = requirements_for_blueprint(audit, strategy) if strategy else []
    return {"registry": audit, "usage": usage, "requirements": requirements}


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the repo artifact registry.")
    parser.add_argument("--registry", type=Path, default=None)
    parser.add_argument("--cell-line", default="K562")
    args = parser.parse_args()
    print(json.dumps(audit_registry(load_registry(args.registry, args.cell_line)), indent=2))


if __name__ == "__main__":
    main()
