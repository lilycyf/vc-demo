from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
STRING_GRAPH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
TARGET_FEATURE_DIM = 48


def _read_targets(path: Path, n_targets: int) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rows.append((int(row["target_index"]), str(row.get("gene_id", "")), str(row.get("symbol", ""))))
    rows.sort(key=lambda x: x[0])
    if len(rows) != n_targets or [r[0] for r in rows] != list(range(n_targets)):
        raise ValueError("official target order mismatch")
    return rows


def _target_features(rows: list[tuple[int, str, str]], n_targets: int) -> torch.Tensor:
    out = torch.empty(n_targets, TARGET_FEATURE_DIM, dtype=torch.float32)
    denom = max(1, n_targets - 1)
    for index, gene_id, symbol in rows:
        digest = hashlib.sha256(f"{index}|{gene_id}|{symbol}".encode()).digest()
        pos = index / denom
        vals = [pos, math.sin(pos * math.tau), math.cos(pos * math.tau), min(len(symbol), 32) / 32.0, 1.0 if gene_id.startswith("ENSG") else 0.0]
        while len(vals) < TARGET_FEATURE_DIM:
            vals.append(digest[(len(vals) - 5) % len(digest)] / 127.5 - 1.0)
        out[index] = torch.tensor(vals[:TARGET_FEATURE_DIM])
    return out


def _graph(rows: list[tuple[int, str, str]], n_targets: int) -> tuple[torch.Tensor, torch.Tensor, int]:
    if not STRING_GRAPH.exists():
        raise FileNotFoundError(STRING_GRAPH)
    gene_to_idx = {gene_id: index for index, gene_id, _ in rows}
    weights: dict[tuple[int, int], float] = {}
    with STRING_GRAPH.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            i = gene_to_idx.get(str(row.get("protein1", "")))
            j = gene_to_idx.get(str(row.get("protein2", "")))
            if i is None or j is None:
                continue
            score = float(row.get("combined_score", 0.0)) / 1000.0
            if score <= 0:
                continue
            weights[(i, j)] = max(weights.get((i, j), 0.0), score)
            weights[(j, i)] = max(weights.get((j, i), 0.0), score)
    graph_edges = len(weights)
    for i in range(n_targets):
        weights[(i, i)] = max(weights.get((i, i), 0.0), 1.0)
    sums: dict[int, float] = {}
    for (i, _), v in weights.items():
        sums[i] = sums.get(i, 0.0) + v
    pairs, vals = [], []
    for (i, j), v in weights.items():
        pairs.append((i, j))
        vals.append(v / max(sums[i], 1e-6))
    return torch.tensor(pairs, dtype=torch.long).t().contiguous(), torch.tensor(vals, dtype=torch.float32), graph_edges


class Block(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden * 2, hidden), nn.Dropout(dropout))
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Artifact-backed K562 multimodal mixture of dense, target, and STRING experts."""
    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(32, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        dropout = float(spec.dropout)
        self.encoder = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout), *[Block(hidden, dropout) for _ in range(max(1, int(spec.depth)))], nn.LayerNorm(hidden))
        self.dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.target_context = nn.Linear(hidden, self.rank * self.n_classes)
        self.graph_context = nn.Linear(hidden, self.rank * self.n_classes)
        self.expert_gate = nn.Sequential(nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, 3))
        rows = _read_targets(TARGET_GENE_TABLE, self.n_targets)
        self.register_buffer("target_features", _target_features(rows, self.n_targets), persistent=False)
        idx, val, graph_edge_count = _graph(rows, self.n_targets)
        self.register_buffer("graph_indices", idx, persistent=False)
        self.register_buffer("graph_values", val, persistent=False)
        self.graph_edge_count = int(graph_edge_count)
        self.target_proj = nn.Sequential(nn.LayerNorm(TARGET_FEATURE_DIM), nn.Linear(TARGET_FEATURE_DIM, self.rank), nn.GELU(), nn.Linear(self.rank, self.rank))
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, self.rank))
        nn.init.normal_(self.target_factors, mean=0.0, std=0.015)
        self.class_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
    def _propagate(self, target_rank: torch.Tensor) -> torch.Tensor:
        adj = torch.sparse_coo_tensor(self.graph_indices.to(target_rank.device), self.graph_values.to(device=target_rank.device, dtype=target_rank.dtype), (self.n_targets, self.n_targets), device=target_rank.device).coalesce()
        return torch.sparse.mm(adj, target_rank)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        dense = self.dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        tf = self.target_features.to(device=x.device, dtype=x.dtype)
        target_rank = torch.nn.functional.layer_norm(self.target_proj(tf) + self.target_factors.to(device=x.device, dtype=x.dtype), (self.rank,))
        graph_rank = torch.nn.functional.layer_norm(target_rank + self._propagate(target_rank), (self.rank,))
        target_ctx = self.target_context(z).view(x.shape[0], self.rank, self.n_classes)
        graph_ctx = self.graph_context(z).view(x.shape[0], self.rank, self.n_classes)
        target_logits = torch.einsum("brc,nr->bnc", target_ctx, target_rank)
        graph_logits = torch.einsum("brc,nr->bnc", graph_ctx, graph_rank)
        offset = self.class_offset(tf).unsqueeze(0)
        weights = torch.softmax(self.expert_gate(z), dim=-1).view(x.shape[0], 3, 1, 1)
        experts = torch.stack([dense, target_logits + offset, graph_logits + offset], dim=1)
        return (weights * experts).sum(dim=1)
