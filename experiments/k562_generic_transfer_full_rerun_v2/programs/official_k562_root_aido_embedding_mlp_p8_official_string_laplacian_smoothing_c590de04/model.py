from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
STRING_GRAPH_PATH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
BASE_TARGET_DIM = 32
GRAPH_FEATURE_DIM = 12
TARGET_FEATURE_DIM = BASE_TARGET_DIM + GRAPH_FEATURE_DIM


def _hash_values(key: str, count: int) -> list[float]:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    values: list[float] = []
    for i in range(count):
        values.append(float(digest[i % len(digest)]) / 127.5 - 1.0)
    return values


def _read_targets(path: Path, n_targets: int) -> list[tuple[int, str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"official target-gene table is required: {path}")
    rows: list[tuple[int, str, str]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows.append((int(row["target_index"]), str(row.get("gene_id", "")), str(row.get("symbol", ""))))
    rows.sort(key=lambda item: item[0])
    if len(rows) != int(n_targets):
        raise ValueError(f"target-gene rows {len(rows)} do not match n_targets {n_targets}")
    if [item[0] for item in rows] != list(range(int(n_targets))):
        raise ValueError("target-gene table must preserve contiguous official target_index order")
    return rows


def _base_features(rows: list[tuple[int, str, str]]) -> torch.Tensor:
    n_targets = len(rows)
    denom = max(1, n_targets - 1)
    out = torch.empty(n_targets, BASE_TARGET_DIM, dtype=torch.float32)
    for index, gene_id, symbol in rows:
        pos = float(index) / float(denom)
        vals = [
            pos,
            math.sin(pos * math.tau),
            math.cos(pos * math.tau),
            min(len(symbol), 32) / 32.0,
            1.0 if gene_id.startswith("ENSG") else 0.0,
        ]
        vals.extend(_hash_values(f"{index}|{gene_id}|{symbol}", BASE_TARGET_DIM - len(vals)))
        out[index] = torch.tensor(vals, dtype=torch.float32)
    return out


def _graph_features(rows: list[tuple[int, str, str]], graph_path: Path) -> torch.Tensor:
    if not graph_path.exists():
        raise FileNotFoundError(f"official STRING graph is required: {graph_path}")
    n_targets = len(rows)
    gene_to_index = {gene_id: index for index, gene_id, _ in rows}
    degree = torch.zeros(n_targets, dtype=torch.float32)
    weighted_degree = torch.zeros(n_targets, dtype=torch.float32)
    max_score = torch.zeros(n_targets, dtype=torch.float32)
    evidence = torch.zeros(n_targets, 4, dtype=torch.float32)
    neighbor_hash_sum = torch.zeros(n_targets, 4, dtype=torch.float32)
    edge_count = 0
    induced_edge_count = 0
    with graph_path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            edge_count += 1
            i = gene_to_index.get(str(row.get("protein1", "")))
            j = gene_to_index.get(str(row.get("protein2", "")))
            if i is None or j is None or i == j:
                continue
            induced_edge_count += 1
            score = float(row.get("combined_score", 0.0) or 0.0) / 1000.0
            degree[i] += 1.0
            degree[j] += 1.0
            weighted_degree[i] += score
            weighted_degree[j] += score
            max_score[i] = torch.maximum(max_score[i], torch.tensor(score))
            max_score[j] = torch.maximum(max_score[j], torch.tensor(score))
            exp = float(row.get("experimental", 0.0) or 0.0) / 1000.0
            db = float(row.get("database", 0.0) or 0.0) / 1000.0
            txt = float(row.get("textmining", 0.0) or 0.0) / 1000.0
            coexp = float(row.get("coexpression", 0.0) or 0.0) / 1000.0
            ev = torch.tensor([exp, db, txt, coexp], dtype=torch.float32) * max(score, 1e-6)
            evidence[i] += ev
            evidence[j] += ev
            hi = torch.tensor(_hash_values(rows[j][1] + rows[j][2], 4), dtype=torch.float32) * score
            hj = torch.tensor(_hash_values(rows[i][1] + rows[i][2], 4), dtype=torch.float32) * score
            neighbor_hash_sum[i] += hi
            neighbor_hash_sum[j] += hj
    denom = degree.clamp_min(1.0).unsqueeze(1)
    log_degree = torch.log1p(degree).unsqueeze(1) / 8.0
    mean_weight = (weighted_degree / degree.clamp_min(1.0)).unsqueeze(1)
    coverage = (degree > 0).float().unsqueeze(1)
    graph = torch.cat(
        [
            log_degree,
            mean_weight,
            max_score.unsqueeze(1),
            coverage,
            evidence / denom,
            neighbor_hash_sum / denom,
        ],
        dim=1,
    )
    if graph.shape[1] != GRAPH_FEATURE_DIM:
        raise AssertionError(f"graph feature dim {graph.shape[1]} != {GRAPH_FEATURE_DIM}")
    graph.edge_count = edge_count  # type: ignore[attr-defined]
    graph.induced_edge_count = induced_edge_count  # type: ignore[attr-defined]
    return graph



def _normalized_adjacency(rows: list[tuple[int, str, str]], graph_path: Path) -> torch.Tensor:
    if not graph_path.exists():
        raise FileNotFoundError(f"official STRING graph is required: {graph_path}")
    n_targets = len(rows)
    gene_to_index = {gene_id: index for index, gene_id, _ in rows}
    adjacency = torch.zeros(n_targets, n_targets, dtype=torch.float32)
    with graph_path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            i = gene_to_index.get(str(row.get("protein1", "")))
            j = gene_to_index.get(str(row.get("protein2", "")))
            if i is None or j is None or i == j:
                continue
            score = float(row.get("combined_score", 0.0) or 0.0) / 1000.0
            if score <= 0.0:
                continue
            adjacency[i, j] = max(float(adjacency[i, j]), score)
            adjacency[j, i] = max(float(adjacency[j, i]), score)
    adjacency.fill_diagonal_(1.0)
    degree = adjacency.sum(dim=1).clamp_min(1e-6)
    inv_sqrt = torch.rsqrt(degree)
    return inv_sqrt.unsqueeze(1) * adjacency * inv_sqrt.unsqueeze(0)

def _target_graph_features(n_targets: int) -> torch.Tensor:
    rows = _read_targets(TARGET_GENE_TABLE, n_targets)
    return torch.cat([_base_features(rows), _graph_features(rows, STRING_GRAPH_PATH)], dim=1)


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
    """STRING Laplacian-smoothed target head over official K562 targets.

    This node reads the source-backed STRING keep20 graph and official target-gene
    order, builds a symmetric normalized adjacency matrix, and applies a fixed
    Laplacian smoothing coefficient to target factors before producing logits.
    Genes absent from the induced graph retain self-loop features only; no edges
    or artifacts are fabricated.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(32, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 160))
        self.attention_heads = 4
        self.graph_k = 1
        self.smoothing_alpha = 0.18
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))

        self.input = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[ResidualContextBlock(hidden, dropout) for _ in range(depth)])
        self.context_norm = nn.LayerNorm(hidden)
        self.context_rank = nn.Linear(hidden, self.rank * self.n_classes)
        self.context_query = nn.Linear(hidden, self.attention_heads * self.rank)

        rows = _read_targets(TARGET_GENE_TABLE, self.n_targets)
        target_features = torch.cat([_base_features(rows), _graph_features(rows, STRING_GRAPH_PATH)], dim=1)
        normalized_adjacency = _normalized_adjacency(rows, STRING_GRAPH_PATH)
        self.register_buffer("target_features", target_features, persistent=False)
        self.register_buffer("normalized_adjacency", normalized_adjacency, persistent=False)
        self.target_key = nn.Sequential(nn.LayerNorm(TARGET_FEATURE_DIM), nn.Linear(TARGET_FEATURE_DIM, self.attention_heads * self.rank))
        self.target_factor = nn.Sequential(nn.LayerNorm(TARGET_FEATURE_DIM), nn.Linear(TARGET_FEATURE_DIM, self.rank), nn.GELU(), nn.Linear(self.rank, self.rank))
        self.target_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        rank_logits = self.context_rank(z).view(x.shape[0], self.rank, self.n_classes)
        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        target_factor = self.target_factor(target_features)
        adjacency = self.normalized_adjacency.to(device=x.device, dtype=x.dtype)
        smoothed_factor = torch.matmul(adjacency, target_factor)
        target_factor = (1.0 - self.smoothing_alpha) * target_factor + self.smoothing_alpha * smoothed_factor
        target_factor = torch.nn.functional.layer_norm(target_factor, (self.rank,))
        base_logits = torch.einsum("brc,nr->bnc", rank_logits, target_factor)

        query = self.context_query(z).view(x.shape[0], self.attention_heads, self.rank)
        key = self.target_key(target_features).view(self.n_targets, self.attention_heads, self.rank).permute(1, 0, 2)
        attn = torch.einsum("bhr,hnr->bhn", query, key) / math.sqrt(float(self.rank))
        attn = torch.softmax(attn, dim=-1).mean(dim=1).unsqueeze(-1)
        offsets = self.target_offset(target_features).unsqueeze(0)
        return base_logits + attn * offsets + self.bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
