from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """ESM2 projection node with explicit missing-artifact fallback.

    No protein sequences or precomputed ESM2 embeddings are present in this
    prepared K562 run. The ESM2 branch is a frozen zero prior so the model is
    trainable without fabricating biological foundation embeddings.
    """

    missing_artifact = "protein_sequences_or_esm2_embeddings"
    fallback = "frozen_zero_esm2_prior_plus_tabular_encoder"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
        )
        self.register_buffer("frozen_esm2_prior", torch.zeros(1, hidden), persistent=True)
        self.prior_gate = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.Sigmoid())
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 64)), hidden))
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        prior = self.frozen_esm2_prior.expand(x.shape[0], -1)
        fused = z + self.prior_gate(x) * prior
        rank_logits = self.rank_head(fused).view(x.shape[0], -1, self.n_classes)
        logits = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors)
        return logits + self.bias.unsqueeze(0)
