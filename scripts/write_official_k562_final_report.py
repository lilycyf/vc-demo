from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


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
    manifest = load_json(run_dir / "run_manifest.json")
    trained = [(name, node) for name, node in tree.get("nodes", {}).items() if node.get("status") == "trained"]
    best = max(trained, key=lambda item: float(item[1].get("best_val_macro_f1", -1)), default=("", {}))
    roots = [(name, node) for name, node in trained if not node.get("parent")]
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
        f"- Public static tree nodes cataloged: {static_tree.get('node_count', 'n/a')}",
        f"- Public best path scaffold: `{static_tree.get('best_path', '')}`",
        "- MCTS policy: UCT unless run manifest says otherwise",
        "- Strict artifact rule: missing official artifacts must acquire/block, not fallback",
        "",
        "## Artifact Alignment",
        "",
        f"- Present artifacts: {len(artifact_matrix.get('present', []))}",
        f"- Missing artifacts: {', '.join(artifact_matrix.get('missing', [])) or 'none'}",
        f"- Reconstructed compatibility artifacts: {', '.join(artifact_matrix.get('reconstructed_compatibility', [])) or 'none'}",
        "- STRING_GNN compatibility caveat: reconstructed artifacts must not be claimed as numerically equivalent to unpublished original checkpoints.",
        "",
        "## Results",
        "",
        "| Node | Parent | Backend | Strategy | Val Macro-F1 | Test Macro-F1 |",
        "|---|---|---|---|---:|---:|",
    ]
    for name, node in sorted(trained, key=lambda item: (int(item[1].get("iteration", 0)), item[0])):
        lines.append(f"| `{name}` | `{node.get('parent', '')}` | {node.get('execution_backend', '')} | {node.get('strategy', 'root')} | {float(node.get('best_val_macro_f1', 0)):.4f} | {float(node.get('test_macro_f1', 0)):.4f} |")
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
        "- Remaining scale gap: smoke runs validate the loop; 50/150-node runs are required for paper-level search pressure.",
        "",
        "## Next Commands",
        "",
        "```bash",
        "PYTHONPATH=src python scripts/run_official_k562_harness_search.py \\",
        "  --run-dir experiments/official_k562_gap_closing_small_50 \\",
        "  --experiment official_k562_gap_closing_small_50 \\",
        "  --root-configs \\",
        "    configs/official_k562_root_aido_embedding_mlp.json \\",
        "    configs/official_k562_root_aido_gnn_embedding_mlp.json \\",
        "    configs/official_k562_public_best_node_smoke.json \\",
        "    configs/official_k562_native_public_best_reimplementation.json \\",
        "  --budget-nodes 50 --max-epochs 3 --max-children 3 --stop-no-improve 12 \\",
        "  --selection-policy uct --official-blueprint-space --strict-artifacts \\",
        "  --allow-planned-blueprints --enable-repair-loop --enable-acquisition-loop --reset",
        "```",
    ])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out), "trained_nodes": len(trained), "failed_nodes": len(failures), "best_node": best[0]}, indent=2))


if __name__ == "__main__":
    main()
