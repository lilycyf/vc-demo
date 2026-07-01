from __future__ import annotations

import math
from typing import Any


def uct_score(node: dict[str, Any], total_visits: int, exploration: float) -> float:
    visits = max(int(node.get("visits", 0)), 1)
    value = float(node.get("value", 0.0))
    return value / visits + exploration * math.sqrt(math.log(max(total_visits, 2)) / visits)


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


def select_parent(tree: dict[str, Any], exploration: float, max_children: int) -> tuple[str, list[dict[str, Any]]]:
    candidates = candidate_parents(tree, max_children)
    if not candidates:
        raise ValueError("no trained nodes are available for MCTS parent selection")
    total_visits = sum(max(int(node.get("visits", 0)), 1) for node in tree["nodes"].values()) + 1
    scored = []
    for name in candidates:
        score = uct_score(tree["nodes"][name], total_visits, exploration)
        scored.append({"node": name, "uct": score})
    scored.sort(key=lambda row: row["uct"], reverse=True)
    return scored[0]["node"], scored


def backpropagate(tree: dict[str, Any], node_name: str, reward: float) -> None:
    current = node_name
    while current:
        node = tree["nodes"][current]
        node["visits"] = int(node.get("visits", 0)) + 1
        node["value"] = float(node.get("value", 0.0)) + reward
        current = node.get("parent", "")
