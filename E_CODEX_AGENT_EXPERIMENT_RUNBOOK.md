# Codex VCHarness-Style K562 Experiment Runbook

This document is the instruction sheet for the next Codex agent. The goal is to run one K562 cell-line experiment in a VCHarness-style loop, where the same Codex session acts as the agent that proposes larger child-node changes.

## Starting Point

Work only on the RunPod machine.

```bash
cd /workspace/vc-demo
git pull --ff-only
```

Expected current code includes:

- `src/vc_demo/harness/run.py`: orchestration CLI
- `src/vc_demo/harness/mcts.py`: MCTS parent selection
- `src/vc_demo/harness/agent.py`: current rule-based proposal stub
- `src/vc_demo/harness/executor.py`: node training executor
- `src/vc_demo/harness/report.py`: summary writer
- `configs/k562_roots/*.json`: root candidate configs
- real K562 data under ignored `data/cell_lines/`

## Role of This Codex Session

You are not only running the search. You are also the agent that improves the proposal behavior.

The existing `rule_based_vcharness_stub` is allowed to be edited by you before the formal run. Your job is to make the child proposals meaningfully different, closer to the paper's idea that each node is a different executable model/pipeline hypothesis.

MCTS should remain responsible for parent selection. Codex-agent logic should remain responsible for child design.

## What You May Change

You may edit:

- `src/vc_demo/harness/agent.py`
- `src/vc_demo/harness/report.py`
- `src/vc_demo/harness/run.py`, only if needed for logging or handoff quality
- `src/vc_demo/models.py`, only if adding a clearly named model family and keeping old models compatible
- `configs/k562_roots/*.json`, only if adding a new root config without breaking existing roots
- documentation files for reporting

You may create:

- new proposal strategy names
- new config-level mutation policies
- new model families if they are small enough to train on this pod
- `experiments/k562_vcharness_codex_agent/notes.md`
- final report markdown files

## What You Must Not Change

Do not change:

- raw data under `data/raw/`
- processed dataset contents under `data/cell_lines/`
- train/validation/test split definitions
- metric meaning: validation Macro-F1 remains selection reward
- gitignore rules that keep large node artifacts out of git
- the core claim boundary: this is a one-cell-line approximation, not full paper reproduction

Do not delete previous committed experiment summaries.

Do not commit checkpoints, `nodes/`, pycache, raw data, or processed data.

## Required Node Meaning

Each node must represent one complete trainable candidate pipeline, not a tiny isolated hyperparameter tweak.

A child node should change at least one major dimension, preferably two or more:

- feature source: onehot, delta, concat
- model family: mlp, residual_mlp, gated_mlp, low_rank_mlp, or a new compatible family
- head design: dense head vs low-rank/factorized head
- capacity: width/depth together
- regularization/optimization: dropout, learning rate, weight decay together
- training budget, only if explicitly documented

Avoid generating many children that differ only by learning rate.

## Required Records Per Child Node

For every child proposal, make sure the run writes or preserves:

- parent node id
- child node id
- MCTS candidate scores at selection time
- proposal strategy name
- hypothesis in plain English
- concrete config changes
- validation Macro-F1
- test Macro-F1
- whether it improved over parent
- whether it improved over best root
- failure reason if failed

The current harness already writes proposal JSON files under:

```text
experiments/<experiment>/proposals/
```

and summary/tree files under:

```text
experiments/<experiment>/tree.json
experiments/<experiment>/search_summary.md
experiments/<experiment>/failures.json
```

Node workspaces under `experiments/<experiment>/nodes/` are ignored by git and should not be committed.

## Formal Run Command

After any agent/proposal improvements are complete, run:

```bash
cd /workspace/vc-demo
python -m vc_demo.harness.run \
  --experiment k562_vcharness_codex_agent \
  --root-configs configs/k562_roots/*.json \
  --run-dir experiments/k562_vcharness_codex_agent \
  --budget-nodes 30 \
  --max-epochs 4 \
  --max-children 3 \
  --stop-no-improve 8 \
  --exploration 0.7 \
  --seed 7 \
  --reset
```

If the run is too slow or GPU availability is poor, use this smaller fallback and clearly label it as a pilot:

```bash
cd /workspace/vc-demo
python -m vc_demo.harness.run \
  --experiment k562_vcharness_codex_agent_pilot \
  --root-configs configs/k562_roots/*.json \
  --run-dir experiments/k562_vcharness_codex_agent_pilot \
  --budget-nodes 12 \
  --max-epochs 2 \
  --max-children 3 \
  --stop-no-improve 5 \
  --exploration 0.7 \
  --seed 7 \
  --reset
```

## Stopping Conditions

Stop the experiment when one of these happens:

- harness stops automatically with `no improvement for 8 nodes`
- 30 child nodes have been attempted
- repeated infrastructure failure prevents meaningful training
- GPU cost/time budget is explicitly stopped by the user

Do not stop merely because an early child is worse than its parent. That is expected in tree search.

## Final Conclusion Required

At the end, create a final conclusion document:

```text
experiments/k562_vcharness_codex_agent/final_conclusion.md
```

If you ran the pilot instead, use the pilot experiment directory.

The conclusion must include:

1. Run setup
   - command used
   - GPU/device reported by metrics
   - budget nodes
   - max epochs
   - stop reason

2. Best result
   - best root val/test Macro-F1
   - best overall node val/test Macro-F1
   - improvement over best root
   - path from root to best node

3. Search behavior
   - how many nodes trained
   - how many failed
   - which proposal strategies appeared useful
   - whether MCTS expanded multiple branches or concentrated on one branch

4. Biological/ML interpretation
   - which feature source worked best
   - which model family worked best
   - whether the result suggests representation, architecture, or optimization mattered most

5. Gap to paper
   - clearly state this is one-cell-line K562 only
   - clearly state whether Codex edited proposal/model code before the run
   - clearly state that this is not the full four-cell-line VCHarness benchmark

## Git Commit Requirements

Commit and push only code, configs, proposal JSONs, summaries, and conclusion files.

Before committing, check:

```bash
git status --short --ignored
```

Allowed to commit:

- `src/vc_demo/...`
- `configs/...`
- `experiments/k562_vcharness_codex_agent/tree.json`
- `experiments/k562_vcharness_codex_agent/search_summary.md`
- `experiments/k562_vcharness_codex_agent/failures.json`
- `experiments/k562_vcharness_codex_agent/proposals/*.json`
- `experiments/k562_vcharness_codex_agent/final_conclusion.md`

Do not commit:

- `experiments/**/nodes/`
- `data/`
- `*.pt`
- `__pycache__/`
- `*.egg-info/`

Suggested commit message:

```bash
git add src/vc_demo configs experiments/k562_vcharness_codex_agent E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md
git commit -m "Run Codex-agent K562 harness experiment"
git push origin master
```

If only the runbook is being committed before the experiment, use:

```bash
git add E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md
git commit -m "Add Codex-agent experiment runbook"
git push origin master
```

## One-Sentence Mission

Use MCTS to choose which trained K562 candidate to expand, use Codex-agent judgment to generate larger child pipeline changes, train each child, stop by budget/no-improvement, and produce a final conclusion that says whether the search found a better one-cell-line model than the roots.
