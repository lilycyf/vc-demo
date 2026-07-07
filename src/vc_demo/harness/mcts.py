from __future__ import annotations

import math
from typing import Any, Literal


SelectionPolicy = Literal["uct", "puct"]


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def mean_value(node: dict[str, Any]) -> float:
    visits = max(_as_int(node.get("visits"), 0), 1)
    return _as_float(node.get("value"), 0.0) / visits


def uct_score(node: dict[str, Any], parent_visits: int, exploration: float) -> dict[str, float]:
    """Standard UCT score: Q(s, a) + c * sqrt(log N(s) / N(s, a))."""
    visits = max(_as_int(node.get("visits"), 0), 1)
    exploitation = mean_value(node)
    exploration_term = exploration * math.sqrt(math.log(max(parent_visits, 2)) / visits)
    return {
        "score": exploitation + exploration_term,
        "q": exploitation,
        "exploitation": exploitation,
        "exploration": exploration_term,
        "prior": _as_float(node.get("prior"), 0.0),
        "visits": float(visits),
        "parent_visits": float(parent_visits),
    }


def puct_score(node: dict[str, Any], parent_visits: int, exploration: float, prior: float) -> dict[str, float]:
    """PUCT score: Q(s, a) + c_puct * P(s, a) * sqrt(N(s)) / (1 + N(s, a))."""
    visits = max(_as_int(node.get("visits"), 0), 0)
    exploitation = mean_value(node) if visits > 0 else _as_float(node.get("best_val_macro_f1"), 0.0)
    exploration_term = exploration * prior * math.sqrt(max(parent_visits, 1)) / (1.0 + visits)
    return {
        "score": exploitation + exploration_term,
        "q": exploitation,
        "exploitation": exploitation,
        "exploration": exploration_term,
        "prior": prior,
        "visits": float(visits),
        "parent_visits": float(parent_visits),
    }


def candidate_parents(tree: dict[str, Any], max_children: int) -> list[str]:
    candidates: list[str] = []
    for name, node in tree.get("nodes", {}).items():
        if node.get("status") != "trained":
            continue
        if len(node.get("children", [])) < max_children:
            candidates.append(name)
    if candidates:
        return candidates
    return [name for name, node in tree.get("nodes", {}).items() if node.get("status") == "trained"]


def _normalized_priors(tree: dict[str, Any], candidates: list[str]) -> dict[str, float]:
    raw: dict[str, float] = {}
    for name in candidates:
        node = tree["nodes"][name]
        explicit = node.get("prior")
        if explicit is not None:
            raw[name] = max(_as_float(explicit), 0.0)
            continue
        # If no policy model is available, use a weak empirical prior from the
        # validation reward and leave most of the decision to Q plus exploration.
        raw[name] = max(_as_float(node.get("best_val_macro_f1"), 0.0), 1e-6)
    total = sum(raw.values())
    if total <= 0.0:
        uniform = 1.0 / max(len(candidates), 1)
        return {name: uniform for name in candidates}
    return {name: value / total for name, value in raw.items()}


def select_parent(
    tree: dict[str, Any],
    exploration: float,
    max_children: int,
    policy: SelectionPolicy = "uct",
) -> tuple[str, list[dict[str, Any]]]:
    """Select the next trained parent node to expand.

    The paper-aligned default is UCT because the public VCHarness tree
    artifacts expose visits, Q_v, Exploitation, Exploration, and uct fields.
    PUCT is retained as an optional implementation extension/ablation for cases
    where a caller supplies or accepts an empirical prior. Returned rows include
    score components so proposals and reports can audit why a parent was chosen.
    """
    candidates = candidate_parents(tree, max_children)
    if not candidates:
        raise ValueError("no trained nodes are available for MCTS parent selection")

    parent_visits = sum(max(_as_int(tree["nodes"][name].get("visits"), 0), 1) for name in candidates)
    parent_visits = max(parent_visits, 1)
    priors = _normalized_priors(tree, candidates)

    scored: list[dict[str, Any]] = []
    for name in candidates:
        node = tree["nodes"][name]
        if policy == "uct":
            components = uct_score(node, parent_visits, exploration)
        elif policy == "puct":
            components = puct_score(node, parent_visits, exploration, priors[name])
        else:
            raise ValueError(f"unknown MCTS selection policy {policy!r}")
        value = _as_float(node.get("value"), 0.0)
        scored.append(
            {
                "node": name,
                "policy": policy,
                "score": components["score"],
                "uct": components["score"] if policy == "uct" else None,
                "puct": components["score"] if policy == "puct" else None,
                "q": components["q"],
                "Q_v": value,
                "exploitation": components["exploitation"],
                "Exploitation": components["exploitation"],
                "exploration": components["exploration"],
                "Exploration": components["exploration"],
                "prior": components["prior"],
                "visits": int(components["visits"]),
                "parent_visits": int(components["parent_visits"]),
                "children": len(node.get("children", [])),
                "best_val_macro_f1": _as_float(node.get("best_val_macro_f1"), 0.0),
                "stage": node.get("stage", "draft" if not node.get("parent") else "improve"),
            }
        )
    scored.sort(key=lambda row: (row["score"], row["best_val_macro_f1"]), reverse=True)
    tree.setdefault("mcts", {})
    tree["mcts"]["last_selection"] = scored[0]
    tree["mcts"]["last_candidates"] = scored[: min(16, len(scored))]
    tree["mcts"]["selection_policy"] = policy
    tree["mcts"]["exploration_c"] = exploration
    tree["mcts"]["public_artifact_alignment"] = "uct fields match the public VCHarness tree schema when selection_policy=uct; puct is an optional repo extension"
    return scored[0]["node"], scored


def _update_rollout_stats(node: dict[str, Any], reward: float) -> None:
    visits = _as_int(node.get("visits"), 0) + 1
    value = _as_float(node.get("value"), 0.0) + reward
    squared = _as_float(node.get("squared_value"), 0.0) + reward * reward
    node["visits"] = visits
    node["value"] = value
    node["Q_v"] = value
    node["squared_value"] = squared
    node["mean_reward"] = value / visits
    node["Exploitation"] = node["mean_reward"]
    variance = max(squared / visits - node["mean_reward"] ** 2, 0.0)
    node["reward_variance"] = variance
    node["reward_std"] = math.sqrt(variance)
    node["best_reward"] = max(_as_float(node.get("best_reward"), float("-inf")), reward)
    node["last_reward"] = reward
    rewards = list(node.get("rollout_rewards", []))
    rewards.append(reward)
    node["rollout_rewards"] = rewards[-20:]


def backpropagate(tree: dict[str, Any], node_name: str, reward: float) -> None:
    """Backpropagate one completed rollout reward from leaf to root."""
    current = node_name
    path: list[str] = []
    while current:
        path.append(current)
        node = tree["nodes"][current]
        _update_rollout_stats(node, reward)
        current = node.get("parent", "")
    tree.setdefault("mcts", {})
    tree["mcts"]["last_backpropagation"] = {
        "leaf": node_name,
        "reward": reward,
        "path": path,
        "path_length": len(path),
    }
