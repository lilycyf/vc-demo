from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from vc_demo.harness.artifact_registry import audit_registry, load_registry
from vc_demo.harness.program_agent import rank_blueprint_choices
from vc_demo.harness.state import read_json, write_json


def _check_data_dir(data_dir: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"data_dir": str(data_dir), "present": data_dir.exists(), "splits": {}}
    for split in ["train", "val", "test"]:
        path = data_dir / f"{split}.npz"
        item = {"path": str(path), "present": path.exists()}
        if path.exists():
            with np.load(path, allow_pickle=True) as z:
                item["keys"] = list(z.files)
                item["n_rows"] = int(z["X"].shape[0]) if "X" in z.files else None
                item["n_targets"] = int(len(z["target_genes"])) if "target_genes" in z.files else None
        row["splits"][split] = item
    return row


def run_preflight(root_configs: list[Path], artifact_registry: Path, output: Path, cell_line: str = "K562") -> dict[str, Any]:
    roots = []
    data_dirs: dict[str, dict[str, Any]] = {}
    for path in root_configs:
        cfg = read_json(path)
        data_dir = Path(str(cfg.get("data", {}).get("data_dir", "")))
        roots.append({"path": str(path), "present": path.exists(), "node_name": cfg.get("node_name"), "data_dir": str(data_dir), "model_type": cfg.get("model", {}).get("model_type")})
        if str(data_dir) and str(data_dir) not in data_dirs:
            data_dirs[str(data_dir)] = _check_data_dir(data_dir)
    audit = audit_registry(load_registry(artifact_registry, cell_line))
    ranked = rank_blueprint_choices([
        "scfoundation_cell_encoder",
        "ppi_graph_message_passing",
        "pathway_pooling_encoder",
        "target_gene_embedding_bilinear",
        "dual_path_gated_low_rank",
        "film_conditioned_residual",
    ], audit)
    issues: list[str] = []
    for root in roots:
        if not root["present"]:
            issues.append(f"missing root config: {root['path']}")
    for data in data_dirs.values():
        if not data["present"]:
            issues.append(f"missing data dir: {data['data_dir']}")
        for split, item in data["splits"].items():
            if not item["present"]:
                issues.append(f"missing split {split}: {item['path']}")
    if "string_k562_gene_graph" not in audit.get("present_artifacts", []):
        issues.append("STRING graph artifact is not present; graph blueprints will require acquisition")
    report = {
        "format": "vc_demo_preflight.v1",
        "roots": roots,
        "data_dirs": data_dirs,
        "artifact_registry": audit,
        "artifact_aware_blueprint_preview": ranked,
        "issues": issues,
        "ready": not issues,
    }
    write_json(output, report)
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run formal-search preflight checks.")
    parser.add_argument("--root-configs", nargs="+", type=Path, required=True)
    parser.add_argument("--artifact-registry", type=Path, default=Path("configs/artifacts/k562_registry.json"))
    parser.add_argument("--cell-line", default="K562")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_preflight(args.root_configs, args.artifact_registry, args.output, args.cell_line)


if __name__ == "__main__":
    main()
