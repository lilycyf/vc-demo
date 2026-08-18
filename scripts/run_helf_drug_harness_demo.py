from __future__ import annotations

import argparse
import copy
import json
import math
import random
import shutil
import time
from pathlib import Path
from typing import Any

from vc_demo.train import train

SEARCH_TRANSFORMS = [
    {"id": "backbone_residual", "priority": 0.90, "cost": "medium"},
    {"id": "backbone_gated", "priority": 0.88, "cost": "medium"},
    {"id": "low_rank_head", "priority": 0.76, "cost": "cheap"},
    {"id": "mixture_of_experts", "priority": 0.82, "cost": "medium"},
    {"id": "film_residual", "priority": 0.80, "cost": "medium"},
    {"id": "temperature_calibration", "priority": 0.70, "cost": "cheap"},
    {"id": "feature_dropout", "priority": 0.72, "cost": "cheap"},
    {"id": "capacity_wide", "priority": 0.68, "cost": "medium"},
    {"id": "capacity_deep", "priority": 0.64, "cost": "medium"},
    {"id": "optimizer_low_lr", "priority": 0.58, "cost": "cheap"},
    {"id": "optimizer_high_lr", "priority": 0.56, "cost": "cheap"},
    {"id": "dropout_low", "priority": 0.60, "cost": "cheap"},
    {"id": "dropout_high", "priority": 0.52, "cost": "cheap"},
    {"id": "weighted_ce", "priority": 0.66, "cost": "cheap"},
    {"id": "focal_loss", "priority": 0.62, "cost": "cheap"},
]

