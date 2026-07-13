from __future__ import annotations

from pathlib import Path

import torch
from torch import nn


class ScaledResidualLayer(nn.Module):
    def __init__(self, hidden: int, dropout: float, lr_scale: float) -> None:
        super().__init__()
        self.lr_scale = float(lr_scale)
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
    """Layer-annotated official K562 residual model for discriminative LR experiments."""

    def __init__(self, spec) -> None:
        super().__init__()
        target_path = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
        if not target_path.exists():
            raise FileNotFoundError(f"official target-gene contract is missing: {target_path}")
        rows = [line for line in target_path.read_text().splitlines() if line.strip()]
        if rows and rows[0].split("\t")[0].lower() == "target_index":
            rows = rows[1:]
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        if len(rows) != self.n_targets:
            raise ValueError(f"official target count {len(rows)} != n_targets {self.n_targets}")
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(3, int(spec.depth) + 1)
        self.layerwise_lr_groups = [
            {"name": "input_projection", "lr_scale": 0.35},
            {"name": "middle_layers", "lr_scale": 0.65},
            {"name": "prediction_head", "lr_scale": 1.0},
        ]
        self.input_projection = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout * 0.75),
        )
        scales = torch.linspace(0.45, 1.0, steps=depth).tolist()
        self.layers = nn.ModuleList([ScaledResidualLayer(hidden, dropout * 0.75, scale) for scale in scales])
        self.norm = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.calibration = nn.Sequential(nn.Linear(hidden, self.n_classes), nn.Tanh())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.input_projection(x)
        for layer in self.layers:
            z = layer(z)
        z = self.norm(z)
        logits = self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
        return logits + 0.05 * self.calibration(z).unsqueeze(1)
