from __future__ import annotations

import json
from pathlib import Path

import torch
from torch import nn


class ResidualBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden * 2, hidden), nn.Dropout(dropout)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


def _target_count(path: Path) -> int:
    rows = [line for line in path.read_text().splitlines() if line.strip()]
    if rows and rows[0].split("\t")[0].lower() == "target_index":
        rows = rows[1:]
    return len(rows)


def _train_label_bias(train_path: Path, n_targets: int, n_classes: int) -> torch.Tensor:
    counts = torch.ones(n_targets, n_classes, dtype=torch.float32)
    if not train_path.exists():
        raise FileNotFoundError(f"official train split is missing: {train_path}")
    with train_path.open() as f:
        header = f.readline().rstrip("\n").split("\t")
        label_col = header.index("label")
        for line in f:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            labels = json.loads(parts[label_col])
            if len(labels) != n_targets:
                raise ValueError(f"train label length {len(labels)} != n_targets {n_targets}")
            mapped = torch.tensor(labels, dtype=torch.long) + 1
            mapped = mapped.clamp_(0, n_classes - 1)
            counts.scatter_add_(1, mapped.view(-1, 1), torch.ones(n_targets, 1))
    probs = counts / counts.sum(dim=1, keepdim=True).clamp_min(1.0)
    return probs.log().clamp(min=-6.0, max=2.0)


class GeneratedModel(nn.Module):
    """Target-gene-aware head with train-split-only class-prior initialization."""

    def __init__(self, spec) -> None:
        super().__init__()
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        target_path = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
        if _target_count(target_path) != self.n_targets:
            raise ValueError("official target count does not match model spec")
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(2, int(spec.depth))
        self.rank = max(64, min(int(getattr(spec, "low_rank_dim", 128)), hidden, 192))
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout * 0.8),
            *[ResidualBlock(hidden, dropout * 0.8) for _ in range(depth)], nn.LayerNorm(hidden)
        )
        self.context_rank = nn.Linear(hidden, self.rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, self.rank))
        self.direct = nn.Linear(hidden, self.n_targets * self.n_classes)
        prior = _train_label_bias(Path("data/cell_lines/official_k562_cls/train.tsv"), self.n_targets, self.n_classes)
        self.target_bias = nn.Parameter(prior)
        self.mix = nn.Sequential(nn.Linear(hidden, 1), nn.Sigmoid())
        nn.init.normal_(self.target_factors, mean=0.0, std=0.025)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        rank_logits = self.context_rank(z).view(x.shape[0], self.rank, self.n_classes)
        low_rank = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors) + self.target_bias.unsqueeze(0)
        direct = self.direct(z).view(x.shape[0], self.n_targets, self.n_classes)
        mix = self.mix(z).view(x.shape[0], 1, 1)
        return mix * direct + (1.0 - mix) * low_rank
