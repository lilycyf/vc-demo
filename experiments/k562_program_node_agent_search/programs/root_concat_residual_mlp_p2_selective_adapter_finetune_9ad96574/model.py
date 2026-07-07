from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Selective-adapter node with explicit missing-pretrained-encoder fallback.

    No pretrained encoder artifact is present. A compact base projection is
    frozen after deterministic initialization, and only adapter/head parameters
    are trainable. This records the fallback without pretending to fine-tune a
    real external model.
    """

    missing_artifact = "pretrained_encoder"
    fallback = "frozen_random_base_projection_plus_trainable_adapter"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        bottleneck = max(16, hidden // 4)
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.base = nn.Linear(int(spec.input_dim), hidden)
        nn.init.xavier_uniform_(self.base.weight)
        nn.init.zeros_(self.base.bias)
        for param in self.base.parameters():
            param.requires_grad = False
        self.adapter = nn.Sequential(
            nn.LayerNorm(hidden), nn.Linear(hidden, bottleneck), nn.GELU(), nn.Dropout(dropout), nn.Linear(bottleneck, hidden), nn.GELU()
        )
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base = self.base(x)
        z = base + self.adapter(base)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
