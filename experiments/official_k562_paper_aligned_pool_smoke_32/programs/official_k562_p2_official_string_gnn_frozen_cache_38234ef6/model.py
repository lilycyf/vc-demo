from __future__ import annotations

import csv
import json
from pathlib import Path

import torch
from torch import nn


STRING_DIR = Path("/home/Models/STRING_GNN")
EMBEDDING_PATH = STRING_DIR / "node_embeddings.pt"
NODE_NAMES_PATH = STRING_DIR / "node_names.json"
TARGET_PATH = Path("data/cell_lines/official_k562_cls/target_genes.tsv")


def _target_ids() -> list[str]:
    if not TARGET_PATH.exists():
        raise FileNotFoundError(f"official K562 target gene order missing: {TARGET_PATH}")
    with TARGET_PATH.open(newline="") as f:
        return [row["gene_id"] for row in csv.DictReader(f, delimiter="\t")]


def _load_target_string_cache(n_targets: int) -> tuple[torch.Tensor, torch.Tensor]:
    if not EMBEDDING_PATH.exists() or not NODE_NAMES_PATH.exists():
        raise FileNotFoundError(f"required STRING_GNN cache files missing under {STRING_DIR}")
    embeddings = torch.load(EMBEDDING_PATH, map_location="cpu").float()
    node_names = json.loads(NODE_NAMES_PATH.read_text())
    if len(node_names) != int(embeddings.shape[0]):
        raise ValueError("STRING_GNN node_names length does not match node_embeddings rows")
    targets = _target_ids()
    if len(targets) != n_targets:
        raise ValueError(f"target gene count {len(targets)} != spec.n_targets={n_targets}")
    lookup = {gene: i for i, gene in enumerate(node_names)}
    out = torch.zeros(n_targets, int(embeddings.shape[1]), dtype=torch.float32)
    present = torch.zeros(n_targets, 1, dtype=torch.float32)
    for i, gene in enumerate(targets):
        j = lookup.get(gene)
        if j is not None:
            out[i] = embeddings[j]
            present[i, 0] = 1.0
    if int(present.sum().item()) == 0:
        raise ValueError("STRING_GNN frozen cache has zero overlap with K562 targets; strict fallback forbidden")
    return out, present


class GeneratedModel(nn.Module):
    """Frozen STRING_GNN target-cache head for official K562."""

    def __init__(self, spec) -> None:
        super().__init__()
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 128))
        target_cache, present = _load_target_string_cache(self.n_targets)
        self.register_buffer("target_string_cache", target_cache, persistent=False)
        self.register_buffer("target_string_present", present, persistent=False)
        self.input_encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout)
        )
        self.cache_encoder = nn.Sequential(
            nn.LayerNorm(int(target_cache.shape[1])), nn.Linear(int(target_cache.shape[1]), hidden), nn.GELU()
        )
        self.presence_gate = nn.Sequential(nn.Linear(1, hidden), nn.Sigmoid())
        self.context_rank = nn.Linear(hidden, rank * self.n_classes)
        self.target_rank = nn.Linear(hidden, rank)
        self.cache_head = nn.Linear(hidden, self.n_classes)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.input_encoder(x)
        cache = self.target_string_cache.to(device=x.device, dtype=x.dtype)
        present = self.target_string_present.to(device=x.device, dtype=x.dtype)
        target = self.cache_encoder(cache) * self.presence_gate(present)
        context_rank = self.context_rank(z).view(x.shape[0], -1, self.n_classes)
        target_rank = self.target_rank(target)
        logits = torch.einsum("brc,nr->bnc", context_rank, target_rank)
        return logits + self.cache_head(target).unsqueeze(0) + self.bias.unsqueeze(0)
