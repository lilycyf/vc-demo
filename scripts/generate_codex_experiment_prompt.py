from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a handoff prompt for a Codex formal experiment agent.")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--root-configs", nargs="+", required=True)
    parser.add_argument("--budget-nodes", type=int, default=32)
    parser.add_argument("--max-epochs", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root_configs = " ".join(args.root_configs)
    prompt = f"""# Codex Formal Experiment Prompt\n\nYou are running on RunPod in `/workspace/vc-demo`. Work only on RunPod.\n\n1. Fetch and checkout a new run branch from `{args.branch}`.\n2. Run preflight:\n\n```bash\npython -m vc_demo.harness.preflight \\\n  --root-configs {root_configs} \\\n  --artifact-registry configs/artifacts/k562_registry.json \\\n  --cell-line K562 \\\n  --output {args.run_dir}/preflight.json\n```\n\n3. If preflight is ready, run the autonomous loop:\n\n```bash\npython -m vc_demo.harness.autonomous_run \\\n  --experiment {args.experiment} \\\n  --root-configs {root_configs} \\\n  --run-dir {args.run_dir} \\\n  --budget-nodes {args.budget_nodes} \\\n  --max-epochs {args.max_epochs} \\\n  --max-children 3 \\\n  --stop-no-improve 10 \\\n  --exploration 1.4142135623730951 \\\n  --selection-policy uct \\\n  --artifact-registry configs/artifacts/k562_registry.json \\\n  --seed 53 \\\n  --allow-planned-blueprints \\\n  --auto-implement-pending \\\n  --max-auto-implement-nodes 1 \\\n  --repair-attempts 2 \\\n  --max-cycles 4 \\\n  --reset\n```\n\nRules:
- Do not fabricate missing artifacts. Missing artifacts trigger active acquisition before blocker reporting.
- If `acquisition_queue.json` is non-empty, run the artifact acquisition command from `run_manifest.json`/stdout, follow any generated `ACQUIRE_<artifact>.md`, search/download/build a source-backed artifact when possible, audit it, update the registry, and resume. Do not stop at queue creation unless the acquisition attempt fails with documented provenance/alignment reasons.
- If `CODEX_IMPLEMENTATION_TASK.md` appears, implement only node-local `model.py` and keep data/splits/metrics fixed.\n- Preserve `tree.json`, `search_memory.json`, `run_manifest.json`, `search_summary.md`, queues, proposals, and final conclusion.\n- Commit only code, configs, docs, summaries, tree/proposal metadata, and small reports. Do not commit raw data, checkpoints, node directories, pycache, or secrets.\n"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prompt, encoding="utf-8")
    print(prompt)


if __name__ == "__main__":
    main()
