from __future__ import annotations

import csv
from pathlib import Path

import torch
from torch import nn


GRAPH_PATH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
TARGET_PATH = Path("data/cell_lines/official_k562_cls/target_genes.tsv")


def _target_ids() -> list[str]:
    if not TARGET_PATH.exists():
        raise FileNotFoundError(f"official target gene order is required: {TARGET_PATH}")
    with TARGET_PATH.open(newline="") as f:
        return [row["gene_id"] for row in csv.DictReader(f, delimiter="\t")]


def _graph_condition_features(n_targets: int) -> torch.Tensor:
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(f"official STRING graph artifact is required: {GRAPH_PATH}")
    genes = _target_ids()
    if len(genes) != n_targets:
        raise ValueError(f"target gene count {len(genes)} != spec.n_targets={n_targets}")
    idx = {g: i for i, g in enumerate(genes)}
    degree = torch.ones(n_targets, dtype=torch.float32)
    weighted = torch.ones(n_targets, dtype=torch.float32)
    top = torch.zeros(n_targets, dtype=torch.float32)
    experimental = torch.zeros(n_targets, dtype=torch.float32)
    edges = 0
    with GRAPH_PATH.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            a = idx.get(row.get("protein1", ""))
            b = idx.get(row.get("protein2", ""))
            if a is None or b is None:
                continue
            score_raw = row.get("combined_score") or 0.0
            exp_raw = row.get("experimental") or 0.0
            score = max(0.0, min(float(score_raw) / 1000.0, 1.0))
            exp_score = max(0.0, min(float(exp_raw) / 1000.0, 1.0))
            for j in (a, b):
                degree[j] += 1.0
                weighted[j] += score
                top[j] = max(top[j], score)
                experimental[j] = max(experimental[j], exp_score)
            edges += 1
    if edges == 0:
        raise ValueError("official STRING graph produced no target-aligned edges; strict fallback forbidden")
    log_degree = torch.log1p(degree)
    log_degree = log_degree / log_degree.max().clamp_min(1.0)
    mean_score = weighted / degree.clamp_min(1.0)
    covered = (degree > 1.0).float()
    return torch.stack([log_degree, mean_score, top, experimental, covered], dim=1)


class GeneratedModel(nn.Module):
    """Target graph-conditioned classifier head using the real official STRING graph."""

    def __init__(self, spec) -> None:
        super().__init__()
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 128))
        graph_features = _graph_condition_features(self.n_targets)
        self.register_buffer("graph_condition_features", graph_features, persistent=False)
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.context = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden), nn.GELU())
        self.graph_encoder = nn.Sequential(nn.LayerNorm(5), nn.Linear(5, hidden), nn.GELU(), nn.Linear(hidden, hidden))
        self.context_rank = nn.Linear(hidden, rank * self.n_classes)
        self.graph_rank = nn.Linear(hidden, rank)
        self.direct_graph_head = nn.Linear(hidden, self.n_classes)
        self.coverage_gate = nn.Sequential(nn.Linear(hidden, 1), nn.Sigmoid())
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context(self.encoder(x))
        graph_features = self.graph_condition_features.to(device=x.device, dtype=x.dtype)
        target_graph = self.graph_encoder(graph_features)
        context_rank = self.context_rank(z).view(x.shape[0], -1, self.n_classes)
        graph_rank = self.graph_rank(target_graph)
        bilinear = torch.einsum("brc,nr->bnc", context_rank, graph_rank)
        graph_prior = self.direct_graph_head(target_graph).unsqueeze(0)
        gate = self.coverage_gate(target_graph).unsqueeze(0)
        return bilinear * gate + graph_prior * (1.0 - gate) + self.bias.unsqueeze(0)
