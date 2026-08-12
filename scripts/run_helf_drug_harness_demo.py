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
        active_children = [
            child for child in node.get("children", [])
            if tree["nodes"].get(child, {}).get("status") not in {
                "requires_artifact_acquisition",
                "blocked_missing_artifact",
                "skipped_artifact_suppressed",
                "pruned_not_selected",
                "failed",
                "needs_implementation",
            }
        ]
        if len(active_children) >= max_children:
            continue
        visits = max(1, int(node.get("visits", 1)))
        q = float(node.get("value", 0.0)) / visits
        score = q + exploration * math.sqrt(math.log(total + 1.0) / visits)
        candidates.append((score, name))
    if not candidates:
        raise RuntimeError("no expandable trained parent remains")
    return sorted(candidates, reverse=True)[0][1]


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




def companion_artifact_manifest(artifact_path: str | Path) -> Path:
    path = Path(str(artifact_path))
    if path.suffix:
        return path.with_suffix(path.suffix + ".manifest.json")
    return path / "artifact_manifest.json"


def apply_foundation_blueprint(parent: dict[str, Any], transform: dict[str, Any], child_name: str, registry: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], bool, str]:
    cfg = copy.deepcopy(parent)
    cfg["node_name"] = child_name
    blueprint_id = str(transform.get("blueprint_id") or "")
    required = list(transform.get("required_artifacts", []))
    if blueprint_id in {"pathway_pooling_encoder", "esm2_target_gene_head", "protein_embedding_fusion", "string_graph_message_passing", "graph_laplacian_head"} and required:
        artifact = registry.get(required[0], {})
        artifact_path = artifact.get("path") or artifact.get("expected_path") or ""
        manifest_path = companion_artifact_manifest(artifact_path)
        if manifest_path.exists():
            model = cfg.setdefault("model", {})
            model["model_type"] = "target_aware_bilinear"
            model["artifact_manifest_path"] = str(manifest_path)
            model.setdefault("low_rank_dim", 64)
            cfg.setdefault("metadata", {})["foundation_materializer"] = "target_aware_bilinear_from_aligned_target_artifact"
            cfg["metadata"]["artifact_manifest_path"] = str(manifest_path)
            return cfg, True, "materialized target_aware_bilinear from aligned target artifact manifest"
        return cfg, False, f"missing companion artifact manifest: {manifest_path}"
    return cfg, False, f"no native materializer for foundation blueprint {blueprint_id}"

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


