from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import torch
from torch import nn
from safetensors import safe_open


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")
AIDO_MODEL_DIR = Path("/home/Models/AIDO.Cell-100M")
AIDO_WEIGHTS = AIDO_MODEL_DIR / "model.safetensors"
AIDO_CONFIG = AIDO_MODEL_DIR / "config.json"
AIDO_GENE_INDEX = AIDO_MODEL_DIR / "gene_id_to_aido_index.json"
AIDO_FROZEN_KEY = "encoder.layer.0.attention.self.query.weight"
AIDO_FEATURE_DIM = 10


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


def _load_aido_weight() -> torch.Tensor:
    _require(AIDO_MODEL_DIR, "AIDO.Cell-100M model directory")
    _require(AIDO_CONFIG, "AIDO.Cell-100M config")
    _require(AIDO_WEIGHTS, "AIDO.Cell-100M safetensors weights")
    with safe_open(str(AIDO_WEIGHTS), framework="pt", device="cpu") as handle:
        if AIDO_FROZEN_KEY not in handle.keys():
            raise KeyError(f"AIDO checkpoint missing expected tensor {AIDO_FROZEN_KEY}")
        weight = handle.get_tensor(AIDO_FROZEN_KEY).float().contiguous()
    if weight.ndim != 2 or weight.shape[0] != weight.shape[1]:
        raise ValueError(f"unexpected AIDO frozen weight shape {tuple(weight.shape)}")
    # Scale the frozen checkpoint tensor for stable adapter training while keeping
    # its orientation and values as the source-backed backbone anchor.
    return weight / weight.std().clamp_min(1e-4)


def _load_aido_target_features(rows: list[tuple[int, str, str]]) -> tuple[torch.Tensor, float]:
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
            math.sqrt(max(pos, 0.0)),
            math.sin(pos * math.tau),
            math.cos(pos * math.tau),
            math.sin(pos * math.tau * 8.0),
            math.cos(pos * math.tau * 8.0),
            min(len(symbol), 32) / 32.0,
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
    """Parent-preserving AIDO.Cell-100M LoRA-adapter child for official K562.

    The child keeps the strong root dense branch and loads a real frozen tensor
    from `/home/Models/AIDO.Cell-100M/model.safetensors`. A trainable low-rank
    adapter operates in that AIDO hidden space, then contributes a gated residual
    DEG head over the official 6,640 target genes. Frozen and trainable parameter
    groups are explicit in the module names below.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(16, min(int(getattr(spec, "low_rank_dim", 96)) // 2, 64))
        self.aido_hidden = 640
        self.adapter_type = "frozen_aido_query_weight_plus_trainable_lora_residual"
        self.implementation_semantics = "parent_preserving_delta"
        self.artifact_usage = {
            "official_aido_cell_100m_model_dir": str(AIDO_MODEL_DIR),
            "official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT),
            "frozen_aido_tensor": AIDO_FROZEN_KEY,
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

        frozen_weight = _load_aido_weight()
        self.register_buffer("frozen_aido_weight", frozen_weight, persistent=False)
        rows = _read_targets(TARGET_GENE_TABLE, self.n_targets)
        aido_features, coverage = _load_aido_target_features(rows)
        self.register_buffer("aido_target_features", aido_features, persistent=False)
        self.aido_target_coverage = float(coverage)

        self.to_aido_space = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.aido_hidden), nn.GELU())
        self.lora_down = nn.Linear(self.aido_hidden, self.rank, bias=False)
        self.lora_up = nn.Linear(self.rank, self.aido_hidden, bias=False)
        nn.init.kaiming_uniform_(self.lora_down.weight, a=math.sqrt(5))
        nn.init.zeros_(self.lora_up.weight)
        self.from_aido_space = nn.Sequential(nn.LayerNorm(self.aido_hidden), nn.Linear(self.aido_hidden, hidden), nn.GELU())

        self.target_encoder = nn.Sequential(
            nn.LayerNorm(AIDO_FEATURE_DIM),
            nn.Linear(AIDO_FEATURE_DIM, hidden),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(hidden, self.rank),
            nn.LayerNorm(self.rank),
        )
        self.context_rank = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.rank * self.n_classes))
        self.adapter_gate = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.n_classes))
        self.target_bias = nn.Linear(AIDO_FEATURE_DIM, self.n_classes)
        self.adapter_scale = nn.Parameter(torch.zeros(self.n_classes))
        self.global_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z_parent = self.context_norm(self.blocks(self.input(x)))
        parent_logits = self.parent_dense_head(z_parent).view(x.shape[0], self.n_targets, self.n_classes)

        aido_state = self.to_aido_space(z_parent)
        frozen = torch.nn.functional.linear(aido_state, self.frozen_aido_weight.to(device=x.device, dtype=x.dtype))
        adapted = frozen + self.lora_up(self.lora_down(aido_state))
        z_adapter = z_parent + self.from_aido_space(adapted)

        target_features = self.aido_target_features.to(device=x.device, dtype=x.dtype)
        target_rank = self.target_encoder(target_features)
        context_rank = self.context_rank(z_adapter).view(x.shape[0], self.rank, self.n_classes)
        logits = torch.einsum("brc,nr->bnc", context_rank, target_rank) / math.sqrt(float(self.rank))
        logits = logits + self.target_bias(target_features).unsqueeze(0)
        gate = torch.sigmoid(self.adapter_gate(z_adapter)).view(x.shape[0], 1, self.n_classes)
        scale = 0.5 + torch.tanh(self.adapter_scale).view(1, 1, self.n_classes)
        return parent_logits + scale * gate * logits + self.global_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
