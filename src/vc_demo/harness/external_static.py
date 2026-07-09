from __future__ import annotations

import ast
import csv
import importlib.util
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



def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _preflight_external_static(config: dict[str, Any], static_dir: Path, script_path: Path, mode: str, output_dir: Path) -> dict[str, Any]:
    execution = config.get("execution", {})
    data_dir = Path(str(config.get("data", {}).get("data_dir", "data/cell_lines/official_k562_cls")))
    required_paths = {
        "static_dir": static_dir,
        "script_path": script_path,
        "data_dir": data_dir,
    }
    for name in ["train.tsv", "val.tsv", "test.tsv"]:
        required_paths[f"data/{name}"] = data_dir / name
    for label, raw_path in execution.get("artifact_usage", {}).items():
        if label in {"public_node_code"}:
            continue
        required_paths[f"artifact/{label}"] = Path(str(raw_path))

    missing_paths = {key: str(path) for key, path in required_paths.items() if not path.exists()}
    logger_available = _module_available("tensorboard") or _module_available("tensorboardX")
    issues: list[str] = []
    if missing_paths:
        issues.append("missing_required_paths")
    if not logger_available:
        issues.append("missing_tensorboard_logger_dependency")
    result = {
        "status": "passed" if not issues else "blocked",
        "mode": mode,
        "issues": issues,
        "missing_paths": missing_paths,
        "logger_dependency": {
            "tensorboard": _module_available("tensorboard"),
            "tensorboardX": _module_available("tensorboardX"),
            "required_for": "Lightning TensorBoardLogger used by public VCHarness static node",
            "install_hint": "pip install tensorboard or install requirements-official-k562.txt",
        },
        "metric_contract": {
            "benchmark_requires_test_metric": mode == "benchmark" and not bool(execution.get("allow_test_metric_fallback", False)),
            "smoke_allows_val_fallback": mode == "smoke" and bool(execution.get("allow_test_metric_fallback", True)),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "external_preflight.json", result)
    if issues:
        details = "; ".join(issues)
        raise RuntimeError(f"external static node preflight blocked: {details}; see {output_dir / 'external_preflight.json'}")
    return result

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


def _csv_log_files(static_dir: Path) -> list[Path]:
    return sorted((static_dir / "run" / "logs" / "csv_logs").glob("version_*/metrics.csv"))


def _best_metric_from_csv_logs(static_dir: Path, names: tuple[str, ...]) -> tuple[float | None, str]:
    best: float | None = None
    source = ""
    for path in _csv_log_files(static_dir):
        with path.open(newline="", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for name in names:
                    value = row.get(name)
                    if value in {None, ""}:
                        continue
                    try:
                        parsed = float(value)
                    except ValueError:
                        continue
                    if best is None or parsed > best:
                        best = parsed
                        source = f"{path}:{name}"
    return best, source


def _contains_debug_arg(args: list[str]) -> bool:
    return any(arg in {"--debug-max-step", "--fast-dev-run", "--limit-train-batches", "--limit-val-batches"} for arg in args)


def run_external_static_node(config: dict[str, Any], output_dir: Path, max_epochs: int | None = None) -> dict[str, Any]:
    execution = config.get("execution", {})
    mode = str(execution.get("mode", "smoke"))
    if mode not in {"smoke", "benchmark"}:
        raise ValueError(f"external_static_node execution.mode must be smoke or benchmark, got {mode!r}")
    allow_test_fallback = bool(execution.get("allow_test_metric_fallback", mode == "smoke"))
    static_dir = Path(str(execution.get("static_dir", "")))
    script_path = Path(str(execution.get("script_path", "")))
    if not script_path.is_absolute():
        script_path = static_dir / script_path
    _preflight_external_static(config, static_dir, script_path, mode, output_dir)
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
    configured_args = [str(x) for x in execution.get("args", [])]
    if mode == "benchmark" and _contains_debug_arg(configured_args):
        raise ValueError("benchmark external_static_node cannot include debug/fast-dev arguments")
    args.extend(configured_args)
    if max_epochs is not None and "--max-epochs" not in args:
        args.extend(["--max-epochs", str(max_epochs)])

    started = time.time()
    proc = subprocess.run(args, cwd=static_dir, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration = time.time() - started
    output_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = output_dir / "external_stdout.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"external static node failed with exit code {proc.returncode}; see {stdout_path}")

    score_path = static_dir / "test_score.txt"
    score_metrics = _parse_score_file(score_path)
    best_val, val_source = _best_metric_from_csv_logs(static_dir, ("val/f1", "val/macro_f1", "val_macro_f1"))
    logged_test, logged_test_source = _best_metric_from_csv_logs(static_dir, ("test/f1", "test/macro_f1", "test_macro_f1"))
    test_loss = score_metrics.get("test/loss", score_metrics.get("loss", 0.0))
    score_test = score_metrics.get("test/f1") or score_metrics.get("test/macro_f1") or score_metrics.get("test_macro_f1")
    if score_test is not None:
        test_f1 = float(score_test)
        test_metric_source = str(score_path)
    elif logged_test is not None:
        test_f1 = float(logged_test)
        test_metric_source = logged_test_source
    elif allow_test_fallback and best_val is not None:
        test_f1 = float(best_val)
        test_metric_source = "missing_or_val_fallback"
    else:
        raise RuntimeError("external static benchmark did not emit held-out test Macro-F1 and fallback is disabled")
    if best_val is None:
        best_val = test_f1
        val_source = test_metric_source
    result = {
        "node_name": config.get("node_name", output_dir.name),
        "dataset_type": config.get("data", {}).get("dataset_type", "official_k562_tsv"),
        "execution_backend": "external_static_node",
        "execution_mode": mode,
        "external_script": str(script_path),
        "duration_seconds": duration,
        "best_val_macro_f1": float(best_val),
        "test_macro_f1": float(test_f1),
        "test_loss": float(test_loss),
        "validation_metric_source": val_source,
        "test_metric_source": test_metric_source,
        "external_score_metrics": score_metrics,
        "external_stdout_path": str(stdout_path),
        "external_score_path": str(score_path),
        "external_csv_logs": [str(path) for path in _csv_log_files(static_dir)],
        "artifact_usage": config.get("execution", {}).get("artifact_usage", {}),
        "notes": "External public VCHarness node wrapper. Smoke mode may use validation fallback; benchmark mode forbids it unless explicitly allowed.",
    }
    write_json(output_dir / "metrics.json", result)
    return result
