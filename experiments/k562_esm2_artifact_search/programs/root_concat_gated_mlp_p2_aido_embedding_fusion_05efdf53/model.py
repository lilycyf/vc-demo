from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """AIDO missing-artifact fallback model.

    No real AIDO artifact is present in this run. This model does not fabricate
    AIDO embeddings; it is a compact gated fusion fallback over the available
    tabular input and must be reported as missing_aido_artifact_fallback.
    """

    artifact_status = "missing_aido_artifact_fallback"

    def __init__(self, spec):
        super().__init__()
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        split = max(1, int(spec.input_dim) // 2)
        self.left_dim = split
        self.right_dim = int(spec.input_dim) - split
        self.left = nn.Sequential(nn.LayerNorm(self.left_dim), nn.Linear(self.left_dim, hidden), nn.GELU(), nn.Dropout(dropout))
        self.right = nn.Sequential(nn.LayerNorm(self.right_dim), nn.Linear(self.right_dim, hidden), nn.GELU(), nn.Dropout(dropout))
        self.gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.Sigmoid())
        self.norm = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, spec.n_targets * spec.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        left = x[:, : self.left_dim]
        right = x[:, self.left_dim :]
        zl = self.left(left)
        zr = self.right(right)
        g = self.gate(torch.cat([zl, zr], dim=-1))
        z = self.norm(g * zl + (1.0 - g) * zr)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
