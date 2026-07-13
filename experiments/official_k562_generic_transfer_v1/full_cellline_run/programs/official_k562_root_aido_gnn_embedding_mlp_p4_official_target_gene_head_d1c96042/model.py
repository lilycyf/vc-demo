from __future__ import annotations

from pathlib import Path

import torch
from torch import nn


class ResidualMLPBlock(nn.Module):
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
    """Official target-gene-aware low-rank DEG head.

    The parent root predicts all target genes with one dense head. This child keeps
    the official K562 feature contract but replaces that dense head with an
    explicit target-gene factorization: perturbation/cell context produces
    rank-specific class logits and each official target gene owns an aligned
    factor vector. The target count is validated against the checked-in official
    task contract when available; no split, label, metric, or target order is
    modified here.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        input_dim = int(spec.input_dim)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(32, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 160))

        target_gene_path = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
        if target_gene_path.exists():
            lines = [line.strip() for line in target_gene_path.read_text().splitlines() if line.strip()]
            first = lines[0].lower().split("\t")[0] if lines else ""
            if first in {"target_index", "gene", "gene_id", "target_gene", "target_genes", "symbol"}:
                lines = lines[1:]
            target_count = len(lines)
            if target_count != self.n_targets:
                raise ValueError(f"official target gene count {target_count} != n_targets {self.n_targets}")

        self.input = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[ResidualMLPBlock(hidden, dropout) for _ in range(depth)])
        self.context_norm = nn.LayerNorm(hidden)
        self.context_rank = nn.Linear(hidden, self.rank * self.n_classes)
        self.context_class_bias = nn.Linear(hidden, self.n_classes)

        self.target_factors = nn.Embedding(self.n_targets, self.rank)
        self.target_class_bias = nn.Embedding(self.n_targets, self.n_classes)
        self.target_gate = nn.Sequential(
            nn.LayerNorm(self.rank),
            nn.Linear(self.rank, self.rank),
            nn.GELU(),
            nn.Linear(self.rank, self.n_classes),
        )
        nn.init.normal_(self.target_factors.weight, mean=0.0, std=0.02)
        nn.init.zeros_(self.target_class_bias.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        context_rank = self.context_rank(z).view(x.shape[0], self.rank, self.n_classes)
        target_ids = torch.arange(self.n_targets, device=x.device)
        target_factors = self.target_factors(target_ids).to(dtype=x.dtype)
        logits = torch.einsum("brc,nr->bnc", context_rank, target_factors)
        target_bias = self.target_class_bias(target_ids).to(dtype=x.dtype)
        target_gate = self.target_gate(target_factors).to(dtype=x.dtype)
        context_bias = self.context_class_bias(z).unsqueeze(1)
        return logits + target_bias.unsqueeze(0) + 0.1 * target_gate.unsqueeze(0) + context_bias
