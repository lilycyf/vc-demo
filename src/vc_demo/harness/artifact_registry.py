from __future__ import annotations

import argparse
import json

import numpy as np
from pathlib import Path
from typing import Any


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



def _pathway_membership_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with np.load(path, allow_pickle=True) as z:
            key = "membership" if "membership" in z.files else "membership_matrix"
            membership = z[key]
            target_genes = z["target_genes"] if "target_genes" in z.files else z.get("target_gene_symbols", [])
            pathway_ids = z["pathway_ids"] if "pathway_ids" in z.files else []
            covered = np.asarray(membership.sum(axis=1) > 0)
            return {
                "artifact_name": "Reactome K562 pathway memberships",
                "artifact_family": "pathway_prior",
                "membership_shape_actual": list(membership.shape),
                "n_target_genes_actual": int(len(target_genes)),
                "n_pathways_actual": int(len(pathway_ids)),
                "target_gene_coverage_actual": float(covered.mean()) if len(covered) else 0.0,
                "covered_target_gene_count_actual": int(covered.sum()) if len(covered) else 0,
            }
    except Exception as exc:
        return {"pathway_membership_read_error": str(exc)}



def _class_distribution_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = read_json(path)
    except Exception as exc:
        return {"class_distribution_read_error": str(exc)}
    return {
        "artifact_name": "K562 train-only class distribution",
        "artifact_family": "class_distribution",
        "class_distribution_format": payload.get("format"),
        "split_used_actual": payload.get("split_used"),
        "forbidden_splits_actual": payload.get("forbidden_splits", []),
        "n_train_rows_actual": payload.get("n_train_rows"),
        "n_targets_actual": payload.get("n_targets"),
        "raw_label_counts_actual": payload.get("raw_label_counts", {}),
        "training_label_counts_actual": payload.get("training_label_counts", {}),
        "has_recommended_weights": bool(payload.get("recommended", {}).get("weighted_cross_entropy_class_weights_training_order")),
        "manifest_train_counts_match": payload.get("manifest_train_counts_match"),
        "provenance_actual": payload.get("provenance"),
    }

def audit_registry(registry: dict[str, Any]) -> dict[str, Any]:
    audited: list[dict[str, Any]] = []
    for artifact in registry.get("artifacts", []):
        row = dict(artifact)
        path = Path(str(row.get("path", "")))
        row["present"] = path.exists()
        row["resolved_status"] = "present" if row["present"] else "missing"
        if row.get("family") == "artifact_manifest":
            row.update(_artifact_manifest_summary(path))
        if row.get("family") == "pathway_prior":
            row.update(_pathway_membership_summary(path))
            expected = int(row.get("expected_n_targets") or row.get("n_target_genes") or 0)
            actual = int(row.get("n_target_genes_actual") or 0)
            if row.get("present") and expected and actual and actual != expected:
                row["present"] = False
                row["resolved_status"] = "shape_mismatch"
                row["shape_issue"] = f"expected {expected} target genes, found {actual}"
        if row.get("family") == "class_distribution":
            row.update(_class_distribution_summary(path))
            if row.get("present"):
                issues = []
                if row.get("split_used_actual") != "train":
                    issues.append("split_used must be train")
                if not row.get("manifest_train_counts_match"):
                    issues.append("derived counts do not match official manifest train counts")
                if not row.get("has_recommended_weights"):
                    issues.append("missing recommended train-only class weights")
                forbidden = set(row.get("forbidden_splits_actual") or [])
                if not {"val", "test"}.issubset(forbidden):
                    issues.append("artifact must explicitly forbid val/test label use")
                if issues:
                    row["present"] = False
                    row["resolved_status"] = "invalid_class_distribution"
                    row["class_distribution_issue"] = "; ".join(issues)
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
    return [artifact for artifact in registry_audit.get("artifacts", []) if blueprint_id in artifact.get("required_for_blueprints", [])]


def artifact_by_id_or_alias(registry_audit: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    for artifact in registry_audit.get("artifacts", []):
        ids = {str(artifact.get("id", "")), *[str(alias) for alias in artifact.get("aliases", [])]}
        if artifact_id in ids:
            return artifact
    return {"id": artifact_id, "present": False}


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
