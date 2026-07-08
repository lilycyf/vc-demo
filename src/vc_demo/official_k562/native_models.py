from __future__ import annotations

from pathlib import Path
from typing import Literal

import torch
from torch import nn

Variant = Literal[
    "target_gene_head",
    "string_gnn_attention",
    "aido_lora_adapter",
    "aido_string_fusion",
    "native_public_best_reimplementation",
]


def _require_path(path: str | Path, label: str) -> Path:
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"{label} artifact is required for official K562 native model: {resolved}")
    return resolved


class OfficialK562NativeModel(nn.Module):
    """Compact native implementations for official K562 paper-space nodes.

    These modules are executable proxies for search and repair loops. They consume
    the official K562 feature tensors produced by the dataset backend and verify
    required artifact paths. They do not claim numerical equivalence to the public
    static node unless the exact upstream checkpoints and training recipe are used.
    """

    def __init__(self, spec, variant: Variant = "target_gene_head") -> None:
        super().__init__()
        self.variant = variant
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 96)), hidden, 160))
        artifacts = dict(getattr(spec, "artifacts", {}) or {})
        self.artifact_status = {}
        if variant in {"aido_lora_adapter", "aido_string_fusion", "native_public_best_reimplementation"}:
            self.artifact_status["AIDO.Cell-100M"] = str(_require_path(artifacts.get("aido_model_dir", "/home/Models/AIDO.Cell-100M"), "AIDO.Cell-100M"))
        if variant in {"string_gnn_attention", "aido_string_fusion", "native_public_best_reimplementation"}:
            self.artifact_status["STRING_GNN"] = str(_require_path(artifacts.get("string_gnn_model_dir", "/home/Models/STRING_GNN"), "STRING_GNN"))
        self.input = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout))
        self.adapter_down = nn.Linear(hidden, max(8, hidden // 4))
        self.adapter_up = nn.Linear(max(8, hidden // 4), hidden)
        self.adapter_scale = nn.Parameter(torch.tensor(0.1))
        self.context2 = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden), nn.GELU(), nn.Dropout(dropout))
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.target_tokens = nn.Parameter(torch.empty(self.n_targets, hidden))
        nn.init.normal_(self.target_tokens, std=0.015)
        heads = 4 if hidden % 4 == 0 else 1
        self.attention = nn.MultiheadAttention(hidden, heads, batch_first=True, dropout=dropout)
        self.token_classifier = nn.Linear(hidden, self.n_classes)
        self.fusion_gate = nn.Sequential(nn.Linear(hidden, hidden), nn.Sigmoid())

    def _low_rank_logits(self, z: torch.Tensor) -> torch.Tensor:
        rank_logits = self.rank_head(z).view(z.shape[0], -1, self.n_classes)
        return torch.einsum("brc,nr->bnc", rank_logits, self.target_factors) + self.target_bias.unsqueeze(0)

    def _target_attention_logits(self, z: torch.Tensor) -> torch.Tensor:
        query = self.target_tokens.to(device=z.device, dtype=z.dtype).unsqueeze(0).expand(z.shape[0], -1, -1)
        key_value = torch.stack([z, self.context2(z)], dim=1)
        attended, _ = self.attention(query=query, key=key_value, value=key_value, need_weights=False)
        return self.token_classifier(query + attended)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.input(x)
        if self.variant in {"aido_lora_adapter", "aido_string_fusion", "native_public_best_reimplementation"}:
            adapter = self.adapter_up(torch.nn.functional.gelu(self.adapter_down(z)))
            z = z + self.adapter_scale * adapter
        if self.variant == "target_gene_head":
            return self._low_rank_logits(z)
        if self.variant == "aido_lora_adapter":
            return self._low_rank_logits(self.context2(z))
        if self.variant == "string_gnn_attention":
            return self._target_attention_logits(z)
        if self.variant == "aido_string_fusion":
            low_rank = self._low_rank_logits(z)
            attended = self._target_attention_logits(z)
            gate = self.fusion_gate(z).mean(dim=-1).view(-1, 1, 1)
            return gate * low_rank + (1.0 - gate) * attended
        if self.variant == "native_public_best_reimplementation":
            low_rank = self._low_rank_logits(self.context2(z))
            attended = self._target_attention_logits(z)
            return 0.5 * (low_rank + attended)
        raise ValueError(f"unknown official K562 native variant {self.variant!r}")
