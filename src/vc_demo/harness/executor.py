from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Any

from vc_demo.harness.pipeline import materialize_pipeline_config, pipeline_audit_summary
from vc_demo.harness.state import node_dir, write_json
from vc_demo.train import train


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
