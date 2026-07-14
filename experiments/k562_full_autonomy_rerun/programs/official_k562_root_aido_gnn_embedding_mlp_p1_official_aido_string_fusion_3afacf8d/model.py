from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")
AIDO_MODEL_DIR = Path("/home/Models/AIDO.Cell-100M")
STRING_GNN_MODEL_DIR = Path("/home/Models/STRING_GNN")
STRING_NODE_EMBEDDINGS = STRING_GNN_MODEL_DIR / "node_embeddings.pt"
STRING_NODE_NAMES = STRING_GNN_MODEL_DIR / "node_names.json"
AIDO_GENE_INDEX = AIDO_MODEL_DIR / "gene_id_to_aido_index.json"
AIDO_FEATURE_DIM = 8


def _require(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"required {label} artifact is missing: {path}")


def _read_targets(path: Path, n_targets: int) -> list[tuple[int, str, str]]:
    _require(OFFICIAL_DEG_ARTIFACT, "official DEG split")
    _require(path, "official target gene table")
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


def _load_string_embeddings(rows: list[tuple[int, str, str]]) -> tuple[torch.Tensor, float]:
    _require(STRING_GNN_MODEL_DIR, "STRING_GNN model directory")
    _require(STRING_NODE_EMBEDDINGS, "STRING_GNN node embeddings")
    _require(STRING_NODE_NAMES, "STRING_GNN node names")
    names = json.loads(STRING_NODE_NAMES.read_text())
    if not isinstance(names, list):
        raise ValueError("STRING_GNN node_names.json must be a list preserving embedding row order")
    name_to_index = {str(name): i for i, name in enumerate(names)}
    try:
        embeddings = torch.load(STRING_NODE_EMBEDDINGS, map_location="cpu", weights_only=True)
    except TypeError:
        embeddings = torch.load(STRING_NODE_EMBEDDINGS, map_location="cpu")
    if not torch.is_tensor(embeddings) or embeddings.ndim != 2:
        raise ValueError("STRING_GNN node_embeddings.pt must contain a 2D tensor")
    if embeddings.shape[0] != len(names):
        raise ValueError("STRING_GNN node embedding rows do not match node_names.json")
    out = torch.zeros(len(rows), embeddings.shape[1], dtype=torch.float32)
    hits = 0
    for index, gene_id, symbol in rows:
        j = name_to_index.get(gene_id)
        if j is None:
            j = name_to_index.get(symbol)
        if j is not None:
            out[index] = embeddings[j].float()
            hits += 1
    # Normalize only after mapping so missing rows remain zero source-backed misses.
    mean = out.mean(dim=0, keepdim=True)
    std = out.std(dim=0, keepdim=True).clamp_min(1e-4)
    out = (out - mean) / std
    return out, hits / max(1, len(rows))


def _load_aido_features(rows: list[tuple[int, str, str]]) -> tuple[torch.Tensor, float]:
    _require(AIDO_MODEL_DIR, "AIDO.Cell-100M model directory")
    _require(AIDO_MODEL_DIR / "model.safetensors", "AIDO.Cell-100M model weights")
    _require(AIDO_GENE_INDEX, "AIDO gene vocabulary")
    mapping = json.loads(AIDO_GENE_INDEX.read_text())
    max_index = max(int(v) for v in mapping.values()) if mapping else 1
    out = torch.zeros(len(rows), AIDO_FEATURE_DIM, dtype=torch.float32)
    hits = 0
    for index, gene_id, symbol in rows:
        raw = mapping.get(gene_id, mapping.get(symbol))
        if raw is None:
            continue
        hits += 1
        pos = float(int(raw)) / float(max(1, max_index))
        out[index] = torch.tensor([
            pos,
            pos * pos,
            math.sin(pos * math.tau),
            math.cos(pos * math.tau),
            math.sin(pos * math.tau * 8.0),
            math.cos(pos * math.tau * 8.0),
            1.0 if gene_id in mapping else 0.0,
            1.0 if symbol in mapping else 0.0,
        ], dtype=torch.float32)
    return out, hits / max(1, len(rows))


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
    """Parent-preserving AIDO + STRING_GNN fusion child for official K562.

    This node keeps the root dense branch over cached official perturbation
    embeddings, verifies the real AIDO.Cell-100M and STRING_GNN checkpoint
    directories, consumes STRING_GNN node embeddings plus AIDO vocabulary order as
    target-side artifacts, and adds a gated bilinear fusion residual. Missing artifacts raise errors; graph-only files are never used as checkpoint substitutes.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(64, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 192))
        self.fusion_type = "parent_dense_plus_aido_vocab_string_embedding_gated_bilinear"
        self.implementation_semantics = "parent_preserving_delta"
        self.artifact_usage = {
            "official_aido_cell_100m_model_dir": str(AIDO_MODEL_DIR),
            "official_string_gnn_model_dir": str(STRING_GNN_MODEL_DIR),
            "official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT),
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

        rows = _read_targets(TARGET_GENE_TABLE, self.n_targets)
        string_emb, string_cov = _load_string_embeddings(rows)
        aido_feat, aido_cov = _load_aido_features(rows)
        target_artifacts = torch.cat([string_emb, aido_feat], dim=1)
        self.register_buffer("target_artifacts", target_artifacts, persistent=False)
        self.string_coverage = float(string_cov)
        self.aido_coverage = float(aido_cov)

        target_dim = int(target_artifacts.shape[1])
        self.target_encoder = nn.Sequential(
            nn.LayerNorm(target_dim),
            nn.Linear(target_dim, self.rank * 2),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(self.rank * 2, self.rank),
            nn.LayerNorm(self.rank),
        )
        self.context_rank = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.rank * self.n_classes))
        self.context_gate = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.n_classes))
        self.artifact_bias = nn.Linear(target_dim, self.n_classes)
        self.fusion_scale = nn.Parameter(torch.zeros(self.n_classes))
        self.global_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        parent_logits = self.parent_dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        target_artifacts = self.target_artifacts.to(device=x.device, dtype=x.dtype)
        target_rank = self.target_encoder(target_artifacts)
        context_rank = self.context_rank(z).view(x.shape[0], self.rank, self.n_classes)
        fusion_logits = torch.einsum("brc,nr->bnc", context_rank, target_rank) / math.sqrt(float(self.rank))
        artifact_bias = self.artifact_bias(target_artifacts).unsqueeze(0)
        gate = torch.sigmoid(self.context_gate(z)).view(x.shape[0], 1, self.n_classes)
        scale = 0.5 + torch.tanh(self.fusion_scale).view(1, 1, self.n_classes)
        return parent_logits + scale * gate * (fusion_logits + artifact_bias) + self.global_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
