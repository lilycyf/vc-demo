from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import torch
from torch import nn


class ResidualBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden * 2, hidden), nn.Dropout(dropout))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


def _genes(path: Path, expected: int) -> list[str]:
    rows = [line for line in path.read_text().splitlines() if line.strip()]
    if rows and rows[0].split("\t")[0].lower() == "target_index":
        rows = rows[1:]
    genes = [r.split("\t")[1] for r in rows]
    if len(genes) != expected:
        raise ValueError(f"target gene count {len(genes)} != {expected}")
    return genes


def _graph_tensors(graph_path: Path, genes: list[str], k: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]:
    if not graph_path.exists():
        raise FileNotFoundError(f"STRING graph missing: {graph_path}")
    idx = {g: i for i, g in enumerate(genes)}
    rows: dict[int, list[tuple[float, int]]] = defaultdict(list)
    degree = torch.zeros(len(genes), 2, dtype=torch.float32)
    aligned = 0
    with graph_path.open() as f:
        header = f.readline().strip().split("\t")
        p1, p2, sc = header.index("protein1"), header.index("protein2"), header.index("combined_score")
        for line in f:
            if not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            a, b = idx.get(parts[p1]), idx.get(parts[p2])
            if a is None or b is None:
                continue
            score = float(parts[sc]) / 1000.0
            rows[a].append((score, b)); rows[b].append((score, a))
            degree[a, 0] += 1.0; degree[b, 0] += 1.0
            degree[a, 1] += score; degree[b, 1] += score
            aligned += 1
    if aligned <= 0:
        raise ValueError("no aligned STRING target edges; refusing fallback")
    degree[:, 0] = torch.log1p(degree[:, 0])
    degree[:, 1] = torch.log1p(degree[:, 1])
    degree = (degree - degree.mean(dim=0, keepdim=True)) / degree.std(dim=0, keepdim=True).clamp_min(1e-6)
    n = len(genes)
    nidx = torch.empty((n, k), dtype=torch.long)
    wts = torch.empty((n, k), dtype=torch.float32)
    for i in range(n):
        ranked = sorted(rows.get(i, []), reverse=True)[: max(0, k - 1)]
        pairs = [(1.0, i), *ranked]
        while len(pairs) < k:
            pairs.append((0.0, i))
        w = torch.tensor([max(s, 0.0) for s, _ in pairs[:k]], dtype=torch.float32)
        if float(w.sum()) <= 0: w[0] = 1.0
        nidx[i] = torch.tensor([j for _, j in pairs[:k]], dtype=torch.long)
        wts[i] = w / w.sum().clamp_min(1e-6)
    return nidx, wts, degree, aligned


class GeneratedModel(nn.Module):
    """Graph-conditioned target head using real STRING target neighborhoods."""

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(2, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(64, min(int(getattr(spec, "low_rank_dim", 128)), hidden, 192))
        self.k_neighbors = 16
        genes = _genes(Path("data/cell_lines/official_k562_cls/target_genes.tsv"), self.n_targets)
        nidx, wts, degree_features, _ = _graph_tensors(Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt"), genes, self.k_neighbors)
        self.register_buffer("neighbor_idx", nidx, persistent=False)
        self.register_buffer("neighbor_weight", wts, persistent=False)
        self.register_buffer("graph_features", degree_features, persistent=False)
        self.encoder = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout), *[ResidualBlock(hidden, dropout) for _ in range(depth)], nn.LayerNorm(hidden))
        self.context_rank = nn.Linear(hidden, self.rank * self.n_classes)
        self.target_base = nn.Parameter(torch.empty(self.n_targets, self.rank))
        self.graph_to_factor = nn.Sequential(nn.Linear(2, self.rank), nn.Tanh())
        self.direct = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.smooth_logit = nn.Parameter(torch.tensor(-1.3862944))
        nn.init.normal_(self.target_base, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        graph_feat = self.graph_features.to(device=x.device, dtype=z.dtype)
        target_factor = self.target_base.to(dtype=z.dtype) + self.graph_to_factor(graph_feat)
        rank_logits = self.context_rank(z).view(x.shape[0], self.rank, self.n_classes)
        factor_logits = torch.einsum("brc,nr->bnc", rank_logits, target_factor) + self.target_bias.unsqueeze(0)
        direct = self.direct(z).view(x.shape[0], self.n_targets, self.n_classes)
        base = 0.5 * direct + factor_logits
        idx = self.neighbor_idx.to(device=x.device)
        w = self.neighbor_weight.to(device=x.device, dtype=base.dtype)
        neighbor = (base[:, idx, :] * w.unsqueeze(0).unsqueeze(-1)).sum(dim=2)
        alpha = torch.sigmoid(self.smooth_logit).to(dtype=base.dtype)
        return base + alpha * (neighbor - base)
