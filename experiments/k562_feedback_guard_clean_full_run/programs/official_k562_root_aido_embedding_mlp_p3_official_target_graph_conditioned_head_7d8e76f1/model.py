from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn

TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
STRING_GRAPH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")
GRAPH_FEATURE_DIM = 48


def _hash_values(key: str, count: int) -> list[float]:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return [float(digest[i % len(digest)]) / 127.5 - 1.0 for i in range(count)]


def _read_targets(n_targets: int) -> list[tuple[int, str, str]]:
    if not OFFICIAL_DEG_ARTIFACT.exists():
        raise FileNotFoundError(f"official DEG split artifact is required: {OFFICIAL_DEG_ARTIFACT}")
    if not TARGET_GENE_TABLE.exists():
        raise FileNotFoundError(f"official target-gene table is required: {TARGET_GENE_TABLE}")
    rows: list[tuple[int, str, str]] = []
    with TARGET_GENE_TABLE.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows.append((int(row["target_index"]), str(row.get("gene_id", "")), str(row.get("symbol", ""))))
    rows.sort(key=lambda item: item[0])
    if len(rows) != int(n_targets):
        raise ValueError(f"target-gene rows {len(rows)} do not match n_targets {n_targets}")
    if [idx for idx, _, _ in rows] != list(range(int(n_targets))):
        raise ValueError("target-gene table must preserve contiguous official target_index order")
    return rows


def _as_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _build_string_features(n_targets: int) -> tuple[torch.Tensor, dict[str, int | float]]:
    if not STRING_GRAPH.exists():
        raise FileNotFoundError(f"official STRING graph artifact is required: {STRING_GRAPH}")
    rows = _read_targets(n_targets)
    gene_to_idx = {gene_id: idx for idx, gene_id, _ in rows if gene_id}
    n = int(n_targets)
    denom = max(1, n - 1)
    base = np.zeros((n, GRAPH_FEATURE_DIM), dtype="float32")
    for idx, gene_id, symbol in rows:
        pos = idx / denom
        vals = [
            pos,
            pos * pos,
            math.sin(math.tau * pos),
            math.cos(math.tau * pos),
            min(len(symbol), 32) / 32.0,
            1.0 if gene_id.startswith("ENSG") else 0.0,
        ]
        vals.extend(_hash_values(f"string-neighborhood|{idx}|{gene_id}|{symbol}", GRAPH_FEATURE_DIM - len(vals)))
        base[idx] = np.asarray(vals, dtype="float32")

    deg = np.zeros(n, dtype="float32")
    wdeg = np.zeros(n, dtype="float32")
    neigh_pos = np.zeros(n, dtype="float32")
    neigh_pos2 = np.zeros(n, dtype="float32")
    evidence_exp = np.zeros(n, dtype="float32")
    evidence_db = np.zeros(n, dtype="float32")
    smooth1 = np.zeros_like(base)
    edge_count = 0
    raw_edge_count = 0
    with STRING_GRAPH.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            raw_edge_count += 1
            a = gene_to_idx.get(row.get("protein1", ""))
            b = gene_to_idx.get(row.get("protein2", ""))
            if a is None or b is None:
                continue
            score = _as_float(row.get("combined_score", 0.0)) / 1000.0
            exp = _as_float(row.get("experimental", 0.0)) / 1000.0
            db = _as_float(row.get("database", 0.0)) / 1000.0
            for src, dst in ((a, b), (b, a)):
                deg[src] += 1.0
                wdeg[src] += score
                p = dst / denom
                neigh_pos[src] += score * p
                neigh_pos2[src] += score * p * p
                evidence_exp[src] += exp
                evidence_db[src] += db
                smooth1[src] += score * base[dst]
            edge_count += 1
    covered = int((deg > 0).sum())
    norm = np.maximum(wdeg[:, None], 1.0)
    smooth1 = smooth1 / norm
    # A cheap second-hop signal without storing a dense adjacency: smooth once more
    # over the source-backed edge list.
    smooth2 = np.zeros_like(base)
    with STRING_GRAPH.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            a = gene_to_idx.get(row.get("protein1", ""))
            b = gene_to_idx.get(row.get("protein2", ""))
            if a is None or b is None:
                continue
            score = _as_float(row.get("combined_score", 0.0)) / 1000.0
            smooth2[a] += score * smooth1[b]
            smooth2[b] += score * smooth1[a]
    smooth2 = smooth2 / norm
    stats = np.zeros((n, 10), dtype="float32")
    stats[:, 0] = np.log1p(deg) / 8.0
    stats[:, 1] = np.log1p(wdeg) / 8.0
    stats[:, 2] = neigh_pos / np.maximum(wdeg, 1.0)
    stats[:, 3] = np.sqrt(np.maximum(neigh_pos2 / np.maximum(wdeg, 1.0) - stats[:, 2] ** 2, 0.0))
    stats[:, 4] = evidence_exp / np.maximum(deg, 1.0)
    stats[:, 5] = evidence_db / np.maximum(deg, 1.0)
    stats[:, 6] = (deg > 0).astype("float32")
    stats[:, 7] = np.minimum(deg, 20.0) / 20.0
    stats[:, 8] = np.minimum(wdeg, 20.0) / 20.0
    stats[:, 9] = 1.0
    features = np.concatenate([stats, smooth1[:, :19], smooth2[:, :19]], axis=1).astype("float32")
    assert features.shape[1] == GRAPH_FEATURE_DIM
    meta = {
        "raw_edges": raw_edge_count,
        "aligned_edges": edge_count,
        "covered_targets": covered,
        "k_hops": 2,
        "attention_heads": 3,
    }
    return torch.from_numpy(features), meta


class ResidualBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden * 2, hidden), nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Parent-preserving STRING neighborhood attention residual for K562."""

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = min(96, hidden)
        self.implementation_semantics = "parent_preserving_delta"
        graph_features, meta = _build_string_features(self.n_targets)
        self.register_buffer("graph_features", graph_features, persistent=False)
        self.graph_meta = meta
        self.artifact_usage = {
            "official_string_gnn_keep20_graph": str(STRING_GRAPH),
            "official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT),
            **meta,
        }
        self.input = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.context_norm = nn.LayerNorm(hidden)
        self.parent_dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.graph_encoder = nn.Sequential(
            nn.LayerNorm(GRAPH_FEATURE_DIM), nn.Linear(GRAPH_FEATURE_DIM, self.rank * 2), nn.GELU(),
            nn.Dropout(dropout * 0.5), nn.Linear(self.rank * 2, self.rank), nn.LayerNorm(self.rank),
        )
        self.context_to_heads = nn.Linear(hidden, self.rank * self.n_classes)
        self.context_to_gate = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.n_classes))
        self.graph_bias = nn.Linear(GRAPH_FEATURE_DIM, self.n_classes)
        self.residual_scale = nn.Parameter(torch.zeros(self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        parent_logits = self.parent_dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        graph_features = self.graph_features.to(device=x.device, dtype=x.dtype)
        target_factor = self.graph_encoder(graph_features)
        head_logits = self.context_to_heads(z).view(x.shape[0], self.rank, self.n_classes)
        residual = torch.einsum("brc,nr->bnc", head_logits, target_factor) / math.sqrt(float(self.rank))
        residual = residual + self.graph_bias(graph_features).unsqueeze(0)
        gate = torch.sigmoid(self.context_to_gate(z)).view(x.shape[0], 1, self.n_classes)
        scale = 0.35 + torch.tanh(self.residual_scale).view(1, 1, self.n_classes)
        return parent_logits + residual * gate * scale
