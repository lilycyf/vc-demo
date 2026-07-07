from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vc_demo.harness.pipeline_grammar import program_for_blueprint


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
    memory["motifs"] = infer_motifs(successes, list(failures or []), blocked)
    write_memory(run_dir, memory)
    return memory


def infer_motifs(successes: list[dict[str, Any]], failures: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> dict[str, list[str]]:
    promising: list[str] = []
    discouraged: list[str] = []
    for row in successes[:10]:
        strategy = str(row.get("strategy"))
        program = program_for_blueprint(strategy)
        val = row.get("val")
        if val is not None:
            promising.append(f"{strategy}: {program.get('fusion')} + {program.get('head')} val={float(val):.4f}")
    failed_counts = Counter(str(item.get("strategy", "unknown")) for item in failures)
    for strategy, count in failed_counts.most_common(5):
        if strategy != "unknown":
            discouraged.append(f"{strategy}: {count} failure(s)")
    blocked_counts = Counter(str(item.get("strategy", "unknown")) for item in blocked)
    for strategy, count in blocked_counts.most_common(5):
        if strategy != "unknown":
            discouraged.append(f"{strategy}: blocked by missing artifact {count} time(s)")
    return {"promising": promising[:10], "discouraged": discouraged[:10]}


def repair_prompt(run_dir: Path, node_name: str) -> str:
    tree_path = run_dir / "tree.json"
    if not tree_path.exists():
        return ""
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    node = tree.get("nodes", {}).get(node_name, {})
    strategy = str(node.get("strategy", ""))
    program = program_for_blueprint(strategy)
    return "\n".join([
        f"# Repair Task: `{node_name}`",
        "",
        f"- Strategy: `{strategy}`",
        f"- Grammar: representation={program.get('representation')}, fusion={program.get('fusion')}, prior={program.get('prior')}, head={program.get('head')}",
        f"- Program path: `{node.get('program_model_path', '')}`",
        "",
        "Fix only the node-local implementation unless the traceback proves a harness bug.",
        "Do not change data splits, labels, metric semantics, or artifact provenance.",
    ]) + "\n"


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
