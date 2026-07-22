from __future__ import annotations

from pathlib import Path

import torch
from torch import nn
import torch.nn.functional as F

OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")


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
    """Parent dense head with learnable positive temperature calibration."""
    def __init__(self, spec) -> None:
        super().__init__()
        if not OFFICIAL_DEG_ARTIFACT.exists():
            raise FileNotFoundError(f"official DEG split artifact is required: {OFFICIAL_DEG_ARTIFACT}")
        hidden = int(spec.hidden_dim); dropout = float(spec.dropout); depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets); self.n_classes = int(spec.n_classes)
        self.implementation_semantics = "parent_preserving_calibration_delta"
        self.artifact_usage = {"official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT), "calibration": "learned_train_split_temperature_no_test_tuning"}
        self.input = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.norm = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.raw_temperature = nn.Parameter(torch.tensor(0.0))
        self.class_bias = nn.Parameter(torch.zeros(self.n_classes))
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.norm(self.blocks(self.input(x)))
        logits = self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
        temperature = 0.5 + F.softplus(self.raw_temperature)
        return logits / temperature + self.class_bias.view(1, 1, self.n_classes) + self.target_bias.unsqueeze(0)
