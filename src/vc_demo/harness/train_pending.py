from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vc_demo.harness.executor import run_node
from vc_demo.harness.mcts import backpropagate
from vc_demo.harness.paper_level_guardrails import assert_no_formal_proxy
from vc_demo.harness.report import write_summary
from vc_demo.harness.search_memory import rebuild_memory_from_tree
from vc_demo.harness.state import read_json, write_json


def reward(metrics: dict[str, Any]) -> float:
    return float(metrics["best_val_macro_f1"])


def load_failures(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "failures.json"
    if not path.exists():
        return []
    payload = read_json(path)
    return list(payload.get("failures", []))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def refresh_run_manifest_after_pending_train(run_dir: Path, tree: dict[str, Any], node_name: str, metrics: dict[str, Any], stop_reason: str) -> None:
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        return
    manifest = read_json(manifest_path)
    trained = {name: node for name, node in tree.get("nodes", {}).items() if node.get("status") == "trained"}
    roots = {name: node for name, node in trained.items() if not node.get("parent")}
    best = max(trained.items(), key=lambda item: float(item[1].get("best_val_macro_f1", -1)), default=("", {}))
    best_root = max(roots.items(), key=lambda item: float(item[1].get("best_val_macro_f1", -1)), default=("", {}))
    manifest.setdefault("search", {})["stop_reason"] = stop_reason
    manifest.setdefault("results", {}).update({
        "trained_nodes": len(trained),
        "best_node": best[0],
        "best_val_macro_f1": best[1].get("best_val_macro_f1"),
        "best_test_macro_f1": best[1].get("test_macro_f1"),
        "best_root": best_root[0],
        "best_root_val_macro_f1": best_root[1].get("best_val_macro_f1"),
        "best_root_test_macro_f1": best_root[1].get("test_macro_f1"),
        "last_manual_train_pending_node": node_name,
        "last_manual_train_pending_val_macro_f1": metrics.get("best_val_macro_f1"),
        "last_manual_train_pending_test_macro_f1": metrics.get("test_macro_f1"),
    })
    manifest.setdefault("queues", {})["implementation_queue"] = str(run_dir / "implementation_queue.json")
    write_json(manifest_path, manifest)


def write_queue(run_dir: Path, tree: dict[str, Any]) -> None:
    items = [
        {
            "node": name,
            "program_dir": node.get("program_dir"),
            "implementation_request_path": node.get("implementation_request_path"),
            "program_model_path": node.get("program_model_path"),
            "pipeline_manifest_path": node.get("pipeline_manifest_path"),
            "strategy": node.get("strategy"),
            "artifact_requirements": node.get("artifact_requirements", []),
        }
        for name, node in tree.get("nodes", {}).items()
        if node.get("status") == "needs_implementation"
    ]
    write_json(run_dir / "implementation_queue.json", {"items": items})


def missing_artifacts_for_pending(node: dict[str, Any], proposal: dict[str, Any] | None, config: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for source in [node, proposal or {}]:
        missing.extend(str(item) for item in source.get("missing_required_artifacts", []) or [])
    pipeline_path = config.get("pipeline_manifest_path") or config.get("pipeline", {}).get("manifest_path")
    if pipeline_path and Path(str(pipeline_path)).exists():
        payload = read_json(Path(str(pipeline_path)))
        missing.extend(str(item) for item in payload.get("missing_artifacts", []) or [])
    return sorted(set(item for item in missing if item))


def train_pending_node(run_dir: Path, node_name: str, max_epochs: int | None, summary: Path | None = None, allow_missing_artifact_fallbacks: bool = False) -> dict[str, Any]:
    tree_path = run_dir / "tree.json"
    if not tree_path.exists():
        raise FileNotFoundError(f"missing tree file: {tree_path}")
    tree = read_json(tree_path)
    try:
        node = tree["nodes"][node_name]
    except KeyError as exc:
        raise KeyError(f"node {node_name!r} not found in {tree_path}") from exc
    if node.get("status") != "needs_implementation":
        raise ValueError(f"node {node_name!r} status is {node.get('status')!r}, expected 'needs_implementation'")

    config = read_json(Path(node["config"]))
    model_path = Path(str(config.get("model", {}).get("custom_model_path", node.get("program_model_path", ""))))
    if not model_path.exists():
        raise FileNotFoundError(f"pending node has no implemented model.py yet: {model_path}")

    proposal_raw = str(node.get("proposal", "") or "")
    proposal_path = Path(proposal_raw) if proposal_raw else Path()
    proposal = read_json(proposal_path) if proposal_raw and proposal_path.is_file() else None
    missing = missing_artifacts_for_pending(node, proposal, config)
    if missing and not allow_missing_artifact_fallbacks:
        raise RuntimeError(
            "pending node requires missing artifacts and strict artifact mode forbids fallback training: "
            + ", ".join(missing)
            + "; rerun only after adding real artifacts, or pass --allow-missing-artifact-fallbacks for an explicit ablation"
        )
    assert_no_formal_proxy(config, model_path, context=f"pending node {node_name}")
    metrics = run_node(config, run_dir, proposal=proposal, max_epochs=max_epochs)
    node.update(
        {
            "status": "trained",
            "metrics": str(run_dir / "nodes" / node_name / "metrics.json"),
            "best_val_macro_f1": metrics["best_val_macro_f1"],
            "test_macro_f1": metrics["test_macro_f1"],
            "visits": 1,
            "value": reward(metrics),
            "requires_implementation": False,
            "duration_seconds": metrics.get("duration_seconds"),
            "pipeline": metrics.get("pipeline", {}),
        }
    )
    rollout_reward = reward(metrics)
    backpropagate(tree, node_name, rollout_reward)
    backprop = tree.get("mcts", {}).get("last_backpropagation", {})
    append_jsonl(run_dir / "mcts_trace.jsonl", {
        "event": "manual_train_pending_backpropagation",
        "time": _now(),
        "leaf": node_name,
        "reward": rollout_reward,
        "backprop_path": backprop.get("path", []),
        "best_val_macro_f1": metrics.get("best_val_macro_f1"),
        "test_macro_f1": metrics.get("test_macro_f1"),
        "policy": "manual_train_pending_only_trained_nodes_backpropagate",
    })
    append_jsonl(run_dir / "agent_decision_trace.jsonl", {
        "event": "trained_and_backpropagated",
        "time": _now(),
        "node": node_name,
        "strategy": node.get("strategy"),
        "best_val_macro_f1": metrics.get("best_val_macro_f1"),
        "test_macro_f1": metrics.get("test_macro_f1"),
        "source": "train_pending",
    })
    failures = load_failures(run_dir)
    rebuild_memory_from_tree(run_dir, tree, failures)
    write_json(tree_path, tree)
    write_queue(run_dir, tree)
    stop_reason = "pending implementation trained"
    refresh_run_manifest_after_pending_train(run_dir, tree, node_name, metrics, stop_reason)
    if summary is None:
        summary = run_dir / "search_summary.md"
    write_summary(tree, summary, failures, stop_reason)
    result = {"node": node_name, "metrics": metrics, "tree": str(tree_path), "summary": str(summary)}
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a needs_implementation program node after Codex has created its model.py.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--allow-missing-artifact-fallbacks", action="store_true")
    args = parser.parse_args()
    train_pending_node(args.run_dir, args.node, args.max_epochs, args.summary, args.allow_missing_artifact_fallbacks)


if __name__ == "__main__":
    main()
