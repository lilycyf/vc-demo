from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """ESM2 projection node with explicit missing-artifact fallback.

    The selected blueprint requires frozen ESM2 protein embeddings, but this
    RunPod experiment does not contain protein sequences or precomputed ESM2
    vectors. To preserve split/metric semantics without fabricating biological
    embeddings, the foundation branch is a frozen zero prior and all trainable
    signal comes from the existing K562 tabular features. This makes the node
    executable while recording that the Level 5 artifact was missing.
    """

    missing_artifact = "protein_sequences_or_esm2_embeddings"
    fallback = "frozen_zero_foundation_prior_plus_tabular_encoder"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        depth = max(1, min(int(spec.depth), 3))
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)

        layers: list[nn.Module] = [nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout)]
        for _ in range(depth - 1):
            layers.extend([nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout)])
        self.tabular_encoder = nn.Sequential(*layers)

        self.register_buffer("frozen_foundation_prior", torch.zeros(1, hidden), persistent=True)
        self.prior_gate = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.Sigmoid())
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 64)), hidden))
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded = self.tabular_encoder(x)
        prior = self.frozen_foundation_prior.expand(x.shape[0], -1)
        gate = self.prior_gate(x)
        fused = encoded + gate * prior
        rank_logits = self.rank_head(fused).view(x.shape[0], -1, self.n_classes)
        logits = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors)
        return logits + self.bias.unsqueeze(0)
