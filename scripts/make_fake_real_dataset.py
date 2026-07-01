from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def write_split(path: Path, features: np.ndarray, labels: np.ndarray) -> None:
    np.savez_compressed(path, features=features.astype("float32"), labels=labels.astype("int64"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a tiny NPZ fixture that exercises the real-data loader.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/cell_lines/k562_demo"))
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    args.data_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    n_features = 64
    n_targets = 96
    counts = {"train": 48, "val": 16, "test": 16}
    gene_weights = rng.normal(size=(n_features, n_targets)).astype("float32")

    for split, n_rows in counts.items():
        features = rng.normal(size=(n_rows, n_features)).astype("float32")
        logits = features @ gene_weights / np.sqrt(float(n_features))
        labels = np.ones_like(logits, dtype="int64")
        labels[logits < -0.7] = 0
        labels[logits > 0.7] = 2
        write_split(args.data_dir / f"{split}.npz", features, labels)

    manifest = {
        "format": "npz",
        "cell_line": "K562_demo_fixture",
        "task": "CRISPR_KO_DEG_classification",
        "feature_key": "features",
        "label_key": "labels",
        "n_classes": 3,
        "class_names": ["down", "unchanged", "up"],
        "files": {"train": "train.npz", "val": "val.npz", "test": "test.npz"},
        "notes": "Tiny deterministic fixture for loader validation only; not a biological dataset.",
    }
    (args.data_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"data_dir": str(args.data_dir), "manifest": str(args.data_dir / "manifest.json")}, indent=2))


if __name__ == "__main__":
    main()
