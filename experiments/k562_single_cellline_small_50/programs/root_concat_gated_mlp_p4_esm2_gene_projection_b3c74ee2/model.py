from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    artifact_usage = "esm2_gene_embedding_h5ad_via_k562_esm2_feature_dataset"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        input_dim = int(spec.input_dim)
        emb_dim = int(getattr(spec, "perturbation_embedding_dim", 1280) or 1280)
        if input_dim <= emb_dim:
            emb_dim = input_dim
        context_dim = input_dim - emb_dim
        if context_dim <= 0:
            context_dim = input_dim
            emb_dim = input_dim
        self.context_dim = context_dim
        self.emb_dim = emb_dim
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        dropout = float(spec.dropout)
        self.context_encoder = nn.Sequential(
            nn.Linear(context_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.esm2_encoder = nn.Sequential(
            nn.Linear(emb_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.Sigmoid())
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        context = x[:, : self.context_dim]
        esm2 = x[:, -self.emb_dim :]
        c = self.context_encoder(context)
        e = self.esm2_encoder(esm2)
        gate = self.gate(torch.cat([c, e], dim=-1))
        z = c * (1.0 - gate) + e * gate
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
