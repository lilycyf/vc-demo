from __future__ import annotations

from pathlib import Path

import torch
from torch import nn

OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")
CLASS_DISTRIBUTION = Path("data/artifacts/official_k562/class_distribution_train.json")


class ResidualBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden * 2, hidden),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Parent-preserving dense head for focal-loss training strategy.

    The blueprint delta is the training objective (`focal_loss` in base_config),
    so the node-local model preserves the parent dense all-target route without
    importing smoke-only native helpers or changing the official task contract.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        if not OFFICIAL_DEG_ARTIFACT.exists():
            raise FileNotFoundError(f"official DEG split artifact is required: {OFFICIAL_DEG_ARTIFACT}")
        if not CLASS_DISTRIBUTION.exists():
            raise FileNotFoundError(f"train-only class distribution artifact is required: {CLASS_DISTRIBUTION}")
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.focal_gamma = float(getattr(spec, "focal_gamma", 2.0))
        self.implementation_semantics = "parent_preserving_training_delta"
        self.artifact_usage = {
            "official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT),
            "class_distribution": str(CLASS_DISTRIBUTION),
            "focal_gamma": self.focal_gamma,
        }
        self.input = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.norm = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.norm(self.blocks(self.input(x)))
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
