from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import torch
from torch import nn
import torch.nn.functional as F

TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
STRING_GRAPH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
TARGET_FEATURE_DIM = 32
DEFAULT_K = 16


def _load_targets(path: Path, n_targets: int) -> list[tuple[int, str, str]]:
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
    if [idx for idx, _, _ in rows] != list(range(int(n_targets))):
        raise ValueError("target-gene table must preserve contiguous official target_index order")
    return rows


def _target_features(rows: list[tuple[int, str, str]]) -> torch.Tensor:
    n_targets = len(rows)
    denom = max(1, n_targets - 1)
    feats = torch.zeros(n_targets, TARGET_FEATURE_DIM, dtype=torch.float32)
    for idx, gene_id, symbol in rows:
        pos = float(idx) / float(denom)
        vals = [
            pos,
            math.sin(math.tau * pos),
            math.cos(math.tau * pos),
            min(len(symbol), 32) / 32.0,
            1.0 if gene_id.startswith("ENSG") else 0.0,
        ]
        # Stable lexical features from the source-backed target table; no label use.
        seed = sum((i + 1) * ord(ch) for i, ch in enumerate(gene_id + symbol))
        while len(vals) < TARGET_FEATURE_DIM:
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            vals.append((seed / 0x3FFFFFFF) - 1.0)
        feats[idx] = torch.tensor(vals[:TARGET_FEATURE_DIM], dtype=torch.float32)
    return feats


def _load_string_neighbors(rows: list[tuple[int, str, str]], graph_path: Path, k: int) -> tuple[torch.Tensor, torch.Tensor, int]:
    if not graph_path.exists():
        raise FileNotFoundError(f"official STRING graph is required: {graph_path}")
    gene_to_idx = {gene_id: idx for idx, gene_id, _ in rows}
    adj: dict[int, list[tuple[float, int]]] = defaultdict(list)
    raw_edges = 0
    with graph_path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            g1 = row.get("protein1", "")
            g2 = row.get("protein2", "")
            if g1 not in gene_to_idx or g2 not in gene_to_idx:
                continue
            i = gene_to_idx[g1]
            j = gene_to_idx[g2]
            score = float(row.get("combined_score", 0.0)) / 1000.0
            if score <= 0.0:
                continue
            adj[i].append((score, j))
            adj[j].append((score, i))
            raw_edges += 1
    n_targets = len(rows)
    neighbors = torch.empty(n_targets, k, dtype=torch.long)
    weights = torch.zeros(n_targets, k, dtype=torch.float32)
    for i in range(n_targets):
        ranked = sorted(adj.get(i, []), key=lambda item: item[0], reverse=True)[: max(0, k - 1)]
        entries = [(1.0, i)] + ranked
        while len(entries) < k:
            entries.append((0.0, i))
        for slot, (score, j) in enumerate(entries[:k]):
            neighbors[i, slot] = j
            weights[i, slot] = score
    return neighbors, weights, raw_edges



