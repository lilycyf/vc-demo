from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from vc_demo.harness.pipeline_grammar import program_for_blueprint
from vc_demo.harness.state import read_json


def _trained(tree: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return [(name, node) for name, node in tree.get("nodes", {}).items() if node.get("status") == "trained"]


def build_analysis(run_dir: Path) -> str:
    tree = read_json(run_dir / "tree.json")
    memory = read_json(run_dir / "search_memory.json") if (run_dir / "search_memory.json").exists() else {}
    manifest = read_json(run_dir / "run_manifest.json") if (run_dir / "run_manifest.json").exists() else {}
    failures = read_json(run_dir / "failures.json").get("failures", []) if (run_dir / "failures.json").exists() else []
    trained = _trained(tree)
    roots = [(name, node) for name, node in trained if not node.get("parent")]
    best = max(trained, key=lambda item: float(item[1].get("best_val_macro_f1", -1)), default=("", {}))
    best_root = max(roots, key=lambda item: float(item[1].get("best_val_macro_f1", -1)), default=("", {}))
    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for name, node in trained:
        strategy = str(node.get("strategy") or "root")
        by_strategy[strategy].append({"node": name, "val": node.get("best_val_macro_f1"), "test": node.get("test_macro_f1"), "program": program_for_blueprint(strategy)})
    lines = [
        "# Final Search Analysis",
        "",
        "## Result",
        "",
        f"- Run dir: `{run_dir}`",
        f"- Stop reason: {manifest.get('search', {}).get('stop_reason', 'unknown')}",
        f"- Trained nodes: {len(trained)}",
        f"- Failed nodes: {len(failures)}",
    ]
    if best[0]:
        lines.append(f"- Best overall: `{best[0]}` val={float(best[1].get('best_val_macro_f1', 0)):.4f} test={float(best[1].get('test_macro_f1', 0)):.4f}")
    if best_root[0]:
        improvement = float(best[1].get("best_val_macro_f1", 0)) - float(best_root[1].get("best_val_macro_f1", 0))
        lines.append(f"- Best root: `{best_root[0]}` val={float(best_root[1].get('best_val_macro_f1', 0)):.4f} test={float(best_root[1].get('test_macro_f1', 0)):.4f}")
        lines.append(f"- Improvement over best root: {improvement:.4f} validation Macro-F1")
    lines += ["", "## Strategy Families", "", "| Strategy | N | Best val | Best test | Grammar alignment |", "|---|---:|---:|---:|---|"]
    for strategy, rows in sorted(by_strategy.items()):
        best_row = max(rows, key=lambda row: float(row.get("val") or -1))
        program = best_row.get("program", {})
        lines.append(f"| `{strategy}` | {len(rows)} | {float(best_row.get('val') or 0):.4f} | {float(best_row.get('test') or 0):.4f} | {program.get('paper_alignment', '')} |")
    lines += ["", "## Artifact Interpretation", ""]
    artifacts = manifest.get("artifacts", {})
    lines.append(f"- Present artifacts: {', '.join(artifacts.get('present_artifacts', [])) or 'none'}")
    lines.append(f"- Missing artifacts: {', '.join(artifacts.get('missing_artifacts', [])) or 'none'}")
    blocked = memory.get("blocked_artifacts", [])
    if blocked:
        lines.append(f"- Blocked artifact events: {len(blocked)}")
    lines += ["", "## Memory-Derived Motifs", ""]
    motifs = memory.get("motifs", {})
    lines.append(f"- Promising: {', '.join(motifs.get('promising', [])) or 'none recorded'}")
    lines.append(f"- Discouraged: {', '.join(motifs.get('discouraged', [])) or 'none recorded'}")
    lines += ["", "## Next Search Recommendations", ""]
    if artifacts.get("missing_artifacts"):
        lines.append("- Acquire or explicitly reject missing high-value artifacts before claiming paper-level model-space coverage.")
    lines.append("- Expand strategies that beat the best root; prune repeated strategies that fail to improve after the repeat limit.")
    lines.append("- Treat training-only changes separately from architecture or biological-prior changes.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a paper-style final analysis for a completed run.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    text = build_analysis(args.run_dir)
    output = args.output or args.run_dir / "final_analysis.md"
    output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
