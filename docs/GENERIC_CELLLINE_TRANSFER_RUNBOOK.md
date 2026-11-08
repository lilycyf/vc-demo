# Generic Cell-Line Transfer Runbook

Read CODEX_AGENT_COOKBOOK.md and docs/RESEARCH_PROTOCOL.md first. This document
describes the cell-line classification adapter, not a universal model/dataset
template. A regression, lineage or survival task uses its own source-backed
adapter and tensor/metric contract, while reusing the shared research safeguards.

## Short Handoff

Use BASE_BRANCH, RUN_BRANCH, CELL_LINE_ID (or TASK_ID), RUN_TYPE, TEST_LEVEL,
RUN_DIR and the approved resource limit. TARGET_VAL_MACRO_F1 is an optional
classification objective unless the user explicitly requires a threshold.
Do not copy long historical rules into prompts. Do not infer another cell line
or its target universe, split, labels or artifact vocabulary from an example.

## Preparation

1. Work in the specified remote repo; preserve the user's work and current branch
   unless a separate run branch was requested.
2. Read primary task/data sources. Identify the independent group, available
   observation window, endpoint, metric/direction, sampling and batch limits.
3. Acquire data/artifacts from verifiable sources. Lack of a resolver requires
   same-session Codex investigation, not immediate termination.
4. Register research_protocol.json and exact benchmark recipes, including known
   strong historical recipes. Record encoding, scaling and actual source hashes.
5. Declare independent coverage/optimization/confirmation budgets, effective
   per-family training policy, stopping rules and optional scientific targets.
6. A from-scratch scientific run uses a fresh RUN_DIR. Never reset a directory
   with executed recipes or a confirmation lock. Resume only an open protocol.

## Execution Profiles

`scripts/run_generic_cellline_transfer_test.py` provides named classification
profiles: preflight, transfer_64x16, transfer_150x40 and full_cellline_run.
The first three validate execution mechanics; their scores are not scientific
model evidence. The full profile's300/100/8 settings are defaults for that
adapter, not universal scientific minima or valid settings for every model.
Formal adequacy comes from the registered task/training/validation plan.

```bash
PYTHONPATH=src python scripts/run_generic_cellline_transfer_test.py \
  --cell-line "$CELL_LINE_ID" --run-type "$RUN_TYPE" --level "$TEST_LEVEL" \
  --run-dir "$RUN_DIR" --execute
```

Use --resume for an existing open run. The wrapper writes an invocation plan.
Other task adapters must use their actual entrypoints; never run a regression
through the classification adapter's n_targets/n_classes contract. Missing
backend registration is implementation work, not justification for synthetic
data or another cell line's backend.

## Active Codex Loop

Inspect development-only feedback, select a trained parent, generate multiple
hypotheses, re-rank the retained global queue and train the best next rollout.
Availability is a subsequent acquisition gate, not a ranking bonus. Pruned and
unselected proposals do not train. Only successful formal development results
backpropagate, exactly once.

For selected planned nodes, handle the request now: acquire actual dependencies,
choose the full model/composition, update research_hypothesis.json, implement,
compile, native-smoke, train_pending and resume. Codex may replace or simplify
the parent. Do not rewrite an existing custom model with a template. After real
unsuccessful attempts, record infeasibility/skip and continue other candidates;
do not leave an unprocessed queue as the final product.

Use explicit coverage allocation to inventory methods; spend optimization
allocation on development evidence. Do not force named foundation families to
the top because they are large, complex, available or paper-branded. Replenish
and re-rank after every completed rollout, including resumed implementations.

## Evaluation And Closure

Evaluate strongest references, mechanical/null controls, group-aware uncertainty
and task-relevant strata during development. Residuals/stackers need inner OOF;
uniform epoch counts are not evidence of fair optimization opportunity.

Stop at the registered budget/stopping condition or an explicit validity/resource
boundary, not because one queue item was handled. An optional target does not
override the spending limit. A null model result can still be an executed study.

Freeze selected executable fingerprints using research_contract --freeze-selection.
Only then perform confirmation. Search cannot resume after that lock; exposed
test groups stay exposed even in another branch. Static scripts that evaluate
test are confirmation/reference tracks, not adaptive proposal parents.

## Delivery

Report separate execution, protocol, scientific, artifact-attribution and transfer
verdicts. Include exact root/child recipes, independent sample counts, primary and
conditional metrics, paired uncertainty, budgets/costs, acquisition and repair,
negative findings and prior exposure. Do not claim framework superiority from
one task or one positive seed. Use docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md.

Commit only allowed source/config/metadata/tests/reports. Keep datasets, fitted
models, arrays, environments and credentials off GitHub; verify staged paths and
secrets. Preserve the approved stop timer and do not extend cloud spending.

