from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
BASE_TARGET_DIM = 32


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


def _target_features(rows: list[tuple[int, str, str]]) -> torch.Tensor:
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


class LowRankTargetHead(nn.Module):
    def __init__(self, hidden: int, rank: int, n_classes: int, dropout: float) -> None:
        super().__init__()
        self.rank = rank
        self.n_classes = n_classes
        self.context = nn.Sequential(nn.LayerNorm(hidden), nn.Dropout(dropout), nn.Linear(hidden, rank * n_classes))

    def forward(self, z: torch.Tensor, target_factor: torch.Tensor) -> torch.Tensor:
        rank_logits = self.context(z).view(z.shape[0], self.rank, self.n_classes)
        return torch.einsum("brc,nr->bnc", rank_logits, target_factor)


class GeneratedModel(nn.Module):
    """Multimodal mixture-of-experts over official K562 cached modalities.

    Active experts are AIDO cached embedding, STRING-GNN cached embedding, joint
    fused embedding, and target-prior offset. The router sees the same official
    cached perturbation features as the parent root and records its active expert
    names through attributes for audit. No expert substitutes missing artifacts;
    the official task artifact and target-gene order are required.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        input_dim = int(spec.input_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.aido_dim = 640 if input_dim >= 896 else max(1, input_dim // 2)
        self.gnn_dim = 256 if input_dim >= 896 else max(1, input_dim - self.aido_dim)
        self.extra_dim = max(0, input_dim - self.aido_dim - self.gnn_dim)
        self.rank = max(48, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        self.active_experts = ["aido_cached", "string_gnn_cached", "joint_fusion", "target_prior"]
        self.router_inputs = ["aido_cached_embedding", "string_gnn_cached_embedding", "optional_extra_features"]

        self.aido_encoder = nn.Sequential(nn.Linear(self.aido_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.gnn_encoder = nn.Sequential(nn.Linear(self.gnn_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.joint_encoder = nn.Sequential(nn.Linear(input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.aido_blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.gnn_blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.joint_blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.router = nn.Sequential(nn.LayerNorm(hidden * 3), nn.Linear(hidden * 3, hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, 4))

        rows = _read_targets(TARGET_GENE_TABLE, self.n_targets)
        target_features = _target_features(rows)
        self.register_buffer("target_features", target_features, persistent=False)
        self.target_factor = nn.Sequential(nn.LayerNorm(BASE_TARGET_DIM), nn.Linear(BASE_TARGET_DIM, self.rank), nn.GELU(), nn.Linear(self.rank, self.rank))
        self.aido_head = LowRankTargetHead(hidden, self.rank, self.n_classes, dropout)
        self.gnn_head = LowRankTargetHead(hidden, self.rank, self.n_classes, dropout)
        self.joint_head = LowRankTargetHead(hidden, self.rank, self.n_classes, dropout)
        self.target_prior = nn.Linear(BASE_TARGET_DIM, self.n_classes)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        aido = x[:, : self.aido_dim]
        gnn = x[:, self.aido_dim : self.aido_dim + self.gnn_dim]
        za = self.aido_blocks(self.aido_encoder(aido))
        zg = self.gnn_blocks(self.gnn_encoder(gnn))
        zj = self.joint_blocks(self.joint_encoder(x))
        router = torch.softmax(self.router(torch.cat([za, zg, zj], dim=1)), dim=1)
        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        target_factor = self.target_factor(target_features)
        target_factor = torch.nn.functional.layer_norm(target_factor, (self.rank,))
        expert_logits = torch.stack(
            [
                self.aido_head(za, target_factor),
                self.gnn_head(zg, target_factor),
                self.joint_head(zj, target_factor),
                self.target_prior(target_features).unsqueeze(0).expand(x.shape[0], -1, -1),
            ],
            dim=1,
        )
        logits = (router.view(x.shape[0], 4, 1, 1) * expert_logits).sum(dim=1)
        return logits + self.bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