class FeatureGroupDropout(nn.Module):
    def __init__(self, input_dim: int, group_count: int = 16, drop_prob: float = 0.06) -> None:
        super().__init__()
        self.input_dim = int(input_dim)
        self.group_count = max(1, min(int(group_count), self.input_dim))
        self.drop_prob = float(drop_prob)
        boundaries = torch.linspace(0, self.input_dim, self.group_count + 1, dtype=torch.long)
        group_ids = torch.empty(self.input_dim, dtype=torch.long)
        for group in range(self.group_count):
            group_ids[int(boundaries[group].item()):int(boundaries[group + 1].item())] = group
        self.register_buffer("group_ids", group_ids, persistent=False)
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if (not self.training) or self.drop_prob <= 0.0:
            return x
        keep = torch.rand((x.shape[0], self.group_count), device=x.device, dtype=x.dtype) > self.drop_prob
        mask = keep[:, self.group_ids.to(device=x.device)].to(dtype=x.dtype) / max(1e-6, 1.0 - self.drop_prob)
        return x * mask

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
    """Official K562 layerwise-LR recorded dense/graph head.

    Uses only the source-backed official STRING keep20 graph for target-gene
    neighborhoods. Missing target genes are represented by self-loops only.
    Perturbation context comes from the parent official AIDO+GNN input features. A dense target-logit branch preserves root-level capacity while graph attention contributes a STRING residual.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.k_neighbors = int(getattr(spec, "string_k", DEFAULT_K))
        self.attention_heads = 4
        self.rank = max(32, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        dropout = float(spec.dropout)

        rows = _load_targets(TARGET_GENE_TABLE, self.n_targets)
        feats = _target_features(rows)
        neighbors, weights, raw_edges = _load_string_neighbors(rows, STRING_GRAPH, self.k_neighbors)
        self.register_buffer("target_features", feats, persistent=False)
        self.register_buffer("neighbor_index", neighbors, persistent=False)
        self.register_buffer("neighbor_score", weights, persistent=False)
        self.graph_edge_count = int(raw_edges)

        self.feature_augmentation = FeatureGroupDropout(int(spec.input_dim), group_count=16, drop_prob=0.06)
        self.augmentation_name = "official_layerwise_lr_schedule"
        self.layerwise_lr_schedule = [
            {"name": "context_and_dense_head", "lr_scale": 1.00},
            {"name": "graph_target_prior", "lr_scale": 0.75},
            {"name": "target_bias_and_offsets", "lr_scale": 1.25},
        ]
        self.context = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            *[ResidualBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))],
            nn.LayerNorm(hidden),
        )
        self.dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.context_rank_logits = nn.Linear(hidden, self.rank * self.n_classes)
        self.context_gate = nn.Sequential(nn.Linear(hidden, self.rank), nn.Sigmoid())
        self.graph_residual_scale = nn.Parameter(torch.tensor(0.25))

        self.target_seed = nn.Parameter(torch.empty(self.n_targets, hidden))
        nn.init.normal_(self.target_seed, mean=0.0, std=0.02)
        self.target_feature_proj = nn.Sequential(
            nn.LayerNorm(TARGET_FEATURE_DIM),
            nn.Linear(TARGET_FEATURE_DIM, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
        )
        self.query = nn.Linear(hidden, hidden, bias=False)
        self.key = nn.Linear(hidden, hidden, bias=False)
        self.value = nn.Linear(hidden, hidden, bias=False)
        self.graph_out = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.rank), nn.GELU(), nn.Linear(self.rank, self.rank))
        self.target_class_offset = nn.Linear(hidden, self.n_classes)
        self.class_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.head_rank = self.rank

    def _target_rank(self, dtype: torch.dtype, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.target_features.to(device=device, dtype=dtype)
        seed = self.target_seed.to(device=device, dtype=dtype) + self.target_feature_proj(features)
        nbr = self.neighbor_index.to(device=device)
        score = self.neighbor_score.to(device=device, dtype=dtype)
        neigh = seed[nbr]
        q = self.query(seed).unsqueeze(1)
        k = self.key(neigh)
        v = self.value(neigh)
        attn_logits = (q * k).sum(-1) / math.sqrt(seed.shape[-1])
        attn_logits = attn_logits + torch.log(score.clamp_min(1e-6))
        attn = torch.softmax(attn_logits, dim=1)
        graph_context = (attn.unsqueeze(-1) * v).sum(dim=1)
        target_rank = self.graph_out(graph_context)
        target_rank = F.layer_norm(target_rank, (self.rank,))
        offsets = self.target_class_offset(graph_context)
        return target_rank, offsets

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x_aug = self.feature_augmentation(x)
        z = self.context(x_aug)
        rank_logits = self.context_rank_logits(z).view(x.shape[0], self.rank, self.n_classes)
        rank_logits = rank_logits * self.context_gate(z).view(x.shape[0], self.rank, 1)
        target_rank, offsets = self._target_rank(dtype=x.dtype, device=x.device)
        dense_logits = self.dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        graph_logits = torch.einsum("brc,nr->bnc", rank_logits, target_rank)
        return dense_logits + self.graph_residual_scale.tanh() * graph_logits + offsets.unsqueeze(0) + self.class_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
