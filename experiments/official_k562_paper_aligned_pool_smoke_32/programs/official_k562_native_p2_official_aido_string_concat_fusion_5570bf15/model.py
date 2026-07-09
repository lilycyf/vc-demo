from __future__ import annotations

from pathlib import Path

import torch
from torch import nn


AIDO_DIR = Path("/home/Models/AIDO.Cell-100M")
STRING_DIR = Path("/home/Models/STRING_GNN")


class GeneratedModel(nn.Module):
    """AIDO + STRING/GNN cached embedding concat fusion for official K562."""

    def __init__(self, spec) -> None:
        super().__init__()
        if not (AIDO_DIR / "config.json").exists():
            raise FileNotFoundError(f"required AIDO.Cell-100M artifact missing: {AIDO_DIR}")
        if not (STRING_DIR / "config.json").exists():
            raise FileNotFoundError(f"required STRING_GNN artifact missing: {STRING_DIR}")
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        input_dim = int(spec.input_dim)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 128))
        self.aido_dim = min(640, input_dim)
        self.string_dim = max(0, input_dim - self.aido_dim)
        if self.string_dim <= 0:
            raise ValueError("AIDO_STRING concat fusion requires a non-empty STRING/GNN cached embedding slice")
        self.aido_encoder = nn.Sequential(nn.Linear(self.aido_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.string_encoder = nn.Sequential(nn.Linear(self.string_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.concat_encoder = nn.Sequential(
            nn.Linear(hidden * 2, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(),
        )
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        aido = self.aido_encoder(x[:, : self.aido_dim])
        string = self.string_encoder(x[:, self.aido_dim :])
        fused = self.concat_encoder(torch.cat([aido, string], dim=-1))
        rank_logits = self.rank_head(fused).view(x.shape[0], -1, self.n_classes)
        logits = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors)
        return logits + self.target_bias.unsqueeze(0)
