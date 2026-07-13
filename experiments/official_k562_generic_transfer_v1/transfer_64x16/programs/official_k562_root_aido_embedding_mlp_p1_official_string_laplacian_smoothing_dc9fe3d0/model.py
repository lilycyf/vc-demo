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
    if not path.exists():
        raise FileNotFoundError(f"official target-gene table is required: {path}")
    rows: list[tuple[int, str, str]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows.append((int(row["target_index"]), str(row.get("gene_id", "")), str(row.get("symbol", ""))))
    rows.sort(key=lambda item: item[0])
    if len(rows) != int(n_targets) or [r[0] for r in rows] != list(range(int(n_targets))):
        raise ValueError("target-gene table must match official contiguous target order")
    return rows


def _target_features(rows: list[tuple[int, str, str]], n_targets: int) -> torch.Tensor:
    features = torch.empty(n_targets, TARGET_FEATURE_DIM, dtype=torch.float32)
    denom = max(1, n_targets - 1)
    for index, gene_id, symbol in rows:
        digest = hashlib.sha256(f"{index}|{gene_id}|{symbol}|laplacian".encode("utf-8")).digest()
        position = float(index) / float(denom)
        vals = [position, math.sin(position * math.tau), math.cos(position * math.tau), min(len(symbol), 32) / 32.0]
        while len(vals) < TARGET_FEATURE_DIM:
            vals.append(float(digest[(len(vals) - 4) % len(digest)]) / 127.5 - 1.0)
        features[index] = torch.tensor(vals, dtype=torch.float32)
    return features


def _normalized_string_adjacency(target_path: Path, graph_path: Path, n_targets: int) -> tuple[torch.Tensor, dict[str, float]]:
    if not graph_path.exists():
        raise FileNotFoundError(f"official STRING graph artifact is required: {graph_path}")
    rows = _read_targets(target_path, n_targets)
    gene_to_index = {gene_id: idx for idx, gene_id, _ in rows}
    edge_weights: dict[tuple[int, int], float] = {}
    raw_edges = 0
    retained_edges = 0
    with graph_path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            raw_edges += 1
            g1, g2 = row["protein1"], row["protein2"]
            if g1 not in gene_to_index or g2 not in gene_to_index:
                continue
            i, j = gene_to_index[g1], gene_to_index[g2]
            if i == j:
                continue
            score = float(row.get("combined_score", 0.0)) / 1000.0
            if score <= 0:
                continue
            retained_edges += 1
            edge_weights[(i, j)] = max(edge_weights.get((i, j), 0.0), score)
            edge_weights[(j, i)] = max(edge_weights.get((j, i), 0.0), score)

    for i in range(n_targets):
        edge_weights[(i, i)] = max(edge_weights.get((i, i), 0.0), 1.0)
    degree = torch.zeros(n_targets, dtype=torch.float32)
    for (i, _), score in edge_weights.items():
        degree[i] += float(score)
    indices = []
    values = []
    for (i, j), score in edge_weights.items():
        indices.append([i, j])
        values.append(float(score) / float(degree[i].clamp_min(1e-6)))
    idx = torch.tensor(indices, dtype=torch.long).t().contiguous()
    vals = torch.tensor(values, dtype=torch.float32)
    adj = torch.sparse_coo_tensor(idx, vals, (n_targets, n_targets)).coalesce()
    covered = (degree > 1.00001).sum().item()
    stats = {"raw_edges": float(raw_edges), "retained_target_edges": float(retained_edges), "covered_targets": float(covered), "coverage_fraction": float(covered / max(1, n_targets))}
    return adj, stats


class ResidualBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden * 2, hidden), nn.Dropout(dropout))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Official K562 STRING Laplacian smoothing head.

    The head first predicts target logits from frozen AIDO features, then applies
    row-normalized smoothing over the real STRING target graph with self loops.
    Missing target genes retain self-loop-only behavior; no graph edges are made.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(48, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 160))
        self.smoothing_alpha = 0.18
        dropout = float(spec.dropout)
        rows = _read_targets(TARGET_GENE_TABLE, self.n_targets)
        self.register_buffer("target_features", _target_features(rows, self.n_targets), persistent=False)
        adj, stats = _normalized_string_adjacency(TARGET_GENE_TABLE, STRING_GRAPH, self.n_targets)
        self.register_buffer("string_adjacency", adj, persistent=False)
        self.graph_raw_edges = int(stats["raw_edges"])
        self.graph_retained_target_edges = int(stats["retained_target_edges"])
        self.graph_covered_targets = int(stats["covered_targets"])
        self.graph_coverage_fraction = float(stats["coverage_fraction"])

        self.context = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
            *[ResidualBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))], nn.LayerNorm(hidden)
        )
        self.context_rank_logits = nn.Linear(hidden, self.rank * self.n_classes)
        self.target_rank = nn.Sequential(nn.LayerNorm(TARGET_FEATURE_DIM), nn.Linear(TARGET_FEATURE_DIM, self.rank), nn.GELU(), nn.Linear(self.rank, self.rank))
        self.target_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context(x)
        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        rank_logits = self.context_rank_logits(z).view(x.shape[0], self.rank, self.n_classes)
        target_rank = torch.nn.functional.layer_norm(self.target_rank(target_features), (self.rank,))
        logits = torch.einsum("brc,nr->bnc", rank_logits, target_rank)
        logits = logits + self.target_offset(target_features).unsqueeze(0) + self.target_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
        adj = self.string_adjacency.to(device=x.device, dtype=x.dtype)
        flat = logits.permute(1, 0, 2).reshape(self.n_targets, -1)
        smooth = torch.sparse.mm(adj, flat).reshape(self.n_targets, x.shape[0], self.n_classes).permute(1, 0, 2)
        return (1.0 - self.smoothing_alpha) * logits + self.smoothing_alpha * smooth
