from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import artifact_by_id_or_alias, missing_requirements_for_blueprint, requirements_for_blueprint
from vc_demo.harness.model_blueprints import blueprint_by_id, selectable_blueprint_ids
from vc_demo.harness.pipeline import default_pipeline_manifest, write_pipeline_manifest
from vc_demo.harness.pipeline_grammar import program_for_blueprint
from vc_demo.harness.state import write_json


def propose_program_child(parent_config: dict[str, Any], parent_node: dict[str, Any], child_index: int, rng: random.Random, program_root: Path, include_planned: bool = False, force_blueprint: str | None = None, registry_audit: dict[str, Any] | None = None, artifact_aware: bool = True, official_k562_only: bool = False, search_memory: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    parent_name = str(parent_config.get("node_name", parent_node.get("name", "node")))
    blueprint_id = force_blueprint or _choose_blueprint(parent_name, parent_node, child_index, rng, include_planned, registry_audit=registry_audit, artifact_aware=artifact_aware, official_k562_only=official_k562_only, search_memory=search_memory)
    blueprint = blueprint_by_id(blueprint_id)
    if blueprint["status"] == "planned" and not include_planned and force_blueprint is None:
        raise ValueError(f"planned blueprint {blueprint_id!r} selected without include_planned=True")

    digest = hashlib.sha1(f"{parent_name}:{child_index}:{blueprint_id}".encode("utf-8")).hexdigest()[:8]
    parent_root = parent_name.split("_p")[0]
    child_name = f"{parent_root}_p{child_index}_{blueprint_id}_{digest}"
    child_dir = program_root / child_name
    child_dir.mkdir(parents=True, exist_ok=True)

    child = copy.deepcopy(parent_config)
    child.setdefault("model", {})
    child.setdefault("training", {})
    child["node_name"] = child_name
    model_cfg = child["model"]
    train_cfg = child["training"]
    old_model = model_cfg.get("model_type", "mlp")
    config_only = blueprint_id in {"official_class_imbalance_training"}
    external_static = blueprint_id in {"official_public_best_node"}
    official_native = blueprint_id in {
        "official_aido_lora_adapter",
        "official_string_gnn_attention",
        "official_aido_string_fusion",
        "official_aido_string_cross_attention",
        "official_string_neighborhood_attention",
        "official_target_gene_head",
        "official_target_graph_conditioned_head",
        "official_aido_full_finetune",
        "official_focal_loss_training",
        "official_native_public_best_reimplementation",
    }
    if not external_static and child.get("execution", {}).get("backend") == "external_static_node":
        child.pop("execution", None)
    if not config_only and not external_static:
        model_cfg["model_type"] = "custom_program"
        model_cfg["custom_model_path"] = str(child_dir / "model.py")
        model_cfg["custom_model_class"] = "GeneratedModel"
    model_cfg["program_blueprint"] = blueprint_id
    model_cfg["hidden_dim"] = _bounded_hidden(model_cfg.get("hidden_dim", 256), blueprint_id)
    model_cfg["depth"] = min(max(int(model_cfg.get("depth", 2) or 2), 1), 3)
    model_cfg["dropout"] = float(model_cfg.get("dropout", 0.1) if model_cfg.get("dropout") is not None else 0.1)
    if blueprint_id in {"dual_path_gated_low_rank", "target_factor_router", "target_gene_embedding_bilinear"}:
        model_cfg["low_rank_dim"] = min(max(int(model_cfg.get("low_rank_dim", 64) or 64), 32), 128)
    if blueprint_id == "esm2_gene_projection":
        esm2_data_dir = Path("data/cell_lines/k562_concat_esm2_gene_embedding")
        if esm2_data_dir.exists():
            child.setdefault("data", {})["data_dir"] = str(esm2_data_dir)
            model_cfg["input_dim"] = "auto"
            model_cfg["perturbation_embedding_dim"] = 1280
            model_cfg["source_feature_dim"] = 1105
    if blueprint_id == "target_gene_embedding_bilinear":
        model_cfg["artifact_manifest_path"] = "data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json"
    if blueprint_id in {"ppi_graph_message_passing", "string_gnn_perturbation_propagator"}:
        model_cfg.setdefault("artifacts", {})
        model_cfg["artifacts"].setdefault("string_graph_edges_path", "data/artifacts/string/k562_target_graph_edges.tsv")
        model_cfg["artifacts"].setdefault("data_dir", child.get("data", {}).get("data_dir", ""))
    if blueprint_id == "pathway_pooling_encoder":
        model_cfg.setdefault("artifacts", {})
        model_cfg["artifacts"].setdefault("pathway_membership_path", "data/artifacts/pathways/k562_target_pathway_membership.npz")
        model_cfg["artifacts"].setdefault("data_dir", child.get("data", {}).get("data_dir", ""))
    if blueprint_id in {"focal_loss_training_strategy", "official_class_imbalance_training", "official_focal_loss_training"}:
        train_cfg["loss_type"] = "focal_loss"
        train_cfg.setdefault("focal_gamma", 2.0)
        train_cfg.setdefault("class_weights", [2.37, 0.51, 2.75])
    if official_native:
        data_cfg = child.setdefault("data", {})
        if data_cfg.get("dataset_type") == "official_k562_tsv" and not data_cfg.get("embedding_h5ad") and not data_cfg.get("embedding_h5ads"):
            if blueprint_id in {"official_string_gnn_attention", "official_aido_string_fusion", "official_aido_string_cross_attention", "official_string_neighborhood_attention", "official_target_graph_conditioned_head", "official_native_public_best_reimplementation"}:
                data_cfg["embedding_h5ads"] = [
                    "data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad",
                    "data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad",
                ]
            else:
                data_cfg["embedding_h5ad"] = "data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad"
        model_cfg.setdefault("artifacts", {})
        model_cfg["artifacts"].setdefault("aido_model_dir", "/home/Models/AIDO.Cell-100M")
        model_cfg["artifacts"].setdefault("string_gnn_model_dir", "/home/Models/STRING_GNN")
        model_cfg["artifacts"].setdefault("string_graph_path", "data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
        model_cfg["low_rank_dim"] = min(max(int(model_cfg.get("low_rank_dim", 96) or 96), 64), 160)
    if blueprint_id == "official_public_best_node":
        child["execution"] = {
            "backend": "external_static_node",
            "static_dir": "/workspace/_external/VCHarness/K562_cls/static",
            "script_path": "node2-1-1-1-1-1_code.py",
            "external_data_root": "/workspace/_external/VCHarness/data",
            "pythonpath": ["/workspace/_external/ModelGenerator/huggingface/aido.cell", "src"],
            "args": ["--debug-max-step", "1", "--micro-batch-size", "1", "--global-batch-size", "1", "--num-workers", "0", "--max-epochs", "1"],
            "artifact_usage": {"AIDO.Cell-100M": "/home/Models/AIDO.Cell-100M", "STRING_GNN": "/home/Models/STRING_GNN"},
        }
    train_cfg["lr"] = min(float(train_cfg.get("lr", 3e-4) or 3e-4), 3e-4)
    train_cfg["weight_decay"] = min(float(train_cfg.get("weight_decay", 1e-4) or 1e-4), 1e-4)

    pipeline_path = child_dir / "pipeline.json"
    child["pipeline_manifest_path"] = str(pipeline_path)
    pipeline_manifest = render_pipeline_manifest(child, proposal_blueprint=blueprint)
    pipeline_program = program_for_blueprint(blueprint_id)

    requires_implementation = blueprint["status"] != "implemented"
    artifact_contract_path = child_dir / "artifact_contract.json"
    smoke_contract_path = child_dir / "smoke_contract.json"
    parent_summary_path = child_dir / "parent_summary.json"
    implementation_request_path = child_dir / "IMPLEMENTATION_REQUEST.md"
    artifact_contract = render_artifact_contract(child_name, blueprint, child, registry_audit)
    smoke_contract = render_smoke_contract(child_name, child)
    parent_summary = render_parent_summary(parent_name, parent_node, parent_config)
    write_json(artifact_contract_path, artifact_contract)
    write_json(smoke_contract_path, smoke_contract)
    write_json(parent_summary_path, parent_summary)
    if requires_implementation:
        implementation_request_path.write_text(render_implementation_request(child_name, blueprint, parent_name, child, artifact_contract, smoke_contract, parent_summary), encoding="utf-8")
    elif not config_only and not external_static:
        (child_dir / "model.py").write_text(render_program_source(blueprint_id), encoding="utf-8")
    (child_dir / "README.md").write_text(render_program_readme(child_name, blueprint, parent_name, requires_implementation), encoding="utf-8")
    write_pipeline_manifest(pipeline_path, pipeline_manifest)
    write_json(child_dir / "base_config.json", child)

    parent_signature = structural_signature(parent_config)
    child_signature = structural_signature(child)
    structural_relation = "replicate" if parent_signature == child_signature else "structural_variant"

    changes = [
        f"program_model:{old_model}->{blueprint_id}",
        f"blueprint_status:{blueprint['status']}",
        f"custom_model_path:{child_dir / 'model.py'}" if not (config_only or external_static) else "model_program:none",
        f"hidden_dim:{parent_config.get('model', {}).get('hidden_dim')}->{model_cfg.get('hidden_dim')}",
        f"depth:{parent_config.get('model', {}).get('depth')}->{model_cfg.get('depth')}",
        f"lr:{parent_config.get('training', {}).get('lr')}->{train_cfg.get('lr')}",
    ]
    proposal = {
        "agent_type": "codex_program_node_agent",
        "node_kind": "program_node",
        "parent": parent_name,
        "child": child_name,
        "strategy": blueprint_id,
        "blueprint": blueprint,
        "requires_implementation": requires_implementation,
        "hypothesis": hypothesis_for(blueprint_id, blueprint),
        "changes": changes,
        "program_dir": str(child_dir),
        "program_model_path": str(child_dir / "model.py") if not (config_only or external_static) else "",
        "pipeline_manifest_path": str(pipeline_path),
        "pipeline_kind": pipeline_manifest.get("kind"),
        "artifact_requirements": pipeline_manifest.get("artifact_requirements", []),
        "artifact_usage_claims": pipeline_manifest.get("artifact_usage_claims", []),
        "pipeline_program": pipeline_program,
        "scientific_selection": scientific_selection_summary(blueprint_id, search_memory),
        "structural_signature": child_signature,
        "parent_structural_signature": parent_signature,
        "structural_relation": structural_relation,
        "implementation_request_path": str(implementation_request_path) if requires_implementation else "",
        "artifact_contract_path": str(artifact_contract_path),
        "smoke_contract_path": str(smoke_contract_path),
        "parent_summary_path": str(parent_summary_path),
        "limits": "Model choice is manifest-driven. Planned blueprints materialize an implementation request instead of pretending to be executable.",
        "artifact_selection": artifact_selection_summary(blueprint_id, registry_audit),
    }
    child["proposal_note"] = f"codex_program_agent blueprint={blueprint_id}; " + "; ".join(changes)
    write_json(child_dir / "proposal.json", proposal)
    return child, proposal


def render_pipeline_manifest(child_config: dict[str, Any], proposal_blueprint: dict[str, Any]) -> dict[str, Any]:
    manifest = default_pipeline_manifest(child_config, {"strategy": proposal_blueprint["id"]})
    blueprint_id = proposal_blueprint["id"]
    manifest["kind"] = "pipeline_program_node"
    manifest["change_level"] = proposal_blueprint.get("change_level")
    manifest["paper_family"] = proposal_blueprint.get("paper_family")
    manifest["pipeline_program"] = program_for_blueprint(blueprint_id)
    manifest["artifact_requirements"] = list(proposal_blueprint.get("requires", []))
    manifest["artifact_usage_claims"] = []
    if blueprint_id in {"esm2_gene_projection", "target_gene_embedding_bilinear", "cross_attention_gene_perturbation"}:
        manifest["artifact_usage_claims"].append({"provider": "ESM2", "sides": ["perturbation_gene", "target_gene"], "frozen_by_default": True})
    if blueprint_id == "aido_embedding_fusion":
        manifest["artifact_usage_claims"].append({"provider": "AIDO", "sides": ["perturbation_gene", "target_gene", "cell_state"], "requires_present_artifact": True})
    if blueprint_id == "scfoundation_cell_encoder":
        manifest["artifact_usage_claims"].append({"provider": "scFoundation", "sides": ["cell_state"], "requires_present_artifact": True})
    if blueprint_id in {"ppi_graph_message_passing", "string_gnn_perturbation_propagator"}:
        manifest["artifact_usage_claims"].append({"provider": "STRING", "sides": ["gene_graph"], "requires_present_artifact": True})
    if blueprint_id == "pathway_pooling_encoder":
        manifest["artifact_usage_claims"].append({"provider": "pathway_db", "sides": ["pathway_pooling"], "requires_present_artifact": True})
    if blueprint_id == "official_public_best_node":
        manifest["kind"] = "external_static_node"
        manifest["artifact_usage_claims"].append({"provider": "VCHarness public K562 best node", "sides": ["AIDO", "STRING_GNN", "official_k562_tsv"], "requires_present_artifact": True})
    if blueprint_id in {"official_aido_lora_adapter", "official_aido_string_fusion", "official_aido_string_cross_attention", "official_aido_full_finetune", "official_native_public_best_reimplementation"}:
        manifest["artifact_usage_claims"].append({"provider": "AIDO.Cell-100M", "sides": ["perturbation_gene"], "requires_present_artifact": True})
    if blueprint_id in {"official_string_gnn_attention", "official_aido_string_fusion", "official_aido_string_cross_attention", "official_string_neighborhood_attention", "official_target_graph_conditioned_head", "official_native_public_best_reimplementation"}:
        manifest["artifact_usage_claims"].append({"provider": "STRING_GNN", "sides": ["gene_graph"], "requires_present_artifact": True})
    if blueprint_id in {"focal_loss_training_strategy", "official_class_imbalance_training", "official_focal_loss_training"}:
        manifest["training"] = {"loss_type": "focal_loss", "loss_notes": "Node-level training strategy patch for class-imbalanced DEG labels."}
        manifest["patches"] = {"training": {"loss_type": "focal_loss", "focal_gamma": 2.0, "class_weights": [2.37, 0.51, 2.75]}}
    return manifest


SCIENTIFIC_PRIORS: dict[str, float] = {
    "official_aido_string_fusion": 1.00,
    "official_aido_string_cross_attention": 0.98,
    "official_string_gnn_attention": 0.96,
    "official_string_neighborhood_attention": 0.94,
    "official_aido_lora_adapter": 0.92,
    "official_target_gene_head": 0.88,
    "official_target_graph_conditioned_head": 0.86,
    "official_pathway_pooling_reactome": 0.84,
    "official_regulatory_network_prior": 0.82,
    "official_class_imbalance_training": 0.74,
    "official_focal_loss_training": 0.72,
    "official_weighted_ce_training": 0.70,
    "official_public_best_node": 0.62,
    "official_public_static_node_family_wrapper": 0.60,
    "official_native_public_best_reimplementation": 0.45,
}

REQUIRED_EARLY_FAMILIES = [
    "official_aido_string_fusion",
    "official_string_gnn_attention",
    "official_aido_lora_adapter",
    "official_target_gene_head",
    "official_class_imbalance_training",
    "official_pathway_pooling_reactome",
    "official_public_best_node",
]


def _choose_blueprint(
    parent_name: str,
    parent_node: dict[str, Any],
    child_index: int,
    rng: random.Random,
    include_planned: bool,
    registry_audit: dict[str, Any] | None = None,
    artifact_aware: bool = True,
    official_k562_only: bool = False,
    search_memory: dict[str, Any] | None = None,
) -> str:
    choices = selectable_blueprint_ids(include_planned, official_k562_only=official_k562_only)
    if not choices:
        raise ValueError("no selectable model blueprints are available")
    ranking_memory = (search_memory or {}) if artifact_aware else {}
    ranked = rank_scientific_blueprint_choices(choices, ranking_memory, parent_node, child_index)
    if child_index <= len(ranked):
        return ranked[child_index - 1]
    parent_offset = int(hashlib.sha1(parent_name.encode("utf-8")).hexdigest(), 16) % len(ranked)
    return ranked[parent_offset % len(ranked)] if ranked else rng.choice(choices)


def artifact_selection_summary(blueprint_id: str, registry_audit: dict[str, Any] | None) -> dict[str, Any]:
    if not registry_audit:
        return {"policy": "unavailable"}
    required = requirements_for_blueprint(registry_audit, blueprint_id)
    missing = [item for item in required if not item.get("present")]
    return {
        "policy": "feasibility_gate_after_scientific_selection",
        "required_artifacts": [item.get("id") for item in required],
        "missing_required_artifacts": [item.get("id") for item in missing],
        "all_required_present": bool(required) and not missing,
    }


def rank_blueprint_choices(choices: list[str], registry_audit: dict[str, Any]) -> list[str]:
    """Backward-compatible alias: artifact feasibility is no longer a scientific ranking signal."""
    return rank_scientific_blueprint_choices(choices, {}, {}, 1)


BLOCKED_ARTIFACT_SUPPRESSION_THRESHOLD = 2
BLOCKED_STRATEGY_SUPPRESSION_THRESHOLD = 2
BLOCKED_FAMILY_SUPPRESSION_THRESHOLD = 3


def blocked_policy_for_blueprint(blueprint_id: str, memory: dict[str, Any]) -> dict[str, Any]:
    """Return strict-mode blocked-family policy signals for blueprint ranking.

    This is intentionally not an artifact-present preference. It only reacts to
    artifacts that have already blocked nodes in the current run. The search can
    still record/acquire missing artifacts, but repeated unavailable artifacts
    should not keep consuming expansion budget while other paper-level families
    remain unexplored.
    """
    blueprint = blueprint_by_id(blueprint_id)
    family = str(blueprint.get("paper_family") or blueprint.get("category") or blueprint_id)
    required = set(str(item) for item in blueprint.get("requires", []) or [])
    blocked_rows = list(memory.get("blocked_artifacts", []) or [])
    artifact_counts: dict[str, int] = {}
    strategy_block_count = 0
    family_block_count = 0
    for row in blocked_rows:
        strategy = str(row.get("strategy") or "")
        row_family = str(row.get("family") or "")
        missing = [str(item) for item in row.get("missing", []) or []]
        if strategy == blueprint_id:
            strategy_block_count += 1
        if row_family == family:
            family_block_count += 1
        for artifact_id in missing:
            artifact_counts[artifact_id] = artifact_counts.get(artifact_id, 0) + 1
    repeated_blocked_artifacts = sorted(
        artifact_id for artifact_id in required
        if artifact_counts.get(artifact_id, 0) >= BLOCKED_ARTIFACT_SUPPRESSION_THRESHOLD
    )
    suppress = bool(repeated_blocked_artifacts) or strategy_block_count >= BLOCKED_STRATEGY_SUPPRESSION_THRESHOLD
    # Family suppression is deliberately weaker: only suppress a whole family
    # after repeated blocks when no specific artifact mapping catches it.
    if family_block_count >= BLOCKED_FAMILY_SUPPRESSION_THRESHOLD and not repeated_blocked_artifacts:
        suppress = True
    soft_penalty = 0.0
    if suppress:
        soft_penalty = 10.0
    elif family_block_count > 0:
        soft_penalty = min(0.20 * family_block_count, 0.80)
    return {
        "blocked_policy": "blocked_artifact_budget_reallocation",
        "blocked_policy_active": bool(blocked_rows),
        "suppressed_by_blocked_artifact": suppress,
        "blocked_policy_penalty": soft_penalty,
        "repeated_blocked_artifacts": repeated_blocked_artifacts,
        "strategy_block_count": strategy_block_count,
        "family_block_count": family_block_count,
        "blocked_artifact_counts": {artifact_id: artifact_counts.get(artifact_id, 0) for artifact_id in sorted(required)},
    }


def scientific_score(blueprint_id: str, memory: dict[str, Any], child_index: int) -> dict[str, Any]:
    blueprint = blueprint_by_id(blueprint_id)
    counts = memory.get("blueprint_counts", {}) or {}
    family_counts = memory.get("family_counts", {}) or {}
    count = int(counts.get(blueprint_id, 0) or 0)
    family = str(blueprint.get("paper_family") or blueprint.get("category") or blueprint_id)
    family_count = int(family_counts.get(family, 0) or 0)
    base = SCIENTIFIC_PRIORS.get(blueprint_id, 0.50 + 0.04 * int(blueprint.get("change_level", 0) or 0))
    coverage_bonus = 0.35 if count == 0 else 0.0
    family_bonus = 0.25 if family_count == 0 else 0.0
    early_bonus = 0.20 if child_index <= len(REQUIRED_EARLY_FAMILIES) and blueprint_id in REQUIRED_EARLY_FAMILIES else 0.0
    repeat_penalty = min(0.12 * count, 0.60)
    native_repeat_penalty = 0.45 if blueprint_id == "official_native_public_best_reimplementation" and count > 0 else 0.0
    blocked_policy = blocked_policy_for_blueprint(blueprint_id, memory)
    blocked_policy_penalty = float(blocked_policy.get("blocked_policy_penalty", 0.0) or 0.0)
    score = base + coverage_bonus + family_bonus + early_bonus - repeat_penalty - native_repeat_penalty - blocked_policy_penalty
    return {"score": score, "base": base, "coverage_bonus": coverage_bonus, "family_bonus": family_bonus, "early_bonus": early_bonus, "repeat_penalty": repeat_penalty, "native_repeat_penalty": native_repeat_penalty, "blocked_policy_penalty": blocked_policy_penalty, "count": count, "family": family, "family_count": family_count, **blocked_policy}


def rank_scientific_blueprint_choices(choices: list[str], memory: dict[str, Any], parent_node: dict[str, Any], child_index: int) -> list[str]:
    indexed = list(enumerate(choices))
    scored = [(index, blueprint_id, scientific_score(blueprint_id, memory, child_index)) for index, blueprint_id in indexed]
    eligible = [row for row in scored if not row[2].get("suppressed_by_blocked_artifact")]
    pool = eligible if eligible else scored

    def key(item: tuple[int, str, dict[str, Any]]) -> tuple[float, int, int, int]:
        index, blueprint_id, score = item
        blueprint = blueprint_by_id(blueprint_id)
        return (score["score"], int(blueprint.get("change_level", 0) or 0), -score["count"], -index)

    return [blueprint_id for _, blueprint_id, _ in sorted(pool, key=key, reverse=True)]


def scientific_selection_summary(blueprint_id: str, memory: dict[str, Any] | None) -> dict[str, Any]:
    return {"policy": "scientific_priority_with_blocked_artifact_budget_reallocation", **scientific_score(blueprint_id, memory or {}, 1)}


def structural_signature(config: dict[str, Any]) -> str:
    model = copy.deepcopy(config.get("model", {}))
    training = copy.deepcopy(config.get("training", {}))
    data = copy.deepcopy(config.get("data", {}))
    for key in ["custom_model_path"]:
        model.pop(key, None)
    payload = {"data": data, "model": model, "training": training, "execution": config.get("execution", {})}
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _bounded_hidden(current: Any, blueprint_id: str) -> int:
    value = int(current or 256)
    if blueprint_id == "mixture_of_experts":
        return min(max(value, 256), 384)
    return min(max(value, 192), 384)


def render_artifact_contract(child_name: str, blueprint: dict[str, Any], child_config: dict[str, Any], registry_audit: dict[str, Any] | None) -> dict[str, Any]:
    required = list(blueprint.get("requires", []))
    present: list[str] = []
    missing: list[str] = []
    for artifact_id in required:
        row = artifact_by_id_or_alias(registry_audit or {}, artifact_id)
        if row.get("present"):
            present.append(artifact_id)
        else:
            missing.append(artifact_id)
    return {
        "format": "vc_demo_node_artifact_contract.v1",
        "node": child_name,
        "blueprint": blueprint.get("id"),
        "strict_official_mode": True,
        "fallback_allowed": bool(blueprint.get("fallback_allowed", False)),
        "required_artifacts": required,
        "present_required_artifacts": present,
        "missing_required_artifacts": missing,
        "artifact_policy": "present_or_acquire_real_artifact_else_block; never train silent fallback in strict official mode",
        "artifact_rows": [artifact_by_id_or_alias(registry_audit or {}, artifact_id) for artifact_id in required],
        "model_artifacts_config": child_config.get("model", {}).get("artifacts", {}),
    }


def render_smoke_contract(child_name: str, child_config: dict[str, Any]) -> dict[str, Any]:
    custom_model_path = child_config.get("model", {}).get("custom_model_path", "")
    return {
        "format": "vc_demo_node_smoke_contract.v1",
        "node": child_name,
        "expected_output_shape": "[batch, 6640, 3] for official K562; [batch, n_targets, n_classes] in generic spec terms",
        "compile_command": f"python -m compileall -q {custom_model_path}" if custom_model_path else "config-only or external node; no node-local model.py compile step",
        "native_smoke_command": "PYTHONPATH=src python -m vc_demo.harness.native_program_smoke --config <child-config>",
        "training_smoke_command": "PYTHONPATH=src python -m vc_demo.harness.train_pending --run-dir <run-dir> --node <node> --max-epochs 1",
        "repair_attempt_limit": {"compile": 3, "forward_shape": 3, "backward": 3, "train": 3},
    }


def render_parent_summary(parent_name: str, parent_node: dict[str, Any], parent_config: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": "vc_demo_parent_summary.v1",
        "parent": parent_name,
        "parent_status": parent_node.get("status"),
        "parent_best_val_macro_f1": parent_node.get("best_val_macro_f1"),
        "parent_test_macro_f1": parent_node.get("test_macro_f1"),
        "parent_strategy": parent_node.get("strategy", "root"),
        "parent_config_model": parent_config.get("model", {}),
        "parent_config_training": parent_config.get("training", {}),
        "parent_artifact_usage": parent_node.get("artifact_usage", {}),
    }


def render_implementation_request(child_name: str, blueprint: dict[str, Any], parent_name: str, child_config: dict[str, Any], artifact_contract: dict[str, Any], smoke_contract: dict[str, Any], parent_summary: dict[str, Any]) -> str:
    acceptance = "\n".join(f"- {item}" for item in blueprint.get("acceptance", []))
    requires = ", ".join(blueprint.get("requires", []))
    missing = ", ".join(artifact_contract.get("missing_required_artifacts", [])) or "none"
    lines = [
        f"# Implementation Request: {child_name}", "",
        "## Research Task", "", "K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.", "",
        "## Parent", "", f"`{parent_name}`", f"- parent val Macro-F1: `{parent_summary.get('parent_best_val_macro_f1')}`", f"- parent strategy: `{parent_summary.get('parent_strategy')}`", "",
        "## Blueprint", "",
        f"- id: `{blueprint['id']}`", f"- status: `{blueprint['status']}`", f"- category: `{blueprint['category']}`", f"- paper family: `{blueprint.get('paper_family', '')}`", f"- role: {blueprint['role']}", f"- requires: {requires}", f"- missing required artifacts now: {missing}", "",
        "## Contract Files", "", "- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy", "- `smoke_contract.json`: compile, forward/backward, and training-smoke commands", "- `parent_summary.json`: parent score/config/artifact context", "- `pipeline.json`: executable pipeline grammar and artifact claims", "",
        "## Implementation Notes", "", blueprint.get("implementation_notes", ""), "", "## Pipeline Grammar", "", json_dumps_program(blueprint["id"]), "",
        "## Required File", "", "Create this file:", "", "```text", child_config["model"]["custom_model_path"], "```", "",
        "It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.", "",
        "## Acceptance Criteria", "", acceptance, "",
        "## Guardrails", "", "Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.", "Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.", "Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.", "Smoke gate: run the commands in `smoke_contract.json` before training.", "Keep the model compact enough for the current RunPod GPU.",
    ]
    return "\n".join(lines) + "\n"

def json_dumps_program(blueprint_id: str) -> str:
    import json
    return "```json\n" + json.dumps(program_for_blueprint(blueprint_id), indent=2) + "\n```"

def render_program_readme(child_name: str, blueprint: dict[str, Any], parent_name: str, requires_implementation: bool) -> str:
    lines = [f"# Program Node: {child_name}", "", f"- Parent: `{parent_name}`", f"- Blueprint: `{blueprint['id']}`", f"- Status: `{blueprint['status']}`", f"- Category: `{blueprint['category']}`", f"- Role: {blueprint['role']}", f"- Requires implementation: `{requires_implementation}`", "", "This directory is a node-local architecture program generated by the harness."]
    if requires_implementation:
        lines.append("Implement `model.py` according to `IMPLEMENTATION_REQUEST.md`, then rerun training for this node.")
    return "\n".join(lines) + "\n"


def hypothesis_for(blueprint_id: str, blueprint: dict[str, Any]) -> str:
    mapping = {
        "dual_path_gated_low_rank": "A dual-path encoder with input-conditioned gating and a low-rank target head may share target-gene response structure while preserving perturbation-specific signal.",
        "mixture_of_experts": "A compact router over multiple experts may specialize decision surfaces for different perturbation feature regimes.",
        "target_gene_embedding_bilinear": "A frozen target-gene artifact table may give the classifier target-specific biological geometry instead of learning every target head from scratch.",
    }
    return mapping.get(blueprint_id, blueprint.get("role", f"Implement and test blueprint {blueprint_id}."))


def render_program_source(blueprint_id: str) -> str:
    sources = {"dual_path_gated_low_rank": DUAL_PATH_GATED_LOW_RANK, "mixture_of_experts": MIXTURE_OF_EXPERTS, "esm2_gene_projection": ESM2_GENE_PROJECTION, "target_gene_embedding_bilinear": TARGET_GENE_EMBEDDING_BILINEAR, "ppi_graph_message_passing": STRING_GRAPH_MESSAGE_PASSING, "string_gnn_perturbation_propagator": STRING_GNN_PERTURBATION_PROPAGATOR, "pathway_pooling_encoder": PATHWAY_POOLING_ENCODER, "official_target_gene_head": OFFICIAL_TARGET_GENE_HEAD, "official_string_gnn_attention": OFFICIAL_STRING_GNN_ATTENTION, "official_aido_lora_adapter": OFFICIAL_AIDO_LORA_ADAPTER, "official_aido_string_fusion": OFFICIAL_AIDO_STRING_FUSION, "official_native_public_best_reimplementation": OFFICIAL_NATIVE_PUBLIC_BEST_REIMPLEMENTATION}
    try:
        return sources[blueprint_id]
    except KeyError as exc:
        raise ValueError(f"blueprint {blueprint_id!r} is not implemented and cannot be executed") from exc


DUAL_PATH_GATED_LOW_RANK = """from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        rank = max(8, min(int(getattr(spec, \"low_rank_dim\", 64)), hidden))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.left = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(spec.dropout))
        self.right = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU())
        self.gate = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.Sigmoid())
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate = self.gate(x)
        z = self.left(x) * gate + self.right(x) * (1.0 - gate)
        rank_logits = self.rank_head(z).view(x.shape[0], -1, self.n_classes)
        logits = torch.einsum(\"brc,nr->bnc\", rank_logits, self.target_factors)
        return logits + self.bias.unsqueeze(0)
"""


MIXTURE_OF_EXPERTS = """from __future__ import annotations

import torch
from torch import nn


def expert_block(input_dim: int, hidden: int, dropout: float) -> nn.Sequential:
    return nn.Sequential(nn.Linear(input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden), nn.GELU())


class GeneratedModel(nn.Module):
    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.experts = nn.ModuleList([expert_block(spec.input_dim, hidden, spec.dropout) for _ in range(3)])
        self.router = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.GELU(), nn.Linear(hidden, 3), nn.Softmax(dim=-1))
        self.norm = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        weights = self.router(x)
        stacked = torch.stack([expert(x) for expert in self.experts], dim=1)
        z = torch.sum(stacked * weights.unsqueeze(-1), dim=1)
        logits = self.head(self.norm(z))
        return logits.view(x.shape[0], self.n_targets, self.n_classes)
"""


TARGET_GENE_EMBEDDING_BILINEAR = """from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from torch import nn


def mlp_block(in_dim: int, out_dim: int, dropout: float) -> list[nn.Module]:
    return [nn.Linear(in_dim, out_dim), nn.LayerNorm(out_dim), nn.GELU(), nn.Dropout(dropout)]


def load_npz_array(path: str | Path, key: str) -> torch.Tensor:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"artifact array path does not exist: {path}")
    with np.load(path) as data:
        if key not in data.files:
            raise KeyError(f"artifact array {path} missing key {key!r}; available={data.files}")
        return torch.from_numpy(np.asarray(data[key], dtype="float32"))


class GeneratedModel(nn.Module):
    def __init__(self, spec) -> None:
        super().__init__()
        manifest_path = getattr(spec, "artifact_manifest_path", "") or getattr(spec, "artifacts", {}).get("artifact_manifest_path", "")
        if manifest_path == "auto":
            manifest_path = "data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json"
        if not manifest_path:
            raise ValueError("target_gene_embedding_bilinear requires model.artifact_manifest_path or auto-bound artifact manifest")
        with Path(manifest_path).open() as f:
            manifest = json.load(f)
        target_info = manifest.get("target_gene_embeddings", {})
        target_embeddings = load_npz_array(target_info.get("path", ""), target_info.get("key", "target_gene_embeddings"))
        if target_embeddings.shape[0] != int(spec.n_targets):
            raise ValueError(f"target embedding rows {target_embeddings.shape[0]} != n_targets {spec.n_targets}")
        hidden = int(spec.hidden_dim)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 64)), hidden, 128))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        layers: list[nn.Module] = [nn.Linear(spec.input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(spec.dropout)]
        for _ in range(max(0, int(spec.depth) - 1)):
            layers.extend(mlp_block(hidden, hidden, spec.dropout))
        self.encoder = nn.Sequential(*layers)
        self.context_rank = nn.Linear(hidden, rank * self.n_classes)
        self.target_projection = nn.Sequential(nn.LayerNorm(target_embeddings.shape[1]), nn.Linear(target_embeddings.shape[1], rank))
        self.target_residual = nn.Linear(target_embeddings.shape[1], self.n_classes)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.register_buffer("target_embeddings", target_embeddings, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        context = self.encoder(x)
        context_rank = self.context_rank(context).view(x.shape[0], -1, self.n_classes)
        target_embeddings = self.target_embeddings.to(device=x.device, dtype=x.dtype)
        target_rank = self.target_projection(target_embeddings)
        logits = torch.einsum("brc,nr->bnc", context_rank, target_rank)
        return logits + self.target_residual(target_embeddings).unsqueeze(0) + self.bias.unsqueeze(0)
"""



STRING_GRAPH_MESSAGE_PASSING = """from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import torch
from torch import nn


def _load_target_genes(data_dir: str) -> list[str]:
    if not data_dir:
        raise ValueError("STRING graph node requires spec.artifacts['data_dir']")
    path = Path(data_dir) / "train.npz"
    if not path.exists():
        raise FileNotFoundError(f"cannot load target genes from {path}")
    with np.load(path, allow_pickle=True) as z:
        return [str(x) for x in z["target_genes"].tolist()]


def _load_adjacency(path: str, target_genes: list[str]) -> torch.Tensor:
    edge_path = Path(path)
    if not edge_path.exists():
        raise FileNotFoundError(f"STRING graph edge artifact does not exist: {edge_path}")
    index = {gene: i for i, gene in enumerate(target_genes)}
    adj = torch.eye(len(target_genes), dtype=torch.float32)
    with edge_path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            a = row.get("source_gene", "")
            b = row.get("target_gene", "")
            if a not in index or b not in index:
                continue
            score = float(row.get("score", 1.0) or 1.0)
            i = index[a]
            j = index[b]
            adj[i, j] = max(adj[i, j], score)
            adj[j, i] = max(adj[j, i], score)
    deg = adj.sum(dim=1).clamp_min(1e-6)
    return adj / deg.unsqueeze(1)


class GeneratedModel(nn.Module):
    artifact_usage = "string_k562_gene_graph"

    def __init__(self, spec) -> None:
        super().__init__()
        artifacts = dict(getattr(spec, "artifacts", {}) or {})
        target_genes = _load_target_genes(str(artifacts.get("data_dir", "")))
        if len(target_genes) != int(spec.n_targets):
            raise ValueError(f"target gene count {len(target_genes)} does not match n_targets {spec.n_targets}")
        graph_path = str(artifacts.get("string_graph_edges_path", "data/artifacts/string/k562_target_graph_edges.tsv"))
        adjacency = _load_adjacency(graph_path, target_genes)
        hidden = int(spec.hidden_dim)
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
        self.base_head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.mix_logit = nn.Parameter(torch.tensor(0.0))
        self.register_buffer("target_adjacency", adjacency, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        base = self.base_head(z).view(x.shape[0], self.n_targets, self.n_classes)
        adj = self.target_adjacency.to(device=x.device, dtype=x.dtype)
        propagated = torch.einsum("ij,bjc->bic", adj, base)
        mix = torch.sigmoid(self.mix_logit)
        return mix * propagated + (1.0 - mix) * base
"""



PATHWAY_POOLING_ENCODER = """from __future__ import annotations

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
"""



STRING_GNN_PERTURBATION_PROPAGATOR = """from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import torch
from torch import nn


def _load_target_genes(data_dir: str) -> list[str]:
    if not data_dir:
        raise ValueError("STRING GNN node requires spec.artifacts['data_dir']")
    path = Path(data_dir) / "train.npz"
    if not path.exists():
        raise FileNotFoundError(f"cannot load target genes from {path}")
    with np.load(path, allow_pickle=True) as z:
        return [str(x) for x in z["target_genes"].tolist()]


def _load_adjacency(path: str, target_genes: list[str], power: int = 2) -> torch.Tensor:
    edge_path = Path(path)
    if not edge_path.exists():
        raise FileNotFoundError(f"STRING graph edge artifact does not exist: {edge_path}")
    index = {gene: i for i, gene in enumerate(target_genes)}
    adj = torch.eye(len(target_genes), dtype=torch.float32)
    with edge_path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            a = row.get("source_gene", "")
            b = row.get("target_gene", "")
            if a not in index or b not in index:
                continue
            score = float(row.get("score", 1.0) or 1.0)
            i = index[a]
            j = index[b]
            adj[i, j] = max(adj[i, j], score)
            adj[j, i] = max(adj[j, i], score)
    deg = adj.sum(dim=1).clamp_min(1e-6)
    norm = adj / deg.unsqueeze(1)
    propagated = norm
    for _ in range(max(1, power) - 1):
        propagated = torch.matmul(propagated, norm)
    propagated = 0.5 * norm + 0.5 * propagated
    propagated = propagated / propagated.sum(dim=1, keepdim=True).clamp_min(1e-6)
    return propagated


class GeneratedModel(nn.Module):
    artifact_usage = "string_k562_gene_graph"

    def __init__(self, spec) -> None:
        super().__init__()
        artifacts = dict(getattr(spec, "artifacts", {}) or {})
        target_genes = _load_target_genes(str(artifacts.get("data_dir", "")))
        if len(target_genes) != int(spec.n_targets):
            raise ValueError(f"target gene count {len(target_genes)} does not match n_targets {spec.n_targets}")
        graph_path = str(artifacts.get("string_graph_edges_path", "data/artifacts/string/k562_target_graph_edges.tsv"))
        adjacency = _load_adjacency(graph_path, target_genes)
        hidden = int(spec.hidden_dim)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 64)), hidden, 128))
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
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.direct = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.mix_logit = nn.Parameter(torch.tensor(0.0))
        self.register_buffer("target_adjacency", adjacency, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        rank_logits = self.rank_head(z).view(x.shape[0], -1, self.n_classes)
        factor_logits = torch.einsum("brc,nr->bnc", rank_logits, self.target_factors)
        direct = self.direct(z).view(x.shape[0], self.n_targets, self.n_classes)
        base = 0.5 * factor_logits + 0.5 * direct
        adj = self.target_adjacency.to(device=x.device, dtype=x.dtype)
        propagated = torch.einsum("ij,bjc->bic", adj, base)
        mix = torch.sigmoid(self.mix_logit)
        return mix * propagated + (1.0 - mix) * base
"""



ESM2_GENE_PROJECTION = """from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    artifact_usage = "esm2_gene_embedding_h5ad_via_k562_esm2_feature_dataset"

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        input_dim = int(spec.input_dim)
        emb_dim = int(getattr(spec, "perturbation_embedding_dim", 1280) or 1280)
        if input_dim <= emb_dim:
            emb_dim = input_dim
        context_dim = input_dim - emb_dim
        if context_dim <= 0:
            context_dim = input_dim
            emb_dim = input_dim
        self.context_dim = context_dim
        self.emb_dim = emb_dim
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        dropout = float(spec.dropout)
        self.context_encoder = nn.Sequential(
            nn.Linear(context_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.esm2_encoder = nn.Sequential(
            nn.Linear(emb_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.gate = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.Sigmoid())
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        context = x[:, : self.context_dim]
        esm2 = x[:, -self.emb_dim :]
        c = self.context_encoder(context)
        e = self.esm2_encoder(esm2)
        gate = self.gate(torch.cat([c, e], dim=-1))
        z = c * (1.0 - gate) + e * gate
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
"""


OFFICIAL_TARGET_GENE_HEAD = """from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    def __init__(self, spec) -> None:
        super().__init__(spec, variant=\"target_gene_head\")
"""

OFFICIAL_STRING_GNN_ATTENTION = """from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    def __init__(self, spec) -> None:
        super().__init__(spec, variant=\"string_gnn_attention\")
"""

OFFICIAL_AIDO_LORA_ADAPTER = """from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    def __init__(self, spec) -> None:
        super().__init__(spec, variant=\"aido_lora_adapter\")
"""

OFFICIAL_AIDO_STRING_FUSION = """from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    def __init__(self, spec) -> None:
        super().__init__(spec, variant=\"aido_string_fusion\")
"""

OFFICIAL_NATIVE_PUBLIC_BEST_REIMPLEMENTATION = """from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    def __init__(self, spec) -> None:
        super().__init__(spec, variant=\"native_public_best_reimplementation\")
"""
