from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from vc_demo.harness.state import write_json


def _copy_or_link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        return
    try:
        dst.symlink_to(src)
    except OSError:
        shutil.copy2(src, dst)


def _prepare_official_data_links(data_dir: Path, external_data_root: Path) -> None:
    for name in ["train.tsv", "val.tsv", "test.tsv"]:
        src = data_dir / name
        if not src.exists():
            raise FileNotFoundError(f"official K562 TSV missing: {src}")
        _copy_or_link(src.resolve(), external_data_root / name)


def _parse_score_file(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    text = path.read_text(errors="replace")
    metrics: dict[str, float] = {}
    first = re.search(r"test_results:\s*(\[.*\])", text)
    if first:
        try:
            rows = ast.literal_eval(first.group(1))
            if rows:
                for key, value in rows[0].items():
                    if isinstance(value, (int, float)):
                        metrics[str(key)] = float(value)
        except Exception:
            pass
    for line in text.splitlines():
        match = re.match(r"\s*([^:]+):\s*([-+0-9.eE]+)\s*$", line)
        if match:
            try:
                metrics[match.group(1).strip()] = float(match.group(2))
            except ValueError:
                pass
    return metrics


def _best_val_from_csv_logs(static_dir: Path) -> float | None:
    candidates = sorted((static_dir / "run" / "logs" / "csv_logs").glob("version_*/metrics.csv"))
    best: float | None = None
    for path in candidates:
        text = path.read_text(errors="replace").splitlines()
        if not text:
            continue
        header = text[0].split(",")
        if "val/f1" not in header:
            continue
        idx = header.index("val/f1")
        for line in text[1:]:
            parts = line.split(",")
            if idx >= len(parts) or not parts[idx]:
                continue
            try:
                value = float(parts[idx])
            except ValueError:
                continue
            best = value if best is None else max(best, value)
    return best


def run_external_static_node(config: dict[str, Any], output_dir: Path, max_epochs: int | None = None) -> dict[str, Any]:
    execution = config.get("execution", {})
    static_dir = Path(str(execution.get("static_dir", "")))
    script_path = Path(str(execution.get("script_path", "")))
    if not script_path.is_absolute():
        script_path = static_dir / script_path
    if not script_path.exists():
        raise FileNotFoundError(f"external static node script missing: {script_path}")

    data_dir = Path(str(config.get("data", {}).get("data_dir", "data/cell_lines/official_k562_cls")))
    external_data_root = Path(str(execution.get("external_data_root", static_dir.parent.parent / "data")))
    _prepare_official_data_links(data_dir, external_data_root)

    env = os.environ.copy()
    pythonpath = execution.get("pythonpath") or []
    if isinstance(pythonpath, str):
        pythonpath = [pythonpath]
    if pythonpath:
        env["PYTHONPATH"] = os.pathsep.join([*map(str, pythonpath), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)

    args = ["python", str(script_path.name)]
    args.extend(str(x) for x in execution.get("args", []))
    if max_epochs is not None and "--max-epochs" not in args:
        args.extend(["--max-epochs", str(max_epochs)])

    started = time.time()
    proc = subprocess.run(args, cwd=static_dir, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration = time.time() - started
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "external_stdout.txt").write_text(proc.stdout, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"external static node failed with exit code {proc.returncode}; see {output_dir / 'external_stdout.txt'}")

    score_path = static_dir / "test_score.txt"
    score_metrics = _parse_score_file(score_path)
    best_val = _best_val_from_csv_logs(static_dir)
    test_loss = score_metrics.get("test/loss", score_metrics.get("loss", 0.0))
    test_f1 = score_metrics.get("test/f1") or score_metrics.get("test/macro_f1") or best_val or 0.0
    result = {
        "node_name": config.get("node_name", output_dir.name),
        "dataset_type": config.get("data", {}).get("dataset_type", "official_k562_tsv"),
        "execution_backend": "external_static_node",
        "external_script": str(script_path),
        "duration_seconds": duration,
        "best_val_macro_f1": float(best_val if best_val is not None else test_f1),
        "test_macro_f1": float(test_f1),
        "test_loss": float(test_loss),
        "external_score_metrics": score_metrics,
        "artifact_usage": config.get("execution", {}).get("artifact_usage", {}),
        "notes": "External public VCHarness node wrapper. Fast-dev/debug runs may not emit held-out test F1; test_macro_f1 is val/f1-derived when no test F1 is logged.",
    }
    write_json(output_dir / "metrics.json", result)
    return result
