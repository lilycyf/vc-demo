from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import audit_for_config


ALLOWED_TOP_LEVEL_PATCHES = {"model", "training", "data"}


def deep_update(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_update(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def default_pipeline_manifest(config: dict[str, Any], proposal: dict[str, Any] | None = None) -> dict[str, Any]:
    model_cfg = config.get("model", {})
    training_cfg = config.get("training", {})
    strategy = str((proposal or {}).get("strategy") or model_cfg.get("program_blueprint", "root"))
    return {
        "format": "vc_demo_pipeline_node.v1",
        "kind": "model_only" if strategy == "root" else "program_node",
        "strategy": strategy,
        "model_entrypoint": model_cfg.get("custom_model_path", ""),
        "training": {
            "loss_type": training_cfg.get("loss_type", "cross_entropy"),
            "loss_notes": training_cfg.get("loss_notes", "default CrossEntropyLoss over flattened target-gene classes"),
        },
        "artifact_requirements": [],
        "artifact_usage_claims": [],
        "patches": {},
        "guardrails": {
            "preserve_splits": True,
            "preserve_metric": "validation Macro-F1",
            "do_not_fabricate_artifacts": True,
        },
    }


def write_pipeline_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_pipeline_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open() as f:
        return json.load(f)


def apply_pipeline_manifest(config: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(config)
    patches = manifest.get("patches", {})
    for key, patch in patches.items():
        if key not in ALLOWED_TOP_LEVEL_PATCHES:
            raise ValueError(f"pipeline patch {key!r} is not allowed; choose from {sorted(ALLOWED_TOP_LEVEL_PATCHES)}")
        if not isinstance(patch, dict):
            raise ValueError(f"pipeline patch {key!r} must be an object")
        out[key] = deep_update(out.get(key, {}), patch)
    out.setdefault("pipeline", {})
    out["pipeline"].update({k: v for k, v in manifest.items() if k != "patches"})
    return out


def materialize_pipeline_config(config: dict[str, Any], proposal: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    path = config.get("pipeline_manifest_path") or config.get("pipeline", {}).get("manifest_path")
    if path:
        manifest = load_pipeline_manifest(path)
    else:
        manifest = default_pipeline_manifest(config, proposal)
    materialized = apply_pipeline_manifest(config, manifest)
    materialized.setdefault("pipeline", {})["manifest"] = manifest
    materialized["pipeline"]["audit"] = audit_for_config(materialized, proposal)
    return materialized, manifest


def pipeline_audit_summary(config: dict[str, Any]) -> dict[str, Any]:
    pipeline = config.get("pipeline", {})
    audit = pipeline.get("audit", {})
    usage = audit.get("usage", {})
    requirements = audit.get("requirements", [])
    return {
        "pipeline_kind": pipeline.get("kind", "model_only"),
        "pipeline_strategy": pipeline.get("strategy", ""),
        "loss_type": usage.get("loss_type", config.get("training", {}).get("loss_type", "cross_entropy")),
        "uses_real_artifact": bool(usage.get("uses_real_artifact")),
        "artifact_sides": usage.get("artifact_sides", []),
        "artifact_manifest_path": usage.get("artifact_manifest_path", ""),
        "required_artifacts": [item.get("id") for item in requirements],
        "missing_required_artifacts": [item.get("id") for item in requirements if not item.get("present")],
    }
