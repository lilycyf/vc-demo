from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    """Cross-attention target-gene/perturbation program node.

    The request permits a learnable target token table. The model creates target
    tokens, derives compact perturbation/context tokens from the existing K562
    feature vector, and cross-attends target tokens to context before predicting
    per-target DEG class logits.
    """

    missing_artifact = "none_learnable_gene_tokens_used"
    fallback = "learnable_target_token_table"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.n_context = 4
        self.target_tokens = nn.Parameter(torch.empty(self.n_targets, hidden))
        nn.init.normal_(self.target_tokens, std=0.02)
        self.context = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden * self.n_context), nn.GELU(), nn.Dropout(dropout)
        )
        heads = 4 if hidden % 4 == 0 else 1
        self.attn = nn.MultiheadAttention(hidden, heads, dropout=dropout, batch_first=True)
        self.norm = nn.LayerNorm(hidden)
        self.ffn = nn.Sequential(nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden * 2, hidden))
        self.classifier = nn.Linear(hidden, self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b = x.shape[0]
        target = self.target_tokens.unsqueeze(0).expand(b, -1, -1)
        context = self.context(x).view(b, self.n_context, -1)
        attended, _ = self.attn(target, context, context, need_weights=False)
        z = self.norm(target + attended)
        z = self.norm(z + self.ffn(z))
        return self.classifier(z)
