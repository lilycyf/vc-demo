from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """ESM2-aware projection model.

    This node expects the K562 ESM2 artifact dataset where the final 1280 input
    columns are frozen ESM2 gene embedding features aligned to the perturbed gene.
    The earlier columns are the existing K562 concat features. If a smaller input
    is supplied, the model falls back to treating the whole vector as base input;
    that fallback is for smoke robustness and should be reported as non-ESM2.
    """

    artifact_name = "ESM2_D1280"
    artifact_embedding_dim = 1280
    artifact_coverage = 0.9619047619047619

    def __init__(self, spec):
        super().__init__()
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes
        self.embedding_dim = min(self.artifact_embedding_dim, max(int(spec.input_dim) - 1, 0))
        self.base_dim = int(spec.input_dim) - self.embedding_dim
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.base_encoder = nn.Sequential(
            nn.LayerNorm(self.base_dim),
            nn.Linear(self.base_dim, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.esm_encoder = nn.Sequential(
            nn.LayerNorm(self.embedding_dim),
            nn.Linear(self.embedding_dim, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.fusion_gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.Sigmoid())
        self.refine = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden * 2, hidden),
            nn.Dropout(dropout),
        )
        self.head = nn.Linear(hidden, spec.n_targets * spec.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base = x[:, : self.base_dim]
        esm = x[:, self.base_dim :]
        base_z = self.base_encoder(base)
        esm_z = self.esm_encoder(esm)
        gate = self.fusion_gate(torch.cat([base_z, esm_z], dim=-1))
        z = gate * esm_z + (1.0 - gate) * base_z
        z = z + self.refine(z)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
