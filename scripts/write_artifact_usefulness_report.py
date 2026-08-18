from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def nodes_from_tree(tree: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = tree.get("nodes", {})
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items() if isinstance(v, dict)}
    if isinstance(raw, list):
        return {str(n.get("name") or n.get("id") or i): n for i, n in enumerate(raw) if isinstance(n, dict)}
    return {}


def metric(node: dict[str, Any], key: str) -> float | None:
    value = node.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_report(run_dir: Path) -> dict[str, Any]:
    tree = read_json(run_dir / "tree.json")
    nodes = nodes_from_tree(tree)
    trained = {name: node for name, node in nodes.items() if node.get("status") == "trained"}
    roots = {name: node for name, node in trained.items() if not node.get("parent")}
    children = {name: node for name, node in trained.items() if node.get("parent")}
    foundation = {
        name: node for name, node in children.items()
        if node.get("proposal_type") == "foundation_artifact_blueprint"
        or node.get("foundation_augmentation_policy")
        or node.get("required_artifacts")
    }
    foundation = {
        name: node for name, node in foundation.items()
        if node.get("status") == "trained" and not node.get("missing_required_artifacts")
    }
    controls = {name: node for name, node in children.items() if node.get("proposal_type") == "artifact_usefulness_control"}
    dense_children = {
        name: node for name, node in children.items()
        if node.get("status") == "trained"
        and not node.get("required_artifacts")
        and node.get("proposal_type") != "foundation_artifact_blueprint"
    }
    best_root = max(roots.items(), key=lambda item: metric(item[1], "best_val_macro_f1") or -1.0, default=("", {}))
    best_child = max(children.items(), key=lambda item: metric(item[1], "best_val_macro_f1") or -1.0, default=("", {}))
    best_foundation = max(foundation.items(), key=lambda item: metric(item[1], "best_val_macro_f1") or -1.0, default=("", {}))
    best_dense = max(dense_children.items(), key=lambda item: metric(item[1], "best_val_macro_f1") or -1.0, default=("", {}))
    best_control = max(controls.items(), key=lambda item: metric(item[1], "best_val_macro_f1") or -1.0, default=("", {}))

    paired = []
    for control_name, control in controls.items():
        artifact_name = str(control.get("paired_artifact_child") or "")
        artifact = trained.get(artifact_name)
        if artifact is None:
            continue
        a_val = metric(artifact, "best_val_macro_f1")
        c_val = metric(control, "best_val_macro_f1")
        paired.append({
            "artifact_child": artifact_name,
            "control_child": control_name,
            "artifact_strategy": artifact.get("strategy"),
            "control_strategy": control.get("strategy"),
            "artifact_val_macro_f1": a_val,
            "artifact_test_macro_f1": metric(artifact, "test_macro_f1"),
            "control_val_macro_f1": c_val,
            "control_test_macro_f1": metric(control, "test_macro_f1"),
            "artifact_incremental_val_gain": (a_val - c_val) if a_val is not None and c_val is not None else None,
        })
    root_val = metric(best_root[1], "best_val_macro_f1") if best_root[1] else None
    child_val = metric(best_child[1], "best_val_macro_f1") if best_child[1] else None
    foundation_val = metric(best_foundation[1], "best_val_macro_f1") if best_foundation[1] else None
    dense_val = metric(best_dense[1], "best_val_macro_f1") if best_dense[1] else None
    control_val = metric(best_control[1], "best_val_macro_f1") if best_control[1] else None
    comparator_val = control_val if control_val is not None else dense_val
    return {
        "format": "vc_demo_artifact_usefulness_report.v1",
        "run_dir": str(run_dir),
        "counts": {
            "trained_roots": len(roots),
            "trained_children": len(children),
            "trained_foundation_artifact_children": len(foundation),
            "trained_dense_no_artifact_children": len(dense_children),
            "trained_dense_matched_controls": len(controls),
        },
        "best_root": {"node": best_root[0], "val_macro_f1": root_val, "test_macro_f1": metric(best_root[1], "test_macro_f1") if best_root[1] else None},
        "best_generated_child": {"node": best_child[0], "val_macro_f1": child_val, "test_macro_f1": metric(best_child[1], "test_macro_f1") if best_child[1] else None},
        "best_foundation_artifact_child": {"node": best_foundation[0], "val_macro_f1": foundation_val, "test_macro_f1": metric(best_foundation[1], "test_macro_f1") if best_foundation[1] else None},
        "best_dense_no_artifact_child": {"node": best_dense[0], "val_macro_f1": dense_val, "test_macro_f1": metric(best_dense[1], "test_macro_f1") if best_dense[1] else None},
        "best_dense_matched_no_artifact_control": {"node": best_control[0], "val_macro_f1": control_val, "test_macro_f1": metric(best_control[1], "test_macro_f1") if best_control[1] else None},
        "deltas": {
            "best_child_vs_root_val": (child_val - root_val) if child_val is not None and root_val is not None else None,
            "foundation_vs_root_val": (foundation_val - root_val) if foundation_val is not None and root_val is not None else None,
            "foundation_vs_best_dense_no_artifact_val": (foundation_val - dense_val) if foundation_val is not None and dense_val is not None else None,
            "foundation_vs_dense_matched_control_val": (foundation_val - comparator_val) if foundation_val is not None and comparator_val is not None else None,
        },
        "paired_comparisons": paired,
        "verdict": {
            "child_beats_root": bool(child_val is not None and root_val is not None and child_val > root_val),
            "foundation_artifact_beats_root": bool(foundation_val is not None and root_val is not None and foundation_val > root_val),
            "foundation_artifact_beats_dense_control": bool(foundation_val is not None and comparator_val is not None and foundation_val > comparator_val),
            "artifact_incremental_gain_proven": bool(foundation_val is not None and comparator_val is not None and foundation_val > comparator_val),
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    deltas = report.get("deltas", {})
    verdict = report.get("verdict", {})
    lines = [
        "# Artifact Usefulness Report",
        "",
        f"- Run dir: `{report.get('run_dir')}`",
        f"- Artifact incremental gain proven: `{verdict.get('artifact_incremental_gain_proven')}`",
        f"- Best child vs root val delta: `{deltas.get('best_child_vs_root_val')}`",
        f"- Foundation vs root val delta: `{deltas.get('foundation_vs_root_val')}`",
        f"- Foundation vs dense no-artifact val delta: `{deltas.get('foundation_vs_best_dense_no_artifact_val')}`",
        f"- Foundation vs dense matched-control val delta: `{deltas.get('foundation_vs_dense_matched_control_val')}`",
        "",
        "## Best Nodes",
        "",
        "| Role | Node | Val Macro-F1 | Test Macro-F1 |",
        "|---|---|---:|---:|",
    ]
    for key, label in [
        ("best_root", "Best root"),
        ("best_generated_child", "Best generated child"),
        ("best_foundation_artifact_child", "Best foundation artifact child"),
        ("best_dense_no_artifact_child", "Best dense no-artifact child"),
        ("best_dense_matched_no_artifact_control", "Best dense matched control"),
    ]:
        row = report.get(key, {}) or {}
        lines.append(f"| {label} | `{row.get('node')}` | {row.get('val_macro_f1')} | {row.get('test_macro_f1')} |")
    paired = report.get("paired_comparisons", []) or []
    if paired:
        lines += ["", "## Paired Artifact Controls", "", "| Artifact child | Control child | Artifact val | Control val | Incremental gain |", "|---|---|---:|---:|---:|"]
        for row in paired:
            lines.append(f"| `{row.get('artifact_child')}` | `{row.get('control_child')}` | {row.get('artifact_val_macro_f1')} | {row.get('control_val_macro_f1')} | {row.get('artifact_incremental_val_gain')} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "A child can beat the root because of capacity, loss, optimization, or artifacts. This report only treats biological artifacts as useful when a source-backed artifact child beats the best available dense no-artifact or paired dense matched-capacity control under the same validation-only selection policy.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write artifact incremental usefulness report for a completed harness run.")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.run_dir)
    (args.run_dir / "artifact_usefulness_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.run_dir / "artifact_usefulness_report.md")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
