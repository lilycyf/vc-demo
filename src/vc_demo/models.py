from __future__ import annotations

from dataclasses import dataclass

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


MODEL_TYPES = {
    "mlp": PerturbationMLP,
    "residual_mlp": ResidualPerturbationMLP,
    "gated_mlp": GatedPerturbationMLP,
    "low_rank_mlp": LowRankPerturbationMLP,
}


def build_model(config: dict) -> nn.Module:
    model_cfg = dict(config.get("model", {}))
    spec = ModelSpec(**model_cfg)
    try:
        model_cls = MODEL_TYPES[spec.model_type]
    except KeyError as exc:
        raise ValueError(f"unknown model_type {spec.model_type!r}; choose from {sorted(MODEL_TYPES)}") from exc
    return model_cls(spec)
