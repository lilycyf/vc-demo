from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any

from vc_demo.harness.pipeline import materialize_pipeline_config, pipeline_audit_summary
from vc_demo.harness.state import node_dir, write_json
from vc_demo.train import train
from vc_demo.harness.external_static import run_external_static_node
from vc_demo.harness.native_program_smoke import smoke_config


def _allows_external_static_backend(config: dict[str, Any], proposal: dict[str, Any] | None) -> bool:
    model_cfg = config.get("model", {})
    strategy = str((proposal or {}).get("strategy") or model_cfg.get("program_blueprint", ""))
    node_name = str(config.get("node_name", ""))
    return (
        strategy == "official_public_best_node"
        or model_cfg.get("model_type") == "external_static_node"
        or node_name in {"official_k562_public_best_node2_1_1_1_1_1_smoke", "official_k562_public_best_node2_1_1_1_1_1_benchmark"}
    )


def run_node(config: dict[str, Any], run_dir: Path, proposal: dict[str, Any] | None, max_epochs: int | None) -> dict[str, Any]:
    name = str(config["node_name"])
    out_dir = node_dir(run_dir, name)
    out_dir.mkdir(parents=True, exist_ok=True)
    materialized_config, pipeline_manifest = materialize_pipeline_config(config, proposal)
    pipeline_summary = pipeline_audit_summary(materialized_config)
    write_json(out_dir / "config.json", materialized_config)
    write_json(out_dir / "pipeline.json", pipeline_manifest)
    write_json(out_dir / "pipeline_audit.json", pipeline_summary)
    if proposal is not None:
        write_json(out_dir / "proposal.json", proposal)
    write_json(out_dir / "status.json", {"status": "training", "pipeline": pipeline_summary})
    started = time.time()
    try:
        if materialized_config.get("execution", {}).get("backend") == "external_static_node":
            if not _allows_external_static_backend(materialized_config, proposal):
                strategy = str((proposal or {}).get("strategy") or materialized_config.get("model", {}).get("program_blueprint", ""))
                raise ValueError(
                    "external_static_node backend is only allowed for official public static wrappers; "
                    f"node {name!r} strategy {strategy!r} must use native/program-node training"
                )
            metrics = run_external_static_node(materialized_config, out_dir, max_epochs=max_epochs)
            duration = metrics.get("duration_seconds", time.time() - started)
        else:
            if materialized_config.get("model", {}).get("model_type") == "custom_program":
                smoke = smoke_config(materialized_config, batch_size=1)
                write_json(out_dir / "native_program_smoke.json", smoke)
            metrics = train(materialized_config, out_dir, max_epochs=max_epochs)
            duration = time.time() - started
        metrics["duration_seconds"] = duration
        metrics["pipeline"] = pipeline_summary
        write_json(out_dir / "metrics.json", metrics)
        write_json(out_dir / "status.json", {"status": "trained", "best_val_macro_f1": metrics["best_val_macro_f1"], "duration_seconds": duration, "pipeline": pipeline_summary})
        return metrics
    except Exception as exc:
        duration = time.time() - started
        write_json(
            out_dir / "status.json",
            {
                "status": "failed",
                "error": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
                "traceback": traceback.format_exc(),
                "duration_seconds": duration,
                "pipeline": pipeline_summary,
            },
        )
        raise
