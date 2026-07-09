# Autonomous Agent Loop Upgrade

This repo now supports a bounded single-cell-line VCHarness-style autonomous loop. It does not call the Codex API internally; the active Codex window is the coding agent, and the repo provides queues, state, prompts, audits, and runnable commands.

## Codex Execution Model

Read `CODEX_AGENT_COOKBOOK.md` before formal runs. The harness may generate `IMPLEMENTATION_REQUEST.md`, `CODEX_IMPLEMENTATION_TASK.md`, or `ACQUIRE_<artifact>.md`; the active Codex agent executes those tasks directly in the repo. Do not add internal Codex/OpenAI API calls for the formal experiment path.

## Closed Loop

```text
preflight
-> program_run MCTS parent selection
-> artifact-aware blueprint proposal
-> duplicate/memory guard
-> strict artifact check
-> train executable node OR create implementation/acquisition queue
-> implementation_agent writes node-local model.py when a safe template exists
-> train_pending executes implemented nodes
-> search_memory records successes, failures, blocked artifacts, and blueprint counts
-> run_manifest records reproducibility state
-> autonomous_run repeats within a bounded cycle budget
```

## New Entrypoints

### Preflight

```bash
python -m vc_demo.harness.preflight   --root-configs configs/k562_roots/root_concat_gated_mlp.json configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json configs/k562_roots/root_concat_esm2_target_aware_bilinear.json   --artifact-registry configs/artifacts/k562_registry.json   --cell-line K562   --output experiments/<run>/preflight.json
```

### Autonomous loop

```bash
python -m vc_demo.harness.autonomous_run   --experiment <experiment>   --root-configs <root configs>   --run-dir experiments/<run>   --budget-nodes 32   --max-epochs 4   --selection-policy uct   --artifact-registry configs/artifacts/k562_registry.json   --allow-planned-blueprints   --auto-implement-pending   --auto-acquire-known   --repair-attempts 2   --max-cycles 4   --reset
```

### Implementation agent

```bash
python -m vc_demo.harness.implementation_agent   --run-dir experiments/<run>   --train   --max-epochs 4   --repair-attempts 2
```

### Handoff prompt generator

```bash
python scripts/generate_codex_experiment_prompt.py   --branch framework-autonomous-agent-loop   --experiment k562_autonomous_formal_search   --run-dir experiments/k562_autonomous_formal_search   --root-configs configs/k562_roots/root_concat_gated_mlp.json configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json configs/k562_roots/root_concat_esm2_target_aware_bilinear.json   --budget-nodes 32   --max-epochs 4   --output experiments/k562_autonomous_formal_search/CODEX_EXPERIMENT_PROMPT.md
```

## What Is Automatic Now

- MCTS chooses the parent node.
- Artifact-aware proposal ranking prefers executable high-level blueprints with present artifacts.
- Duplicate guards avoid repeatedly expanding the same blueprint on the same parent and limit global blueprint repeats.
- Known executable templates are written into node-local `model.py` by `implementation_agent`.
- Pending nodes can be trained automatically after implementation.
- Known artifact acquisition can run automatically and resume when all queued artifacts become present.
- `search_memory.json` and `run_manifest.json` preserve state for later agents.

## What Still Requires External Codex Or Human Review

- Blueprints without a safe built-in template produce `CODEX_IMPLEMENTATION_TASK.md` for the active Codex agent to implement directly.
- Missing artifacts with uncertain public sources produce `ACQUIRE_<artifact>.md`; the active Codex agent must search official/primary sources, attempt source-backed acquisition/build/audit, and only stop with a blocker after that attempt fails.
- Large external model downloads, license-gated resources, and underspecified pretrained encoders must stop for review.

## Formal-Test Guardrails

- No fake artifacts.
- No fallback model in strict search unless explicitly running an ablation.
- No changes to data splits, labels, or metric semantics during node implementation.
- Do not commit raw data, checkpoints, `nodes/`, cache files, or secrets.

## Paper Alignment Layers 1-4

See `PAPER_ALIGNMENT_LAYERS_1_4.md` for the current alignment of the Codex execution layer, MCTS/proposal policy, model-space grammar, and artifact readiness layer.

## Paper Alignment Layers 5-8

See `PAPER_ALIGNMENT_LAYERS_5_8.md` for benchmark audit, search scale planning, failure repair workflow, and paper-style final analysis.
