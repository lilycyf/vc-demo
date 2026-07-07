# Task: K562 Program-Node VCHarness-Style Search

This is a concrete task file. The general rules live in `CODEX_AGENT_OPERATING_RULES.md`, `E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md`, and `PAPER_LEVEL_SEARCH_SPACE_SPEC.md`.

## Research Question

For K562 CRISPR perturbation differential-expression-label prediction, can a VCHarness-style program-node search discover a model/pipeline that improves validation Macro-F1 over the best root baseline while preserving the existing data split?

## Data And Split

Use existing K562 real NPZ data prepared in this repo.

- Do not modify `data/raw/`.
- Do not modify `data/cell_lines/`.
- Do not alter train/validation/test splits.

## Metric

- Search reward: validation Macro-F1
- Final report: validation Macro-F1 and test Macro-F1

## Branch

Work on a new branch unless the user has already placed you on one:

```bash
git checkout -b k562-program-node-agent-search
```

Do not push directly to `master`.

## Starting Commands

```bash
cd /workspace/vc-demo
git pull --ff-only
sed -n '1,260p' PAPER_LEVEL_SEARCH_SPACE_SPEC.md
sed -n '1,220p' CODEX_AGENT_OPERATING_RULES.md
sed -n '1,220p' TASK_K562_PROGRAM_SEARCH.md
```

## Paper-Level Search-Space Requirement

This task is still scoped to one cell line, but the search should use the paper-level blueprint space. Do not pre-implement every blueprint. Use `MODEL_BLUEPRINTS` as a manifest. If a selected blueprint is planned, materialize an implementation request and implement only that selected node.

For a small serious run, target at least:

- 30 trained nodes if budget allows
- 5 planned blueprint proposals
- 2 planned blueprints implemented on demand
- at least one Level 4 or Level 5 child
- explicit recording of missing artifacts, fallbacks, costs, and wall time
- auditable MCTS selection using UCT or PUCT score components and rollout/backpropagation statistics

If the user asks for a shorter smoke run, record that the run validates the loop but does not validate paper-scale model discovery.

## Formal Search Command

Start with a run that allows planned blueprints to materialize implementation requests:

```bash
python -m vc_demo.harness.program_run   --experiment k562_program_node_agent_search   --root-configs configs/k562_roots/*.json   --run-dir experiments/k562_program_node_agent_search   --budget-nodes 30   --max-epochs 4   --max-children 3   --stop-no-improve 12   --exploration 0.7   --selection-policy puct   --seed 11   --allow-planned-blueprints   --max-pending-implementations 2   --reset
```

## If A Planned Blueprint Is Selected

Inspect:

```bash
python -m json.tool experiments/k562_program_node_agent_search/implementation_queue.json
```

For each queued node:

1. Read its `IMPLEMENTATION_REQUEST.md`.
2. Implement only that node's `model.py`.
3. Run:

```bash
python -m compileall -q src/vc_demo experiments/k562_program_node_agent_search/programs
```

4. Train the implemented node:

```bash
python -m vc_demo.harness.train_pending   --run-dir experiments/k562_program_node_agent_search   --node <NODE_ID>   --max-epochs 4
```

5. Continue the search if budget remains and the task still has no final conclusion.

## Final Deliverable

Create:

```text
experiments/k562_program_node_agent_search/final_conclusion.md
```

It must state:

- best root and metrics
- best overall node and metrics
- improvement over best root
- best path in the tree
- which blueprints were used
- which planned blueprints were implemented on demand
- failed/pending nodes
- limitations versus the paper
- which child nodes were Level 1/2/3/4/5 changes
- whether any foundation-model or graph-prior blueprint was blocked by missing artifacts
- wall-time and GPU-hour estimate when available

## Commit And Push

Allowed to commit:

- source/framework changes
- generated `programs/<node>/model.py` for implemented planned nodes
- `proposals/*.json`
- `tree.json`
- `failures.json`
- `implementation_queue.json`
- `search_summary.md`
- `final_conclusion.md`

Do not commit:

- `experiments/**/nodes/`
- `data/`
- checkpoints
- pycache
- egg-info

Push to your branch only.
