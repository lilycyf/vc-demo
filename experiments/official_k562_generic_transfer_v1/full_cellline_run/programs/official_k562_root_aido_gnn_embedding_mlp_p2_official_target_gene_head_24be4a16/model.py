from __future__ import annotations

import math

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Target-gene-aware DEG head for the official K562 task.

    This node keeps the official input features and task geometry fixed, then
    replaces the dense all-target classifier with an explicit target factor bank.
    Each class receives its own context projection, so every target gene has a
    learned target-specific decision surface while preserving the exact 6,640
    target order supplied by the official dataset loader.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        hidden = int(spec.hidden_dim)
        depth = max(1, int(spec.depth))
        dropout = float(spec.dropout)
        rank = max(32, min(int(getattr(spec, "low_rank_dim", 96) or 96), hidden, 192))

        layers: list[nn.Module] = [
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        ]
        for _ in range(depth - 1):
            layers.extend([
                nn.Linear(hidden, hidden),
                nn.LayerNorm(hidden),
                nn.GELU(),
                nn.Dropout(dropout),
            ])
        self.encoder = nn.Sequential(*layers)
        self.context_to_class_rank = nn.Linear(hidden, self.n_classes * rank)
        self.context_residual = nn.Linear(hidden, self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        self.target_class_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.target_residual = nn.Parameter(torch.empty(self.n_targets, self.n_classes))
        nn.init.normal_(self.target_factors, mean=0.0, std=1.0 / math.sqrt(rank))
        nn.init.normal_(self.target_residual, mean=0.0, std=0.01)
        self.rank = rank

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        context = self.encoder(x)
        class_rank = self.context_to_class_rank(context).view(x.shape[0], self.n_classes, self.rank)
        logits = torch.einsum("bcr,nr->bnc", class_rank, self.target_factors)
        residual = self.context_residual(context).unsqueeze(1) * self.target_residual.unsqueeze(0)
        return logits + residual + self.target_class_bias.unsqueeze(0)
