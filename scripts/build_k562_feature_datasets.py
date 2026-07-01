from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np


def load_split(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


def zscore_by_train(train: np.ndarray, arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    mean = train.mean(axis=0, keepdims=True)
    std = train.std(axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    return {split: ((value - mean) / std).astype("float32") for split, value in arrays.items()}


def write_split(path: Path, template: dict[str, np.ndarray], features: np.ndarray) -> None:
    payload = {key: value for key, value in template.items() if key != "features"}
    payload["features"] = features.astype("float32")
    np.savez_compressed(path, **payload)


def copy_dataset(src_dir: Path, out_dir: Path, manifest_extra: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((src_dir / "manifest.json").read_text())
    for split, name in manifest["files"].items():
        shutil.copy2(src_dir / name, out_dir / name)
    manifest.update(manifest_extra)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_feature_sets(src_dir: Path, output_root: Path) -> dict[str, str]:
    manifest = json.loads((src_dir / "manifest.json").read_text())
    files = manifest["files"]
    splits = {split: load_split(src_dir / name) for split, name in files.items()}

    onehot_dir = output_root / "k562_onehot"
    copy_dataset(
        src_dir,
        onehot_dir,
        {
            "feature_set": "onehot",
            "feature_description": "Perturbation identity one-hot baseline copied from data/cell_lines/k562.",
        },
    )

    delta_arrays = {split: payload["delta_mean"].astype("float32") for split, payload in splits.items()}
    delta_scaled = zscore_by_train(delta_arrays["train"], delta_arrays)
    delta_dir = output_root / "k562_delta"
    delta_dir.mkdir(parents=True, exist_ok=True)
    for split, name in files.items():
        write_split(delta_dir / name, splits[split], delta_scaled[split])
    delta_manifest = dict(manifest)
    delta_manifest.update(
        {
            "feature_set": "delta_expression",
            "feature_description": "Z-scored perturbation mean expression delta vs control for selected target genes.",
            "n_features": int(delta_scaled["train"].shape[1]),
        }
    )
    (delta_dir / "manifest.json").write_text(json.dumps(delta_manifest, indent=2), encoding="utf-8")

    concat_dir = output_root / "k562_concat"
    concat_dir.mkdir(parents=True, exist_ok=True)
    for split, name in files.items():
        onehot = splits[split]["features"].astype("float32")
        concat = np.concatenate([onehot, delta_scaled[split]], axis=1).astype("float32")
        write_split(concat_dir / name, splits[split], concat)
    concat_manifest = dict(manifest)
    concat_manifest.update(
        {
            "feature_set": "onehot_plus_delta_expression",
            "feature_description": "Concatenated perturbation one-hot and z-scored mean expression delta features.",
            "n_features": int(splits["train"]["features"].shape[1] + delta_scaled["train"].shape[1]),
        }
    )
    (concat_dir / "manifest.json").write_text(json.dumps(concat_manifest, indent=2), encoding="utf-8")

    return {"onehot": str(onehot_dir), "delta": str(delta_dir), "concat": str(concat_dir)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build multiple K562 feature datasets from the current real_npz dataset.")
    parser.add_argument("--source-dir", type=Path, default=Path("data/cell_lines/k562"))
    parser.add_argument("--output-root", type=Path, default=Path("data/cell_lines"))
    args = parser.parse_args()
    outputs = build_feature_sets(args.source_dir, args.output_root)
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
