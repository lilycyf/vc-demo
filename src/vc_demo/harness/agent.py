from __future__ import annotations

import copy
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
    "feature_swap",
    "backbone_swap",
    "capacity_jump",
    "regularization_shift",
    "head_factorization",
    "combined_pipeline",
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


def propose_child(
    parent_config: dict[str, Any],
    parent_node: dict[str, Any],
    child_index: int,
    rng: random.Random,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate one child design from a parent node.

    This is intentionally a rule-based agent stub. It keeps the paper-like
    contract that MCTS chooses a parent and an agent proposes the next executable
    pipeline, while avoiding a second live coding agent inside this demo run.
    """
    child = copy.deepcopy(parent_config)
    child.setdefault("data", {})
    child.setdefault("model", {})
    child.setdefault("training", {})

    parent_name = str(parent_config.get("node_name", parent_node.get("name", "node")))
    strategy = rng.choice(STRATEGIES)
    changes: list[str] = []

    current_feature = _feature_label(child)
    current_model = child["model"].get("model_type", "mlp")

    if strategy in {"feature_swap", "combined_pipeline"}:
        label, data_dir = rng.choice([(label, path) for label, path in FEATURE_DIRS if label != current_feature] or FEATURE_DIRS)
        child["data"]["data_dir"] = data_dir
        changes.append(f"feature_source:{current_feature}->{label}")

    if strategy in {"backbone_swap", "combined_pipeline"}:
        next_model = _choice_not_current(rng, MODEL_TYPES, current_model)
        child["model"]["model_type"] = next_model
        changes.append(f"model_type:{current_model}->{next_model}")

    if strategy in {"capacity_jump", "combined_pipeline"}:
        old_hidden = child["model"].get("hidden_dim", 256)
        old_depth = child["model"].get("depth", 2)
        child["model"]["hidden_dim"] = _choice_not_current(rng, HIDDEN_DIMS, old_hidden)
        child["model"]["depth"] = _choice_not_current(rng, DEPTHS, old_depth)
        changes.append(f"capacity:hidden {old_hidden}->{child['model']['hidden_dim']}, depth {old_depth}->{child['model']['depth']}")

    if strategy in {"regularization_shift", "combined_pipeline"}:
        old_dropout = child["model"].get("dropout", 0.1)
        old_lr = child["training"].get("lr", 3e-4)
        old_wd = child["training"].get("weight_decay", 1e-4)
        child["model"]["dropout"] = _choice_not_current(rng, DROPOUTS, old_dropout)
        child["training"]["lr"] = _choice_not_current(rng, LRS, old_lr)
        child["training"]["weight_decay"] = _choice_not_current(rng, WEIGHT_DECAYS, old_wd)
        changes.append(
            "regularization:dropout "
            f"{old_dropout}->{child['model']['dropout']}, lr {old_lr}->{child['training']['lr']}, wd {old_wd}->{child['training']['weight_decay']}"
        )

    if strategy == "head_factorization" or child["model"].get("model_type") == "low_rank_mlp":
        old_rank = child["model"].get("low_rank_dim", 64)
        child["model"]["model_type"] = "low_rank_mlp"
        child["model"]["low_rank_dim"] = _choice_not_current(rng, LOW_RANK_DIMS, old_rank)
        changes.append(f"head:low_rank_dim {old_rank}->{child['model']['low_rank_dim']}")

    if not changes:
        old_hidden = child["model"].get("hidden_dim", 256)
        child["model"]["hidden_dim"] = _choice_not_current(rng, HIDDEN_DIMS, old_hidden)
        changes.append(f"fallback:hidden {old_hidden}->{child['model']['hidden_dim']}")

    child_name = f"{parent_name}_child_{child_index}_{strategy}"
    child["node_name"] = child_name
    child["proposal_note"] = f"agent_stub strategy={strategy}; " + "; ".join(changes)

    proposal = {
        "agent_type": "rule_based_vcharness_stub",
        "parent": parent_name,
        "child": child_name,
        "strategy": strategy,
        "hypothesis": hypothesis_for(strategy),
        "changes": changes,
        "limits": "This stub proposes config-level pipeline changes. It does not edit Python model source during the run.",
    }
    return child, proposal


def hypothesis_for(strategy: str) -> str:
    mapping = {
        "feature_swap": "Different perturbation feature representations may expose a stronger signal for this cell line.",
        "backbone_swap": "Changing the model family may improve the inductive bias beyond width/dropout tuning.",
        "capacity_jump": "A larger or shallower capacity profile may better match the current feature dimensionality.",
        "regularization_shift": "The parent may be under- or over-regularized, so optimization settings should move together.",
        "head_factorization": "A factorized target-gene head may improve generalization by sharing structure across genes.",
        "combined_pipeline": "Large coordinated changes can test a materially different executable pipeline.",
    }
    return mapping.get(strategy, "Explore a child pipeline derived from the selected parent.")
