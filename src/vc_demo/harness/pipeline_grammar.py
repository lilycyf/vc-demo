from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class PipelineProgram:
    blueprint: str
    representation: str
    perturbation_side: str
    target_side: str
    fusion: str
    prior: str
    head: str
    training_strategy: str
    fine_tuning: str
    required_artifacts: tuple[str, ...]
    paper_alignment: str


PROGRAMS: list[PipelineProgram] = [
    PipelineProgram("dual_path_gated_low_rank", "tabular_context", "input_features", "learned_target_factors", "gated_dual_path", "none", "low_rank_target_head", "cross_entropy", "none", (), "compact architecture/head search baseline"),
    PipelineProgram("mixture_of_experts", "tabular_context", "input_features", "learned_target_factors", "router_experts", "none", "dense_target_head", "cross_entropy", "none", (), "conditional computation / expert routing"),
    PipelineProgram("film_conditioned_residual", "tabular_context", "input_features", "learned_target_factors", "film_residual", "none", "dense_target_head", "cross_entropy", "none", (), "conditional computation over perturbation context"),
    PipelineProgram("target_factor_router", "tabular_context", "input_features", "learned_target_factors", "route_conditioned_factors", "none", "low_rank_target_head", "cross_entropy", "none", (), "target-head program search"),
    PipelineProgram("target_gene_embedding_bilinear", "esm2_augmented_context", "perturbation_or_context_features", "esm2_target_gene_embeddings", "bilinear_context_target", "frozen_gene_embedding", "factorized_target_head", "cross_entropy", "frozen_artifact", ("esm2_gene_embedding_h5ad", "esm2_k562_target_manifest"), "explicit perturbed/context and target-gene artifact geometry"),
    PipelineProgram("cross_attention_gene_perturbation", "esm2_augmented_context", "perturbation_context_tokens", "target_gene_tokens", "cross_attention", "frozen_gene_embedding", "target_token_classifier", "cross_entropy", "frozen_artifact", ("esm2_gene_embedding_h5ad", "esm2_k562_target_manifest"), "multimodal target-gene/perturbation fusion"),
    PipelineProgram("ppi_graph_message_passing", "tabular_or_esm2_context", "input_features", "target_gene_logits", "logit_message_passing", "string_ppi_graph", "graph_smoothed_target_head", "cross_entropy", "none", ("string_k562_gene_graph",), "STRING/PPI target-gene graph prior"),
    PipelineProgram("string_gnn_perturbation_propagator", "tabular_or_esm2_context", "perturbation_gene_signal", "target_gene_logits", "graph_propagation", "string_ppi_graph", "propagated_target_head", "cross_entropy", "none", ("string_k562_gene_graph",), "perturbation signal propagation through STRING graph"),
    PipelineProgram("pathway_pooling_encoder", "tabular_or_esm2_context", "input_features", "pathway_membership_targets", "pathway_pooling", "pathway_membership", "pathway_target_head", "cross_entropy", "none", ("pathway_membership_matrix",), "pathway prior over target genes"),
    PipelineProgram("scfoundation_cell_encoder", "cell_state_embedding", "cell_state", "learned_or_artifact_targets", "cell_state_fusion", "scfoundation", "target_classifier", "cross_entropy", "frozen_or_adapter", ("scfoundation_cell_embeddings",), "single-cell foundation model cell-state encoder"),
    PipelineProgram("aido_embedding_fusion", "foundation_embedding", "perturbation_gene_embedding", "target_or_cell_embedding", "multimodal_gate", "aido", "target_classifier", "cross_entropy", "frozen_or_adapter", ("aido_gene_or_cell_embeddings",), "AIDO/foundation embedding fusion"),
    PipelineProgram("selective_adapter_finetune", "pretrained_encoder", "encoder_features", "encoder_or_target_features", "adapter", "pretrained_encoder", "adapter_head", "cross_entropy", "selective_adapter", ("pretrained_encoder",), "selective fine-tuning / adapter search"),
    PipelineProgram("focal_loss_training_strategy", "unchanged", "unchanged", "unchanged", "unchanged", "none", "unchanged", "focal_loss", "none", (), "training-strategy node, not architecture discovery"),
    PipelineProgram("class_balanced_deg_classifier", "unchanged", "unchanged", "unchanged", "unchanged", "none", "class_balanced_head", "weighted_or_balanced_loss", "none", (), "classification-head/imbalance handling"),
    PipelineProgram("uncertainty_calibrated_head", "tabular_context", "input_features", "learned_target_factors", "calibrated_logits", "none", "temperature_scaled_head", "cross_entropy", "none", (), "calibration-aware prediction head"),
    PipelineProgram("gated_multimodal_fusion", "mixed_context", "input_features", "optional_artifact_features", "learned_gates", "optional", "dense_target_head", "cross_entropy", "none", (), "multimodal fusion grammar placeholder"),
]

_PROGRAM_BY_BLUEPRINT = {program.blueprint: program for program in PROGRAMS}


def program_for_blueprint(blueprint: str) -> dict[str, Any]:
    program = _PROGRAM_BY_BLUEPRINT.get(blueprint)
    if program is None:
        return {
            "blueprint": blueprint,
            "representation": "unspecified",
            "perturbation_side": "unspecified",
            "target_side": "unspecified",
            "fusion": "unspecified",
            "prior": "unspecified",
            "head": "unspecified",
            "training_strategy": "unspecified",
            "fine_tuning": "unspecified",
            "required_artifacts": [],
            "paper_alignment": "blueprint not yet mapped into the grammar",
        }
    payload = asdict(program)
    payload["required_artifacts"] = list(program.required_artifacts)
    return payload


def grammar_dimensions() -> dict[str, list[str]]:
    fields = ["representation", "perturbation_side", "target_side", "fusion", "prior", "head", "training_strategy", "fine_tuning"]
    return {field: sorted({str(getattr(program, field)) for program in PROGRAMS}) for field in fields}


def grammar_matrix() -> list[dict[str, Any]]:
    return [program_for_blueprint(program.blueprint) for program in PROGRAMS]


def artifact_coverage_for_program(program: dict[str, Any], present_artifacts: set[str]) -> dict[str, Any]:
    required = set(program.get("required_artifacts", []))
    missing = sorted(required - present_artifacts)
    return {
        "blueprint": program.get("blueprint"),
        "required_artifacts": sorted(required),
        "missing_artifacts": missing,
        "all_required_present": not missing,
        "artifact_backed": bool(required),
    }


def grammar_readiness(present_artifacts: list[str]) -> list[dict[str, Any]]:
    present = set(present_artifacts)
    rows = []
    for program in grammar_matrix():
        row = dict(program)
        row.update(artifact_coverage_for_program(program, present))
        rows.append(row)
    return rows
