from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_memory(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "search_memory.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "format": "vc_demo_search_memory.v1",
        "created_at": _now(),
        "updated_at": _now(),
        "events": [],
        "blueprint_counts": {},
        "parent_blueprints": {},
        "successes": [],
        "failures": [],
        "blocked_artifacts": [],
        "motifs": {"promising": [], "discouraged": []},
    }


def write_memory(run_dir: Path, memory: dict[str, Any]) -> None:
    memory["updated_at"] = _now()
    path = run_dir / "search_memory.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def rebuild_memory_from_tree(run_dir: Path, tree: dict[str, Any], failures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    memory = load_memory(run_dir)
    counts: Counter[str] = Counter()
    parent_blueprints: dict[str, set[str]] = defaultdict(set)
    successes: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for name, node in tree.get("nodes", {}).items():
        strategy = str(node.get("strategy") or "root")
        if strategy != "root":
            counts[strategy] += 1
        parent = str(node.get("parent") or "")
        if parent and strategy != "root":
            parent_blueprints[parent].add(strategy)
        if node.get("status") == "trained" and strategy != "root":
            successes.append({"node": name, "strategy": strategy, "val": node.get("best_val_macro_f1"), "test": node.get("test_macro_f1"), "parent": parent})
        if node.get("status") in {"requires_artifact_acquisition", "blocked_missing_artifact"}:
            blocked.append({"node": name, "strategy": strategy, "missing": node.get("missing_required_artifacts", [])})
    memory["blueprint_counts"] = dict(counts)
    memory["parent_blueprints"] = {parent: sorted(values) for parent, values in parent_blueprints.items()}
    memory["successes"] = sorted(successes, key=lambda row: float(row.get("val") or -1), reverse=True)[:50]
    memory["failures"] = list(failures or [])[-50:]
    memory["blocked_artifacts"] = blocked[-50:]
    write_memory(run_dir, memory)
    return memory


def is_duplicate_proposal(memory: dict[str, Any], parent: str, strategy: str, max_blueprint_repeats: int, allow_parent_duplicate: bool = False) -> tuple[bool, str]:
    if not strategy:
        return False, ""
    if not allow_parent_duplicate and strategy in set(memory.get("parent_blueprints", {}).get(parent, [])):
        return True, f"parent {parent} already expanded blueprint {strategy}"
    count = int(memory.get("blueprint_counts", {}).get(strategy, 0) or 0)
    if max_blueprint_repeats >= 0 and count >= max_blueprint_repeats:
        return True, f"blueprint {strategy} reached repeat limit {max_blueprint_repeats}"
    return False, ""


def record_event(run_dir: Path, kind: str, payload: dict[str, Any]) -> None:
    memory = load_memory(run_dir)
    memory.setdefault("events", []).append({"time": _now(), "kind": kind, **payload})
    write_memory(run_dir, memory)
