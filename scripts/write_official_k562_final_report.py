from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def event_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("event", "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a paper-level single-K562 final report from a harness run directory.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    run_dir = args.run_dir
    out = args.output or run_dir / "final_report.md"

    tree = load_json(run_dir / "tree.json")
    failures = load_json(run_dir / "failures.json").get("failures", [])
    static_tree = load_json(run_dir / "alignment" / "official_k562_static_tree.json")
    artifact_matrix = load_json(run_dir / "alignment" / "official_k562_artifact_alignment_matrix.json")
    search_space_audit = load_json(run_dir / "alignment" / "official_k562_paper_scale_search_space_audit.json")
    family_mapping = load_json(run_dir / "alignment" / "official_k562_family_mapping.json")
    mcts_trace = load_jsonl(run_dir / "mcts_trace.jsonl")
    manifest = load_json(run_dir / "run_manifest.json")
    implementation_queue = load_json(run_dir / "implementation_queue.json").get("items", [])
    search_memory = load_json(run_dir / "search_memory.json")

    trained = [(name, node) for name, node in tree.get("nodes", {}).items() if node.get("status") == "trained"]
    best = max(trained, key=lambda item: float(item[1].get("best_val_macro_f1", -1)), default=("", {}))

    lines = [
        "# Official K562 Paper-Level Single-Cellline Report",
        "",
        "## Task Definition",
        "",
        "- Task: K562 CRISPR perturbation DEG classification",
        "- Split: train 1,388 / validation 154 / test 421 perturbations",
        "- Target genes: 6,640",
        "- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only",
        "",
        "## Search System",
        "",
        f"- Experiment: `{tree.get('experiment', manifest.get('experiment', ''))}`",
        f"- Trained nodes: {len(trained)}",
        f"- Failed nodes: {len(failures)}",
        f"- Pending implementations: {len(implementation_queue)}",
        f"- Public static tree nodes cataloged: {static_tree.get('node_count', 'n/a')}",
        f"- Public best path scaffold: `{static_tree.get('best_path', '')}`",
        f"- Paper-scale estimated candidate count: {search_space_audit.get('estimated_combinatorial_candidate_count', 'n/a')}",
        f"- Paper-scale 600+ manifest target reached: {str(search_space_audit.get('reaches_600_plus', False)).lower()}",
        f"- MCTS trace events: {len(mcts_trace)}",
        f"- MCTS policy: {manifest.get('search', {}).get('selection_policy', 'uct') or 'uct'}",
        "- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective",
        f"- Blueprint families covered: {len(search_memory.get('family_counts', {}))}",
        f"- Structural replicate nodes: {len(search_memory.get('replicate_nodes', []))}",
        "- Strict artifact rule: missing official artifacts must acquire/block, not fallback",
        "",
        "## Artifact Alignment",
        "",
        f"- Present artifacts: {len(artifact_matrix.get('present', []))}",
        f"- Missing artifacts: {', '.join(artifact_matrix.get('missing', [])) or 'none'}",
        f"- Reconstructed compatibility artifacts: {', '.join(artifact_matrix.get('reconstructed_compatibility', [])) or 'none'}",
        "- STRING_GNN compatibility caveat: reconstructed artifacts must not be claimed as numerically equivalent to unpublished original checkpoints.",
        "",
        "## Public Static Tree Alignment",
        "",
        f"- Family groups mapped: {len(family_mapping)}",
        "- The public static scaffold is benchmark/reference only; it is not counted as local search output.",
        "",
        "| Public family | Node count | Local equivalent blueprints |",
        "|---|---:|---|",
    ]
    for family, row in sorted(family_mapping.items()):
        lines.append(f"| {family} | {row.get('node_count', 0)} | {', '.join(row.get('local_equivalent_blueprints', []))} |")

    lines.extend(["", "## Scientific Search Coverage", "", "| Family | Count |", "|---|---:|"])
    for family, count in sorted((search_memory.get("family_counts", {}) or {}).items()):
        lines.append(f"| {family} | {count} |")
    lines.extend(["", "## MCTS Trace Summary", "", "| Event | Count |", "|---|---:|"])
    for event, count in sorted(event_counts(mcts_trace).items()):
        lines.append(f"| {event} | {count} |")

    lines.extend(["", "## Results", "", "| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |", "|---|---|---|---|---|---:|---:|"])
    for name, node in sorted(trained, key=lambda item: (int(item[1].get("iteration", 0)), item[0])):
        lines.append(f"| `{name}` | `{node.get('parent', '')}` | {node.get('execution_backend', '')} | {node.get('strategy', 'root')} | {node.get('structural_relation', '')} | {float(node.get('best_val_macro_f1', 0)):.4f} | {float(node.get('test_macro_f1', 0)):.4f} |")

    lines.extend([
        "",
        "## Best Node",
        "",
        f"- Best validation node: `{best[0]}`",
        f"- Validation Macro-F1: {float(best[1].get('best_val_macro_f1', 0)):.4f}" if best[0] else "- Validation Macro-F1: n/a",
        f"- Test Macro-F1: {float(best[1].get('test_macro_f1', 0)):.4f}" if best[0] else "- Test Macro-F1: n/a",
        "",
        "## Gap Attribution",
        "",
        "- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.",
        "- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.",
        "- Remaining gap: native implementations are compact proxies unless exact public static training recipe/checkpoints are run in benchmark mode.",
        "- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.",
        "- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.",
    ])

    gap_attribution = {
        "format": "official_k562_final_gap_attribution.v1",
        "artifact_gap": {
            "missing": artifact_matrix.get("missing", []),
            "reconstructed_compatibility": artifact_matrix.get("reconstructed_compatibility", []),
        },
        "search_scale_gap": {
            "trained_nodes": len(trained),
            "paper_scale_target_nodes": 600,
            "estimated_candidate_count": search_space_audit.get("estimated_combinatorial_candidate_count"),
        },
        "epoch_budget_gap": manifest.get("search", {}).get("max_epochs"),
        "implementation_gap": {"pending_implementations": len(implementation_queue), "failed_nodes": len(failures), "family_counts": search_memory.get("family_counts", {}), "replicate_nodes": len(search_memory.get("replicate_nodes", []))},
        "metric_contract_gap": "external benchmark mode must supply held-out test metric; smoke mode may mark test as missing_or_val_fallback",
        "stochastic_gap": "single short runs can differ from public/static and paper scores; compare only after 50/150/600-node staged runs",
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    gap_path = out.parent / "final_gap_attribution.json"
    gap_path.write_text(json.dumps(gap_attribution, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out), "gap_attribution": str(gap_path), "trained_nodes": len(trained), "failed_nodes": len(failures), "best_node": best[0]}, indent=2))


if __name__ == "__main__":
    main()
