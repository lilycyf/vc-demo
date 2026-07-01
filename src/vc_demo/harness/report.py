from __future__ import annotations

from pathlib import Path
from typing import Any

from vc_demo.harness.state import read_json


def _config_for(node: dict[str, Any]) -> dict[str, Any]:
    return read_json(Path(node["config"]))


def trained_rows(tree: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, node in tree.get("nodes", {}).items():
        if node.get("status") != "trained":
            continue
        cfg = _config_for(node)
        data_cfg = cfg.get("data", {})
        model_cfg = cfg.get("model", {})
        training_cfg = cfg.get("training", {})
        rows.append(
            {
                "iteration": int(node.get("iteration", 0)),
                "node": name,
                "parent": node.get("parent", ""),
                "agent_type": node.get("agent_type", "root"),
                "strategy": node.get("strategy", "root"),
                "data_dir": data_cfg.get("data_dir", "synthetic"),
                "model_type": model_cfg.get("model_type", "mlp"),
                "hidden_dim": model_cfg.get("hidden_dim"),
                "depth": model_cfg.get("depth"),
                "dropout": model_cfg.get("dropout"),
                "low_rank_dim": model_cfg.get("low_rank_dim", ""),
                "lr": training_cfg.get("lr"),
                "weight_decay": training_cfg.get("weight_decay"),
                "val": float(node["best_val_macro_f1"]),
                "test": float(node["test_macro_f1"]),
                "note": cfg.get("proposal_note", "root"),
            }
        )
    return sorted(rows, key=lambda row: (row["iteration"], row["node"]))


def write_summary(tree: dict[str, Any], summary_path: Path, failures: list[dict[str, Any]], stop_reason: str) -> None:
    rows = trained_rows(tree)
    roots = [row for row in rows if row["iteration"] == 0]
    best = max(rows, key=lambda row: row["val"]) if rows else None
    best_root = max(roots, key=lambda row: row["val"]) if roots else None

    lines = [
        "# VCHarness-Style K562 Search Summary",
        "",
        "This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.",
        "The proposal agent is a task-aware rule policy: it uses K562 feature/model priors plus parent validation results to propose config-level child pipelines without changing data, splits, or metric semantics.",
        "",
        f"- Stop reason: {stop_reason}",
        f"- Trained nodes: {len(rows)}",
        f"- Failed nodes: {len(failures)}",
    ]
    if best:
        lines.append(f"- Best node: `{best['node']}` val={best['val']:.4f} test={best['test']:.4f}")
    if best and best_root:
        lines.append(f"- Best root: `{best_root['node']}` val={best_root['val']:.4f} test={best_root['test']:.4f}")
        lines.append(f"- Improvement over best root: {best['val'] - best_root['val']:.4f} validation Macro-F1")

    lines.extend(["", "## Root Baselines", "", "| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |", "|---|---|---|---:|---:|"])
    for row in roots:
        lines.append(f"| `{row['node']}` | `{row['data_dir']}` | {row['model_type']} | {row['val']:.4f} | {row['test']:.4f} |")

    lines.extend([
        "",
        "## All Trained Nodes",
        "",
        "| Iter | Node | Parent | Agent | Strategy | Data dir | Model | Hidden | Depth | Dropout | Rank | LR | WD | Val | Test |",
        "|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in rows:
        lines.append(
            f"| {row['iteration']} | `{row['node']}` | `{row['parent']}` | {row['agent_type']} | {row['strategy']} | `{row['data_dir']}` | {row['model_type']} | {row['hidden_dim']} | {row['depth']} | {row['dropout']} | {row['low_rank_dim']} | {row['lr']} | {row['weight_decay']} | {row['val']:.4f} | {row['test']:.4f} |"
        )

    lines.extend(["", "## Best-So-Far Curve", "", "| Iter | Best val Macro-F1 |", "|---:|---:|"])
    best_so_far = -1.0
    for row in rows:
        best_so_far = max(best_so_far, row["val"])
        lines.append(f"| {row['iteration']} | {best_so_far:.4f} |")

    lines.extend(["", "## Tree", ""])

    def append_tree(name: str, depth: int) -> None:
        node = tree["nodes"][name]
        label = f"{'  ' * depth}- `{name}` status={node.get('status')} visits={node.get('visits')}"
        if node.get("status") == "trained":
            label += f" val={node['best_val_macro_f1']:.4f} test={node['test_macro_f1']:.4f}"
        if node.get("strategy"):
            label += f" strategy={node['strategy']}"
        lines.append(label)
        for child in node.get("children", []):
            append_tree(child, depth + 1)

    for root in tree.get("root_nodes", []):
        append_tree(root, 0)

    if failures:
        lines.extend(["", "## Failures", "", "| Node | Parent | Error |", "|---|---|---|"])
        for failure in failures:
            err = str(failure.get("error", "")).replace("|", " ").splitlines()[-1]
            lines.append(f"| `{failure.get('node')}` | `{failure.get('parent')}` | {err} |")

    lines.extend([
        "",
        "## Reproducibility Notes",
        "",
        "- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.",
        "- MCTS decides which already-trained parent is worth expanding next using UCT.",
        "- The proposal agent decides how to modify that parent into one executable child config.",
        "- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.",
    ])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
