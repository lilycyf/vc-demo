from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import torch
from torch.utils.data import Dataset

from vc_demo.official_k562.dataset import OfficialK562TSVDataset, OfficialK562TSVSpec

Split = Literal["train", "val", "test"]


@dataclass(frozen=True)
class SyntheticSpec:
    n_perturbations: int = 240
    n_targets: int = 664
    n_features: int = 128
    n_classes: int = 3
    seed: int = 7


class SyntheticPerturbationDataset(Dataset):
    """Small deterministic stand-in for one cell-line DEG classification data.

    Each item represents one perturbation. The model receives a perturbation feature
    vector and predicts, for every target gene, whether expression is down, unchanged,
    or up. This mirrors the interface needed for the paper's CRISPR KO DEG task while
    staying cheap enough for a smoke test.
    """

    def __init__(self, split: Split, spec: SyntheticSpec | None = None) -> None:
        self.spec = spec or SyntheticSpec()
        rng = np.random.default_rng(self.spec.seed)
        features = rng.normal(size=(self.spec.n_perturbations, self.spec.n_features)).astype("float32")

        gene_weights = rng.normal(size=(self.spec.n_features, self.spec.n_targets)).astype("float32")
        logits = np.einsum("pf,ft->pt", features, gene_weights, optimize=False) / np.sqrt(float(self.spec.n_features))
        logits = logits.astype("float32")
        logits += 0.35 * rng.normal(size=logits.shape).astype("float32")

        labels = np.ones_like(logits, dtype="int64")
        labels[logits < -0.75] = 0
        labels[logits > 0.75] = 2

        train_end = int(0.7 * self.spec.n_perturbations)
        val_end = int(0.85 * self.spec.n_perturbations)
        if split == "train":
            sl = slice(0, train_end)
        elif split == "val":
            sl = slice(train_end, val_end)
        elif split == "test":
            sl = slice(val_end, self.spec.n_perturbations)
        else:
            raise ValueError(f"unknown split: {split}")

        self.features = torch.from_numpy(features[sl])
        self.labels = torch.from_numpy(labels[sl])

    def __len__(self) -> int:
        return self.features.shape[0]

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        return {"x": self.features[idx], "y": self.labels[idx]}


@dataclass(frozen=True)
class RealNPZSpec:
    data_dir: str
    feature_key: str = "features"
    label_key: str = "labels"
    split_key: str = "split"
    n_classes: int = 3


class RealPerturbationDataset(Dataset):
    """NPZ-backed one-cell-line perturbation dataset.

    Expected layout:

    - `manifest.json` in `data_dir`
    - either split files such as `train.npz`, `val.npz`, `test.npz`
    - or one shared NPZ plus a `split` array

    Each NPZ must expose a 2-D feature matrix and a 2-D integer label matrix.
    Labels follow the DEG convention used by the demo: 0=down, 1=unchanged, 2=up.
    """

    def __init__(self, split: Split, spec: RealNPZSpec) -> None:
        self.spec = spec
        self.data_dir = Path(spec.data_dir)
        manifest = load_real_manifest(self.data_dir)
        feature_key = str(manifest.get("feature_key", spec.feature_key))
        label_key = str(manifest.get("label_key", spec.label_key))
        split_key = str(manifest.get("split_key", spec.split_key))

        if "files" in manifest:
            files = manifest["files"]
            if split not in files:
                raise KeyError(f"manifest files must include split {split!r}")
            data = np.load(self.data_dir / files[split])
            features = data[feature_key]
            labels = data[label_key]
        elif "file" in manifest:
            data = np.load(self.data_dir / manifest["file"])
            split_values = data[split_key]
            if split_values.dtype.kind in {"S", "O"}:
                split_values = split_values.astype(str)
            mask = split_values == split
            features = data[feature_key][mask]
            labels = data[label_key][mask]
        else:
            raise KeyError("manifest must define either `files` or `file`")

        self.features = torch.from_numpy(np.asarray(features, dtype="float32"))
        self.labels = torch.from_numpy(np.asarray(labels, dtype="int64"))
        validate_arrays(self.features, self.labels, split, spec.n_classes)

    def __len__(self) -> int:
        return self.features.shape[0]

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        return {"x": self.features[idx], "y": self.labels[idx]}


def load_real_manifest(data_dir: Path) -> dict:
    import json

    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing real dataset manifest: {manifest_path}")
    with manifest_path.open() as f:
        manifest = json.load(f)
    if manifest.get("format") not in {None, "npz"}:
        raise ValueError("only manifest format `npz` is supported in this scaffold")
    return manifest


def validate_arrays(features: torch.Tensor, labels: torch.Tensor, split: Split, n_classes: int) -> None:
    if features.ndim != 2:
        raise ValueError(f"{split} features must be 2-D [perturbations, features], got {tuple(features.shape)}")
    if labels.ndim != 2:
        raise ValueError(f"{split} labels must be 2-D [perturbations, target_genes], got {tuple(labels.shape)}")
    if features.shape[0] != labels.shape[0]:
        raise ValueError(f"{split} features/labels row mismatch: {features.shape[0]} vs {labels.shape[0]}")
    if labels.numel() and (labels.min().item() < 0 or labels.max().item() >= n_classes):
        raise ValueError(f"{split} labels must be integer classes in [0, {n_classes - 1}]")


def build_datasets(config: dict) -> tuple[Dataset, Dataset, Dataset]:
    data_cfg = config.get("data", {})
    dataset_type = data_cfg.get("dataset_type", "synthetic")
    if dataset_type == "synthetic":
        spec_cfg = {k: v for k, v in data_cfg.items() if k != "dataset_type"}
        spec = SyntheticSpec(**spec_cfg)
        return (
            SyntheticPerturbationDataset("train", spec),
            SyntheticPerturbationDataset("val", spec),
            SyntheticPerturbationDataset("test", spec),
        )
    if dataset_type == "official_k562_tsv":
        spec = OfficialK562TSVSpec(
            data_dir=str(data_cfg["data_dir"]),
            embedding_h5ad=data_cfg.get("embedding_h5ad"),
            n_classes=int(data_cfg.get("n_classes", 3)),
        )
        return (
            OfficialK562TSVDataset("train", spec),
            OfficialK562TSVDataset("val", spec),
            OfficialK562TSVDataset("test", spec),
        )
    if dataset_type == "real_npz":
        spec = RealNPZSpec(
            data_dir=str(data_cfg["data_dir"]),
            feature_key=str(data_cfg.get("feature_key", "features")),
            label_key=str(data_cfg.get("label_key", "labels")),
            split_key=str(data_cfg.get("split_key", "split")),
            n_classes=int(data_cfg.get("n_classes", 3)),
        )
        return (
            RealPerturbationDataset("train", spec),
            RealPerturbationDataset("val", spec),
            RealPerturbationDataset("test", spec),
        )
    raise ValueError(f"unknown dataset_type: {dataset_type}")
