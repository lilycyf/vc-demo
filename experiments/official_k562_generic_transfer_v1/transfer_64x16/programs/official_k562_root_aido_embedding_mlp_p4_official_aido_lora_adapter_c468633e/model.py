from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
AIDO_CACHE_H5AD = Path("data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad")
AIDO_MODEL_DIR = Path("/home/Models/AIDO.Cell-100M")
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
        key = f"{index}|{gene_id}|{symbol}|aido-cache-fusion".encode("utf-8")
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
    """Official K562 AIDO low-rank adapter head.

    The dataloader supplies frozen AIDO.Cell-100M cached embeddings from the
    official h5ad artifact. This node validates the model directory and cache
    path, then learns a low-rank adapter fusion over cached AIDO context features and the
    fixed official target-gene order.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        if not AIDO_MODEL_DIR.exists():
            raise FileNotFoundError(f"AIDO.Cell-100M model directory is required: {AIDO_MODEL_DIR}")
        if not AIDO_CACHE_H5AD.exists():
            raise FileNotFoundError(f"AIDO cached embedding h5ad is required: {AIDO_CACHE_H5AD}")

        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(48, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        dropout = float(spec.dropout)
        self.aido_cache_path = str(AIDO_CACHE_H5AD)
        self.aido_model_dir = str(AIDO_MODEL_DIR)

        self.lora_down = nn.Linear(int(spec.input_dim), max(16, min(64, int(spec.input_dim) // 8)), bias=False)
        self.lora_up = nn.Linear(max(16, min(64, int(spec.input_dim) // 8)), int(spec.input_dim), bias=False)
        self.lora_scale = nn.Parameter(torch.tensor(0.1))
        self.cache_encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            *[ResidualBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))],
            nn.LayerNorm(hidden),
        )
        self.cache_gate = nn.Sequential(nn.Linear(hidden, self.rank), nn.Sigmoid())
        self.cache_rank_logits = nn.Linear(hidden, self.rank * self.n_classes)
        self.cache_residual_logits = nn.Linear(hidden, self.n_classes)

        target_features = _target_gene_features(TARGET_GENE_TABLE, self.n_targets)
        self.register_buffer("target_features", target_features, persistent=False)
        self.target_rank = nn.Sequential(
            nn.LayerNorm(TARGET_FEATURE_DIM),
            nn.Linear(TARGET_FEATURE_DIM, self.rank),
            nn.GELU(),
            nn.Linear(self.rank, self.rank),
        )
        self.target_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        adapted_x = x + self.lora_scale.to(device=x.device, dtype=x.dtype) * self.lora_up(torch.nn.functional.gelu(self.lora_down(x)))
        z = self.cache_encoder(adapted_x)
        rank_logits = self.cache_rank_logits(z).view(x.shape[0], self.rank, self.n_classes)
        rank_logits = rank_logits * self.cache_gate(z).view(x.shape[0], self.rank, 1)
        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        target_rank = torch.nn.functional.layer_norm(self.target_rank(target_features), (self.rank,))
        logits = torch.einsum("brc,nr->bnc", rank_logits, target_rank)
        residual = self.cache_residual_logits(z).unsqueeze(1)
        return logits + residual + self.target_offset(target_features).unsqueeze(0) + self.target_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
