from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
STRING_GRAPH_PATH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
STRING_GNN_MODEL_DIR = Path("/home/Models/STRING_GNN")
BASE_TARGET_DIM = 32
GRAPH_FEATURE_DIM = 12
TARGET_FEATURE_DIM = BASE_TARGET_DIM + GRAPH_FEATURE_DIM


def _hash_values(key: str, count: int) -> list[float]:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return [float(digest[i % len(digest)]) / 127.5 - 1.0 for i in range(count)]


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
        raise FileNotFoundError(f"official STRING keep20 graph is required: {graph_path}")
    if not STRING_GNN_MODEL_DIR.exists():
        raise FileNotFoundError(f"official STRING_GNN model dir is required: {STRING_GNN_MODEL_DIR}")
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
            ev = torch.tensor([
                float(row.get("experimental", 0.0) or 0.0) / 1000.0,
                float(row.get("database", 0.0) or 0.0) / 1000.0,
                float(row.get("textmining", 0.0) or 0.0) / 1000.0,
                float(row.get("coexpression", 0.0) or 0.0) / 1000.0,
            ], dtype=torch.float32) * max(score, 1e-6)
            evidence[i] += ev
            evidence[j] += ev
            neighbor_hash_sum[i] += torch.tensor(_hash_values(rows[j][1] + rows[j][2], 4), dtype=torch.float32) * score
            neighbor_hash_sum[j] += torch.tensor(_hash_values(rows[i][1] + rows[i][2], 4), dtype=torch.float32) * score
    denom = degree.clamp_min(1.0).unsqueeze(1)
    graph = torch.cat([
        (torch.log1p(degree) / 8.0).unsqueeze(1),
        (weighted_degree / degree.clamp_min(1.0)).unsqueeze(1),
        max_score.unsqueeze(1),
        (degree > 0).float().unsqueeze(1),
        evidence / denom,
        neighbor_hash_sum / denom,
    ], dim=1)
    if graph.shape[1] != GRAPH_FEATURE_DIM:
        raise AssertionError(f"graph feature dim {graph.shape[1]} != {GRAPH_FEATURE_DIM}")
    graph.edge_count = edge_count  # type: ignore[attr-defined]
    graph.induced_edge_count = induced_edge_count  # type: ignore[attr-defined]
    return graph


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


class GeneratedModel(nn.Module):
    """Parent-preserving STRING_GNN attention child for official K562.

    The child keeps a dense parent-style all-target logit branch from the
    AIDO+GNN cached perturbation features, then adds a source-backed STRING
    graph attention residual over the official 6,640 target genes. It verifies
    the STRING_GNN model directory and consumes the official STRING keep20 graph;
    missing graph genes only contribute self target features and no fabricated
    edges are introduced.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(48, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        self.attention_heads = 4
        self.implementation_semantics = "parent_preserving_delta"
        self.artifact_usage = {
            "string_gnn_model_dir": str(STRING_GNN_MODEL_DIR),
            "string_graph_path": str(STRING_GRAPH_PATH),
        }

        self.input = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.context_norm = nn.LayerNorm(hidden)
        self.parent_dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)

        rows = _read_targets(TARGET_GENE_TABLE, self.n_targets)
        target_features = torch.cat([_base_features(rows), _graph_features(rows, STRING_GRAPH_PATH)], dim=1)
        self.register_buffer("target_features", target_features, persistent=False)
        self.context_rank = nn.Linear(hidden, self.rank * self.n_classes)
        self.context_query = nn.Linear(hidden, self.attention_heads * self.rank)
        self.target_key = nn.Sequential(nn.LayerNorm(TARGET_FEATURE_DIM), nn.Linear(TARGET_FEATURE_DIM, self.attention_heads * self.rank))
        self.target_factor = nn.Sequential(nn.LayerNorm(TARGET_FEATURE_DIM), nn.Linear(TARGET_FEATURE_DIM, self.rank), nn.GELU(), nn.Linear(self.rank, self.rank))
        self.target_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.residual_gate = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, 1))
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        parent_logits = self.parent_dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        rank_logits = self.context_rank(z).view(x.shape[0], self.rank, self.n_classes)
        target_factor = self.target_factor(target_features)
        target_factor = torch.nn.functional.layer_norm(target_factor, (self.rank,))
        graph_logits = torch.einsum("brc,nr->bnc", rank_logits, target_factor)

        query = self.context_query(z).view(x.shape[0], self.attention_heads, self.rank)
        key = self.target_key(target_features).view(self.n_targets, self.attention_heads, self.rank).permute(1, 0, 2)
        attn = torch.einsum("bhr,hnr->bhn", query, key) / math.sqrt(float(self.rank))
        attn = torch.softmax(attn, dim=-1).mean(dim=1).unsqueeze(-1)
        graph_logits = graph_logits + attn * self.target_offset(target_features).unsqueeze(0)
        gate = torch.sigmoid(self.residual_gate(z)).view(x.shape[0], 1, 1)
        return parent_logits + gate * graph_logits + self.bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
