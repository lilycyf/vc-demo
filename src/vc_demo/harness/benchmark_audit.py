from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from vc_demo.harness.state import read_json, write_json


EXPECTED = {
    "task_type": "CRISPR perturbation target-gene DEG classification",
    "cell_line": "K562",
    "metric": "Macro-F1 over flattened target-gene DEG classes",
    "label_classes": 3,
    "split_policy": "fixed train/val/test perturbation examples; test is not used for selection",
}


def _split_summary(path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"path": str(path), "present": path.exists()}
    if not path.exists():
        return row
    with np.load(path, allow_pickle=True) as z:
        row["keys"] = list(z.files)
        feature_key = "X" if "X" in z.files else "features" if "features" in z.files else ""
        label_key = "y" if "y" in z.files else "labels" if "labels" in z.files else ""
        if feature_key:
            x = z[feature_key]
            row["feature_key"] = feature_key
            row["n_rows"] = int(x.shape[0])
            row["input_dim"] = int(x.shape[1])
        if label_key:
            y = z[label_key]
            row["label_key"] = label_key
            row["label_shape"] = list(y.shape)
            row["label_classes_observed"] = sorted(int(v) for v in np.unique(y))
            values, counts = np.unique(y, return_counts=True)
            row["label_distribution"] = {str(int(v)): int(c) for v, c in zip(values, counts)}
        if "perturbations" in z.files:
            perts = [str(x) for x in z["perturbations"].tolist()]
            row["n_unique_perturbations"] = len(set(perts))
            row["n_rows_with_perturbation_ids"] = len(perts)
        if "target_genes" in z.files:
            targets = [str(x) for x in z["target_genes"].tolist()]
            row["n_target_genes"] = len(targets)
            row["target_gene_sample"] = targets[:10]
    return row


def audit(root_configs: list[Path], output: Path) -> dict[str, Any]:
    roots: list[dict[str, Any]] = []
    data_dirs: dict[str, Any] = {}
    issues: list[str] = []
    for cfg_path in root_configs:
        cfg = read_json(cfg_path)
        data_dir = Path(str(cfg.get("data", {}).get("data_dir", "")))
        roots.append({"config": str(cfg_path), "node_name": cfg.get("node_name"), "cell_line": cfg.get("data", {}).get("cell_line"), "data_dir": str(data_dir), "model_type": cfg.get("model", {}).get("model_type")})
        if str(data_dir) not in data_dirs:
            split_rows = {split: _split_summary(data_dir / f"{split}.npz") for split in ["train", "val", "test"]}
            data_dirs[str(data_dir)] = {"data_dir": str(data_dir), "splits": split_rows}
            target_counts = {split: row.get("n_target_genes") for split, row in split_rows.items() if row.get("present")}
            if len(set(target_counts.values())) > 1:
                issues.append(f"target gene count differs across splits in {data_dir}: {target_counts}")
            input_dims = {split: row.get("input_dim") for split, row in split_rows.items() if row.get("present")}
            if len(set(input_dims.values())) > 1:
                issues.append(f"input dim differs across splits in {data_dir}: {input_dims}")
            for split, row in split_rows.items():
                if not row.get("present"):
                    issues.append(f"missing {split}.npz in {data_dir}")
                if row.get("label_classes_observed") and not set(row["label_classes_observed"]).issubset({0, 1, 2}):
                    issues.append(f"unexpected label classes in {split}: {row['label_classes_observed']}")
    report = {
        "format": "vc_demo_benchmark_alignment_audit.v1",
        "expected_contract": EXPECTED,
        "roots": roots,
        "data_dirs": data_dirs,
        "issues": issues,
        "alignment_status": "ready_for_single_cell_line_formal_search" if not issues else "blocked_or_needs_review",
        "paper_repo_alignment": {
            "paper_case_study": "VCHarness Essential dataset includes K562 plus additional public classification tracks that must be discovered only from the user-specified CELL_LINE_ID during transfer.",
            "repo_task_scope": "This audit covers only the K562 single-cell-line CRISPR_KO_DEG_classification track.",
            "data_source_in_this_repo": "NormanWeissman2019_filtered.h5ad from scPerturb Zenodo record 7041849, with repo-local top-1000 target-gene and percentile DEG label construction.",
            "numeric_reproduction_status": "framework-aligned but not certified numerically identical to the paper until exact VCHarness K562 split, target universe, label rule, and expert baseline configs are matched."
        },
        "remaining_paper_alignment_questions": [
            "Confirm the public paper's exact K562 split policy if claiming numeric reproduction rather than framework reproduction.",
            "Confirm DEG label construction and target gene universe against the paper artifact if available.",
            "Confirm expert baseline identity and hyperparameters before comparing absolute numbers to the paper.",
        ],
    }
    write_json(output, report)
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit benchmark/task alignment for a single-cell-line formal run.")
    parser.add_argument("--root-configs", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(args.root_configs, args.output)


if __name__ == "__main__":
    main()
