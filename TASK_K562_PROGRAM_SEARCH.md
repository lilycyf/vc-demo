# Task: K562 Program-Node VCHarness-Style Search

This is a concrete task file. The general rules live in `CODEX_AGENT_OPERATING_RULES.md` and `E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md`.

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
sed -n '1,220p' CODEX_AGENT_OPERATING_RULES.md
sed -n '1,220p' TASK_K562_PROGRAM_SEARCH.md
```

## Formal Search Command

Start with a run that allows planned blueprints to materialize implementation requests:

```bash
python -m vc_demo.harness.program_run   --experiment k562_program_node_agent_search   --root-configs configs/k562_roots/*.json   --run-dir experiments/k562_program_node_agent_search   --budget-nodes 16   --max-epochs 4   --max-children 3   --stop-no-improve 8   --exploration 0.7   --seed 11   --allow-planned-blueprints   --max-pending-implementations 1   --reset
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
