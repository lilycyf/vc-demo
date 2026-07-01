from __future__ import annotations

import copy
import hashlib
import random
from typing import Any


FEATURE_DIRS = [
    ("onehot", "data/cell_lines/k562_onehot"),
    ("delta", "data/cell_lines/k562_delta"),
    ("concat", "data/cell_lines/k562_concat"),
]

MODEL_TYPES = ["mlp", "residual_mlp", "gated_mlp", "low_rank_mlp"]
HIDDEN_DIMS = [128, 192, 256, 384, 512]
DEPTHS = [1, 2, 3, 4]
DROPOUTS = [0.0, 0.05, 0.1, 0.2, 0.35]
LOW_RANK_DIMS = [16, 32, 64, 128]
LRS = [1e-4, 2e-4, 3e-4, 5e-4, 8e-4]
WEIGHT_DECAYS = [0.0, 1e-5, 1e-4, 5e-4, 1e-3]

STRATEGIES = [
    "feature_to_concat",
    "optimizer_refine",
    "capacity_refine",
    "backbone_probe",
    "head_factorization",
    "regularization_probe",
    "representation_probe",
]


def _choice_not_current(rng: random.Random, options: list[Any], current: Any) -> Any:
    choices = [item for item in options if item != current]
    return rng.choice(choices or options)


def _feature_label(config: dict[str, Any]) -> str:
    data_dir = config.get("data", {}).get("data_dir", "")
    for label, path in FEATURE_DIRS:
        if data_dir == path:
            return label
    return "custom"


def _set_feature(config: dict[str, Any], label: str) -> str:
    before = _feature_label(config)
    for candidate, path in FEATURE_DIRS:
        if candidate == label:
            config.setdefault("data", {})["data_dir"] = path
            return f"feature_source:{before}->{label}"
    raise ValueError(f"unknown feature label {label!r}")


def _next_from(options: list[Any], current: Any, preferred: list[Any]) -> Any:
    for item in preferred:
        if item in options and item != current:
            return item
    for item in options:
        if item != current:
            return item
    return current


