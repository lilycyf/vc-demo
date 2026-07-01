from __future__ import annotations

from typing import Any


MODEL_BLUEPRINTS: list[dict[str, Any]] = [
    {"id": "dual_path_gated_low_rank", "status": "implemented", "category": "architecture_program", "role": "Dual encoder with input-conditioned gating and a low-rank target-gene head.", "requires": ["tabular_features"], "implementation_notes": "Already implemented as a generated node-local PyTorch model.", "acceptance": ["Defines GeneratedModel(spec)", "Forward returns [batch, n_targets, n_classes] logits"]},
    {"id": "mixture_of_experts", "status": "implemented", "category": "architecture_program", "role": "Compact router over several MLP experts for perturbation feature regimes.", "requires": ["tabular_features"], "implementation_notes": "Already implemented as a generated node-local PyTorch model.", "acceptance": ["Defines GeneratedModel(spec)", "Forward returns [batch, n_targets, n_classes] logits"]},
    {"id": "film_conditioned_residual", "status": "planned", "category": "architecture_program", "role": "Residual blocks modulated by the original perturbation vector.", "requires": ["tabular_features"], "implementation_notes": "Implement FiLM-style residual blocks. Use the input vector to generate gamma/beta modulation for hidden residual layers.", "acceptance": ["No external data required", "Defines GeneratedModel(spec)", "Uses spec.input_dim, hidden_dim, depth, dropout, n_targets, n_classes", "Forward returns [batch, n_targets, n_classes] logits"]},
    {"id": "target_factor_router", "status": "planned", "category": "architecture_program", "role": "Route-conditioned low-rank target-gene factor head.", "requires": ["tabular_features"], "implementation_notes": "Implement a compact encoder, a route/context projection, and target-gene factors that combine with rank logits.", "acceptance": ["No external data required", "Defines GeneratedModel(spec)", "Keeps parameter count modest", "Forward returns [batch, n_targets, n_classes] logits"]},
    {"id": "gene_embedding_adapter", "status": "planned", "category": "biological_prior", "role": "Learn or load gene embeddings and condition target heads on gene identity.", "requires": ["gene_ids"], "implementation_notes": "Requires a target-gene id list or embedding table before it can be executable.", "acceptance": ["Documents required gene metadata", "Does not alter train/val/test split"]},
    {"id": "ppi_graph_message_passing", "status": "planned", "category": "biological_prior", "role": "Use a STRING/PPI-like graph prior for target-gene message passing.", "requires": ["gene_graph"], "implementation_notes": "Requires graph edges aligned to target genes. If graph is absent, generate a request rather than fake a graph.", "acceptance": ["Documents graph source", "Defines how missing genes are handled"]},
    {"id": "foundation_embedding_fusion", "status": "planned", "category": "foundation_model_fusion", "role": "Fuse frozen biological foundation-model embeddings with perturbation features.", "requires": ["external_embeddings"], "implementation_notes": "Requires an embedding file or loader. Do not download large embeddings unless user approves.", "acceptance": ["Documents embedding source", "Keeps embedding frozen unless task allows fine-tuning"]},
    {"id": "cross_attention_gene_perturbation", "status": "planned", "category": "fusion", "role": "Cross-attend target-gene tokens against perturbation/context tokens.", "requires": ["gene_tokens"], "implementation_notes": "Requires token-level gene representation or a learnable target token table.", "acceptance": ["Defines attention dimensions", "Forward returns target-level class logits"]},
    {"id": "selective_adapter_finetune", "status": "planned", "category": "fine_tuning", "role": "Freeze a base encoder and train small adapters/LoRA-style modules.", "requires": ["pretrained_encoder"], "implementation_notes": "Requires a pretrained encoder. Generate a request unless the encoder is already present in the repo.", "acceptance": ["Documents frozen/trainable parameter groups", "Does not silently train a huge model"]},
    {"id": "multi_task_cellline_conditioning", "status": "planned", "category": "multi_cellline", "role": "Condition predictions on cell-line identity for multi-cell-line experiments.", "requires": ["multiple_cell_lines"], "implementation_notes": "Requires multiple cell lines and a cell-line id field; not suitable for a one-cell-line run unless used as a no-op ablation.", "acceptance": ["Documents cell-line metadata", "Preserves per-cell-line splits"]},
]


def blueprints(status: str | None = None) -> list[dict[str, Any]]:
    if status is None:
        return list(MODEL_BLUEPRINTS)
    return [item for item in MODEL_BLUEPRINTS if item["status"] == status]


def implemented_blueprint_ids() -> list[str]:
    return [item["id"] for item in blueprints("implemented")]


def selectable_blueprint_ids(include_planned: bool = False) -> list[str]:
    if include_planned:
        return [item["id"] for item in MODEL_BLUEPRINTS if item["status"] in {"implemented", "planned"}]
    return implemented_blueprint_ids()


def blueprint_by_id(blueprint_id: str) -> dict[str, Any]:
    for item in MODEL_BLUEPRINTS:
        if item["id"] == blueprint_id:
            return item
    raise KeyError(f"unknown model blueprint {blueprint_id!r}")
