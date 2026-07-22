from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
PATHWAY_ARTIFACT = Path("data/artifacts/pathways/k562_target_pathway_membership.npz")
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


def _aligned_pathway_membership(rows: list[tuple[int, str, str]], n_targets: int) -> tuple[torch.Tensor, int, int]:
    if not PATHWAY_ARTIFACT.exists():
        raise FileNotFoundError(f"Reactome pathway artifact is required: {PATHWAY_ARTIFACT}")
    artifact = np.load(PATHWAY_ARTIFACT, allow_pickle=True)
    membership = artifact["membership"].astype("float32")
    pathway_targets = [str(x) for x in artifact["target_genes"].tolist()]
    if membership.shape[0] != len(pathway_targets):
        raise ValueError("pathway membership rows must match artifact target_genes")
    symbol_to_artifact = {symbol: i for i, symbol in enumerate(pathway_targets)}
    aligned = np.zeros((int(n_targets), membership.shape[1]), dtype="float32")
    covered = 0
    for index, _gene_id, symbol in rows:
        artifact_index = symbol_to_artifact.get(symbol)
        if artifact_index is None:
            continue
        aligned[index] = membership[artifact_index]
        covered += 1
    row_sums = aligned.sum(axis=1, keepdims=True)
    aligned = np.divide(aligned, np.maximum(row_sums, 1.0), out=np.zeros_like(aligned), where=row_sums >= 0)
    return torch.from_numpy(aligned), covered, membership.shape[1]


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
    """Parent-preserving K562 Reactome pathway pooling head."""

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(32, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        dropout = float(spec.dropout)

        self.input = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[ResidualContextBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))])
        self.context_norm = nn.LayerNorm(hidden)
        self.parent_dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.context_rank_logits = nn.Linear(hidden, self.rank * self.n_classes)
        self.pathway_gate = nn.Sequential(nn.Linear(hidden, self.rank), nn.Sigmoid())

        rows = _read_official_targets(TARGET_GENE_TABLE, self.n_targets)
        self.register_buffer("target_features", _target_gene_features(rows, self.n_targets), persistent=False)
        pathway_membership, covered_targets, n_pathways = _aligned_pathway_membership(rows, self.n_targets)
        self.register_buffer("pathway_membership", pathway_membership, persistent=False)
        self.covered_targets = int(covered_targets)
        self.n_pathways = int(n_pathways)
        self.pathway_coverage = float(covered_targets) / float(max(1, self.n_targets))

        self.pathway_embeddings = nn.Parameter(torch.empty(self.n_pathways, self.rank))
        nn.init.normal_(self.pathway_embeddings, mean=0.0, std=0.02)
        self.target_projection = nn.Sequential(
            nn.LayerNorm(TARGET_FEATURE_DIM),
            nn.Linear(TARGET_FEATURE_DIM, self.rank),
            nn.GELU(),
            nn.Linear(self.rank, self.rank),
        )
        self.target_class_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.residual_scale = nn.Parameter(torch.tensor(0.1, dtype=torch.float32))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        dense_logits = self.parent_dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        rank_logits = self.context_rank_logits(z).view(x.shape[0], self.rank, self.n_classes)
        rank_logits = rank_logits * self.pathway_gate(z).view(x.shape[0], self.rank, 1)

        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        membership = self.pathway_membership.to(device=x.device, dtype=x.dtype)
        pathway_embeddings = self.pathway_embeddings.to(device=x.device, dtype=x.dtype)
        pathway_target_rank = membership @ pathway_embeddings
        target_rank = self.target_projection(target_features) + pathway_target_rank
        target_rank = torch.nn.functional.layer_norm(target_rank, (self.rank,))
        pathway_logits = torch.einsum("brc,nr->bnc", rank_logits, target_rank)
        offsets = self.target_class_offset(target_features).unsqueeze(0)
        return dense_logits + self.residual_scale.to(device=x.device, dtype=x.dtype) * pathway_logits + offsets
