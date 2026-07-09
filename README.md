# vc-demo

`vc-demo` is now an official-K562-focused VCHarness-style harness. The current mainline is not the early synthetic demo; it is a single-cell-line automatic modeling loop for K562 CRISPR DEG classification with:

- official K562 task/data contracts;
- artifact registry and acquisition guardrails;
- MCTS proposal pools with UCT-style selection;
- on-demand Codex implementation for selected planned nodes;
- strict no-fallback artifact behavior;
- public VCHarness static-node wrapper and native public-best reimplementation paths.

## Current Entry Points

Read these first for formal work:

```bash
cat OFFICIAL_K562_IMPLEMENTATION_LOOP.md
cat ARTIFACT_ACQUISITION_RUNBOOK.md
cat CODEX_AGENT_COOKBOOK.md
cat docs/OFFICIAL_K562_GAP_CLOSING.md
```

Core command wrapper:

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py --help
```

Generate a handoff prompt for an experiment Codex:

```bash
python scripts/generate_codex_experiment_prompt.py \
  --branch official-k562-gap-closing \
  --experiment official_k562_formal_run \
  --run-dir experiments/official_k562_formal_run \
  --root-configs \
    configs/official_k562_root_aido_embedding_mlp.json \
    configs/official_k562_root_aido_gnn_embedding_mlp.json \
    configs/official_k562_native_public_best_reimplementation.json \
    configs/official_k562_public_best_node_smoke.json \
  --budget-nodes 150 \
  --max-epochs 1 \
  --output /tmp/CODEX_EXPERIMENT_PROMPT.md
```

## Artifact Rule

Formal runs do not train fallback models for missing foundation-model artifacts. If a selected node needs a missing artifact, the run creates `acquisition_queue.json`. The next action is active acquisition:

```bash
python -m vc_demo.harness.artifact_acquisition \
  --queue <run_dir>/acquisition_queue.json \
  --registry configs/artifacts/k562_registry.json \
  --sources configs/artifacts/acquisition_sources.json \
  --cell-line K562 \
  --output-dir <run_dir>/artifact_acquisition \
  --execute-known
```

If this creates `ACQUIRE_<artifact>.md`, follow it: search official/primary sources, download or build only source-backed artifacts, audit provenance/alignment, update the registry, and resume. Block only after acquisition fails with documented source or tensor-contract reasons.

## Smoke Checks

Cheap static checks:

```bash
python -m compileall -q src scripts
python scripts/audit_official_k562_paper_scale_search_space.py \
  --config configs/official_k562_paper_scale_search_space.json \
  --output-json /tmp/official_k562_paper_scale_search_space_audit.json \
  --output-md /tmp/official_k562_paper_scale_search_space_audit.md
```

Official K562 artifact audit, assuming artifacts are prepared on the RunPod volume:

```bash
python -m vc_demo.harness.artifact_registry --cell-line K562
```

## Repo Hygiene

- Do not commit `data/`, model checkpoints, `experiments/**/nodes/`, pycache, egg-info, secrets, or large raw artifacts.
- Commit formal run metadata only when intentionally requested: `tree.json`, summaries, queues, proposals, small audit JSON, and node-local source files.
- Historical early-stage demo outputs have been removed from the mainline. Use git history if you need the old synthetic scaffold notes.
