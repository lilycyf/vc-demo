from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import torch
from torch import nn


def _load_target_genes(data_dir: str) -> list[str]:
    if not data_dir:
        raise ValueError("STRING GNN node requires spec.artifacts['data_dir']")
    path = Path(data_dir) / "train.npz"
    if not path.exists():
        raise FileNotFoundError(f"cannot load target genes from {path}")
    with np.load(path, allow_pickle=True) as z:
        return [str(x) for x in z["target_genes"].tolist()]


def _load_adjacency(path: str, target_genes: list[str], power: int = 2) -> torch.Tensor:
    edge_path = Path(path)
    if not edge_path.exists():
        raise FileNotFoundError(f"STRING graph edge artifact does not exist: {edge_path}")
    index = {gene: i for i, gene in enumerate(target_genes)}
    adj = torch.eye(len(target_genes), dtype=torch.float32)
    with edge_path.open() as f:
        reader = csv.DictReader(f, delimiter="	")
        for row in reader:
            a = row.get("source_gene", "")
            b = row.get("target_gene", "")
            if a not in index or b not in index:
                continue
            score = float(row.get("score", 1.0) or 1.0)
            i = index[a]
            j = index[b]
            adj[i, j] = max(adj[i, j], score)
            adj[j, i] = max(adj[j, i], score)
    deg = adj.sum(dim=1).clamp_min(1e-6)
    norm = adj / deg.unsqueeze(1)
    propagated = norm
    for _ in range(max(1, power) - 1):
        propagated = torch.matmul(propagated, norm)
    propagated = 0.5 * norm + 0.5 * propagated
    propagated = propagated / propagated.sum(dim=1, keepdim=True).clamp_min(1e-6)
    return propagated


class GeneratedModel(nn.Module):
    artifact_usage = "string_k562_gene_graph"

    def __init__(self, spec) -> None:
        super().__init__()
        artifacts = dict(getattr(spec, "artifacts", {}) or {})
        target_genes = _load_target_genes(str(artifacts.get("data_dir", "")))
        if len(target_genes) != int(spec.n_targets):
            raise ValueError(f"target gene count {len(target_genes)} does not match n_targets {spec.n_targets}")
        graph_path = str(artifacts.get("string_graph_edges_path", "data/artifacts/string/k562_target_graph_edges.tsv"))
        adjacency = _load_adjacency(graph_path, target_genes)
        hidden = int(spec.hidden_dim)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 64)), hidden, 128))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(float(spec.dropout)),
            nn.Linear(hidden, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
        )
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.direct = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.mix_logit = nn.Parameter(torch.tensor(0.0))
        self.register_buffer("target_adjacency", adjacency, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        rank_logits = self.rank_head(z).view(x.shape[0], -1, self.n_classes)
        factor_logits = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors)
        direct = self.direct(z).view(x.shape[0], self.n_targets, self.n_classes)
        base = 0.5 * factor_logits + 0.5 * direct
        adj = self.target_adjacency.to(device=x.device, dtype=x.dtype)
        propagated = torch.einsum("ij,bjc->bic", adj, base)
        mix = torch.sigmoid(self.mix_logit)
        return mix * propagated + (1.0 - mix) * base
