from __future__ import annotations

import argparse
import json
from pathlib import Path

from vc_demo.data import RealNPZSpec, RealPerturbationDataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a real one-cell-line NPZ dataset directory.")
    parser.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()

    manifest_path = args.data_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    spec = RealNPZSpec(
        data_dir=str(args.data_dir),
        feature_key=str(manifest.get("feature_key", "features")),
        label_key=str(manifest.get("label_key", "labels")),
        split_key=str(manifest.get("split_key", "split")),
        n_classes=int(manifest.get("n_classes", 3)),
    )

    report = {"data_dir": str(args.data_dir), "cell_line": manifest.get("cell_line"), "splits": {}}
    for split in ("train", "val", "test"):
        dataset = RealPerturbationDataset(split, spec)
        report["splits"][split] = {
            "n_perturbations": len(dataset),
            "feature_dim": int(dataset.features.shape[1]),
            "n_targets": int(dataset.labels.shape[1]),
            "label_min": int(dataset.labels.min().item()) if dataset.labels.numel() else None,
            "label_max": int(dataset.labels.max().item()) if dataset.labels.numel() else None,
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
