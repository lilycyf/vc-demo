from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        rank = max(8, min(int(getattr(spec, "low_rank_dim", 64)), hidden))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.left = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(spec.dropout))
        self.right = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU())
        self.gate = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.Sigmoid())
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate = self.gate(x)
        z = self.left(x) * gate + self.right(x) * (1.0 - gate)
        rank_logits = self.rank_head(z).view(x.shape[0], -1, self.n_classes)
        logits = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors)
        return logits + self.bias.unsqueeze(0)
