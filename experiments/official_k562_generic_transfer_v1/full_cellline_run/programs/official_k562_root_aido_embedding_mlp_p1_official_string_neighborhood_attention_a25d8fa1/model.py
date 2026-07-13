from __future__ import annotations

from collections import defaultdict
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


def _read_target_gene_ids(path: Path, expected: int) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"official target gene order file is missing: {path}")
    genes: list[str] = []
    for i, line in enumerate(path.read_text().splitlines()):
        if not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        if i == 0 and parts[0].lower() == "target_index":
            continue
        if len(parts) < 2:
            raise ValueError(f"malformed target gene row in {path}: {line!r}")
        genes.append(parts[1])
    if len(genes) != expected:
        raise ValueError(f"target gene count {len(genes)} != expected n_targets {expected}")
    return genes


def _build_string_neighbors(graph_path: Path, target_genes: list[str], k: int) -> tuple[torch.Tensor, torch.Tensor, int]:
    if not graph_path.exists():
        raise FileNotFoundError(f"official STRING graph artifact is missing: {graph_path}")
    index = {gene: i for i, gene in enumerate(target_genes)}
    rows: dict[int, list[tuple[float, int]]] = defaultdict(list)
    raw_edges = 0
    with graph_path.open() as f:
        header = f.readline().strip().split("\t")
        try:
            p1_idx = header.index("protein1")
            p2_idx = header.index("protein2")
            score_idx = header.index("combined_score")
        except ValueError as exc:
            raise ValueError(f"STRING graph must contain protein1/protein2/combined_score columns: {header}") from exc
        for line in f:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(p1_idx, p2_idx, score_idx):
                continue
            a = index.get(parts[p1_idx])
            b = index.get(parts[p2_idx])
            if a is None or b is None:
                continue
            score = float(parts[score_idx]) / 1000.0
            rows[a].append((score, b))
            rows[b].append((score, a))
            raw_edges += 1
    n = len(target_genes)
    neighbor_idx = torch.empty((n, k), dtype=torch.long)
    neighbor_weight = torch.empty((n, k), dtype=torch.float32)
    for i in range(n):
        ranked = sorted(rows.get(i, []), reverse=True)[: max(0, k - 1)]
        pairs = [(1.0, i), *ranked]
        while len(pairs) < k:
            pairs.append((0.0, i))
        weights = torch.tensor([max(0.0, s) for s, _ in pairs[:k]], dtype=torch.float32)
        if float(weights.sum()) <= 0.0:
            weights[0] = 1.0
        weights = weights / weights.sum().clamp_min(1e-6)
        neighbor_idx[i] = torch.tensor([j for _, j in pairs[:k]], dtype=torch.long)
        neighbor_weight[i] = weights
    return neighbor_idx, neighbor_weight, raw_edges


class GeneratedModel(nn.Module):
    """STRING neighborhood attention over the real official K562 graph artifact."""

    def __init__(self, spec) -> None:
        super().__init__()
        input_dim = int(spec.input_dim)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.k_neighbors = 12
        self.attention_heads = 1

        target_genes = _read_target_gene_ids(Path("data/cell_lines/official_k562_cls/target_genes.tsv"), self.n_targets)
        neighbor_idx, neighbor_weight, raw_edges = _build_string_neighbors(
            Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt"),
            target_genes,
            self.k_neighbors,
        )
        if raw_edges <= 0:
            raise ValueError("official STRING graph contains no target-target edges after alignment; refusing fallback")
        self.register_buffer("neighbor_idx", neighbor_idx, persistent=False)
        self.register_buffer("neighbor_weight", neighbor_weight, persistent=False)

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            *[ResidualBlock(hidden, dropout) for _ in range(depth)],
            nn.LayerNorm(hidden),
        )
        self.base_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.graph_mix = nn.Sequential(nn.Linear(hidden, self.n_classes), nn.Sigmoid())
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        base = self.base_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        idx = self.neighbor_idx.to(device=x.device)
        weights = self.neighbor_weight.to(device=x.device, dtype=base.dtype)
        gathered = base[:, idx, :]
        neighborhood = (gathered * weights.unsqueeze(0).unsqueeze(-1)).sum(dim=2)
        mix = self.graph_mix(z).view(x.shape[0], 1, self.n_classes)
        return base * (1.0 - mix) + neighborhood * mix + self.target_bias.unsqueeze(0)
