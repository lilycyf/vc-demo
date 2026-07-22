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


def _read_official_targets(path: Path, n_targets: int) -> list[tuple[int, str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"official target-gene table is required: {path}")
    rows: list[tuple[int, str, str]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows.append((int(row["target_index"]), str(row.get("gene_id", "")), str(row.get("symbol", ""))))
    if len(rows) != int(n_targets):
        raise ValueError(f"target-gene rows {len(rows)} do not match n_targets {n_targets}")
    rows.sort(key=lambda item: item[0])
    if [item[0] for item in rows] != list(range(int(n_targets))):
        raise ValueError("target-gene table must contain a contiguous official target_index order")
    return rows


def _target_gene_features(rows: list[tuple[int, str, str]], n_targets: int) -> torch.Tensor:
    features = torch.empty(int(n_targets), TARGET_FEATURE_DIM, dtype=torch.float32)
    denom = max(1, int(n_targets) - 1)
    for index, gene_id, symbol in rows:
        key = f"{index}|{gene_id}|{symbol}".encode("utf-8")
        digest = hashlib.sha256(key).digest()
        vals = []
        position = float(index) / float(denom)
        vals.extend([position, math.sin(position * math.tau), math.cos(position * math.tau)])
        vals.append(min(len(symbol), 32) / 32.0)
        vals.append(1.0 if gene_id.startswith("ENSG") else 0.0)
        while len(vals) < TARGET_FEATURE_DIM:
            byte = digest[(len(vals) - 5) % len(digest)]
            vals.append((float(byte) / 127.5) - 1.0)
        features[index] = torch.tensor(vals[:TARGET_FEATURE_DIM], dtype=torch.float32)
    return features


def _string_sparse_adjacency(rows: list[tuple[int, str, str]], n_targets: int) -> tuple[torch.Tensor, torch.Tensor, int]:
    if not STRING_GRAPH.exists():
        raise FileNotFoundError(f"official STRING graph is required: {STRING_GRAPH}")
    gene_to_index = {gene_id: index for index, gene_id, _symbol in rows}
    weights: dict[tuple[int, int], float] = {}
    with STRING_GRAPH.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            i = gene_to_index.get(str(row.get("protein1", "")))
            j = gene_to_index.get(str(row.get("protein2", "")))
            if i is None or j is None:
                continue
            score = float(row.get("combined_score", 0.0)) / 1000.0
            if score <= 0:
                continue
            weights[(i, j)] = max(weights.get((i, j), 0.0), score)
            weights[(j, i)] = max(weights.get((j, i), 0.0), score)
    for i in range(int(n_targets)):
        weights[(i, i)] = max(weights.get((i, i), 0.0), 1.0)
    row_sums: dict[int, float] = {}
    for (i, _j), value in weights.items():
        row_sums[i] = row_sums.get(i, 0.0) + value
    indices = []
    values = []
    for (i, j), value in weights.items():
        indices.append((i, j))
        values.append(value / max(row_sums.get(i, 1.0), 1e-6))
    idx = torch.tensor(indices, dtype=torch.long).t().contiguous()
    val = torch.tensor(values, dtype=torch.float32)
    return idx, val, len(weights) - int(n_targets)


class ResidualContextBlock(nn.Module):
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
    """Parent-preserving K562 STRING neighborhood attention residual."""

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(32, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        dropout = float(spec.dropout)
        self.k_hops = 1
        self.attention_heads = 4

        self.input = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.blocks = nn.Sequential(*[ResidualContextBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))])
        self.context_norm = nn.LayerNorm(hidden)
        self.parent_dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.context_rank_logits = nn.Linear(hidden, self.rank * self.n_classes)
        self.graph_gate = nn.Sequential(nn.Linear(hidden, self.rank), nn.Sigmoid())

        rows = _read_official_targets(TARGET_GENE_TABLE, self.n_targets)
        self.register_buffer("target_features", _target_gene_features(rows, self.n_targets), persistent=False)
        idx, val, graph_edge_count = _string_sparse_adjacency(rows, self.n_targets)
        self.register_buffer("graph_indices", idx, persistent=False)
        self.register_buffer("graph_values", val, persistent=False)
        self.graph_edge_count = int(graph_edge_count)

        self.target_projection = nn.Sequential(nn.LayerNorm(TARGET_FEATURE_DIM), nn.Linear(TARGET_FEATURE_DIM, self.rank), nn.GELU(), nn.Linear(self.rank, self.rank))
        self.learned_target_factors = nn.Parameter(torch.empty(self.n_targets, self.rank))
        nn.init.normal_(self.learned_target_factors, mean=0.0, std=0.015)
        self.target_class_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.residual_scale = nn.Parameter(torch.tensor(0.1, dtype=torch.float32))

    def _graph_propagate(self, target_rank: torch.Tensor) -> torch.Tensor:
        adj = torch.sparse_coo_tensor(
            self.graph_indices.to(target_rank.device),
            self.graph_values.to(device=target_rank.device, dtype=target_rank.dtype),
            (self.n_targets, self.n_targets),
            device=target_rank.device,
        ).coalesce()
        return torch.sparse.mm(adj, target_rank)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        dense_logits = self.parent_dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        rank_logits = self.context_rank_logits(z).view(x.shape[0], self.rank, self.n_classes)
        rank_logits = rank_logits * self.graph_gate(z).view(x.shape[0], self.rank, 1)

        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        base_target_rank = self.target_projection(target_features) + self.learned_target_factors.to(device=x.device, dtype=x.dtype)
        graph_target_rank = self._graph_propagate(base_target_rank)
        target_rank = torch.nn.functional.layer_norm(base_target_rank + graph_target_rank, (self.rank,))
        graph_logits = torch.einsum("brc,nr->bnc", rank_logits, target_rank)
        offsets = self.target_class_offset(target_features).unsqueeze(0)
        return dense_logits + self.residual_scale.to(device=x.device, dtype=x.dtype) * graph_logits + offsets
