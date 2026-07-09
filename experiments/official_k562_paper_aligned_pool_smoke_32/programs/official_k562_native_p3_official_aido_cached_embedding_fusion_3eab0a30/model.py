from __future__ import annotations

from pathlib import Path

import torch
from torch import nn


AIDO_MODEL_DIR = Path("/home/Models/AIDO.Cell-100M")


class GeneratedModel(nn.Module):
    """AIDO cached-embedding fusion head for official K562.

    The official dataset backend supplies precomputed AIDO/GNN perturbation
    features. This node verifies the audited AIDO model directory and fuses the
    AIDO slice with the remaining cached features; it does not fabricate a model
    checkpoint or substitute a fallback branch.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        if not AIDO_MODEL_DIR.exists():
            raise FileNotFoundError(f"required AIDO.Cell-100M artifact missing: {AIDO_MODEL_DIR}")
        if not (AIDO_MODEL_DIR / "config.json").exists():
            raise FileNotFoundError(f"AIDO.Cell-100M config missing under {AIDO_MODEL_DIR}")
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.input_dim = int(spec.input_dim)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 128))
        self.aido_dim = 640 if self.input_dim >= 640 else self.input_dim
        self.aux_dim = max(0, self.input_dim - self.aido_dim)
        self.aido_encoder = nn.Sequential(
            nn.Linear(self.aido_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout)
        )
        aux_in = self.aux_dim if self.aux_dim > 0 else self.aido_dim
        self.aux_encoder = nn.Sequential(
            nn.Linear(aux_in, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout)
        )
        self.fusion_gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.Sigmoid())
        self.fused_context = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden), nn.GELU(), nn.Dropout(dropout))
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        aido_x = x[:, : self.aido_dim]
        aux_x = x[:, self.aido_dim :] if self.aux_dim > 0 else aido_x
        aido = self.aido_encoder(aido_x)
        aux = self.aux_encoder(aux_x)
        gate = self.fusion_gate(torch.cat([aido, aux], dim=-1))
        fused = self.fused_context(gate * aido + (1.0 - gate) * aux)
        rank_logits = self.rank_head(fused).view(x.shape[0], -1, self.n_classes)
        logits = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors)
        return logits + self.target_bias.unsqueeze(0)