def _parent_val(parent_node: dict[str, Any]) -> float:
    try:
        return float(parent_node.get("best_val_macro_f1", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _strategy_for(parent_config: dict[str, Any], parent_node: dict[str, Any], child_index: int, rng: random.Random) -> str:
    feature = _feature_label(parent_config)
    val = _parent_val(parent_node)
    model_type = parent_config.get("model", {}).get("model_type", "mlp")

    if feature != "concat" and child_index == 1:
        return "feature_to_concat"

    if val >= 0.58 and feature == "concat":
        plan = ["optimizer_refine", "capacity_refine", "regularization_probe"]
    elif feature == "concat" and model_type == "mlp":
        plan = ["optimizer_refine", "backbone_probe", "capacity_refine"]
    elif feature == "concat":
        plan = ["optimizer_refine", "regularization_probe", "head_factorization"]
    else:
        plan = ["representation_probe", "feature_to_concat", "backbone_probe"]

    strategy = plan[(child_index - 1) % len(plan)]
    if child_index > 3 and rng.random() < 0.25:
        strategy = rng.choice(STRATEGIES)
    return strategy


def propose_child(
    parent_config: dict[str, Any],
    parent_node: dict[str, Any],
    child_index: int,
    rng: random.Random,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate one child design from a selected parent.

    The policy is intentionally lightweight but task-aware: K562 roots showed
    stronger validation signal from concat features, so weak feature parents are
    first converted to concat. Strong concat parents are expanded through
    optimizer, regularization, capacity, and small model-family probes.
    """
    child = copy.deepcopy(parent_config)
    child.setdefault("data", {})
    child.setdefault("model", {})
    child.setdefault("training", {})

    parent_name = str(parent_config.get("node_name", parent_node.get("name", "node")))
    strategy = _strategy_for(parent_config, parent_node, child_index, rng)
    changes: list[str] = []

    current_feature = _feature_label(child)
    model_cfg = child["model"]
    train_cfg = child["training"]
    current_model = model_cfg.get("model_type", "mlp")

    if strategy == "feature_to_concat":
        changes.append(_set_feature(child, "concat"))
        if current_model != "mlp":
            model_cfg["model_type"] = "mlp"
            changes.append(f"model_type:{current_model}->mlp")
        old_hidden = model_cfg.get("hidden_dim", 256)
        model_cfg["hidden_dim"] = max(int(old_hidden), 384)
        if model_cfg["hidden_dim"] != old_hidden:
            changes.append(f"hidden_dim:{old_hidden}->{model_cfg['hidden_dim']}")

    elif strategy == "representation_probe":
        target = "concat" if current_feature != "concat" else rng.choice(["delta", "onehot"])
        changes.append(_set_feature(child, target))

    elif strategy == "optimizer_refine":
        old_lr = train_cfg.get("lr", 3e-4)
        old_wd = train_cfg.get("weight_decay", 1e-4)
        preferred_lr = [5e-4, 8e-4, 3e-4, 2e-4]
        preferred_wd = [1e-5, 0.0, 1e-4, 5e-4]
        train_cfg["lr"] = _next_from(LRS, old_lr, preferred_lr)
        train_cfg["weight_decay"] = _next_from(WEIGHT_DECAYS, old_wd, preferred_wd)
        changes.append(f"optimizer:lr {old_lr}->{train_cfg['lr']}, wd {old_wd}->{train_cfg['weight_decay']}")

    elif strategy == "capacity_refine":
        old_hidden = model_cfg.get("hidden_dim", 256)
        old_depth = model_cfg.get("depth", 2)
        if int(old_hidden) < 512:
            model_cfg["hidden_dim"] = _next_from(HIDDEN_DIMS, old_hidden, [384, 512, 256, 192])
        else:
            model_cfg["hidden_dim"] = 384
        model_cfg["depth"] = _next_from(DEPTHS, old_depth, [2, 3, 1, 4])
        changes.append(f"capacity:hidden {old_hidden}->{model_cfg['hidden_dim']}, depth {old_depth}->{model_cfg['depth']}")

    elif strategy == "backbone_probe":
        old_model = current_model
        model_cfg["model_type"] = _next_from(MODEL_TYPES, old_model, ["residual_mlp", "gated_mlp", "mlp", "low_rank_mlp"])
        if model_cfg["model_type"] == "low_rank_mlp":
            model_cfg["low_rank_dim"] = model_cfg.get("low_rank_dim", 64)
        changes.append(f"model_type:{old_model}->{model_cfg['model_type']}")

    elif strategy == "head_factorization":
        old_model = current_model
        old_rank = model_cfg.get("low_rank_dim", 64)
        model_cfg["model_type"] = "low_rank_mlp"
        model_cfg["low_rank_dim"] = _next_from(LOW_RANK_DIMS, old_rank, [32, 64, 128, 16])
        changes.append(f"head:{old_model}->low_rank_mlp rank {old_rank}->{model_cfg['low_rank_dim']}")

    elif strategy == "regularization_probe":
        old_dropout = model_cfg.get("dropout", 0.1)
        old_wd = train_cfg.get("weight_decay", 1e-4)
        model_cfg["dropout"] = _next_from(DROPOUTS, old_dropout, [0.05, 0.0, 0.1, 0.2])
        train_cfg["weight_decay"] = _next_from(WEIGHT_DECAYS, old_wd, [0.0, 1e-5, 1e-4])
        changes.append(f"regularization:dropout {old_dropout}->{model_cfg['dropout']}, wd {old_wd}->{train_cfg['weight_decay']}")

    if not changes:
        old_hidden = model_cfg.get("hidden_dim", 256)
        model_cfg["hidden_dim"] = _choice_not_current(rng, HIDDEN_DIMS, old_hidden)
        changes.append(f"fallback:hidden {old_hidden}->{model_cfg['hidden_dim']}")

    parent_root = parent_name.split("_child_")[0]
    parent_digest = hashlib.sha1(parent_name.encode("utf-8")).hexdigest()[:8]
    child_name = f"{parent_root}_c{child_index}_{strategy}_{parent_digest}"
    child["node_name"] = child_name
    child["proposal_note"] = f"codex_agent strategy={strategy}; " + "; ".join(changes)

    proposal = {
        "agent_type": "codex_task_aware_rule_agent",
        "parent": parent_name,
        "child": child_name,
        "strategy": strategy,
        "parent_val_macro_f1": _parent_val(parent_node),
        "hypothesis": hypothesis_for(strategy),
        "changes": changes,
        "limits": "Config-level proposal agent; data, split, metric semantics, and historical results are not modified.",
    }
    return child, proposal


def hypothesis_for(strategy: str) -> str:
    mapping = {
        "feature_to_concat": "Concat features combine perturbation identity with expression delta signal and should improve weak onehot/delta parents.",
        "optimizer_refine": "K562 concat models may be optimization-limited at short epoch budgets; coordinated lr and weight-decay changes can improve validation Macro-F1.",
        "capacity_refine": "The response label has many target genes, so moderate capacity changes may capture shared perturbation response structure without changing the split.",
        "backbone_probe": "Residual or gated nonlinear backbones may improve the inductive bias over a plain MLP for perturbation response prediction.",
        "head_factorization": "A factorized target-gene head may share signal across genes and improve generalization under limited perturbation count.",
        "regularization_probe": "The best parent may be slightly over-regularized; lower dropout or weight decay can improve Macro-F1 at four epochs.",
        "representation_probe": "A different fixed feature representation can test whether improvements come from model design or biological input representation.",
    }
    return mapping.get(strategy, "Explore a child pipeline derived from the selected parent.")
