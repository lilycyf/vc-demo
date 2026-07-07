from __future__ import annotations

import argparse
import json
from pathlib import Path

import importlib.util


def _load_validate_model_dir():
    script = Path(__file__).with_name("download_hf_model_snapshot.py")
    spec = importlib.util.spec_from_file_location("download_hf_model_snapshot", script)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_model_dir


validate_model_dir = _load_validate_model_dir()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate local official VCHarness model directories.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        validate_model_dir(Path("/home/Models/AIDO.Cell-100M"), "genbio-ai/AIDO.Cell-100M")
        if Path("/home/Models/AIDO.Cell-100M").exists()
        else {
            "path": "/home/Models/AIDO.Cell-100M",
            "repo_id": "genbio-ai/AIDO.Cell-100M",
            "status": "missing",
            "warnings": ["directory does not exist"],
        },
        validate_model_dir(Path("/home/Models/STRING_GNN"), "genbio-ai/STRING_GNN")
        if Path("/home/Models/STRING_GNN").exists()
        else {
            "path": "/home/Models/STRING_GNN",
            "repo_id": "genbio-ai/STRING_GNN",
            "status": "missing",
            "warnings": ["directory does not exist; Hugging Face repo currently lists no weight files"],
        },
    ]
    result = {
        "status": "passed_with_warnings" if any(row.get("status") == "usable_with_warnings" for row in rows) else "blocked",
        "model_dirs": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