def choose_candidate_pool(transforms: list[dict[str, Any]], foundation: list[dict[str, Any]], parent_val: float, strategy_counts: dict[str, int], rng: random.Random, pool_size: int, suppressed_artifacts: set[str], blocked_blueprints: set[str]) -> list[dict[str, Any]]:
    light = transforms[:]
    found = [bp for bp in foundation if bp.get("blueprint_id") not in blocked_blueprints and not any(str(a) in suppressed_artifacts for a in bp.get("required_artifacts", []))]
    rng.shuffle(light)
    rng.shuffle(found)
    light = sorted(light, key=lambda t: cheap_score(t, parent_val, strategy_counts.get(t["id"], 0))["score"], reverse=True)
    found = sorted(found, key=lambda t: (bool(t.get("all_required_artifacts_present")), cheap_score(t, parent_val, strategy_counts.get(t["id"], 0))["score"]), reverse=True)
    foundation_slots = min(len(found), max(1, pool_size // 2)) if found else 0
    selected = found[:foundation_slots]
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
    for blueprint in foundation_blueprints:
        required = list(blueprint.get("required_artifacts", []))
        ready = bool(required) and not missing_required_artifacts(required, artifact_registry)
        blueprint["all_required_artifacts_present"] = ready
        if ready:
            blueprint["priority"] = float(blueprint.get("priority", 0.0)) + 0.75
    write_json(args.run_dir / "artifact_registry_audit.json", {"registry": str(args.artifact_registry), "artifacts": artifact_audit, "ready_foundation_blueprints": [bp for bp in foundation_blueprints if bp.get("all_required_artifacts_present")]})
    acquisition_queue: dict[str, Any] = {"items": []}
    suppressed_artifacts: set[str] = set()
    blocked_blueprints: set[str] = set()
    tree = {"experiment": args.experiment, "task_id": task_id, "task_type": task_label, "nodes": {}, "root_nodes": [], "events": [], "search_space_config": str(args.search_space_config), "artifact_registry": str(args.artifact_registry)}
    rng = random.Random(args.seed)

    for root in args.root_configs:
        cfg_path = Path(root)
        cfg = read_json(cfg_path)
        metrics = run_config(cfg, args.run_dir, args.max_epochs)
        add_node(tree, cfg["node_name"], cfg_path, "", "trained", metrics)
    generated = trained_children = failed = blocked = skipped = 0
    strategy_counts: dict[str, int] = {}
    queued: list[tuple[float, str]] = []
    stop_reason = "budget exhausted"

    while generated < args.budget_proposals or queued:
        if trained_children >= args.budget_trained_nodes:
            stop_reason = f"trained-node budget exhausted ({trained_children}/{args.budget_trained_nodes})"
            break
        if generated < args.budget_proposals:
            try:
                parent = uct_select_parent(tree, args.max_children, args.exploration)
            except RuntimeError:
                stop_reason = f"no expandable trained parent remains after {generated} generated proposals; draining queued candidates"
                if not queued:
                    break
                parent = ""
            if parent:
                parent_cfg = read_json(Path(tree["nodes"][parent]["config"]))
                parent_val = float(tree["nodes"][parent].get("best_val_macro_f1", 0.0))
                transforms = choose_candidate_pool(SEARCH_TRANSFORMS, foundation_blueprints, parent_val, strategy_counts, rng, args.candidate_pool_size, suppressed_artifacts, blocked_blueprints)
                write_trace(args.run_dir, {"event": "proposal_pool_generated", "parent": parent, "pool_size": len(transforms), "foundation_candidates": sum(1 for t in transforms if t.get("proposal_type") == "foundation_artifact_blueprint")})
                for rank, transform in enumerate(transforms, start=1):
                    if generated >= args.budget_proposals:
                        break
                    generated += 1
                    child = f"{parent}_p{generated}_{transform['id']}"
                    if transform.get("proposal_type"):
                        cfg, materialized, materialization_note = apply_foundation_blueprint(parent_cfg, transform, child, artifact_registry)
                    else:
                        cfg = apply_transform(parent_cfg, transform["id"], child)
                        materialized, materialization_note = True, "lightweight executable transform"
                    missing_artifacts = missing_required_artifacts(transform.get("required_artifacts", []), artifact_registry)
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
                        "materialized": materialized,
                        "materialization_note": materialization_note,
                        "codex_action": transform.get("codex_action"),
                        "cheap_screen_score": cheap_score(transform, parent_val, strategy_counts.get(transform["id"], 0)),
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
                    tree["nodes"][child]["materialized"] = materialized
                    tree["nodes"][child]["materialization_note"] = materialization_note
                    queued.append((proposal["cheap_screen_score"]["score"], child))
            write_json(args.run_dir / "tree.json", tree)
        if not queued:
            stop_reason = f"proposal budget exhausted ({generated}/{args.budget_proposals})"
            break
        queued.sort(reverse=True)
        selected = ""
        proposal: dict[str, Any] = {}
        node: dict[str, Any] = {}
        while queued:
            _, candidate = queued.pop(0)
            candidate_node = tree["nodes"][candidate]
            candidate_proposal = read_json(Path(candidate_node["proposal"]))
            candidate_artifacts = {str(x) for x in candidate_proposal.get("required_artifacts", [])}
            candidate_blueprint = str(candidate_proposal.get("blueprint_id") or "")
            if candidate_artifacts.intersection(suppressed_artifacts) or candidate_blueprint in blocked_blueprints:
                candidate_node["status"] = "skipped_artifact_suppressed"
                candidate_node["skipped_reason"] = "artifact or blueprint was blocked by a prior source-backed acquisition check"
                write_trace(args.run_dir, {"event": "proposal_skipped", "node": candidate, "reason": candidate_node["skipped_reason"], "suppressed_artifacts": sorted(suppressed_artifacts)})
                skipped += 1
                continue
            selected = candidate
            node = candidate_node
            proposal = candidate_proposal
            break
        if not selected:
            continue
        node["status"] = "selected_for_training"
        write_trace(args.run_dir, {"event": "selected_for_training", "node": selected, "proposal_type": proposal.get("proposal_type"), "strategy": proposal.get("strategy")})
        if proposal.get("missing_required_artifacts"):
            node.update({"status": "requires_artifact_acquisition", "blocked_reason": "missing source-backed foundation artifact", "missing_required_artifacts": proposal.get("missing_required_artifacts", [])})
            for missing in proposal.get("missing_required_artifacts", []):
                artifact_id = str(missing.get("artifact_id", "unknown"))
                suppressed_artifacts.add(artifact_id)
                acquisition_queue["items"].append({"artifact_id": artifact_id, "expected_path": missing.get("expected_path"), "node": selected, "proposal": node.get("proposal"), "strategy": proposal.get("strategy"), "family": proposal.get("family"), "missing_required_artifacts": [missing], "resolution": "block until source, shape, vocabulary/order, and provenance can be verified"})
            if proposal.get("blueprint_id"):
                blocked_blueprints.add(str(proposal.get("blueprint_id")))
            write_json(args.run_dir / "acquisition_queue.json", acquisition_queue)
            write_trace(args.run_dir, {"event": "artifact_acquisition_block", "node": selected, "missing_required_artifacts": proposal.get("missing_required_artifacts", []), "suppressed_artifacts": sorted(suppressed_artifacts)})
            blocked += 1
            write_json(args.run_dir / "tree.json", tree)
            continue
        if proposal.get("proposal_type") == "foundation_artifact_blueprint" and not proposal.get("materialized"):
            node.update({"status": "needs_implementation", "blocked_reason": "foundation artifact is present but this demo runner has no automatic model materializer"})
            skipped += 1
            if proposal.get("blueprint_id"):
                blocked_blueprints.add(str(proposal.get("blueprint_id")))
            write_json(args.run_dir / "implementation_queue.json", {"items": [{"node": selected, "proposal": node.get("proposal"), "reason": node.get("blocked_reason")}]})
            write_json(args.run_dir / "tree.json", tree)
            continue
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
        "pruned_not_selected": sum(1 for n in tree["nodes"].values() if n.get("status") == "pruned_not_selected"),
        "skipped_artifact_suppressed": sum(1 for n in tree["nodes"].values() if n.get("status") == "skipped_artifact_suppressed"),
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
        "suppressed_artifacts": sorted(suppressed_artifacts),
        "blocked_blueprints": sorted(blocked_blueprints),
    }
    write_json(args.run_dir / "tree.json", tree)
    write_json(args.run_dir / "run_manifest.json", summary)
    lines = [f"# {task_id} Harness Demo Report", "", f"- Task type: `{task_label}`", f"- Stop reason: `{stop_reason}`", f"- Generated proposals: `{generated}`", f"- Trained selected rollouts: `{trained_children}`", f"- Pruned not selected: `{summary['pruned_not_selected']}`", f"- Requires artifact acquisition / blocked: `{summary['requires_artifact_acquisition']}`", f"- Skipped: `{skipped}`", f"- Failed: `{failed}`", f"- Fallback/proxy count: `0`", f"- Backprop non-trained count: `0`", "", "## Artifact Policy", "", "Foundation blueprints are generated with priority, but selected blueprints are blocked unless required artifacts have source-backed, shape/order/provenance-verifiable files. Lightweight PyTorch transforms are the executable baseline path for this demo.", "", "## Best Root", "", f"- Val Macro-F1: `{best_root.get('best_val_macro_f1')}`", f"- Test Macro-F1: `{best_root.get('test_macro_f1')}`", "", "## Best Generated Child", ""]
    if best_child:
        lines += [f"- Strategy: `{best_child.get('strategy')}`", f"- Val Macro-F1: `{best_child.get('best_val_macro_f1')}`", f"- Test Macro-F1: `{best_child.get('test_macro_f1')}`"]
    else:
        lines.append("No generated child was trained.")
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
