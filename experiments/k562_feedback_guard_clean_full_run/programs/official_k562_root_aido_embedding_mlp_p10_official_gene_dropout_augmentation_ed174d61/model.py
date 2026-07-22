from __future__ import annotations

from pathlib import Path

import torch
from torch import nn

OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")


class FeatureDropout(nn.Module):
    def __init__(self, p: float) -> None:
        super().__init__()
        self.p = float(p)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if not self.training or self.p <= 0:
            return x
        keep = torch.rand_like(x) > self.p
        return x * keep.to(dtype=x.dtype) / max(1e-6, 1.0 - self.p)


class ResidualBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden * 2, hidden), nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Parent dense head with training-time feature dropout augmentation."""

    def __init__(self, spec) -> None:
        super().__init__()
        if not OFFICIAL_DEG_ARTIFACT.exists():
            raise FileNotFoundError(f"official DEG split artifact is required: {OFFICIAL_DEG_ARTIFACT}")
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.feature_dropout_p = 0.08
        self.implementation_semantics = "parent_preserving_regularization_delta"
        self.artifact_usage = {
            "official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT),
            "augmentation": "training_only_feature_dropout",
            "feature_dropout_p": self.feature_dropout_p,
        }
        self.feature_dropout = FeatureDropout(self.feature_dropout_p)
        self.input = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.norm = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.feature_dropout(x)
        z = self.norm(self.blocks(self.input(x)))
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
