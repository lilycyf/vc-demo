from __future__ import annotations

from pathlib import Path

import torch
from torch import nn


TASK_DATA = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")


class GeneratedModel(nn.Module):
    """Low-rank target-specific head for official K562 DEG labels."""

    def __init__(self, spec) -> None:
        super().__init__()
        if not TASK_DATA.exists():
            raise FileNotFoundError(f"official K562 task artifact missing: {TASK_DATA}")
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        rank = max(32, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 160))
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
        )
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        nn.init.normal_(self.target_factors, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        rank_logits = self.rank_head(z).view(x.shape[0], -1, self.n_classes)
        return torch.einsum("brc,nr->bnc", rank_logits, self.target_factors) + self.target_bias.unsqueeze(0)
