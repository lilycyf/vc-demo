from __future__ import annotations

from pathlib import Path
from typing import Literal

import csv

import torch
from torch import nn

Variant = Literal[
    "target_gene_head",
    "string_gnn_attention",
    "aido_lora_adapter",
    "aido_string_fusion",
    "aido_string_cross_attention",
    "string_neighborhood_attention",
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
        if variant in {"aido_lora_adapter", "aido_string_fusion", "aido_string_cross_attention", "native_public_best_reimplementation"}:
            self.artifact_status["AIDO.Cell-100M"] = str(_require_path(artifacts.get("aido_model_dir", "/home/Models/AIDO.Cell-100M"), "AIDO.Cell-100M"))
        if variant in {"string_gnn_attention", "aido_string_fusion", "aido_string_cross_attention", "string_neighborhood_attention", "native_public_best_reimplementation"}:
            self.artifact_status["STRING_GNN"] = str(_require_path(artifacts.get("string_gnn_model_dir", "/home/Models/STRING_GNN"), "STRING_GNN"))
        graph_path = artifacts.get("string_graph_path", "data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
        if variant in {"string_gnn_attention", "aido_string_fusion", "aido_string_cross_attention", "string_neighborhood_attention", "native_public_best_reimplementation"}:
            self.artifact_status["STRING_graph"] = str(_require_path(graph_path, "official STRING keep20 graph"))
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
        self.cross_query = nn.Linear(hidden, hidden)
        self.cross_key_value = nn.Linear(hidden, hidden)
        self.neighborhood_k = 2
        self.attention_heads = heads
        if variant == "string_neighborhood_attention":
            prior = self._load_string_target_prior(artifacts.get("string_graph_path", graph_path))
        else:
            prior = torch.zeros(self.n_targets, 1)
        self.register_buffer("string_target_prior", prior, persistent=False)


    def _load_string_target_prior(self, graph_path: str | Path) -> torch.Tensor:
        """Load a real STRING graph-derived target prior without altering target order."""
        target_path = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
        _require_path(target_path, "official K562 target gene order")
        graph_path = _require_path(graph_path, "official STRING keep20 graph")
        targets: list[str] = []
        with target_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                targets.append(row["gene_id"])
        target_set = set(targets)
        degree = {gene: 0.0 for gene in targets}
        edge_count = 0
        with graph_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                a = row.get("protein1", "")
                b = row.get("protein2", "")
                try:
                    score = float(row.get("combined_score", 0.0)) / 1000.0
                except ValueError:
                    score = 0.0
                touched = False
                if a in target_set:
                    degree[a] += score
                    touched = True
                if b in target_set:
                    degree[b] += score
                    touched = True
                if touched:
                    edge_count += 1
        values = torch.tensor([degree[gene] for gene in targets], dtype=torch.float32).view(-1, 1)
        if values.numel() != self.n_targets:
            raise ValueError(f"STRING graph prior target count {values.numel()} does not match spec.n_targets {self.n_targets}")
        if edge_count == 0:
            raise ValueError(f"STRING graph artifact {graph_path} has no edges touching official target genes")
        values = torch.log1p(values)
        values = (values - values.mean()) / values.std().clamp_min(1e-6)
        self.artifact_status["STRING_graph_target_edges"] = str(edge_count)
        return values

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
        if self.variant == "string_neighborhood_attention":
            logits = self._target_attention_logits(z)
            return logits + self.string_target_prior.to(device=z.device, dtype=z.dtype).unsqueeze(0)
        if self.variant == "aido_string_cross_attention":
            query = self.cross_query(z).unsqueeze(1)
            key_value = self.cross_key_value(self.target_tokens.to(device=z.device, dtype=z.dtype)).unsqueeze(0).expand(z.shape[0], -1, -1)
            cross, _ = self.attention(query=query, key=key_value, value=key_value, need_weights=False)
            z_cross = z + cross.squeeze(1)
            low_rank = self._low_rank_logits(z_cross)
            attended = self._target_attention_logits(z_cross)
            gate = self.fusion_gate(z_cross).mean(dim=-1).view(-1, 1, 1)
            return gate * attended + (1.0 - gate) * low_rank
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
