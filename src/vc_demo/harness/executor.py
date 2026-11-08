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
from vc_demo.harness.paper_level_guardrails import assert_no_formal_proxy
from vc_demo.harness.research_contract import evaluation_policy, capture_execution_recipe, ResearchContractError


def run_node(config: dict[str, Any], run_dir: Path, proposal: dict[str, Any] | None, max_epochs: int | None) -> dict[str, Any]:
    name = str(config["node_name"])
    materialized_config, pipeline_manifest = materialize_pipeline_config(config, proposal)
    phase, evaluate_test = evaluation_policy(materialized_config, run_dir)
    out_dir = run_dir / 'confirmation' / name if phase == 'confirmation' else node_dir(run_dir, name)
    out_dir.mkdir(parents=True, exist_ok=True)
    if phase == 'confirmation':
        materialized_config.setdefault('evaluation', {})['confirmation_lock_path'] = str(run_dir / 'confirmation_lock.json')
    recipe = capture_execution_recipe(materialized_config, run_dir, is_benchmark=proposal is None, max_epochs=max_epochs)
    if phase == 'confirmation':
        from vc_demo.harness.state import read_json
        lock = read_json(run_dir / 'confirmation_lock.json')
        if recipe['fingerprint'] != lock['recipe_fingerprints'][name]:
            raise ResearchContractError('Confirmation recipe differs from the frozen selected model')
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
            if phase != 'confirmation':
                raise ResearchContractError('External static backend must prove development-only execution or run after confirmation freeze')
            metrics = run_external_static_node(materialized_config, out_dir, max_epochs=max_epochs)
            duration = metrics.get("duration_seconds", time.time() - started)
        else:
            if materialized_config.get("model", {}).get("model_type") == "custom_program":
                model_path = Path(str(materialized_config.get("model", {}).get("custom_model_path", "")))
                assert_no_formal_proxy(materialized_config, model_path, context=f"node {name}")
                smoke = smoke_config(materialized_config, batch_size=1)
                write_json(out_dir / "native_program_smoke.json", smoke)
            metrics = train(materialized_config, out_dir, max_epochs=max_epochs)
            duration = time.time() - started
        metrics["duration_seconds"] = duration
        metrics['executable_recipe_fingerprint'] = recipe['fingerprint']
        metrics['evidence_phase'] = phase
        if not evaluate_test:
            metrics['test_macro_f1'] = None
            metrics['test_loss'] = None
            metrics['test_metric_source'] = 'withheld_until_confirmation'
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
