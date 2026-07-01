from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def node_dir(run_dir: Path, node_name: str) -> Path:
    return run_dir / "nodes" / node_name


def metrics_path(run_dir: Path, node_name: str) -> Path:
    return node_dir(run_dir, node_name) / "metrics.json"


def reset_run_dir(run_dir: Path) -> None:
    shutil.rmtree(run_dir / "nodes", ignore_errors=True)
    shutil.rmtree(run_dir / "proposals", ignore_errors=True)
    shutil.rmtree(run_dir / "programs", ignore_errors=True)
    for name in ["tree.json", "search_summary.md", "failures.json"]:
        path = run_dir / name
        if path.exists():
            path.unlink()
    (run_dir / "proposals").mkdir(parents=True, exist_ok=True)
    (run_dir / "nodes").mkdir(parents=True, exist_ok=True)


def empty_tree(experiment: str) -> dict[str, Any]:
    return {"experiment": experiment, "root_nodes": [], "nodes": {}, "events": []}
