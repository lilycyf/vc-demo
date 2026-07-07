from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Gated multimodal fusion using active tabular K562 modalities.

    Available modalities in this run are the fixed real_npz feature vector only.
    The model splits that vector into expression/context projections and fuses
    them through learned gates. Optional external prior/foundation branches are
    recorded as inactive rather than fabricated.
    """

    active_modalities = "tabular_features"
    inactive_modalities = "external_prior_embeddings"
    fallback = "two_view_tabular_gated_fusion"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        input_dim = int(spec.input_dim)
        self.cell_view = nn.Sequential(nn.Linear(input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.perturb_view = nn.Sequential(nn.Linear(input_dim, hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU())
        self.gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.Sigmoid())
        self.residual = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden), nn.GELU(), nn.Dropout(dropout))
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        cell = self.cell_view(x)
        perturb = self.perturb_view(x)
        gate = self.gate(torch.cat([cell, perturb], dim=-1))
        fused = gate * cell + (1.0 - gate) * perturb
        fused = fused + self.residual(fused)
        return self.head(fused).view(x.shape[0], self.n_targets, self.n_classes)
