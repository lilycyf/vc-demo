from __future__ import annotations

import torch
from torch import nn


def expert_block(input_dim: int, hidden: int, dropout: float) -> nn.Sequential:
    return nn.Sequential(nn.Linear(input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden), nn.GELU())


class GeneratedModel(nn.Module):
    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.experts = nn.ModuleList([expert_block(spec.input_dim, hidden, spec.dropout) for _ in range(3)])
        self.router = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.GELU(), nn.Linear(hidden, 3), nn.Softmax(dim=-1))
        self.norm = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        weights = self.router(x)
        stacked = torch.stack([expert(x) for expert in self.experts], dim=1)
        z = torch.sum(stacked * weights.unsqueeze(-1), dim=1)
        logits = self.head(self.norm(z))
        return logits.view(x.shape[0], self.n_targets, self.n_classes)
