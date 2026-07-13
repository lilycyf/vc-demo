from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn
import torch.nn.functional as F

TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
OFFICIAL_TASK_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")
TARGET_FEATURE_DIM = 48
AIDO_CACHE = Path("data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad")
GNN_CACHE = Path("data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad")


def _target_gene_features(path: Path, n_targets: int) -> torch.Tensor:
    if not path.exists():
        raise FileNotFoundError(f"official target-gene table is required: {path}")
    if not OFFICIAL_TASK_ARTIFACT.exists():
        raise FileNotFoundError(f"official DEG split artifact is required: {OFFICIAL_TASK_ARTIFACT}")
    rows = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows.append((int(row["target_index"]), str(row.get("gene_id", "")), str(row.get("symbol", ""))))
    rows.sort(key=lambda item: item[0])
    if len(rows) != int(n_targets) or [r[0] for r in rows] != list(range(int(n_targets))):
        raise ValueError("official target-gene table must match n_targets and target_index order")
    feats = torch.empty(int(n_targets), TARGET_FEATURE_DIM, dtype=torch.float32)
    denom = max(1, int(n_targets) - 1)
    for index, gene_id, symbol in rows:
        key = f"{index}|{gene_id}|{symbol}".encode("utf-8")
        digest = hashlib.sha256(key).digest()
        pos = float(index) / float(denom)
        vals = [pos, math.sin(pos * math.tau), math.cos(pos * math.tau), min(len(symbol), 32) / 32.0, 1.0 if gene_id.startswith("ENSG") else 0.0]
        while len(vals) < TARGET_FEATURE_DIM:
            vals.append(float(digest[(len(vals) - 5) % len(digest)]) / 127.5 - 1.0)
        feats[index] = torch.tensor(vals[:TARGET_FEATURE_DIM], dtype=torch.float32)
    return feats


class ResidualContextBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden * 2, hidden), nn.Dropout(dropout)
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Official K562 target bilinear head with dense and bilinear residual branches."""

    def __init__(self, spec) -> None:
        super().__init__()
        self.input_dim = int(spec.input_dim)
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(64, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 160))
        dropout = float(spec.dropout)
        self.target_head_policy = "cached_aido_gnn_modality_gated_fusion_plus_bilinear_head"
        if not AIDO_CACHE.exists():
            raise FileNotFoundError(f"official AIDO cached embedding h5ad is required: {AIDO_CACHE}")
        if not GNN_CACHE.exists():
            raise FileNotFoundError(f"official GNN cached embedding h5ad is required: {GNN_CACHE}")
        self.aido_dim = min(640, self.input_dim)
        self.gnn_dim = max(0, self.input_dim - self.aido_dim)

        self.full_trunk = nn.Sequential(nn.LayerNorm(self.input_dim), nn.Linear(self.input_dim, hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden))
        self.aido_trunk = nn.Sequential(nn.LayerNorm(self.aido_dim), nn.Linear(self.aido_dim, hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden))
        self.gnn_trunk = nn.Sequential(nn.LayerNorm(max(1, self.gnn_dim)), nn.Linear(max(1, self.gnn_dim), hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden))
        self.modality_router = nn.Sequential(nn.LayerNorm(self.input_dim), nn.Linear(self.input_dim, hidden), nn.GELU(), nn.Linear(hidden, 3))
        self.blocks = nn.Sequential(*[ResidualContextBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))])
        self.norm = nn.LayerNorm(hidden)
        self.dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.rank_head = nn.Linear(hidden, self.rank * self.n_classes)
        self.rank_gate = nn.Sequential(nn.Linear(hidden, self.rank), nn.Sigmoid())

        target_features = _target_gene_features(TARGET_GENE_TABLE, self.n_targets)
        self.register_buffer("target_features", target_features, persistent=False)
        self.target_projection = nn.Sequential(
            nn.LayerNorm(TARGET_FEATURE_DIM),
            nn.Linear(TARGET_FEATURE_DIM, self.rank),
            nn.GELU(),
            nn.Linear(self.rank, self.rank),
        )
        self.target_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.learned_target_factors = nn.Parameter(torch.empty(self.n_targets, self.rank))
        nn.init.normal_(self.learned_target_factors, mean=0.0, std=0.012)
        self.class_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.residual_scale = nn.Parameter(torch.tensor(0.25))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        aido = x[:, :self.aido_dim]
        gnn = x[:, self.aido_dim:] if self.gnn_dim > 0 else x.new_zeros((x.shape[0], 1))
        experts = torch.stack([self.full_trunk(x), self.aido_trunk(aido), self.gnn_trunk(gnn)], dim=1)
        weights = torch.softmax(self.modality_router(x), dim=-1).unsqueeze(-1)
        z = self.norm(self.blocks((weights * experts).sum(dim=1)))
        dense_logits = self.dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        rank_logits = self.rank_head(z).view(x.shape[0], self.rank, self.n_classes)
        rank_logits = rank_logits * self.rank_gate(z).view(x.shape[0], self.rank, 1)
        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        target_rank = self.target_projection(target_features) + self.learned_target_factors.to(device=x.device, dtype=x.dtype)
        target_rank = F.layer_norm(target_rank, (self.rank,))
        residual_logits = torch.einsum("brc,nr->bnc", rank_logits, target_rank)
        offsets = self.target_offset(target_features).unsqueeze(0)
        return dense_logits + self.residual_scale.tanh() * residual_logits + offsets + self.class_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
