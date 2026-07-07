from __future__ import annotations

import argparse
import json
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


def audit_registry(registry: dict[str, Any]) -> dict[str, Any]:
    audited: list[dict[str, Any]] = []
    for artifact in registry.get("artifacts", []):
        row = dict(artifact)
        path = Path(str(row.get("path", "")))
        row["present"] = path.exists()
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
    return [artifact for artifact in registry_audit.get("artifacts", []) if blueprint_id in artifact.get("required_for_blueprints", [])]


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
    uses_perturbation_embedding = "gene_embedding" in data_name or model_type in {"target_aware_bilinear"} or strategy in {"esm2_gene_projection", "target_gene_embedding_bilinear"}
    sides: list[str] = []
    if uses_perturbation_embedding:
        sides.append("perturbation_gene_or_context")
    if uses_target_manifest or model_type == "target_aware_bilinear" or strategy == "target_gene_embedding_bilinear":
        sides.append("target_gene")
    if strategy in {"ppi_graph_message_passing", "string_gnn_perturbation_propagator"}:
        sides.append("gene_graph")
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
