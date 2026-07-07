from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """ESM2 bottleneck-adapter model.

    The run has real frozen ESM2 input features but no pretrained trainable
    encoder checkpoint. This model therefore trains small bottleneck adapters on
    top of the frozen input features; it must be reported as adapter-style
    training over ESM2 features, not as full pretrained-encoder fine-tuning.
    """

    artifact_name = "ESM2_D1280"
    artifact_embedding_dim = 1280
    adapter_status = "esm2_feature_adapter_no_pretrained_encoder_checkpoint"

    def __init__(self, spec):
        super().__init__()
        self.n_targets = spec.n_targets
        self.n_classes = spec.n_classes
        self.esm_dim = min(self.artifact_embedding_dim, max(int(spec.input_dim) - 1, 0))
        self.base_dim = int(spec.input_dim) - self.esm_dim
        hidden = int(spec.hidden_dim)
        bottleneck = max(32, hidden // 4)
        dropout = float(spec.dropout)
        self.base = nn.Sequential(nn.LayerNorm(self.base_dim), nn.Linear(self.base_dim, hidden), nn.GELU(), nn.Dropout(dropout))
        self.esm_adapter = nn.Sequential(
            nn.LayerNorm(self.esm_dim),
            nn.Linear(self.esm_dim, bottleneck),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(bottleneck, hidden),
        )
        self.adapter_gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.Sigmoid())
        self.post = nn.Sequential(nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.head = nn.Linear(hidden, spec.n_targets * spec.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base = x[:, : self.base_dim]
        esm = x[:, self.base_dim :]
        base_z = self.base(base)
        esm_z = self.esm_adapter(esm)
        gate = self.adapter_gate(torch.cat([base_z, esm_z], dim=-1))
        z = self.post(base_z + gate * esm_z)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
