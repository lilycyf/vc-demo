# E. VCHarness-Style One-Cell-Line Harness Handoff

This stage adds a paper-like orchestration layer for a single K562 experiment. It does not reproduce the full VCHarness paper system, but it makes the demo closer in structure:

- MCTS selects which trained parent node to expand next.
- An agent-style proposal step generates the next child pipeline.
- The executor trains the child node and writes node memory artifacts.
- The report summarizes root baselines, all trained nodes, the best-so-far curve, failures, and the tree.

## What Changed

New package:

- `src/vc_demo/harness/mcts.py`: UCT-based parent selection and reward backpropagation.
- `src/vc_demo/harness/agent.py`: rule-based agent stub that proposes larger config-level changes.
- `src/vc_demo/harness/executor.py`: node training wrapper around `vc_demo.train.train`.
- `src/vc_demo/harness/report.py`: summary writer for tree and node metrics.
- `src/vc_demo/harness/run.py`: CLI orchestrator.

The key separation is intentional: MCTS does not design the child. MCTS only decides which parent looks worth expanding. The agent stub designs the child from that parent.

## What One Node Means Here

One node is one complete executable candidate pipeline:

- feature source: `k562_onehot`, `k562_delta`, or `k562_concat`
- model family: `mlp`, `residual_mlp`, `gated_mlp`, or `low_rank_mlp`
- structural settings: hidden width, depth, low-rank head dimension
- optimization settings: dropout, learning rate, weight decay
- one fresh training/evaluation run

Node workspaces are written under `experiments/<name>/nodes/` and ignored by git. Summaries, tree metadata, and proposals are written outside `nodes/`.

## Current Limitation

The agent is currently `rule_based_vcharness_stub`. It creates larger architecture/pipeline proposals, but it does not call a live Codex agent to edit Python source files during the search. This keeps the run controlled and reproducible while preserving the paper-like loop shape.

## Smoke Test Command

```bash
python -m vc_demo.harness.run   --experiment k562_vcharness_smoke   --root-configs configs/k562_roots/root_concat_mlp.json configs/k562_roots/root_concat_residual_mlp.json   --run-dir experiments/k562_vcharness_smoke   --budget-nodes 2   --max-epochs 1   --max-children 2   --stop-no-improve 2   --reset
```

## Formal One-Cell-Line Experiment Command

```bash
cd /workspace/vc-demo
python -m vc_demo.harness.run   --experiment k562_vcharness_style   --root-configs configs/k562_roots/*.json   --run-dir experiments/k562_vcharness_style   --budget-nodes 30   --max-epochs 4   --max-children 3   --stop-no-improve 8   --exploration 0.7   --seed 7   --reset
```

For a closer-to-paper run, increase `--budget-nodes` and `--max-epochs`. For a cheaper run, reduce them.
