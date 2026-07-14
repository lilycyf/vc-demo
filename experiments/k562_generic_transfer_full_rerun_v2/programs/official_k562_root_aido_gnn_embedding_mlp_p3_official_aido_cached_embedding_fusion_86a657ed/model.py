from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
AIDO_CACHE_PATH = Path("data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad")
GNN_CACHE_PATH = Path("data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad")
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


class GeneratedModel(nn.Module):
    """AIDO cached embedding fusion model for the official K562 task.

    The official dataset input for this root concatenates source-backed cached
    AIDO.Cell-100M perturbation embeddings (640 dimensions) and STRING-GNN
    cached embeddings (256 dimensions). This model verifies those cache files are
    present, splits the input by provenance, learns a gated fusion, then predicts
    all official target-gene logits with a target-aware low-rank head. It does
    not load or emulate the AIDO checkpoint and does not fabricate embeddings.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        if not AIDO_CACHE_PATH.exists():
            raise FileNotFoundError(f"AIDO cached embedding artifact is required: {AIDO_CACHE_PATH}")
        if not GNN_CACHE_PATH.exists():
            raise FileNotFoundError(f"GNN cached embedding artifact is required: {GNN_CACHE_PATH}")
        input_dim = int(spec.input_dim)
        if input_dim < 896:
            raise ValueError(f"expected concatenated AIDO(640)+GNN(256) features, got input_dim={input_dim}")
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.aido_dim = 640
        self.gnn_dim = 256
        self.extra_dim = input_dim - self.aido_dim - self.gnn_dim
        self.rank = max(48, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        self.cache_paths = (str(AIDO_CACHE_PATH), str(GNN_CACHE_PATH))

        self.aido_encoder = nn.Sequential(nn.Linear(self.aido_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.gnn_encoder = nn.Sequential(nn.Linear(self.gnn_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.extra_encoder = nn.Sequential(nn.Linear(max(1, self.extra_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.gate = nn.Sequential(nn.Linear(hidden * 3, hidden), nn.GELU(), nn.Linear(hidden, 3))
        self.blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.context_norm = nn.LayerNorm(hidden)
        self.context_rank = nn.Linear(hidden, self.rank * self.n_classes)

        rows = _read_targets(TARGET_GENE_TABLE, self.n_targets)
        target_features = _target_features(rows)
        self.register_buffer("target_features", target_features, persistent=False)
        self.target_factor = nn.Sequential(nn.LayerNorm(BASE_TARGET_DIM), nn.Linear(BASE_TARGET_DIM, self.rank), nn.GELU(), nn.Linear(self.rank, self.rank))
        self.target_offset = nn.Linear(BASE_TARGET_DIM, self.n_classes)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        aido = x[:, : self.aido_dim]
        gnn = x[:, self.aido_dim : self.aido_dim + self.gnn_dim]
        if self.extra_dim > 0:
            extra = x[:, self.aido_dim + self.gnn_dim :]
        else:
            extra = x.new_zeros((x.shape[0], 1))
        za = self.aido_encoder(aido)
        zg = self.gnn_encoder(gnn)
        ze = self.extra_encoder(extra)
        weights = torch.softmax(self.gate(torch.cat([za, zg, ze], dim=1)), dim=1)
        z = weights[:, 0:1] * za + weights[:, 1:2] * zg + weights[:, 2:3] * ze
        z = self.context_norm(self.blocks(z))
        rank_logits = self.context_rank(z).view(x.shape[0], self.rank, self.n_classes)
        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        target_factor = self.target_factor(target_features)
        target_factor = torch.nn.functional.layer_norm(target_factor, (self.rank,))
        logits = torch.einsum("brc,nr->bnc", rank_logits, target_factor)
        return logits + self.target_offset(target_features).unsqueeze(0) + self.bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
