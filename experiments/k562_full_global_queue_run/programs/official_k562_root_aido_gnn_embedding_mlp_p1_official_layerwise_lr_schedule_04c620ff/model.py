from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
TARGET_FEATURE_DIM = 48


def _target_gene_features(path: Path, n_targets: int) -> torch.Tensor:
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

    def lr_parameter_groups(self, base_lr: float) -> list[dict]:
        named = dict(self.named_parameters())
        groups = []
        used = set()
        for group in self.layerwise_lr_schedule:
            params = []
            for name, param in named.items():
                if any(name.startswith(prefix) for prefix in group["modules"]):
                    params.append(param)
                    used.add(name)
            if params:
                groups.append({"params": params, "lr": float(base_lr) * float(group["lr_scale"]), "name": group["name"]})
        rest = [param for name, param in named.items() if name not in used]
        if rest:
            groups.append({"params": rest, "lr": float(base_lr), "name": "unmatched"})
        return groups

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Official K562 layerwise-LR schedule candidate.

    The architecture is a full target-aware low-rank DEG classifier over the
    official AIDO+GNN features. It exposes named parameter groups for
    discriminative/layerwise learning-rate decay while preserving official
    splits, target-gene order, and Macro-F1 semantics.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(64, min(int(getattr(spec, "low_rank_dim", 128)), hidden, 192))
        dropout = float(spec.dropout)

        self.input = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[ResidualContextBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))])
        self.context_norm = nn.LayerNorm(hidden)
        self.context_rank_logits = nn.Linear(hidden, self.rank * self.n_classes)
        self.context_gate = nn.Sequential(nn.Linear(hidden, self.rank), nn.Sigmoid())

        target_features = _target_gene_features(TARGET_GENE_TABLE, self.n_targets)
        self.register_buffer("target_features", target_features, persistent=False)
        self.target_projection = nn.Sequential(
            nn.LayerNorm(TARGET_FEATURE_DIM),
            nn.Linear(TARGET_FEATURE_DIM, self.rank),
            nn.GELU(),
            nn.Linear(self.rank, self.rank),
        )
        self.target_class_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.learned_target_factors = nn.Parameter(torch.empty(self.n_targets, self.rank))
        nn.init.normal_(self.learned_target_factors, mean=0.0, std=0.015)
        self.class_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.head_rank = self.rank
        self.head_depth = max(1, int(spec.depth))
        self.layerwise_lr_schedule = [
            {"name": "input_encoder", "lr_scale": 0.50, "modules": ["input"]},
            {"name": "context_blocks", "lr_scale": 0.75, "modules": ["blocks", "context_norm"]},
            {"name": "target_head", "lr_scale": 1.00, "modules": ["context_rank_logits", "context_gate", "target_projection", "target_class_offset", "learned_target_factors", "class_bias"]},
        ]

    def lr_parameter_groups(self, base_lr: float) -> list[dict]:
        named = dict(self.named_parameters())
        groups = []
        used = set()
        for group in self.layerwise_lr_schedule:
            params = []
            for name, param in named.items():
                if any(name.startswith(prefix) for prefix in group["modules"]):
                    params.append(param)
                    used.add(name)
            if params:
                groups.append({"params": params, "lr": float(base_lr) * float(group["lr_scale"]), "name": group["name"]})
        rest = [param for name, param in named.items() if name not in used]
        if rest:
            groups.append({"params": rest, "lr": float(base_lr), "name": "unmatched"})
        return groups

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        rank_logits = self.context_rank_logits(z).view(x.shape[0], self.rank, self.n_classes)
        gate = self.context_gate(z).view(x.shape[0], self.rank, 1)
        rank_logits = rank_logits * gate

        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        target_rank = self.target_projection(target_features) + self.learned_target_factors.to(device=x.device, dtype=x.dtype)
        target_rank = torch.nn.functional.layer_norm(target_rank, (self.rank,))
        logits = torch.einsum("brc,nr->bnc", rank_logits, target_rank)
        offsets = self.target_class_offset(target_features).unsqueeze(0)
        return logits + offsets + self.class_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
