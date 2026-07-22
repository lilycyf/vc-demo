from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
PATHWAY_MEMBERSHIP = Path("data/artifacts/pathways/k562_target_pathway_membership.npz")
OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")


def _read_official_symbols(n_targets: int) -> list[str]:
    if not OFFICIAL_DEG_ARTIFACT.exists():
        raise FileNotFoundError(f"official DEG split artifact is required: {OFFICIAL_DEG_ARTIFACT}")
    if not TARGET_GENE_TABLE.exists():
        raise FileNotFoundError(f"official target-gene table is required: {TARGET_GENE_TABLE}")
    rows: list[tuple[int, str]] = []
    with TARGET_GENE_TABLE.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows.append((int(row["target_index"]), str(row.get("symbol", ""))))
    rows.sort(key=lambda item: item[0])
    if len(rows) != int(n_targets):
        raise ValueError(f"target-gene rows {len(rows)} do not match n_targets {n_targets}")
    if [idx for idx, _ in rows] != list(range(int(n_targets))):
        raise ValueError("target-gene table must preserve contiguous official target_index order")
    return [sym for _, sym in rows]


def _aligned_membership(n_targets: int) -> tuple[torch.Tensor, int, int]:
    if not PATHWAY_MEMBERSHIP.exists():
        raise FileNotFoundError(f"Reactome pathway membership artifact is required: {PATHWAY_MEMBERSHIP}")
    z = np.load(PATHWAY_MEMBERSHIP, allow_pickle=False)
    membership = z["membership"].astype("float32")
    artifact_symbols = [str(x) for x in z["target_genes"]]
    pathway_count = int(membership.shape[1])
    if membership.shape[0] != len(artifact_symbols):
        raise ValueError("pathway membership row count does not match target_genes")

    official_symbols = _read_official_symbols(n_targets)
    symbol_to_official = {symbol: idx for idx, symbol in enumerate(official_symbols) if symbol}
    aligned = np.zeros((int(n_targets), pathway_count), dtype="float32")
    covered = 0
    for row_idx, symbol in enumerate(artifact_symbols):
        official_idx = symbol_to_official.get(symbol)
        if official_idx is not None:
            aligned[official_idx] = membership[row_idx]
            covered += 1
    pathway_degrees = np.maximum(aligned.sum(axis=0, keepdims=True), 1.0)
    aligned = aligned / pathway_degrees
    return torch.from_numpy(aligned), covered, pathway_count


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
    """Parent-preserving Reactome pathway pooling child for official K562.

    The model keeps the parent AIDO+GNN dense all-target branch and adds a real
    Reactome membership residual. The membership matrix is aligned back to the
    official 6,640 target-gene order; targets outside the source-backed pathway
    artifact receive zero pathway residual rather than a fabricated assignment.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.implementation_semantics = "parent_preserving_pathway_pooling_replicate_delta"

        self.input = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.context_norm = nn.LayerNorm(hidden)
        self.parent_dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)

        membership, covered_targets, pathway_count = _aligned_membership(self.n_targets)
        self.register_buffer("target_pathway", membership, persistent=False)
        self.covered_targets = int(covered_targets)
        self.pathway_count = int(pathway_count)
        self.artifact_usage = {
            "pathway_membership_matrix": str(PATHWAY_MEMBERSHIP),
            "official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT),
            "covered_targets": self.covered_targets,
            "pathway_count": self.pathway_count,
        }

        self.pathway_context = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(hidden, self.pathway_count * self.n_classes),
        )
        self.pathway_gate = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, self.n_classes),
        )
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.residual_scale = nn.Parameter(torch.zeros(self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        parent_logits = self.parent_dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        pathway_logits = self.pathway_context(z).view(x.shape[0], self.pathway_count, self.n_classes)
        membership = self.target_pathway.to(device=x.device, dtype=x.dtype)
        residual = torch.einsum("bpc,np->bnc", pathway_logits, membership)
        residual = residual / math.sqrt(max(1.0, float(self.pathway_count)))
        gate = torch.sigmoid(self.pathway_gate(z)).view(x.shape[0], 1, self.n_classes)
        scale = 0.5 + torch.tanh(self.residual_scale).view(1, 1, self.n_classes)
        return parent_logits + residual * gate * scale + self.target_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
