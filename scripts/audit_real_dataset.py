from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def is_one_hot(features: np.ndarray) -> bool:
    if features.ndim != 2:
        return False
    if not np.all((features == 0) | (features == 1)):
        return False
    row_sums = features.sum(axis=1)
    return bool(np.all(row_sums == 1))


def split_report(data_dir: Path, file_name: str, feature_key: str, label_key: str) -> dict:
    data = np.load(data_dir / file_name)
    features = data[feature_key]
    labels = data[label_key]
    unique, counts = np.unique(labels, return_counts=True)
    class_counts = {str(int(k)): int(v) for k, v in zip(unique, counts)}
    return {
        "file": file_name,
        "n_perturbations": int(features.shape[0]),
        "feature_dim": int(features.shape[1]),
        "n_targets": int(labels.shape[1]),
        "feature_dtype": str(features.dtype),
        "label_dtype": str(labels.dtype),
        "feature_min": float(np.min(features)) if features.size else None,
        "feature_max": float(np.max(features)) if features.size else None,
        "is_one_hot_features": is_one_hot(features),
        "class_counts": class_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a real_npz perturbation dataset for handoff/review.")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    manifest_path = args.data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    feature_key = manifest.get("feature_key", "features")
    label_key = manifest.get("label_key", "labels")
    files = manifest.get("files")
    if not files:
        raise ValueError("audit_real_dataset.py currently expects split-file manifest with `files`")

    report = {
        "data_dir": str(args.data_dir),
        "cell_line": manifest.get("cell_line"),
        "source": manifest.get("source"),
        "label_rule": manifest.get("label_rule"),
        "target_gene_selection": manifest.get("target_gene_selection"),
        "splits": {split: split_report(args.data_dir, file_name, feature_key, label_key) for split, file_name in files.items()},
    }
    all_counts: dict[str, int] = {}
    for split in report["splits"].values():
        for cls, count in split["class_counts"].items():
            all_counts[cls] = all_counts.get(cls, 0) + count
    report["total_class_counts"] = all_counts
    report["all_splits_one_hot_features"] = all(split["is_one_hot_features"] for split in report["splits"].values())

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
