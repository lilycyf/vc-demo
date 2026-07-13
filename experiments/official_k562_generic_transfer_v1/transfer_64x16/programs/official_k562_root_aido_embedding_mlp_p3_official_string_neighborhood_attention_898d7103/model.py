from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
STRING_GRAPH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
GRAPH_FEATURE_DIM = 56
HASH_DIMS = 24


def _hash_unit(key: str, dim: int = HASH_DIMS) -> torch.Tensor:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    vals = [float(digest[i % len(digest)]) / 127.5 - 1.0 for i in range(dim)]
    return torch.tensor(vals, dtype=torch.float32)


def _read_targets(path: Path, n_targets: int) -> list[tuple[int, str, str]]:
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
        raise ValueError("target-gene table must preserve contiguous official target_index order")
    return rows


def _string_graph_features(target_path: Path, graph_path: Path, n_targets: int) -> tuple[torch.Tensor, dict[str, float]]:
    if not graph_path.exists():
        raise FileNotFoundError(f"official STRING graph artifact is required: {graph_path}")
    rows = _read_targets(target_path, n_targets)
    gene_to_index = {gene_id: idx for idx, gene_id, _ in rows}
    symbol_by_index = {idx: symbol for idx, _, symbol in rows}

    degree = torch.zeros(n_targets, dtype=torch.float32)
    weighted_degree = torch.zeros(n_targets, dtype=torch.float32)
    evidence = torch.zeros(n_targets, 7, dtype=torch.float32)
    neighbor_hash = torch.zeros(n_targets, HASH_DIMS, dtype=torch.float32)
    top_score = torch.zeros(n_targets, dtype=torch.float32)
    edge_count = 0
    retained_edges = 0

    with graph_path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"protein1", "protein2", "combined_score"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"STRING graph missing required columns: {sorted(missing)}")
        ev_cols = [c for c in ["neighborhood", "fusion", "cooccurence", "coexpression", "experimental", "database", "textmining"] if c in (reader.fieldnames or [])]
        for row in reader:
            edge_count += 1
            g1 = row["protein1"]
            g2 = row["protein2"]
            if g1 not in gene_to_index or g2 not in gene_to_index:
                continue
            i = gene_to_index[g1]
            j = gene_to_index[g2]
            if i == j:
                continue
            score = float(row.get("combined_score", 0.0)) / 1000.0
            if score <= 0.0:
                continue
            retained_edges += 1
            for a, b in ((i, j), (j, i)):
                degree[a] += 1.0
                weighted_degree[a] += score
                top_score[a] = torch.maximum(top_score[a], torch.tensor(score))
                neighbor_hash[a] += score * _hash_unit(f"{rows[b][1]}|{symbol_by_index[b]}")
                for k, col in enumerate(ev_cols[:7]):
                    evidence[a, k] += float(row.get(col, 0.0) or 0.0) / 1000.0

    covered = degree > 0
    self_loop_only = ~covered
    safe_degree = degree.clamp_min(1.0)
    neighbor_hash = neighbor_hash / safe_degree.unsqueeze(1)
    evidence = evidence / safe_degree.unsqueeze(1)

    max_degree = degree.max().clamp_min(1.0)
    max_weighted = weighted_degree.max().clamp_min(1.0)
    pos = torch.arange(n_targets, dtype=torch.float32) / float(max(1, n_targets - 1))
    identity = torch.stack([
        pos,
        torch.sin(pos * math.tau),
        torch.cos(pos * math.tau),
        covered.float(),
        self_loop_only.float(),
        degree / max_degree,
        torch.log1p(degree) / torch.log1p(max_degree),
        weighted_degree / max_weighted,
        top_score,
    ], dim=1)
    symbol_hash = torch.stack([_hash_unit(f"{idx}|{gene_id}|{symbol}", dim=16) for idx, gene_id, symbol in rows])
    features = torch.cat([identity, evidence, neighbor_hash, symbol_hash], dim=1)
    if features.shape[1] != GRAPH_FEATURE_DIM:
        raise AssertionError(f"graph feature width changed: {features.shape[1]}")
    stats = {
        "raw_edges": float(edge_count),
        "retained_target_edges": float(retained_edges),
        "covered_targets": float(covered.sum().item()),
        "coverage_fraction": float(covered.float().mean().item()),
    }
    return features, stats


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
    """Official K562 STRING neighborhood attention head.

    This node reads the real STRING keep20 graph artifact and builds fixed target
    neighborhood priors for the official 6,640 target genes. Genes absent from
    the graph receive only an explicit self-loop/missing-neighborhood indicator;
    no synthetic graph edges are created.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(32, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 160))
        self.k_hops = 1
        self.attention_heads = 4
        dropout = float(spec.dropout)

        graph_features, stats = _string_graph_features(TARGET_GENE_TABLE, STRING_GRAPH, self.n_targets)
        self.register_buffer("graph_features", graph_features, persistent=False)
        self.graph_raw_edges = int(stats["raw_edges"])
        self.graph_retained_target_edges = int(stats["retained_target_edges"])
        self.graph_covered_targets = int(stats["covered_targets"])
        self.graph_coverage_fraction = float(stats["coverage_fraction"])

        self.context = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            *[ResidualBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))],
            nn.LayerNorm(hidden),
        )
        self.query = nn.Linear(hidden, self.attention_heads * self.rank)
        self.value = nn.Linear(hidden, self.rank * self.n_classes)
        self.graph_key = nn.Sequential(
            nn.LayerNorm(GRAPH_FEATURE_DIM),
            nn.Linear(GRAPH_FEATURE_DIM, self.attention_heads * self.rank),
            nn.GELU(),
            nn.Linear(self.attention_heads * self.rank, self.attention_heads * self.rank),
        )
        self.graph_value = nn.Sequential(
            nn.LayerNorm(GRAPH_FEATURE_DIM),
            nn.Linear(GRAPH_FEATURE_DIM, self.rank),
            nn.GELU(),
            nn.Linear(self.rank, self.rank),
        )
        self.graph_offset = nn.Linear(GRAPH_FEATURE_DIM, self.n_classes)
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.rank_scale = nn.Parameter(torch.tensor(1.0 / math.sqrt(float(self.rank))))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context(x)
        graph_features = self.graph_features.to(device=x.device, dtype=x.dtype)
        q = self.query(z).view(x.shape[0], self.attention_heads, self.rank)
        k = self.graph_key(graph_features).view(self.n_targets, self.attention_heads, self.rank)
        attn = torch.einsum("bhr,nhr->bnh", q, k) * self.rank_scale.to(device=x.device, dtype=x.dtype)
        attn = torch.sigmoid(attn).mean(dim=-1).unsqueeze(-1)

        context_value = self.value(z).view(x.shape[0], self.rank, self.n_classes)
        graph_value = self.graph_value(graph_features)
        logits = torch.einsum("brc,nr->bnc", context_value, graph_value)
        offsets = self.graph_offset(graph_features).unsqueeze(0)
        return logits * attn + offsets + self.target_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
