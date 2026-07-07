from __future__ import annotations

import importlib.util
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class ModelSpec:
    input_dim: int = 128
    hidden_dim: int = 256
    n_targets: int = 664
    n_classes: int = 3
    dropout: float = 0.1
    depth: int = 2
    model_type: str = "mlp"
    low_rank_dim: int = 64
    artifact_manifest_path: str = ""
    source_feature_dim: int = 0
    perturbation_embedding_dim: int = 0
    target_gene_embedding_dim: int = 0
    artifacts: dict[str, Any] = field(default_factory=dict)


def mlp_block(in_dim: int, out_dim: int, dropout: float) -> list[nn.Module]:
    return [nn.Linear(in_dim, out_dim), nn.LayerNorm(out_dim), nn.GELU(), nn.Dropout(dropout)]


class PerturbationMLP(nn.Module):
    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        dim = spec.input_dim
        for _ in range(spec.depth):
            layers.extend(mlp_block(dim, spec.hidden_dim, spec.dropout))
            dim = spec.hidden_dim
        self.encoder = nn.Sequential(*layers)
        self.head = nn.Linear(dim, spec.n_targets * spec.n_classes)
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)


class ResidualBlock(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class ResidualPerturbationMLP(nn.Module):
    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        self.input = nn.Sequential(nn.Linear(spec.input_dim, spec.hidden_dim), nn.GELU())
        self.blocks = nn.Sequential(*[ResidualBlock(spec.hidden_dim, spec.dropout) for _ in range(spec.depth)])
        self.norm = nn.LayerNorm(spec.hidden_dim)
        self.head = nn.Linear(spec.hidden_dim, spec.n_targets * spec.n_classes)
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.norm(self.blocks(self.input(x)))
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)


class GatedPerturbationMLP(nn.Module):
    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        trunk: list[nn.Module] = []
        dim = spec.input_dim
        for _ in range(spec.depth):
            trunk.extend(mlp_block(dim, spec.hidden_dim, spec.dropout))
            dim = spec.hidden_dim
        self.trunk = nn.Sequential(*trunk)
        self.gate = nn.Sequential(nn.Linear(spec.input_dim, spec.hidden_dim), nn.Sigmoid())
        self.head = nn.Linear(spec.hidden_dim, spec.n_targets * spec.n_classes)
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.trunk(x) * self.gate(x)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)


class LowRankPerturbationMLP(nn.Module):
    """Factorized target-gene head.

    Instead of predicting all target-gene logits with one dense layer, this model
    predicts rank-specific class logits and combines them with learned target-gene
    factors. This is a larger architectural move than tuning width/dropout, and it
    mimics the idea of changing the model head/fusion strategy per search node.
    """

    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        dim = spec.input_dim
        for _ in range(spec.depth):
            layers.extend(mlp_block(dim, spec.hidden_dim, spec.dropout))
            dim = spec.hidden_dim
        self.encoder = nn.Sequential(*layers)
        self.rank = max(4, min(spec.low_rank_dim, spec.hidden_dim))
        self.class_head = nn.Linear(dim, self.rank * spec.n_classes)
        self.gene_factors = nn.Parameter(torch.empty(spec.n_targets, self.rank))
        nn.init.normal_(self.gene_factors, std=0.02)
        self.bias = nn.Parameter(torch.zeros(spec.n_targets, spec.n_classes))
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        rank_logits = self.class_head(z).view(x.shape[0], self.rank, self.n_classes)
        logits = torch.einsum("brc,nr->bnc", rank_logits, self.gene_factors)
        return logits + self.bias.unsqueeze(0)



def _load_npz_array(path: str | Path, key: str) -> torch.Tensor:
    if not path:
        raise ValueError(f"artifact key {key!r} requires a non-empty path")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"artifact array path does not exist: {path}")
    with np.load(path) as data:
        if key not in data.files:
            raise KeyError(f"artifact array {path} does not contain key {key!r}; available={data.files}")
        return torch.from_numpy(np.asarray(data[key], dtype="float32"))


def load_artifact_manifest(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"artifact manifest does not exist: {path}")
    with path.open() as f:
        manifest = json.load(f)
    manifest.setdefault("manifest_path", str(path))
    return manifest


