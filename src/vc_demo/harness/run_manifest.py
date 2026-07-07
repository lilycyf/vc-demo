from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _trained_nodes(tree: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return [(name, node) for name, node in tree.get("nodes", {}).items() if node.get("status") == "trained"]


def build_run_manifest(run_dir: Path, args: Any, tree: dict[str, Any], failures: list[dict[str, Any]], stop_reason: str, registry_audit: dict[str, Any]) -> dict[str, Any]:
    trained = _trained_nodes(tree)
    roots = [(name, node) for name, node in trained if not node.get("parent")]
    best = max(trained, key=lambda item: float(item[1].get("best_val_macro_f1", -1.0)), default=("", {}))
    best_root = max(roots, key=lambda item: float(item[1].get("best_val_macro_f1", -1.0)), default=("", {}))
    acquisition_queue = run_dir / "acquisition_queue.json"
    implementation_queue = run_dir / "implementation_queue.json"
    return {
        "format": "vc_demo_run_manifest.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment": getattr(args, "experiment", tree.get("experiment", "")),
        "run_dir": str(run_dir),
        "git": {
            "branch": _git(["branch", "--show-current"]),
            "commit": _git(["rev-parse", "HEAD"]),
            "status_short": _git(["status", "--short"]),
        },
        "search": {
            "selection_policy": getattr(args, "selection_policy", ""),
            "exploration": getattr(args, "exploration", None),
            "budget_nodes": getattr(args, "budget_nodes", None),
            "max_children": getattr(args, "max_children", None),
            "max_epochs": getattr(args, "max_epochs", None),
            "stop_no_improve": getattr(args, "stop_no_improve", None),
            "allow_planned_blueprints": bool(getattr(args, "allow_planned_blueprints", False)),
            "allow_missing_artifact_fallbacks": bool(getattr(args, "allow_missing_artifact_fallbacks", False)),
            "artifact_aware_blueprint_policy": bool(getattr(args, "artifact_aware_blueprint_policy", False)),
            "stop_reason": stop_reason,
        },
        "artifacts": {
            "registry_path": str(getattr(args, "artifact_registry", "") or "configs/artifacts/k562_registry.json"),
            "present_artifacts": registry_audit.get("present_artifacts", []),
            "missing_artifacts": registry_audit.get("missing_artifacts", []),
        },
        "queues": {
            "implementation_queue": str(implementation_queue),
            "acquisition_queue": str(acquisition_queue),
            "artifact_acquisition_command": f"python -m vc_demo.harness.artifact_acquisition --queue {acquisition_queue} --registry {getattr(args, 'artifact_registry', None) or Path('configs/artifacts/k562_registry.json')} --sources configs/artifacts/acquisition_sources.json --cell-line K562 --output-dir {run_dir / 'artifact_acquisition'} --execute-known",
        },
        "results": {
            "trained_nodes": len(trained),
            "failed_nodes": len(failures),
            "best_node": best[0],
            "best_val_macro_f1": best[1].get("best_val_macro_f1"),
            "best_test_macro_f1": best[1].get("test_macro_f1"),
            "best_root": best_root[0],
            "best_root_val_macro_f1": best_root[1].get("best_val_macro_f1"),
            "best_root_test_macro_f1": best_root[1].get("test_macro_f1"),
        },
        "mcts": tree.get("mcts", {}),
    }


def write_run_manifest(run_dir: Path, args: Any, tree: dict[str, Any], failures: list[dict[str, Any]], stop_reason: str, registry_audit: dict[str, Any]) -> Path:
    path = run_dir / "run_manifest.json"
    manifest = build_run_manifest(run_dir, args, tree, failures, stop_reason, registry_audit)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path