MODEL_FOR_TRANSFORM = {
    "backbone_residual": "residual_mlp",
    "backbone_gated": "gated_mlp",
    "low_rank_head": "low_rank_mlp",
    "mixture_of_experts": "mixture_of_experts_mlp",
    "film_residual": "film_residual_mlp",
    "temperature_calibration": "temperature_calibrated_mlp",
    "feature_dropout": "feature_dropout_mlp",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_config(config: dict[str, Any], run_dir: Path, max_epochs: int) -> dict[str, Any]:
    out = run_dir / "nodes" / str(config["node_name"])
    started = time.time()
    metrics = train(config, out, max_epochs=max_epochs)
    metrics["duration_seconds"] = time.time() - started
    metrics["metrics_path"] = str(out / "metrics.json")
    return metrics


def add_node(tree: dict[str, Any], name: str, config_path: Path, parent: str, status: str, metrics: dict[str, Any] | None = None, proposal: dict[str, Any] | None = None) -> None:
    row = {"config": str(config_path), "parent": parent, "children": [], "status": status, "visits": 0, "value": 0.0}
    if metrics:
        row.update({"best_val_macro_f1": metrics["best_val_macro_f1"], "test_macro_f1": metrics["test_macro_f1"], "metrics": metrics.get("metrics_path", ""), "visits": 1, "value": float(metrics["best_val_macro_f1"])})
    if proposal:
        row.update({"strategy": proposal["strategy"], "proposal": str(config_path.parent / f"{name}.proposal.json"), "cheap_screen_score": proposal.get("cheap_screen_score", {})})
    tree["nodes"][name] = row
    if parent:
        tree["nodes"][parent].setdefault("children", []).append(name)
    else:
        tree.setdefault("root_nodes", []).append(name)


def backprop(tree: dict[str, Any], node: str, reward: float) -> None:
    path = []
    cur = node
    while cur:
        path.append(cur)
        row = tree["nodes"][cur]
        row["visits"] = int(row.get("visits", 0)) + 1
        row["value"] = float(row.get("value", 0.0)) + reward
        cur = str(row.get("parent") or "")
    tree["last_backprop_path"] = path


def uct_select_parent(tree: dict[str, Any], max_children: int, exploration: float) -> str:
    candidates = []
    total = sum(max(1, int(n.get("visits", 0))) for n in tree["nodes"].values() if n.get("status") == "trained")
    for name, node in tree["nodes"].items():
        if node.get("status") != "trained":
            continue
        if len(node.get("children", [])) >= max_children:
            continue
        visits = max(1, int(node.get("visits", 1)))
        q = float(node.get("value", 0.0)) / visits
        score = q + exploration * math.sqrt(math.log(total + 1.0) / visits)
        candidates.append((score, name))
    if not candidates:
        raise RuntimeError("no expandable trained parent remains")
    return sorted(candidates, reverse=True)[0][1]



def apply_foundation_augmentation(parent: dict[str, Any], transform: dict[str, Any], child_name: str) -> dict[str, Any]:
    """Materialize artifact-present foundation proposals as parent-preserving augmentation.

    The selected foundation artifact is a residual/gated correction on top of a
    strong dense parent path. It must not replace the dense branch unless a future
    blueprint explicitly marks itself as an ablation.
    """
    cfg = copy.deepcopy(parent)
    cfg["node_name"] = child_name
    model = cfg.setdefault("model", {})
    training = cfg.setdefault("training", {})
    model["model_type"] = "artifact_augmented_residual_mlp"
    model.setdefault("hidden_dim", 256)
    model.setdefault("depth", 2)
    model.setdefault("dropout", 0.15)
    model.setdefault("low_rank_dim", 64)
    artifacts = model.setdefault("artifacts", {})
    tables: list[dict[str, str]] = []
    required = set(transform.get("required_artifacts", []))
    if "reactome_pathway_membership" in required:
        tables.append({"artifact_id": "reactome_pathway_membership", "path": "data/artifacts/helf/reactome_pathway_membership.npz", "key": "target_gene_embeddings"})
    if "string_gene_graph" in required:
        tables.append({"artifact_id": "string_gene_graph", "path": "data/artifacts/helf/string_gene_graph_features.npz", "key": "target_gene_embeddings"})
    if "esm2_gene_or_protein_embeddings" in required:
        tables.append({"artifact_id": "esm2_gene_or_protein_embeddings", "path": "data/artifacts/helf/esm2_gene_embeddings.npz", "key": "target_gene_embeddings"})
    drug_tables: list[dict[str, str]] = []
    if "chemical_encoder_checkpoint_or_drug_fingerprints" in required:
        drug_tables.append({"artifact_id": "chemical_encoder_checkpoint_or_drug_fingerprints", "path": "data/artifacts/helf/drug_embeddings.npz", "key": "drug_embeddings"})
        artifacts["drug_onehot_dim"] = 10
    if not tables and not drug_tables:
        # Artifact-heavy checkpoints such as scGPT/Geneformer should remain in
        # acquisition/block unless a real aligned embedding artifact is built.
        tables.extend([])
    artifacts["artifact_tables"] = tables
    artifacts["drug_embedding_tables"] = drug_tables
    model["foundation_augmentation_policy"] = {
        "mode": "parent_dense_logits_plus_gated_artifact_residual",
        "preserve_parent_dense_path": True,
        "artifact_branch_initial_scale": "sigmoid(-2.5)",
        "no_fallback_or_proxy": True,
    }
    training.setdefault("loss_type", "cross_entropy")
    return cfg



def apply_artifact_matched_dense_control(parent: dict[str, Any], child_name: str, source_strategy: str) -> dict[str, Any]:
    """Create a no-artifact capacity/loss control paired to a foundation child.

    The control keeps the same parent and receives comparable dense capacity, but
    no artifact tables. This lets reports estimate whether a source-backed
    artifact added information beyond a stronger dense baseline.
    """
    cfg = copy.deepcopy(parent)
    cfg["node_name"] = child_name
    model = cfg.setdefault("model", {})
    training = cfg.setdefault("training", {})
    model["model_type"] = "residual_mlp"
    model["hidden_dim"] = min(max(int(model.get("hidden_dim", 256)) * 2, 256), 1024)
    model["depth"] = min(max(int(model.get("depth", 2)) + 1, 3), 5)
    model["dropout"] = max(float(model.get("dropout", 0.15)), 0.15)
    model.pop("foundation_augmentation_policy", None)
    model.setdefault("artifacts", {})["artifact_tables"] = []
    training.setdefault("loss_type", "cross_entropy")
    cfg.setdefault("metadata", {})["artifact_usefulness_control"] = {
        "control_type": "dense_matched_capacity_no_artifact",
        "paired_source_strategy": source_strategy,
        "purpose": "estimate capacity/loss gain separately from artifact incremental gain",
    }
    return cfg

def apply_transform(parent: dict[str, Any], transform_id: str, child_name: str) -> dict[str, Any]:
    cfg = copy.deepcopy(parent)
    cfg["node_name"] = child_name
    model = cfg.setdefault("model", {})
    training = cfg.setdefault("training", {})
    if transform_id in MODEL_FOR_TRANSFORM:
        model["model_type"] = MODEL_FOR_TRANSFORM[transform_id]
    if transform_id == "capacity_wide":
        model["hidden_dim"] = min(max(int(model.get("hidden_dim", 256)) * 2, 256), 1024)
    if transform_id == "capacity_deep":
        model["depth"] = min(int(model.get("depth", 2)) + 1, 5)
    if transform_id == "dropout_low":
        model["dropout"] = max(0.0, float(model.get("dropout", 0.1)) - 0.1)
    if transform_id == "dropout_high":
        model["dropout"] = min(0.5, float(model.get("dropout", 0.1)) + 0.15)
    if transform_id == "optimizer_low_lr":
        training["lr"] = max(5e-5, float(training.get("lr", 3e-4)) * 0.5)
    if transform_id == "optimizer_high_lr":
        training["lr"] = min(1e-3, float(training.get("lr", 3e-4)) * 1.7)
    if transform_id == "weighted_ce":
        training["loss_type"] = "weighted_cross_entropy"
        n_classes = model.get("n_classes", 12)
        n_classes = 12 if n_classes == "auto" else int(n_classes)
        training["class_weights"] = [1.0] * n_classes
    if transform_id == "focal_loss":
        training["loss_type"] = "focal_loss"
        training["focal_gamma"] = 2.0
    if transform_id == "low_rank_head":
        model["low_rank_dim"] = min(max(int(model.get("low_rank_dim", 32)), 8), 64)
    return cfg


def cheap_score(transform: dict[str, Any], parent_val: float, seen_strategy_count: int) -> dict[str, Any]:
    cost_bonus = {"cheap": 0.04, "medium": 0.0, "expensive": -0.05}.get(transform.get("cost"), 0.0)
    novelty = 0.08 if seen_strategy_count == 0 else -0.04 * seen_strategy_count
    score = parent_val + float(transform["priority"]) * 0.1 + cost_bonus + novelty
    return {"score": score, "parent_val": parent_val, "priority": transform["priority"], "cost_bonus": cost_bonus, "novelty": novelty}



def load_artifact_registry(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = read_json(path)
    return {str(item.get("id")): item for item in payload.get("artifacts", [])}


def artifact_is_present(item: dict[str, Any]) -> bool:
    expected = item.get("path") or item.get("expected_path")
    if not expected:
        return False
    path = Path(str(expected))
    if not path.exists():
        return False
    if path.is_dir():
        return any(child.is_file() for child in path.rglob("*"))
    return path.is_file() and path.stat().st_size > 0


def missing_required_artifacts(required: list[str], registry: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    missing = []
    for artifact_id in required:
        item = registry.get(artifact_id, {"id": artifact_id, "status": "not_registered"})
        if not artifact_is_present(item):
            missing.append({
                "artifact_id": artifact_id,
                "expected_path": item.get("expected_path"),
                "status": item.get("status", "missing"),
                "acquisition_policy": item.get("acquisition_policy", "unknown"),
                "provenance_requirement": item.get("provenance_requirement", "source-backed validation required"),
            })
    return missing


def load_foundation_blueprints(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = read_json(path)
    blueprints: list[dict[str, Any]] = []
    for family_index, family in enumerate(payload.get("foundation_families", [])):
        family_id = str(family.get("id") or family.get("family") or family.get("name") or f"family_{family_index}")
        for blueprint_index, blueprint in enumerate(family.get("blueprints", [])):
            blueprint_id = str(blueprint.get("id") or f"blueprint_{family_index}_{blueprint_index}")
            blueprints.append({
                "id": f"foundation_{blueprint_id}",
                "blueprint_id": blueprint_id,
                "family": family_id,
                "priority": 1.10 - min(0.30, 0.01 * len(blueprints)),
                "cost": "artifact_required",
                "proposal_type": "foundation_artifact_blueprint",
                "required_artifacts": [str(x) for x in blueprint.get("required_artifacts", [])],
                "codex_action": blueprint.get("codex_action", "source-backed implementation required"),
            })
    return blueprints


def _has_present_required_artifacts(transform: dict[str, Any], registry: dict[str, dict[str, Any]]) -> bool:
    required = transform.get("required_artifacts", [])
    return bool(required) and not missing_required_artifacts(required, registry)


def choose_candidate_pool(transforms: list[dict[str, Any]], foundation: list[dict[str, Any]], parent_val: float, strategy_counts: dict[str, int], rng: random.Random, pool_size: int, registry: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    light = transforms[:]
    found = foundation[:]
    registry = registry or {}
    rng.shuffle(light)
    rng.shuffle(found)
    light = sorted(light, key=lambda t: cheap_score(t, parent_val, strategy_counts.get(t["id"], 0))["score"], reverse=True)
    found = sorted(found, key=lambda t: cheap_score(t, parent_val, strategy_counts.get(t["id"], 0))["score"], reverse=True)

    present_foundation = [t for t in found if _has_present_required_artifacts(t, registry)]
    other_foundation = [t for t in found if t not in present_foundation]
    foundation_slots = min(len(found), max(1, pool_size // 2)) if found else 0
    executable_slots = min(len(present_foundation), max(1, foundation_slots // 2)) if present_foundation else 0
    selected = present_foundation[:executable_slots]
    selected.extend(other_foundation[: max(0, foundation_slots - len(selected))])
    selected.extend([t for t in present_foundation[executable_slots:] if t not in selected][: max(0, foundation_slots - len(selected))])
    selected.extend(light[: max(0, pool_size - len(selected))])
    return selected[:pool_size]


def write_trace(run_dir: Path, event: dict[str, Any]) -> None:
    with (run_dir / "mcts_trace.jsonl").open("a") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")

def best_rows(tree: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    trained = [(name, n) for name, n in tree["nodes"].items() if n.get("status") == "trained"]
    best_root = max(((name, n) for name, n in trained if not n.get("parent")), key=lambda x: x[1].get("best_val_macro_f1", -1))[1]
    children = [(name, n) for name, n in trained if n.get("parent")]
    best_child = max(children, key=lambda x: x[1].get("best_val_macro_f1", -1))[1] if children else None
    return best_root, best_child



def _node_val(node: dict[str, Any]) -> float | None:
    value = node.get("best_val_macro_f1")
    return float(value) if value is not None else None


def _node_test(node: dict[str, Any]) -> float | None:
    value = node.get("test_macro_f1")
    return float(value) if value is not None else None


def build_artifact_usefulness_summary(tree: dict[str, Any]) -> dict[str, Any]:
    nodes = tree.get("nodes", {})
    trained = {name: node for name, node in nodes.items() if node.get("status") == "trained"}
    roots = {name: node for name, node in trained.items() if not node.get("parent")}
    foundation = {
        name: node for name, node in trained.items()
        if node.get("proposal_type") == "foundation_artifact_blueprint"
        and node.get("required_artifacts")
        and not node.get("missing_required_artifacts")
    }
    controls = {name: node for name, node in trained.items() if node.get("proposal_type") == "artifact_usefulness_control"}
    best_root = max(roots.items(), key=lambda item: _node_val(item[1]) or -1.0, default=("", {}))
    best_foundation = max(foundation.items(), key=lambda item: _node_val(item[1]) or -1.0, default=("", {}))
    best_control = max(controls.items(), key=lambda item: _node_val(item[1]) or -1.0, default=("", {}))
    paired_rows = []
    for control_name, control in controls.items():
        artifact_name = str(control.get("paired_artifact_child") or "")
        artifact = trained.get(artifact_name)
        if not artifact:
            continue
        c_val = _node_val(control)
        a_val = _node_val(artifact)
        paired_rows.append({
            "artifact_child": artifact_name,
            "control_child": control_name,
            "artifact_strategy": artifact.get("strategy"),
            "artifact_val_macro_f1": a_val,
            "artifact_test_macro_f1": _node_test(artifact),
            "control_val_macro_f1": c_val,
            "control_test_macro_f1": _node_test(control),
            "artifact_incremental_val_gain": (a_val - c_val) if a_val is not None and c_val is not None else None,
        })
    root_val = _node_val(best_root[1]) if best_root[1] else None
    found_val = _node_val(best_foundation[1]) if best_foundation[1] else None
    control_val = _node_val(best_control[1]) if best_control[1] else None
    return {
        "best_root": {"node": best_root[0], "val_macro_f1": root_val, "test_macro_f1": _node_test(best_root[1]) if best_root[1] else None},
        "best_foundation_artifact_child": {"node": best_foundation[0], "val_macro_f1": found_val, "test_macro_f1": _node_test(best_foundation[1]) if best_foundation[1] else None},
        "best_dense_matched_no_artifact_control": {"node": best_control[0], "val_macro_f1": control_val, "test_macro_f1": _node_test(best_control[1]) if best_control[1] else None},
        "foundation_vs_root_val_gain": (found_val - root_val) if found_val is not None and root_val is not None else None,
        "foundation_vs_dense_control_val_gain": (found_val - control_val) if found_val is not None and control_val is not None else None,
        "paired_comparisons": paired_rows,
        "trained_foundation_artifact_children": len(foundation),
        "trained_dense_matched_controls": len(controls),
        "interpretation": "artifact useful beyond capacity" if found_val is not None and control_val is not None and found_val > control_val else "artifact gain not proven beyond dense matched-capacity control",
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small VCHarness-style HELF demo over NPZ task data.")
    parser.add_argument("--root-configs", nargs="+", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--experiment", default="helf_drug_harness_demo")
    parser.add_argument("--budget-proposals", type=int, default=48)
    parser.add_argument("--budget-trained-nodes", type=int, default=16)
    parser.add_argument("--candidate-pool-size", type=int, default=4)
    parser.add_argument("--max-children", type=int, default=6)
    parser.add_argument("--max-epochs", type=int, default=6)
    parser.add_argument("--exploration", type=float, default=1.2)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--search-space-config", type=Path, default=Path("configs/helf_perturb_search_space.json"))
    parser.add_argument("--artifact-registry", type=Path, default=Path("configs/artifacts/helf_perturb_registry.json"))
    args = parser.parse_args()

    if args.reset and args.run_dir.exists():
        shutil.rmtree(args.run_dir)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    proposal_dir = args.run_dir / "proposals"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    first_root = read_json(Path(args.root_configs[0]))
    data_dir = Path(first_root.get("dataset", {}).get("data_dir", ""))
    task_manifest = {}
    if data_dir and (data_dir / "manifest.json").exists():
        task_manifest = read_json(data_dir / "manifest.json")
    task_id = str(task_manifest.get("task_id", "HELF_DEMO"))
    task_label = str(task_manifest.get("task_type", task_id))
    artifact_registry = load_artifact_registry(args.artifact_registry)
    foundation_blueprints = load_foundation_blueprints(args.search_space_config)
    artifact_audit = {artifact_id: {**item, "present": artifact_is_present(item)} for artifact_id, item in artifact_registry.items()}
    write_json(args.run_dir / "artifact_registry_audit.json", {"registry": str(args.artifact_registry), "artifacts": artifact_audit})
    acquisition_queue: dict[str, Any] = {"items": []}
    tree = {"experiment": args.experiment, "task_id": task_id, "task_type": task_label, "nodes": {}, "root_nodes": [], "events": [], "search_space_config": str(args.search_space_config), "artifact_registry": str(args.artifact_registry)}
    rng = random.Random(args.seed)

    for root in args.root_configs:
        cfg_path = Path(root)
        cfg = read_json(cfg_path)
        metrics = run_config(cfg, args.run_dir, args.max_epochs)
        add_node(tree, cfg["node_name"], cfg_path, "", "trained", metrics)
    generated = trained_children = failed = blocked = skipped = 0
    artifact_usefulness_controls_generated = 0
    strategy_counts: dict[str, int] = {}
    queued: list[tuple[float, str]] = []
    stop_reason = "budget exhausted"

    while generated < args.budget_proposals or queued:
        if trained_children >= args.budget_trained_nodes:
            stop_reason = f"trained-node budget exhausted ({trained_children}/{args.budget_trained_nodes})"
            break
        if generated < args.budget_proposals:
            parent = uct_select_parent(tree, args.max_children, args.exploration)
            parent_cfg = read_json(Path(tree["nodes"][parent]["config"]))
            parent_val = float(tree["nodes"][parent].get("best_val_macro_f1", 0.0))
            transforms = choose_candidate_pool(SEARCH_TRANSFORMS, foundation_blueprints, parent_val, strategy_counts, rng, args.candidate_pool_size, artifact_registry)
            write_trace(args.run_dir, {"event": "proposal_pool_generated", "parent": parent, "pool_size": len(transforms), "foundation_candidates": sum(1 for t in transforms if t.get("proposal_type") == "foundation_artifact_blueprint"), "materializable_foundation_candidates": sum(1 for t in transforms if t.get("proposal_type") == "foundation_artifact_blueprint" and _has_present_required_artifacts(t, artifact_registry))})
            for rank, transform in enumerate(transforms, start=1):
                if generated >= args.budget_proposals:
                    break
                generated += 1
                child = f"{parent}_p{generated}_{transform['id']}"
                missing_artifacts = missing_required_artifacts(transform.get("required_artifacts", []), artifact_registry)
                if transform.get("proposal_type") == "foundation_artifact_blueprint" and not missing_artifacts:
                    cfg = apply_foundation_augmentation(parent_cfg, transform, child)
                else:
                    cfg = apply_transform(parent_cfg, transform["id"], child) if not transform.get("proposal_type") else copy.deepcopy(parent_cfg)
                    cfg["node_name"] = child
                score_row = cheap_score(transform, parent_val, strategy_counts.get(transform["id"], 0))
                if transform.get("proposal_type") == "foundation_artifact_blueprint" and transform.get("required_artifacts") and not missing_artifacts:
                    score_row = {**score_row, "rollout_feasibility_bonus": 0.08, "score": float(score_row["score"]) + 0.08}
                proposal = {
                    "strategy": transform["id"],
                    "parent": parent,
                    "child": child,
                    "candidate_rank": rank,
                    "candidate_pool_size": args.candidate_pool_size,
                    "proposal_type": transform.get("proposal_type", "lightweight_executable_transform"),
                    "blueprint_id": transform.get("blueprint_id"),
                    "family": transform.get("family"),
                    "required_artifacts": transform.get("required_artifacts", []),
                    "missing_required_artifacts": missing_artifacts,
                    "codex_action": transform.get("codex_action"),
                    "cheap_screen_score": score_row,
                    "hypothesis": f"Test {transform['id']} for {task_label}.",
                }
                cfg.setdefault("metadata", {})["proposal_type"] = proposal["proposal_type"]
                cfg["metadata"]["required_artifacts"] = proposal["required_artifacts"]
                cfg_path = proposal_dir / f"{child}.json"
                prop_path = proposal_dir / f"{child}.proposal.json"
                write_json(cfg_path, cfg)
                write_json(prop_path, proposal)
                add_node(tree, child, cfg_path, parent, "candidate_queued", proposal=proposal)
                tree["nodes"][child]["proposal_type"] = proposal["proposal_type"]
                tree["nodes"][child]["required_artifacts"] = proposal["required_artifacts"]
                tree["nodes"][child]["missing_required_artifacts"] = missing_artifacts
                queued.append((proposal["cheap_screen_score"]["score"], child))
                if proposal["proposal_type"] == "foundation_artifact_blueprint" and proposal["required_artifacts"] and not missing_artifacts:
                    control_child = f"{child}_dense_control"
                    control_cfg = apply_artifact_matched_dense_control(parent_cfg, control_child, transform["id"])
                    control_score = {
                        "score": float(score_row["score"]) - 0.025,
                        "parent_val": parent_val,
                        "priority": transform["priority"],
                        "cost_bonus": 0.0,
                        "novelty": 0.0,
                        "paired_control_for": child,
                    }
                    control_proposal = {
                        "strategy": "dense_matched_capacity_no_artifact_control",
                        "parent": parent,
                        "child": control_child,
                        "candidate_rank": rank,
                        "candidate_pool_size": args.candidate_pool_size,
                        "proposal_type": "artifact_usefulness_control",
                        "paired_artifact_child": child,
                        "paired_source_strategy": transform["id"],
                        "required_artifacts": [],
                        "missing_required_artifacts": [],
                        "codex_action": "train a no-artifact dense matched-capacity control for artifact incremental gain attribution",
                        "cheap_screen_score": control_score,
                        "hypothesis": f"Control for capacity/loss gain paired with {transform['id']} for {task_label}.",
                    }
                    control_cfg.setdefault("metadata", {})["proposal_type"] = control_proposal["proposal_type"]
                    control_cfg["metadata"]["paired_artifact_child"] = child
                    control_cfg_path = proposal_dir / f"{control_child}.json"
                    control_prop_path = proposal_dir / f"{control_child}.proposal.json"
                    write_json(control_cfg_path, control_cfg)
                    write_json(control_prop_path, control_proposal)
                    add_node(tree, control_child, control_cfg_path, parent, "candidate_queued", proposal=control_proposal)
                    tree["nodes"][control_child]["proposal_type"] = control_proposal["proposal_type"]
                    tree["nodes"][control_child]["required_artifacts"] = []
                    tree["nodes"][control_child]["missing_required_artifacts"] = []
                    tree["nodes"][control_child]["paired_artifact_child"] = child
                    queued.append((control_score["score"], control_child))
                    artifact_usefulness_controls_generated += 1
                    write_trace(args.run_dir, {"event": "artifact_usefulness_control_generated", "artifact_child": child, "control_child": control_child, "source_strategy": transform["id"]})
            write_json(args.run_dir / "tree.json", tree)
        if not queued:
            stop_reason = f"proposal budget exhausted ({generated}/{args.budget_proposals})"
            break
        queued.sort(reverse=True)
        _, selected = queued.pop(0)
        node = tree["nodes"][selected]
        proposal = read_json(Path(node["proposal"]))
        node["status"] = "selected_for_training"
        write_trace(args.run_dir, {"event": "selected_for_training", "node": selected, "proposal_type": proposal.get("proposal_type"), "strategy": proposal.get("strategy")})
        if proposal.get("missing_required_artifacts"):
            node.update({"status": "requires_artifact_acquisition", "blocked_reason": "missing source-backed foundation artifact", "missing_required_artifacts": proposal.get("missing_required_artifacts", [])})
            acquisition_queue["items"].append({"node": selected, "proposal": node.get("proposal"), "strategy": proposal.get("strategy"), "family": proposal.get("family"), "missing_required_artifacts": proposal.get("missing_required_artifacts", []), "resolution": "block until source, shape, vocabulary/order, and provenance can be verified"})
            write_json(args.run_dir / "acquisition_queue.json", acquisition_queue)
            write_trace(args.run_dir, {"event": "artifact_acquisition_block", "node": selected, "missing_required_artifacts": proposal.get("missing_required_artifacts", [])})
            blocked += 1
            write_json(args.run_dir / "tree.json", tree)
            continue
        if proposal.get("proposal_type") == "foundation_artifact_blueprint":
            cfg_for_foundation = read_json(Path(node["config"]))
            artifacts_cfg = cfg_for_foundation.get("model", {}).get("artifacts", {})
            tables = artifacts_cfg.get("artifact_tables", [])
            drug_tables = artifacts_cfg.get("drug_embedding_tables", [])
            if not tables and not drug_tables:
                node.update({"status": "implementation_skipped", "blocked_reason": "selected foundation blueprint requires a real aligned model/embedding artifact that has not been materialized"})
                skipped += 1
                write_trace(args.run_dir, {"event": "implementation_skipped", "node": selected, "reason": node.get("blocked_reason")})
                write_json(args.run_dir / "tree.json", tree)
                continue
            node["foundation_augmentation_policy"] = cfg_for_foundation.get("model", {}).get("foundation_augmentation_policy", {})
        try:
            metrics = run_config(read_json(Path(node["config"])), args.run_dir, args.max_epochs)
            node.update({"status": "trained", "best_val_macro_f1": metrics["best_val_macro_f1"], "test_macro_f1": metrics["test_macro_f1"], "metrics": metrics.get("metrics_path", str(args.run_dir / "nodes" / selected / "metrics.json")), "visits": 1, "value": float(metrics["best_val_macro_f1"])})
            strategy_counts[proposal["strategy"]] = strategy_counts.get(proposal["strategy"], 0) + 1
            backprop(tree, selected, float(metrics["best_val_macro_f1"]))
            write_trace(args.run_dir, {"event": "trained_and_backpropagated", "node": selected, "reward": float(metrics["best_val_macro_f1"])})
            trained_children += 1
        except Exception as exc:
            node.update({"status": "failed", "error": repr(exc)})
            failed += 1
        write_json(args.run_dir / "tree.json", tree)

    for _, name in queued:
        if tree["nodes"].get(name, {}).get("status") == "candidate_queued":
            tree["nodes"][name]["status"] = "pruned_not_selected"
            tree["nodes"][name]["pruned_reason"] = "not selected before trained-node budget/stop condition"
            write_trace(args.run_dir, {"event": "proposal_pruned", "node": name, "reason": tree["nodes"][name]["pruned_reason"]})
    best_root, best_child = best_rows(tree)
    summary = {
        "experiment": args.experiment,
        "run_dir": str(args.run_dir),
        "stop_reason": stop_reason,
        "generated_proposals": generated,
        "trained_selected_rollouts": trained_children,
        "generated_artifact_usefulness_controls": artifact_usefulness_controls_generated,
        "pruned_not_selected": sum(1 for n in tree["nodes"].values() if n.get("status") == "pruned_not_selected"),
        "skipped": skipped,
        "blocked": blocked,
        "requires_artifact_acquisition": sum(1 for n in tree["nodes"].values() if n.get("status") == "requires_artifact_acquisition"),
        "failed": failed,
        "best_root": best_root,
        "best_generated_child": best_child,
        "fallback_count": 0,
        "proxy_count": 0,
        "backprop_nontrained_count": 0,
        "artifact_blockers": blocked,
    }
    trained_foundation = sum(1 for n in tree["nodes"].values() if n.get("status") == "trained" and n.get("proposal_type") == "foundation_artifact_blueprint")
    summary["trained_foundation_artifact_children"] = trained_foundation
    artifact_usefulness = build_artifact_usefulness_summary(tree)
    summary["artifact_usefulness"] = artifact_usefulness
    write_json(args.run_dir / "artifact_usefulness_report.json", artifact_usefulness)
    write_json(args.run_dir / "tree.json", tree)
    write_json(args.run_dir / "run_manifest.json", summary)
    lines = [f"# {task_id} Harness Demo Report", "", f"- Task type: `{task_label}`", f"- Stop reason: `{stop_reason}`", f"- Generated proposals: `{generated}`", f"- Trained selected rollouts: `{trained_children}`", f"- Generated artifact-usefulness controls: `{artifact_usefulness_controls_generated}`", f"- Trained foundation-artifact children: `{trained_foundation}`", f"- Pruned not selected: `{summary['pruned_not_selected']}`", f"- Requires artifact acquisition / blocked: `{summary['requires_artifact_acquisition']}`", f"- Skipped: `{skipped}`", f"- Failed: `{failed}`", f"- Fallback/proxy count: `0`", f"- Backprop non-trained count: `0`", "", "## Artifact Policy", "", "Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.", "", "## Best Root", "", f"- Val Macro-F1: `{best_root.get('best_val_macro_f1')}`", f"- Test Macro-F1: `{best_root.get('test_macro_f1')}`", "", "## Best Generated Child", ""]
    if best_child:
        lines += [f"- Strategy: `{best_child.get('strategy')}`", f"- Val Macro-F1: `{best_child.get('best_val_macro_f1')}`", f"- Test Macro-F1: `{best_child.get('test_macro_f1')}`"]
    else:
        lines.append("No generated child was trained.")
    lines += ["", "## Artifact Usefulness", ""]
    artifact_usefulness = summary.get("artifact_usefulness", {})
    lines += [
        f"- Best foundation-artifact child: `{artifact_usefulness.get('best_foundation_artifact_child', {}).get('node')}` val={artifact_usefulness.get('best_foundation_artifact_child', {}).get('val_macro_f1')}",
        f"- Best dense matched no-artifact control: `{artifact_usefulness.get('best_dense_matched_no_artifact_control', {}).get('node')}` val={artifact_usefulness.get('best_dense_matched_no_artifact_control', {}).get('val_macro_f1')}",
        f"- Foundation vs root val gain: `{artifact_usefulness.get('foundation_vs_root_val_gain')}`",
        f"- Foundation vs dense-control val gain: `{artifact_usefulness.get('foundation_vs_dense_control_val_gain')}`",
        f"- Interpretation: `{artifact_usefulness.get('interpretation')}`",
    ]
    paired = artifact_usefulness.get("paired_comparisons", [])
    if paired:
        lines += ["", "| Artifact child | Dense control | Artifact val | Control val | Incremental val gain |", "|---|---|---:|---:|---:|"]
        for row in paired[:20]:
            lines.append(f"| `{row.get('artifact_child')}` | `{row.get('control_child')}` | {row.get('artifact_val_macro_f1')} | {row.get('control_val_macro_f1')} | {row.get('artifact_incremental_val_gain')} |")
    if acquisition_queue["items"]:
        lines += ["", "## Acquisition / Blocker Summary", ""]
        for item in acquisition_queue["items"][:20]:
            missing_ids = ", ".join(x.get("artifact_id", "unknown") for x in item.get("missing_required_artifacts", []))
            lines.append(f"- `{item.get('strategy')}` blocked for `{missing_ids}`.")
    (args.run_dir / "final_report.md").write_text("\n".join(lines) + "\n")
    (args.run_dir / "search_summary.md").write_text("\n".join(lines) + "\n")
    if not acquisition_queue["items"]:
        write_json(args.run_dir / "acquisition_queue.json", acquisition_queue)
    write_json(args.run_dir / "implementation_queue.json", {"items": []})
    write_json(args.run_dir / "failures.json", {"items": [n for n in tree["nodes"].values() if n.get("status") == "failed"]})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
