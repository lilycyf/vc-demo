from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch import nn


def _load_target_genes(data_dir: str) -> list[str]:
    if not data_dir:
        raise ValueError("pathway pooling node requires spec.artifacts['data_dir']")
    path = Path(data_dir) / "train.npz"
    if not path.exists():
        raise FileNotFoundError(f"cannot load target genes from {path}")
    with np.load(path, allow_pickle=True) as z:
        return [str(x) for x in z["target_genes"].tolist()]


def _load_membership(path: str, target_genes: list[str]) -> torch.Tensor:
    artifact_path = Path(path)
    if not artifact_path.exists():
        raise FileNotFoundError(f"pathway membership artifact does not exist: {artifact_path}")
    with np.load(artifact_path, allow_pickle=True) as z:
        membership = np.asarray(z["membership"], dtype="float32")
        artifact_genes = [str(x) for x in z["target_genes"].tolist()]
    if artifact_genes != list(target_genes):
        raise ValueError("pathway membership target genes are not aligned to the current split target_genes")
    if membership.ndim != 2:
        raise ValueError(f"membership must be [n_targets, n_pathways], got {membership.shape}")
    row_sum = membership.sum(axis=1, keepdims=True)
    row_norm = np.divide(membership, np.maximum(row_sum, 1.0), dtype=np.float32)
    return torch.from_numpy(row_norm)


class GeneratedModel(nn.Module):
    artifact_usage = "pathway_membership_matrix"

    def __init__(self, spec) -> None:
        super().__init__()
        artifacts = dict(getattr(spec, "artifacts", {}) or {})
        target_genes = _load_target_genes(str(artifacts.get("data_dir", "")))
        if len(target_genes) != int(spec.n_targets):
            raise ValueError(f"target gene count {len(target_genes)} does not match n_targets {spec.n_targets}")
        membership_path = str(artifacts.get("pathway_membership_path", "data/artifacts/pathways/k562_target_pathway_membership.npz"))
        membership = _load_membership(membership_path, target_genes)
        hidden = int(spec.hidden_dim)
        n_pathways = int(membership.shape[1])
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.encoder = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(float(spec.dropout)),
            nn.Linear(hidden, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
        )
        self.pathway_head = nn.Linear(hidden, n_pathways * self.n_classes)
        self.direct_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.mix_logit = nn.Parameter(torch.tensor(0.0))
        self.register_buffer("target_pathway", membership, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        pathway_logits = self.pathway_head(z).view(x.shape[0], -1, self.n_classes)
        target_pathway = self.target_pathway.to(device=x.device, dtype=x.dtype)
        pooled = torch.einsum("np,bpc->bnc", target_pathway, pathway_logits)
        direct = self.direct_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        mix = torch.sigmoid(self.mix_logit)
        return mix * pooled + (1.0 - mix) * direct
