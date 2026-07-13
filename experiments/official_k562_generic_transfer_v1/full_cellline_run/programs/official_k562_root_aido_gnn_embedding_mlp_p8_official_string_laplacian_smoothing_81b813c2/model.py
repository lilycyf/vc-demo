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


def _target_gene_ids(path: Path, expected: int) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"official target gene order file is missing: {path}")
    genes = []
    for i, line in enumerate(path.read_text().splitlines()):
        if not line.strip():
            continue
        parts = line.split("\t")
        if i == 0 and parts[0].lower() == "target_index":
            continue
        genes.append(parts[1])
    if len(genes) != expected:
        raise ValueError(f"target gene count {len(genes)} != expected {expected}")
    return genes


def _normalized_neighbors(graph_path: Path, genes: list[str], k: int) -> tuple[torch.Tensor, torch.Tensor, int]:
    if not graph_path.exists():
        raise FileNotFoundError(f"official STRING graph artifact is missing: {graph_path}")
    idx = {g: i for i, g in enumerate(genes)}
    rows: dict[int, list[tuple[float, int]]] = defaultdict(list)
    aligned_edges = 0
    with graph_path.open() as f:
        header = f.readline().strip().split("\t")
        p1 = header.index("protein1")
        p2 = header.index("protein2")
        score_col = header.index("combined_score")
        for line in f:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            a = idx.get(parts[p1])
            b = idx.get(parts[p2])
            if a is None or b is None:
                continue
            score = float(parts[score_col]) / 1000.0
            rows[a].append((score, b))
            rows[b].append((score, a))
            aligned_edges += 1
    if aligned_edges == 0:
        raise ValueError("no aligned target-target STRING edges; refusing fallback")
    n = len(genes)
    neighbor_idx = torch.empty((n, k), dtype=torch.long)
    weights = torch.empty((n, k), dtype=torch.float32)
    for i in range(n):
        ranked = sorted(rows.get(i, []), reverse=True)[:k]
        if not ranked:
            ranked = [(1.0, i)]
        while len(ranked) < k:
            ranked.append((0.0, i))
        w = torch.tensor([max(s, 0.0) for s, _ in ranked[:k]], dtype=torch.float32)
        if float(w.sum()) <= 0.0:
            w[0] = 1.0
        neighbor_idx[i] = torch.tensor([j for _, j in ranked[:k]], dtype=torch.long)
        weights[i] = w / w.sum().clamp_min(1e-6)
    return neighbor_idx, weights, aligned_edges


class GeneratedModel(nn.Module):
    """STRING Laplacian smoothing over source-backed K562 target graph."""

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.k_neighbors = 20
        genes = _target_gene_ids(Path("data/cell_lines/official_k562_cls/target_genes.tsv"), self.n_targets)
        neighbor_idx, weights, _ = _normalized_neighbors(
            Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt"), genes, self.k_neighbors
        )
        self.register_buffer("neighbor_idx", neighbor_idx, persistent=False)
        self.register_buffer("neighbor_weight", weights, persistent=False)
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            *[ResidualBlock(hidden, dropout) for _ in range(depth)],
            nn.LayerNorm(hidden),
        )
        self.base_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.alpha_logit = nn.Parameter(torch.tensor(-1.3862944))  # sigmoid ~= 0.2
        self.target_residual = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        base = self.base_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        idx = self.neighbor_idx.to(device=x.device)
        w = self.neighbor_weight.to(device=x.device, dtype=base.dtype)
        neighbor_mean = (base[:, idx, :] * w.unsqueeze(0).unsqueeze(-1)).sum(dim=2)
        alpha = torch.sigmoid(self.alpha_logit).to(dtype=base.dtype)
        smoothed = base + alpha * (neighbor_mean - base)
        return smoothed + self.target_residual.unsqueeze(0)
