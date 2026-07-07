from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """AIDO fusion node with explicit missing-artifact fallback.

    The selected blueprint requires precomputed AIDO embeddings or an approved
    loader. Neither artifact is present in the prepared K562 real_npz data, and
    this run is not allowed to download large foundation models. The AIDO branch
    is therefore represented as a frozen zero modality with an explicit gate; no
    random biological embedding is substituted.
    """

    missing_artifact = "aido_embeddings"
    fallback = "inactive_frozen_aido_branch_with_gated_tabular_fusion"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)

        self.expression_path = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
        )
        self.context_path = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.GELU(),
        )
        self.register_buffer("frozen_aido_prior", torch.zeros(1, hidden), persistent=True)
        self.modality_gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.Sigmoid())
        self.head = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.n_targets * self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        expr = self.expression_path(x)
        ctx = self.context_path(x)
        aido = self.frozen_aido_prior.expand(x.shape[0], -1)
        gate = self.modality_gate(torch.cat([expr, ctx], dim=-1))
        fused = expr + gate * ctx + (1.0 - gate) * aido
        return self.head(fused).view(x.shape[0], self.n_targets, self.n_classes)
