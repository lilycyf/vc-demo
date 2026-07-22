from __future__ import annotations

import torch
from torch import nn


class ResidualContextBlock(nn.Module):
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
    """Parent-preserving dense K562 head with learnable train-only temperature."""

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            *[ResidualContextBlock(hidden, dropout) for _ in range(depth)],
            nn.LayerNorm(hidden),
        )
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.log_temperature = nn.Parameter(torch.zeros(()))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        logits = self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
        temperature = torch.clamp(self.log_temperature.exp(), min=0.5, max=3.0)
        return logits / temperature
