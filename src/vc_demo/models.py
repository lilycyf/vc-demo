from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class ModelSpec:
    input_dim: int = 128
    hidden_dim: int = 256
    n_targets: int = 664
    n_classes: int = 3
    dropout: float = 0.1
    depth: int = 2


class PerturbationMLP(nn.Module):
    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        dim = spec.input_dim
        for _ in range(spec.depth):
            layers.extend([
                nn.Linear(dim, spec.hidden_dim),
                nn.LayerNorm(spec.hidden_dim),
                nn.GELU(),
                nn.Dropout(spec.dropout),
            ])
            dim = spec.hidden_dim
        self.encoder = nn.Sequential(*layers)
        self.head = nn.Linear(dim, spec.n_targets * spec.n_classes)
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)


def build_model(config: dict) -> nn.Module:
    spec = ModelSpec(**config.get("model", {}))
    return PerturbationMLP(spec)
