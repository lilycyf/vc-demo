from __future__ import annotations

import math

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Frozen AIDO embedding fusion head for the official K562 task.

    The official K562 loader supplies the audited AIDO.Cell-100M cached H5AD
    representation as the input vector for this root family. This node keeps
    that source fixed and learns feature gates plus target-specific factors for
    the 6,640 DEG targets.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        input_dim = int(spec.input_dim)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        rank = max(48, min(int(getattr(spec, "low_rank_dim", 96) or 96), hidden, 192))

        self.aido_projection = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.context_projection = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
        )
        self.feature_gate = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, hidden),
            nn.Sigmoid(),
        )
        self.class_rank_head = nn.Linear(hidden, self.n_classes * rank)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.global_class_bias = nn.Linear(hidden, self.n_classes)
        nn.init.normal_(self.target_factors, mean=0.0, std=1.0 / math.sqrt(rank))
        self.rank = rank

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        aido_context = self.aido_projection(x)
        learned_context = self.context_projection(x)
        gate = self.feature_gate(x)
        fused = gate * aido_context + (1.0 - gate) * learned_context
        rank_logits = self.class_rank_head(fused).view(x.shape[0], self.n_classes, self.rank)
        logits = torch.einsum("bcr,nr->bnc", rank_logits, self.target_factors)
        return logits + self.target_bias.unsqueeze(0) + self.global_class_bias(fused).unsqueeze(1)
