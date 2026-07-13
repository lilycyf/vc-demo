from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

import torch
from torch import nn
import torch.nn.functional as F


TARGET_GENE_TABLE = Path('data/cell_lines/official_k562_cls/target_genes.tsv')
OFFICIAL_TASK_ARTIFACT = Path('data/artifacts/official_k562/essential_deg_with_split.h5ad')
TARGET_FEATURE_DIM = 48


def _target_gene_features(path: Path, n_targets: int) -> torch.Tensor:
    if not path.exists():
        raise FileNotFoundError(f'official target-gene table is required: {path}')
    if not OFFICIAL_TASK_ARTIFACT.exists():
        raise FileNotFoundError(f'official DEG split artifact is required: {OFFICIAL_TASK_ARTIFACT}')
    rows: list[tuple[int, str, str]] = []
    with path.open(newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        for row in reader:
            rows.append((int(row['target_index']), str(row.get('gene_id', '')), str(row.get('symbol', ''))))
    rows.sort(key=lambda item: item[0])
    if len(rows) != int(n_targets) or [item[0] for item in rows] != list(range(int(n_targets))):
        raise ValueError('official target-gene table must match n_targets and target_index order')

    feats = torch.empty(int(n_targets), TARGET_FEATURE_DIM, dtype=torch.float32)
    denom = max(1, int(n_targets) - 1)
    for index, gene_id, symbol in rows:
        key = f'{index}|{gene_id}|{symbol}'.encode('utf-8')
        digest = hashlib.sha256(key).digest()
        pos = float(index) / float(denom)
        vals = [
            pos,
            math.sin(pos * math.tau),
            math.cos(pos * math.tau),
            min(len(symbol), 32) / 32.0,
            1.0 if gene_id.startswith('ENSG') else 0.0,
        ]
        while len(vals) < TARGET_FEATURE_DIM:
            vals.append(float(digest[(len(vals) - 5) % len(digest)]) / 127.5 - 1.0)
        feats[index] = torch.tensor(vals[:TARGET_FEATURE_DIM], dtype=torch.float32)
    return feats


class FeatureGroupDropout(nn.Module):
    '''Training-only feature group dropout for the official cached AIDO+GNN feature vector.'''

    def __init__(self, input_dim: int, group_count: int = 16, drop_prob: float = 0.08) -> None:
        super().__init__()
        self.input_dim = int(input_dim)
        self.group_count = max(1, min(int(group_count), self.input_dim))
        self.drop_prob = float(drop_prob)
        boundaries = torch.linspace(0, self.input_dim, self.group_count + 1, dtype=torch.long)
        group_ids = torch.empty(self.input_dim, dtype=torch.long)
        for group in range(self.group_count):
            start = int(boundaries[group].item())
            end = int(boundaries[group + 1].item())
            group_ids[start:end] = group
        self.register_buffer('group_ids', group_ids, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if (not self.training) or self.drop_prob <= 0.0:
            return x
        keep = torch.rand((x.shape[0], self.group_count), device=x.device, dtype=x.dtype) > self.drop_prob
        scale = 1.0 / max(1e-6, 1.0 - self.drop_prob)
        mask = keep[:, self.group_ids.to(device=x.device)].to(dtype=x.dtype) * scale
        return x * mask


class ResidualContextBlock(nn.Module):
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
    '''Official K562 gene/feature-dropout augmentation model.

    The model keeps the parent root's official cached AIDO+GNN feature interface,
    applies training-only grouped feature dropout for perturbation robustness, and
    predicts all official target genes with a target-aware low-rank head.
    '''

    def __init__(self, spec) -> None:
        super().__init__()
        self.input_dim = int(spec.input_dim)
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = max(64, min(int(getattr(spec, 'low_rank_dim', 128)), hidden, 192))
        dropout = float(spec.dropout)
        self.augmentation_name = 'official_gene_dropout_augmentation'
        self.feature_group_dropout_probability = 0.08
        self.feature_group_count = 16

        self.feature_augmentation = FeatureGroupDropout(
            self.input_dim,
            group_count=self.feature_group_count,
            drop_prob=self.feature_group_dropout_probability,
        )
        self.input = nn.Sequential(
            nn.LayerNorm(self.input_dim),
            nn.Linear(self.input_dim, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
        )
        self.blocks = nn.Sequential(*[ResidualContextBlock(hidden, dropout) for _ in range(max(1, int(spec.depth)))])
        self.context_norm = nn.LayerNorm(hidden)
        self.context_rank_logits = nn.Linear(hidden, self.rank * self.n_classes)
        self.context_gate = nn.Sequential(nn.Linear(hidden, self.rank), nn.Sigmoid())

        target_features = _target_gene_features(TARGET_GENE_TABLE, self.n_targets)
        self.register_buffer('target_features', target_features, persistent=False)
        self.target_projection = nn.Sequential(
            nn.LayerNorm(TARGET_FEATURE_DIM),
            nn.Linear(TARGET_FEATURE_DIM, self.rank),
            nn.GELU(),
            nn.Linear(self.rank, self.rank),
        )
        self.target_class_offset = nn.Linear(TARGET_FEATURE_DIM, self.n_classes)
        self.learned_target_factors = nn.Parameter(torch.empty(self.n_targets, self.rank))
        nn.init.normal_(self.learned_target_factors, mean=0.0, std=0.015)
        self.class_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        augmented = self.feature_augmentation(x)
        z = self.context_norm(self.blocks(self.input(augmented)))
        rank_logits = self.context_rank_logits(z).view(x.shape[0], self.rank, self.n_classes)
        rank_logits = rank_logits * self.context_gate(z).view(x.shape[0], self.rank, 1)

        target_features = self.target_features.to(device=x.device, dtype=x.dtype)
        target_rank = self.target_projection(target_features) + self.learned_target_factors.to(device=x.device, dtype=x.dtype)
        target_rank = F.layer_norm(target_rank, (self.rank,))
        logits = torch.einsum('brc,nr->bnc', rank_logits, target_rank)
        offsets = self.target_class_offset(target_features).unsqueeze(0)
        return logits + offsets + self.class_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
