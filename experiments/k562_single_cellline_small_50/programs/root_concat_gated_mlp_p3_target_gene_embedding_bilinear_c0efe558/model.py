from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from torch import nn


def mlp_block(in_dim: int, out_dim: int, dropout: float) -> list[nn.Module]:
    return [nn.Linear(in_dim, out_dim), nn.LayerNorm(out_dim), nn.GELU(), nn.Dropout(dropout)]


def load_npz_array(path: str | Path, key: str) -> torch.Tensor:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"artifact array path does not exist: {path}")
    with np.load(path) as data:
        if key not in data.files:
            raise KeyError(f"artifact array {path} missing key {key!r}; available={data.files}")
        return torch.from_numpy(np.asarray(data[key], dtype="float32"))


class GeneratedModel(nn.Module):
    def __init__(self, spec) -> None:
        super().__init__()
        manifest_path = getattr(spec, "artifact_manifest_path", "") or getattr(spec, "artifacts", {}).get("artifact_manifest_path", "")
        if manifest_path == "auto":
            manifest_path = "data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json"
        if not manifest_path:
            raise ValueError("target_gene_embedding_bilinear requires model.artifact_manifest_path or auto-bound artifact manifest")
        with Path(manifest_path).open() as f:
            manifest = json.load(f)
        target_info = manifest.get("target_gene_embeddings", {})
        target_embeddings = load_npz_array(target_info.get("path", ""), target_info.get("key", "target_gene_embeddings"))
        if target_embeddings.shape[0] != int(spec.n_targets):
            raise ValueError(f"target embedding rows {target_embeddings.shape[0]} != n_targets {spec.n_targets}")
        hidden = int(spec.hidden_dim)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 64)), hidden, 128))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        layers: list[nn.Module] = [nn.Linear(spec.input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(spec.dropout)]
        for _ in range(max(0, int(spec.depth) - 1)):
            layers.extend(mlp_block(hidden, hidden, spec.dropout))
        self.encoder = nn.Sequential(*layers)
        self.context_rank = nn.Linear(hidden, rank * self.n_classes)
        self.target_projection = nn.Sequential(nn.LayerNorm(target_embeddings.shape[1]), nn.Linear(target_embeddings.shape[1], rank))
        self.target_residual = nn.Linear(target_embeddings.shape[1], self.n_classes)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.register_buffer("target_embeddings", target_embeddings, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        context = self.encoder(x)
        context_rank = self.context_rank(context).view(x.shape[0], -1, self.n_classes)
        target_embeddings = self.target_embeddings.to(device=x.device, dtype=x.dtype)
        target_rank = self.target_projection(target_embeddings)
        logits = torch.einsum("brc,nr->bnc", context_rank, target_rank)
        return logits + self.target_residual(target_embeddings).unsqueeze(0) + self.bias.unsqueeze(0)
