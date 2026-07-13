from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Temperature-calibrated target logits for official K562 DEG labels.

    The calibration parameters are learned only through the training loop and
    validation Macro-F1 remains the reward. Test labels are not used for tuning.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        hidden = int(spec.hidden_dim)
        depth = max(1, int(spec.depth))
        dropout = float(spec.dropout)
        layers: list[nn.Module] = [
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        ]
        for _ in range(depth - 1):
            layers.extend([
                nn.Linear(hidden, hidden),
                nn.LayerNorm(hidden),
                nn.GELU(),
                nn.Dropout(dropout),
            ])
        self.encoder = nn.Sequential(*layers)
        self.raw_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.log_temperature = nn.Parameter(torch.zeros(self.n_classes))
        self.target_temperature_shift = nn.Parameter(torch.zeros(self.n_targets, 1))
        self.class_offset = nn.Parameter(torch.zeros(self.n_classes))
        self.target_offset = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        raw = self.raw_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        temperature = torch.nn.functional.softplus(self.log_temperature).view(1, 1, self.n_classes) + 0.5
        target_scale = torch.nn.functional.softplus(self.target_temperature_shift).view(1, self.n_targets, 1) + 0.5
        calibrated = raw / (temperature * target_scale)
        return calibrated + self.class_offset.view(1, 1, self.n_classes) + self.target_offset.unsqueeze(0)
