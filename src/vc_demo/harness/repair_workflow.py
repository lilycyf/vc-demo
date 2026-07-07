from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from vc_demo.harness.search_memory import repair_prompt
from vc_demo.harness.state import read_json, write_json


def build_repair_tasks(run_dir: Path, output_dir: Path) -> dict[str, Any]:
    tree = read_json(run_dir / "tree.json") if (run_dir / "tree.json").exists() else {"nodes": {}}
    failures = read_json(run_dir / "failures.json").get("failures", []) if (run_dir / "failures.json").exists() else []
    tasks: list[dict[str, Any]] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    failed_nodes = {name: node for name, node in tree.get("nodes", {}).items() if node.get("status") == "failed"}
    for failure in failures:
        node_name = str(failure.get("node", ""))
        if not node_name:
            continue
        prompt = repair_prompt(run_dir, node_name)
        if not prompt:
            prompt = f"# Repair Task: `{node_name}`\n\nFailure: {failure.get('error')}\n"
        prompt += "\n## Failure Record\n\n```json\n" + json.dumps(failure, indent=2) + "\n```\n"
        path = output_dir / f"REPAIR_{node_name}.md"
        path.write_text(prompt, encoding="utf-8")
        tasks.append({"node": node_name, "path": str(path), "error": failure.get("error"), "strategy": failure.get("strategy")})
    report = {"format": "vc_demo_repair_workflow.v1", "run_dir": str(run_dir), "failed_nodes": sorted(failed_nodes), "tasks": tasks}
    write_json(output_dir / "repair_tasks.json", report)
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Codex repair tasks for failed nodes.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_repair_tasks(args.run_dir, args.output_dir)


if __name__ == "__main__":
    main()
