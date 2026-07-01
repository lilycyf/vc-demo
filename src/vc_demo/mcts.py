from __future__ import annotations

import argparse
import json
import math
import random
from copy import deepcopy
from pathlib import Path


def uct_score(node: dict, parent_visits: int, exploration: float) -> float:
    visits = max(int(node.get("visits", 0)), 1)
    value = float(node.get("value", 0.0))
    return value / visits + exploration * math.sqrt(math.log(max(parent_visits, 2)) / visits)


def propose_child_config(parent_config: dict, child_index: int, rng: random.Random) -> dict:
    child = deepcopy(parent_config)
    child["node_name"] = f"{parent_config.get('node_name', 'node')}_child_{child_index}"
    child.setdefault("model", {})
    child.setdefault("training", {})

    mutation = rng.choice(["hidden_dim", "dropout", "depth", "lr", "weight_decay"])
    if mutation == "hidden_dim":
        child["model"]["hidden_dim"] = rng.choice([128, 192, 256, 384, 512])
    elif mutation == "dropout":
        child["model"]["dropout"] = rng.choice([0.0, 0.05, 0.1, 0.2, 0.35])
    elif mutation == "depth":
        child["model"]["depth"] = rng.choice([1, 2, 3, 4])
    elif mutation == "lr":
        child["training"]["lr"] = rng.choice([1e-4, 2e-4, 3e-4, 5e-4, 8e-4])
    elif mutation == "weight_decay":
        child["training"]["weight_decay"] = rng.choice([0.0, 1e-5, 1e-4, 5e-4, 1e-3])
    child["proposal_note"] = f"mutated {mutation} from parent {parent_config.get('node_name', 'node')}"
    return child


def load_tree(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"root": "root_mlp", "nodes": {}}


def main() -> None:
    parser = argparse.ArgumentParser(description="Toy MCTS-style child proposal driver.")
    parser.add_argument("--tree", type=Path, default=Path("experiments/tree.json"))
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--exploration", type=float, default=1.2)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    tree = load_tree(args.tree)
    proposal_dir = args.tree.parent / "proposals"
    proposal_dir.mkdir(parents=True, exist_ok=True)

    root_cfg_path = Path("configs/root_mlp.json")
    root_cfg = json.loads(root_cfg_path.read_text())
    nodes = tree.setdefault("nodes", {})
    nodes.setdefault("root_mlp", {"config": str(root_cfg_path), "visits": 1, "value": 0.0, "children": []})

    created: list[str] = []
    for step in range(args.steps):
        parent_name = max(
            nodes,
            key=lambda name: uct_score(nodes[name], sum(n.get("visits", 0) for n in nodes.values()) + 1, args.exploration),
        )
        parent = nodes[parent_name]
        parent_config = json.loads(Path(parent["config"]).read_text())
        child_config = propose_child_config(parent_config, len(parent.get("children", [])) + 1, rng)
        child_name = child_config["node_name"]
        child_path = proposal_dir / f"{child_name}.json"
        child_path.write_text(json.dumps(child_config, indent=2), encoding="utf-8")

        parent.setdefault("children", []).append(child_name)
        parent["visits"] = int(parent.get("visits", 0)) + 1
        nodes[child_name] = {"config": str(child_path), "visits": 0, "value": 0.0, "children": [], "status": "proposed"}
        created.append(str(child_path))

    args.tree.write_text(json.dumps(tree, indent=2), encoding="utf-8")
    print(json.dumps({"tree": str(args.tree), "created": created}, indent=2))


if __name__ == "__main__":
    main()
