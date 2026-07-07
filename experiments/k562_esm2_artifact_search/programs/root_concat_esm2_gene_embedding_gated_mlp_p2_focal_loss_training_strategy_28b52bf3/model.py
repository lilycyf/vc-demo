from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Class-imbalance-aware head fallback for a focal-loss proposal.

    The current harness trains with its standard loss, so this node cannot fully
    implement focal loss inside model.py. It uses the real ESM2-augmented input
    and adds a calibrated per-class bias plus a compact residual head. Report as
    focal_loss_unavailable_model_head_fallback, not a true focal-loss run.
    """

    artifact_name = "ESM2_D1280"
    proposal_status = "focal_loss_unavailable_model_head_fallback"

    def __init__(self, spec):
        super().__init__()
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.encoder = nn.Sequential(
            nn.LayerNorm(int(spec.input_dim)),
            nn.Linear(int(spec.input_dim), hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.head = nn.Linear(hidden, spec.n_targets * spec.n_classes)
        # Mild prior toward unchanged class for the 5/90/5 DEG label balance.
        self.class_bias = nn.Parameter(torch.tensor([-0.5, 1.0, -0.5], dtype=torch.float32))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        logits = self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
        return logits + self.class_bias.view(1, 1, self.n_classes)
