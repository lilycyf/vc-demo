from __future__ import annotations

from typing import Any


MODEL_BLUEPRINTS: list[dict[str, Any]] = [
    {
        "id": "dual_path_gated_low_rank",
        "status": "implemented",
        "category": "architecture_program",
        "role": "Dual encoder with input-conditioned gating and a low-rank target-gene head.",
        "requires": ["tabular_features"],
    },
    {
        "id": "mixture_of_experts",
        "status": "implemented",
        "category": "architecture_program",
        "role": "Compact router over several MLP experts for perturbation feature regimes.",
        "requires": ["tabular_features"],
    },
    {
        "id": "film_conditioned_residual",
        "status": "planned",
        "category": "architecture_program",
        "role": "Residual blocks modulated by the original perturbation vector.",
        "requires": ["tabular_features"],
    },
    {
        "id": "target_factor_router",
        "status": "planned",
        "category": "architecture_program",
        "role": "Route-conditioned low-rank target-gene factor head.",
        "requires": ["tabular_features"],
    },
    {
        "id": "gene_embedding_adapter",
        "status": "planned",
        "category": "biological_prior",
        "role": "Learn or load gene embeddings and condition target heads on gene identity.",
        "requires": ["gene_ids"],
    },
    {
        "id": "ppi_graph_message_passing",
        "status": "planned",
        "category": "biological_prior",
        "role": "Use a STRING/PPI-like graph prior for target-gene message passing.",
        "requires": ["gene_graph"],
    },
    {
        "id": "foundation_embedding_fusion",
        "status": "planned",
        "category": "foundation_model_fusion",
        "role": "Fuse frozen biological foundation-model embeddings with perturbation features.",
        "requires": ["external_embeddings"],
    },
    {
        "id": "cross_attention_gene_perturbation",
        "status": "planned",
        "category": "fusion",
        "role": "Cross-attend target-gene tokens against perturbation/context tokens.",
        "requires": ["gene_tokens"],
    },
    {
        "id": "selective_adapter_finetune",
        "status": "planned",
        "category": "fine_tuning",
        "role": "Freeze a base encoder and train small adapters/LoRA-style modules.",
        "requires": ["pretrained_encoder"],
    },
    {
        "id": "multi_task_cellline_conditioning",
        "status": "planned",
        "category": "multi_cellline",
        "role": "Condition predictions on cell-line identity for multi-cell-line experiments.",
        "requires": ["multiple_cell_lines"],
    },
]


def blueprints(status: str | None = None) -> list[dict[str, Any]]:
    if status is None:
        return list(MODEL_BLUEPRINTS)
    return [item for item in MODEL_BLUEPRINTS if item["status"] == status]


def implemented_blueprint_ids() -> list[str]:
    return [item["id"] for item in blueprints("implemented")]


def blueprint_by_id(blueprint_id: str) -> dict[str, Any]:
    for item in MODEL_BLUEPRINTS:
        if item["id"] == blueprint_id:
            return item
    raise KeyError(f"unknown model blueprint {blueprint_id!r}")
