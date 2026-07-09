from __future__ import annotations

import csv
from pathlib import Path

import torch
from torch import nn


GRAPH_PATH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
TARGET_PATH = Path("data/cell_lines/official_k562_cls/target_genes.tsv")


def _load_target_gene_ids(path: Path = TARGET_PATH) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"official K562 target gene order file is required: {path}")
    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        genes = [row["gene_id"] for row in reader]
    if not genes:
        raise ValueError(f"no target genes found in {path}")
    return genes


def _load_string_target_features(n_targets: int) -> torch.Tensor:
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(f"official STRING graph artifact is required: {GRAPH_PATH}")
    genes = _load_target_gene_ids()
    if len(genes) != n_targets:
        raise ValueError(f"target gene count {len(genes)} does not match spec.n_targets={n_targets}")
    index = {gene: i for i, gene in enumerate(genes)}
    degree = torch.ones(n_targets, dtype=torch.float32)  # self-loop support for graph-missing targets
    weighted_degree = torch.ones(n_targets, dtype=torch.float32)
    max_score = torch.zeros(n_targets, dtype=torch.float32)
    edge_count = 0
    with GRAPH_PATH.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            a = index.get(row.get("protein1", ""))
            b = index.get(row.get("protein2", ""))
            if a is None or b is None:
                continue
            try:
                score = float(row.get("combined_score", 0.0)) / 1000.0
            except ValueError:
                score = 0.0
            score = max(0.0, min(score, 1.0))
            degree[a] += 1.0
            degree[b] += 1.0
            weighted_degree[a] += score
            weighted_degree[b] += score
            max_score[a] = max(max_score[a], score)
            max_score[b] = max(max_score[b], score)
            edge_count += 1
    if edge_count == 0:
        raise ValueError("official STRING graph produced zero target-aligned edges; refusing fallback")
    log_degree = torch.log1p(degree)
    log_degree = log_degree / log_degree.max().clamp_min(1.0)
    mean_score = weighted_degree / degree.clamp_min(1.0)
    covered = (degree > 1.0).float()
    return torch.stack([log_degree, mean_score, max_score, covered], dim=1)


class GeneratedModel(nn.Module):
    """Compact STRING neighborhood-aware target head for official K562.

    The model consumes the audited official STRING keep20 edge artifact and exact
    K562 target gene order. Missing graph targets receive only self-loop features;
    no synthetic edges or fallback branch are introduced.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 128))
        self.k_hop = 1
        self.attention_heads = 4 if hidden % 4 == 0 else 1
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
        graph_features = _load_string_target_features(self.n_targets)
        self.register_buffer("string_target_features", graph_features, persistent=False)
        self.graph_projector = nn.Sequential(nn.LayerNorm(4), nn.Linear(4, hidden), nn.GELU())
        self.target_base = nn.Parameter(torch.empty(self.n_targets, hidden))
        nn.init.normal_(self.target_base, std=0.015)
        self.context_rank = nn.Linear(hidden, rank * self.n_classes)
        self.target_rank = nn.Linear(hidden, rank)
        self.token_classifier = nn.Linear(hidden, self.n_classes)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.gate = nn.Sequential(nn.Linear(hidden, hidden), nn.Sigmoid())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        graph_features = self.string_target_features.to(device=x.device, dtype=x.dtype)
        target_tokens = self.target_base.to(device=x.device, dtype=x.dtype) + self.graph_projector(graph_features)
        context_rank = self.context_rank(z).view(x.shape[0], -1, self.n_classes)
        target_rank = self.target_rank(target_tokens)
        low_rank_logits = torch.einsum("brc,nr->bnc", context_rank, target_rank)
        graph_logits = self.token_classifier(target_tokens).unsqueeze(0)
        gate = self.gate(z).mean(dim=-1).view(-1, 1, 1)
        return gate * low_rank_logits + (1.0 - gate) * graph_logits + self.bias.unsqueeze(0)
