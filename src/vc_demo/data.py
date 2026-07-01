from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import torch
from torch.utils.data import Dataset

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
        logits = features @ gene_weights / np.sqrt(self.spec.n_features)
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
