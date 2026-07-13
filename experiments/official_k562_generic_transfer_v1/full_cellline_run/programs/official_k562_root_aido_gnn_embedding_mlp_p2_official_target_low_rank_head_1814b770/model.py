from __future__ import annotations

from pathlib import Path

import torch
from torch import nn


class ResidualBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden * 2, hidden),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Official low-rank target-specific classifier for all K562 DEG targets."""

    def __init__(self, spec) -> None:
        super().__init__()
        target_path = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
        if not target_path.exists():
            raise FileNotFoundError(f"official target-gene contract is missing: {target_path}")
        rows = [line for line in target_path.read_text().splitlines() if line.strip()]
        if rows and rows[0].split("\t")[0].lower() == "target_index":
            rows = rows[1:]
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        if len(rows) != self.n_targets:
            raise ValueError(f"official target count {len(rows)} != n_targets {self.n_targets}")
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(2, int(spec.depth))
        self.rank = max(64, min(int(getattr(spec, "low_rank_dim", 128)), hidden, 192))
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            *[ResidualBlock(hidden, dropout) for _ in range(depth)],
            nn.LayerNorm(hidden),
        )
        self.rank_head = nn.Linear(hidden, self.rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, self.rank))
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.direct_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.mix_logit = nn.Parameter(torch.tensor(0.0))
        nn.init.xavier_uniform_(self.target_factors)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        low_rank = torch.einsum(
            "brc,nr->bnc",
            self.rank_head(z).view(x.shape[0], self.rank, self.n_classes),
            self.target_factors,
        ) + self.target_bias.unsqueeze(0)
        direct = self.direct_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        mix = torch.sigmoid(self.mix_logit).to(dtype=z.dtype)
        return mix * direct + (1.0 - mix) * low_rank