class TargetAwareBilinearFusion(nn.Module):
    """Use frozen target-gene artifacts as the prediction head geometry.

    The input vector still carries perturbation/cell-line features, including any
    perturbation-gene embedding already appended by the dataset builder. The head
    separately loads an aligned target-gene embedding table and scores each target
    through a factorized bilinear interaction. This is intentionally closer to a
    paper-level biological-prior node than a dense `[hidden -> all targets]` head.
    """

    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        manifest_path = spec.artifact_manifest_path or spec.artifacts.get("artifact_manifest_path", "")
        if not manifest_path:
            raise ValueError("target_aware_bilinear requires model.artifact_manifest_path")
        manifest = load_artifact_manifest(manifest_path)
        target_info = manifest.get("target_gene_embeddings", {})
        target_embeddings = _load_npz_array(target_info.get("path", ""), str(target_info.get("key", "target_gene_embeddings")))
        if target_embeddings.ndim != 2:
            raise ValueError(f"target embeddings must be 2-D [n_targets, dim], got {tuple(target_embeddings.shape)}")
        if int(target_embeddings.shape[0]) != int(spec.n_targets):
            raise ValueError(f"target embedding rows {target_embeddings.shape[0]} do not match n_targets {spec.n_targets}")

        hidden = int(spec.hidden_dim)
        rank = max(16, min(int(spec.low_rank_dim), hidden, 128))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        layers: list[nn.Module] = [nn.Linear(spec.input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(spec.dropout)]
        for _ in range(max(0, int(spec.depth) - 1)):
            layers.extend(mlp_block(hidden, hidden, spec.dropout))
        self.encoder = nn.Sequential(*layers)
        self.context_rank = nn.Linear(hidden, rank * self.n_classes)
        self.target_projection = nn.Sequential(
            nn.LayerNorm(int(target_embeddings.shape[1])),
            nn.Linear(int(target_embeddings.shape[1]), rank),
        )
        self.target_residual = nn.Linear(int(target_embeddings.shape[1]), self.n_classes)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.register_buffer("target_embeddings", target_embeddings, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        context = self.encoder(x)
        context_rank = self.context_rank(context).view(x.shape[0], -1, self.n_classes)
        target_embeddings = self.target_embeddings.to(device=x.device, dtype=x.dtype)
        target_rank = self.target_projection(target_embeddings)
        logits = torch.einsum("brc,nr->bnc", context_rank, target_rank)
        residual = self.target_residual(target_embeddings).unsqueeze(0)
        return logits + residual + self.bias.unsqueeze(0)


MODEL_TYPES = {
    "mlp": PerturbationMLP,
    "residual_mlp": ResidualPerturbationMLP,
    "gated_mlp": GatedPerturbationMLP,
    "low_rank_mlp": LowRankPerturbationMLP,
    "target_aware_bilinear": TargetAwareBilinearFusion,
}


def _model_spec_from_config(model_cfg: dict) -> ModelSpec:
    allowed = set(ModelSpec.__dataclass_fields__)
    return ModelSpec(**{key: value for key, value in model_cfg.items() if key in allowed})


def _load_custom_program_model(model_cfg: dict, spec: ModelSpec) -> nn.Module:
    try:
        model_path = Path(str(model_cfg["custom_model_path"]))
    except KeyError as exc:
        raise ValueError("custom_program model requires model.custom_model_path") from exc
    class_name = str(model_cfg.get("custom_model_class", "GeneratedModel"))
    if not model_path.exists():
        raise FileNotFoundError(f"custom program model file does not exist: {model_path}")

    digest = hashlib.sha1(str(model_path.resolve()).encode("utf-8")).hexdigest()[:12]
    module_name = f"vc_demo_dynamic_model_{digest}"
    module_spec = importlib.util.spec_from_file_location(module_name, model_path)
    if module_spec is None or module_spec.loader is None:
        raise ImportError(f"cannot import custom model from {model_path}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    try:
        model_cls = getattr(module, class_name)
    except AttributeError as exc:
        raise AttributeError(f"custom model {model_path} does not define class {class_name!r}") from exc
    return model_cls(spec)


def build_model(config: dict) -> nn.Module:
    model_cfg = dict(config.get("model", {}))
    model_type = str(model_cfg.get("model_type", "mlp"))
    spec = _model_spec_from_config(model_cfg)
    if model_type == "custom_program":
        return _load_custom_program_model(model_cfg, spec)
    try:
        model_cls = MODEL_TYPES[spec.model_type]
    except KeyError as exc:
        choices = sorted([*MODEL_TYPES, "custom_program"])
        raise ValueError(f"unknown model_type {spec.model_type!r}; choose from {choices}") from exc
    return model_cls(spec)
