from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Pathway pooling node with explicit missing pathway artifact fallback.

    The selected Level 5 blueprint requires a pathway membership matrix aligned
    to target genes. No such artifact is present in the prepared K562 data and
    this run cannot alter data/splits or download external resources. The model
    therefore records missing pathway coverage and uses learnable pathway slots
    as a compact fallback rather than fabricating biological memberships.
    """

    missing_artifact = "pathway_memberships"
    fallback = "learnable_pathway_slots_without_external_membership"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.n_pathways = min(64, max(16, self.n_targets // 16))
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
        )
        self.pathway_logits = nn.Linear(hidden, self.n_pathways * self.n_classes)
        self.target_pathway_weights = nn.Parameter(torch.empty(self.n_targets, self.n_pathways))
        nn.init.xavier_uniform_(self.target_pathway_weights)
        self.direct_residual = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.mix = nn.Parameter(torch.tensor(0.35))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        pathway = self.pathway_logits(z).view(x.shape[0], self.n_pathways, self.n_classes)
        weights = torch.softmax(self.target_pathway_weights, dim=-1)
        pooled = torch.einsum("bpc,np->bnc", pathway, weights)
        direct = self.direct_residual(z).view(x.shape[0], self.n_targets, self.n_classes)
        alpha = torch.sigmoid(self.mix)
        return alpha * pooled + (1.0 - alpha) * direct
