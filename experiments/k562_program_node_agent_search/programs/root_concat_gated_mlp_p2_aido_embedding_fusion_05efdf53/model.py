from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """AIDO fusion node with explicit missing-artifact fallback.

    No precomputed AIDO embeddings or approved loader are present. The AIDO
    modality is represented as an inactive frozen zero branch, and trainable
    signal comes only from existing K562 tabular features.
    """

    missing_artifact = "aido_embeddings"
    fallback = "inactive_frozen_aido_branch_with_gated_tabular_fusion"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        input_dim = int(spec.input_dim)
        self.cell_path = nn.Sequential(nn.Linear(input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.context_path = nn.Sequential(nn.Linear(input_dim, hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU())
        self.register_buffer("frozen_aido_prior", torch.zeros(1, hidden), persistent=True)
        self.gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.Sigmoid())
        self.head = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.n_targets * self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        cell = self.cell_path(x)
        ctx = self.context_path(x)
        aido = self.frozen_aido_prior.expand(x.shape[0], -1)
        gate = self.gate(torch.cat([cell, ctx], dim=-1))
        fused = cell + gate * ctx + (1.0 - gate) * aido
        return self.head(fused).view(x.shape[0], self.n_targets, self.n_classes)
