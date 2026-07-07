from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Calibration-aware DEG head preserving Macro-F1 reward semantics."""

    calibration_note = "learns temperature-like logit scale during training; no test-threshold tuning"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
        )
        self.mean_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.log_scale = nn.Parameter(torch.zeros(self.n_targets, 1))
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        logits = self.mean_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        scale = torch.nn.functional.softplus(self.log_scale).unsqueeze(0) + 0.5
        return logits / scale + self.bias.unsqueeze(0)
