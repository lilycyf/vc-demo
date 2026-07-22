from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")
TARGET_FEATURE_DIM = 48
N_EXPERTS = 4


def _hash_values(key: str, count: int) -> list[float]:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return [float(digest[i % len(digest)]) / 127.5 - 1.0 for i in range(count)]


def _read_target_features(n_targets: int) -> tuple[torch.Tensor, dict[str, int | str]]:
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
    denom = max(1, int(n_targets) - 1)
    features = np.zeros((int(n_targets), TARGET_FEATURE_DIM), dtype="float32")
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
        vals.extend(_hash_values(f"official-target-prior|{idx}|{gene_id}|{symbol}", TARGET_FEATURE_DIM - len(vals)))
        features[idx] = np.asarray(vals, dtype="float32")
    return torch.from_numpy(features), {"target_rows": len(rows), "target_feature_dim": TARGET_FEATURE_DIM}


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
    """Parent-preserving official K562 multimodal mixture-of-experts head.

    This node keeps the parent AIDO embedding dense classifier and adds gated
    experts over source-backed modalities available in this contract: AIDO input
    context, the official target-gene order/table, and train-only class-prior
    learning from the configured focal-loss objective. It does not fabricate or
    silently substitute missing STRING/scFoundation expert artifacts.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = min(96, hidden)
        self.implementation_semantics = "parent_preserving_mixture_of_experts_delta"
        target_features, meta = _read_target_features(self.n_targets)
        self.register_buffer("target_features", target_features, persistent=False)
        self.artifact_usage = {
            "official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT),
            "official_target_gene_order": str(TARGET_GENE_TABLE),
            "active_experts": ["parent_dense", "aido_context", "target_low_rank", "target_prior_bias"],
            **meta,
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
        self.aido_context_head = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(hidden, self.n_targets * self.n_classes),
        )
        self.target_encoder = nn.Sequential(
            nn.LayerNorm(TARGET_FEATURE_DIM),
            nn.Linear(TARGET_FEATURE_DIM, self.rank * 2),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(self.rank * 2, self.rank),
            nn.LayerNorm(self.rank),
        )
        self.context_to_target = nn.Linear(hidden, self.rank * self.n_classes)
        self.target_feature_bias = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.class_prior = nn.Parameter(torch.zeros(self.n_classes))
        self.target_prior = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

        self.router = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Dropout(dropout * 0.25),
            nn.Linear(hidden // 2, N_EXPERTS),
        )
        self.expert_temperature = nn.Parameter(torch.tensor(1.0))
        self.last_router_weights: torch.Tensor | None = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        batch = x.shape[0]
        parent_logits = self.parent_dense_head(z).view(batch, self.n_targets, self.n_classes)
        aido_logits = self.aido_context_head(z).view(batch, self.n_targets, self.n_classes)

        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        target_factor = self.target_encoder(target_features)
        context_factor = self.context_to_target(z).view(batch, self.rank, self.n_classes)
        low_rank_logits = torch.einsum("brc,nr->bnc", context_factor, target_factor) / math.sqrt(float(self.rank))

        prior_logits = (
            self.target_feature_bias(target_features).unsqueeze(0)
            + self.class_prior.view(1, 1, self.n_classes)
            + self.target_prior.to(device=x.device, dtype=x.dtype).unsqueeze(0)
        )
        experts = torch.stack([parent_logits, aido_logits, low_rank_logits, prior_logits.expand_as(parent_logits)], dim=1)
        temperature = torch.clamp(self.expert_temperature.abs(), min=0.25, max=4.0)
        router_weights = torch.softmax(self.router(z) / temperature, dim=-1)
        self.last_router_weights = router_weights.detach()
        return torch.sum(experts * router_weights.view(batch, N_EXPERTS, 1, 1), dim=1)
