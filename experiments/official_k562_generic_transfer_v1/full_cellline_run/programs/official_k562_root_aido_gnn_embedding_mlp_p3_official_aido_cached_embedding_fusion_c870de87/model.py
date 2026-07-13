from __future__ import annotations

from pathlib import Path

import torch
from torch import nn


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
    """AIDO cached embedding fusion over source-backed official K562 features."""

    def __init__(self, spec) -> None:
        super().__init__()
        model_dir = Path("/home/Models/AIDO.Cell-100M")
        if not model_dir.exists():
            raise FileNotFoundError(f"required AIDO.Cell-100M model directory is missing: {model_dir}")
        input_dim = int(spec.input_dim)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.aido_dim = min(640, input_dim)
        self.aux_dim = max(0, input_dim - self.aido_dim)
        rank = max(48, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 160))
        self.rank = rank

        self.aido_encoder = nn.Sequential(
            nn.Linear(self.aido_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        if self.aux_dim > 0:
            self.aux_encoder = nn.Sequential(
                nn.Linear(self.aux_dim, hidden),
                nn.LayerNorm(hidden),
                nn.GELU(),
                nn.Dropout(dropout),
            )
            self.fusion_gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.Sigmoid())
            fused_dim = hidden * 2
        else:
            self.aux_encoder = None
            self.fusion_gate = None
            fused_dim = hidden
        self.fusion = nn.Sequential(
            nn.Linear(fused_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            *[ResidualBlock(hidden, dropout) for _ in range(depth)],
            nn.LayerNorm(hidden),
        )
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.direct_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        nn.init.normal_(self.target_factors, mean=0.0, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        aido = self.aido_encoder(x[:, : self.aido_dim])
        if self.aux_encoder is not None:
            aux = self.aux_encoder(x[:, self.aido_dim :])
            gate = self.fusion_gate(torch.cat([aido, aux], dim=-1))
            z = torch.cat([aido * gate, aux * (1.0 - gate)], dim=-1)
        else:
            z = aido
        z = self.fusion(z)
        rank_logits = self.rank_head(z).view(x.shape[0], self.rank, self.n_classes)
        factorized = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors)
        direct = self.direct_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        return 0.5 * direct + factorized + self.target_bias.unsqueeze(0)
