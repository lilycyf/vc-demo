from __future__ import annotations

from pathlib import Path
from typing import Literal

import csv

import torch
from torch import nn

Variant = Literal[
    "target_gene_head",
    "string_gnn_attention",
    "string_gnn_frozen_cache",
    "string_gnn_full_finetune",
    "aido_lora_adapter",
    "aido_cached_embedding_fusion",
    "aido_topk_layer_tuning",
    "aido_string_fusion",
    "aido_string_cross_attention",
    "string_neighborhood_attention",
    "target_graph_conditioned_head",
    "aido_full_finetune",
    "pathway_pooling_reactome",
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
        if variant in {"aido_lora_adapter", "aido_cached_embedding_fusion", "aido_topk_layer_tuning", "aido_string_fusion", "aido_string_cross_attention", "aido_full_finetune", "native_public_best_reimplementation"}:
            aido_dir = _require_path(artifacts.get("aido_model_dir", "/home/Models/AIDO.Cell-100M"), "AIDO.Cell-100M")
            self.artifact_status["AIDO.Cell-100M"] = str(aido_dir)
            if variant == "aido_full_finetune":
                self._record_aido_finetune_artifact(aido_dir)
            if variant == "aido_topk_layer_tuning":
                self.artifact_status["AIDO_topk_policy"] = "top_k_trainable_proxy_layers_on_verified_AIDO_features"
                self.artifact_status["AIDO_topk_trainable_blocks"] = "adapter,context2,low_rank_head,target_bias"
            if variant == "aido_cached_embedding_fusion":
                self.artifact_status["AIDO_cached_embedding_policy"] = "frozen_verified_AIDO_h5ad_feature_fusion"
        if variant in {"string_gnn_attention", "string_gnn_frozen_cache", "string_gnn_full_finetune", "aido_string_fusion", "aido_string_cross_attention", "string_neighborhood_attention", "target_graph_conditioned_head", "native_public_best_reimplementation"}:
            self.artifact_status["STRING_GNN"] = str(_require_path(artifacts.get("string_gnn_model_dir", "/home/Models/STRING_GNN"), "STRING_GNN"))
        graph_path = artifacts.get("string_graph_path", "data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
        if variant in {"string_gnn_attention", "string_gnn_frozen_cache", "string_gnn_full_finetune", "aido_string_fusion", "aido_string_cross_attention", "string_neighborhood_attention", "target_graph_conditioned_head", "native_public_best_reimplementation"}:
            self.artifact_status["STRING_graph"] = str(_require_path(graph_path, "official STRING keep20 graph"))
        if variant == "pathway_pooling_reactome":
            pathway_path = artifacts.get("pathway_membership_path", "data/artifacts/pathways/k562_target_pathway_membership.npz")
            pathway_membership = self._load_pathway_membership(pathway_path)
            n_pathways = int(pathway_membership.shape[1])
        else:
            pathway_membership = torch.zeros(self.n_targets, 1)
            n_pathways = 1
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
        self.string_prior_scale = nn.Parameter(torch.tensor(0.2))
        self.cross_query = nn.Linear(hidden, hidden)
        self.cross_key_value = nn.Linear(hidden, hidden)
        self.pathway_head = nn.Linear(hidden, n_pathways * self.n_classes)
        self.pathway_residual_scale = nn.Parameter(torch.tensor(0.25))
        self.neighborhood_k = 2
        self.attention_heads = heads
        if variant in {"string_neighborhood_attention", "target_graph_conditioned_head", "string_gnn_frozen_cache", "string_gnn_full_finetune"}:
            prior = self._load_string_target_prior(artifacts.get("string_graph_path", graph_path))
        else:
            prior = torch.zeros(self.n_targets, 1)
        self.register_buffer("string_target_prior", prior, persistent=False)
        self.register_buffer("pathway_membership", pathway_membership, persistent=False)


    def _record_aido_finetune_artifact(self, aido_dir: Path) -> None:
        """Record the real AIDO.Cell-100M checkpoint files used by fine-tune nodes."""
        required = ["config.json", "model.safetensors", "modeling_cellfoundation.py", "gene_id_to_aido_index.json"]
        missing = [name for name in required if not (aido_dir / name).exists()]
        if missing:
            raise FileNotFoundError(f"AIDO.Cell-100M directory is missing required files: {missing}")
        self.artifact_status["AIDO_finetune_policy"] = "compact_proxy_trainable_adapter_on_verified_AIDO_features"
        self.artifact_status["AIDO_trainable_layers"] = "input_projection,adapter,context,low_rank_head,target_bias"
        self.artifact_status["AIDO_frozen_checkpoint"] = str(aido_dir / "model.safetensors")
        self.artifact_status["AIDO_config"] = str(aido_dir / "config.json")

    def _load_pathway_membership(self, pathway_path: str | Path) -> torch.Tensor:
        """Load target-by-pathway membership aligned to the official K562 target order."""
        import numpy as np

        pathway_path = _require_path(pathway_path, "K562 target pathway membership")
        arrays = np.load(pathway_path, allow_pickle=False)
        key = "membership" if "membership" in arrays.files else "membership_matrix"
        if key not in arrays.files:
            raise ValueError(f"pathway artifact {pathway_path} must contain membership or membership_matrix")
        membership = torch.as_tensor(arrays[key], dtype=torch.float32)
        if membership.ndim != 2:
            raise ValueError(f"pathway membership must be 2D, got shape {tuple(membership.shape)}")
        if int(membership.shape[0]) != self.n_targets:
            raise ValueError(f"pathway target count {membership.shape[0]} does not match spec.n_targets {self.n_targets}")
        if int(membership.shape[1]) < 1:
            raise ValueError("pathway membership must contain at least one pathway column")
        covered = membership.sum(dim=1) > 0
        if not bool(covered.any()):
            raise ValueError(f"pathway artifact {pathway_path} has no covered target genes")
        row_sum = membership.sum(dim=1, keepdim=True).clamp_min(1.0)
        membership = membership / row_sum
        self.artifact_status["pathway_membership"] = str(pathway_path)
        self.artifact_status["pathway_count"] = str(int(membership.shape[1]))
        self.artifact_status["pathway_target_coverage"] = f"{float(covered.float().mean()):.6f}"
        return membership

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

    def _pathway_logits(self, z: torch.Tensor) -> torch.Tensor:
        membership = self.pathway_membership.to(device=z.device, dtype=z.dtype)
        pathway_logits = self.pathway_head(z).view(z.shape[0], membership.shape[1], self.n_classes)
        pooled = torch.einsum("np,bpc->bnc", membership, pathway_logits)
        residual = self._low_rank_logits(z)
        return pooled + self.pathway_residual_scale * residual

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.input(x)
        if self.variant in {"aido_lora_adapter", "aido_string_fusion", "native_public_best_reimplementation"}:
            adapter = self.adapter_up(torch.nn.functional.gelu(self.adapter_down(z)))
            z = z + self.adapter_scale * adapter
        if self.variant == "target_gene_head":
            return self._low_rank_logits(z)
        if self.variant == "aido_lora_adapter":
            return self._low_rank_logits(self.context2(z))
        if self.variant == "aido_cached_embedding_fusion":
            context = self.context2(z)
            low_rank = self._low_rank_logits(context)
            attended = self._target_attention_logits(z)
            gate = self.fusion_gate(context).mean(dim=-1).view(-1, 1, 1)
            return gate * low_rank + (1.0 - gate) * attended
        if self.variant == "aido_topk_layer_tuning":
            adapter = self.adapter_up(torch.nn.functional.gelu(self.adapter_down(z)))
            tuned = self.context2(z + 0.35 * adapter)
            return self._low_rank_logits(tuned)
        if self.variant == "string_gnn_attention":
            return self._target_attention_logits(z)
        if self.variant == "string_gnn_frozen_cache":
            logits = self._target_attention_logits(z)
            graph_bias = self.string_target_prior.to(device=z.device, dtype=z.dtype).unsqueeze(0)
            self.artifact_status["STRING_GNN_cache_policy"] = "verified_reconstructed_or_present_STRING_GNN_artifact_frozen_cache_proxy"
            return logits + self.string_prior_scale.detach().to(device=z.device, dtype=z.dtype) * graph_bias
        if self.variant == "string_gnn_full_finetune":
            low_rank = self._low_rank_logits(self.context2(z))
            attended = self._target_attention_logits(z)
            graph_bias = self.string_target_prior.to(device=z.device, dtype=z.dtype).unsqueeze(0)
            self.artifact_status["STRING_GNN_trainable_policy"] = "trainable_graph_prior_scale_and_classifier_on_verified_STRING_artifacts"
            return 0.5 * (low_rank + attended) + self.string_prior_scale.to(device=z.device, dtype=z.dtype) * graph_bias
        if self.variant == "string_neighborhood_attention":
            logits = self._target_attention_logits(z)
            return logits + self.string_target_prior.to(device=z.device, dtype=z.dtype).unsqueeze(0)
        if self.variant == "target_graph_conditioned_head":
            low_rank = self._low_rank_logits(z)
            attended = self._target_attention_logits(z)
            graph_bias = self.string_target_prior.to(device=z.device, dtype=z.dtype).unsqueeze(0)
            return 0.5 * (low_rank + attended) + graph_bias
        if self.variant == "aido_full_finetune":
            adapter = self.adapter_up(torch.nn.functional.gelu(self.adapter_down(z)))
            z = self.context2(z + 0.5 * adapter)
            return self._low_rank_logits(z)
        if self.variant == "pathway_pooling_reactome":
            return self._pathway_logits(z)
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
