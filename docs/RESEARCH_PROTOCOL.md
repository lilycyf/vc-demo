# Shared Research Protocol

Confirmation evaluates the checkpoint saved by the selected development run;
it does not retrain or tune it. Its checksum is frozen with the selection, and
confirmation outputs live separately under `confirmation/<node>/`. A native
candidate without its original checkpoint cannot enter confirmation. External
scripts that cannot prove development-only evaluation are not search candidates.

## Scope

`harness/research_contract.py`, `research_feedback.py`, and `composition.py` are
task-neutral. Dataset parsing, biological interpretation, tensors and formal
training remain task adapters. The classification executor is not automatically
a regression/survival executor. T47D's completed results remain a frozen prior
protocol and are not recomputed by this framework upgrade.

## Immutable Task And Baselines

Register `research_protocol.json` with task_id, dataset_sha256, split_sha256,
label_semantics, metric `{name, direction}`, group_key and input_policy. Include
`required_benchmarks: {benchmark_id: executable_recipe_fingerprint}` when strong
historical recipes exist. An empty mapping is an explicit no-history declaration,
not permission to ignore a known benchmark.

```bash
PYTHONPATH=src python -m vc_demo.harness.research_contract \
  --run-dir experiments/<fresh_run> --protocol configs/tasks/<task_protocol>.json
```

`executable_recipe()` hashes effective config, actual code files, full input and
artifact contents, environment and epoch override. `capture_execution_recipe()`
is wired into the classification executor and registers roots under benchmarks/.
Task adapters must supply additional external source helpers and consumed inputs
through research.code_files/data_files/artifact_files. Declared model artifact
paths are validated and hashed, not accepted because a directory exists.

Never use a model name, input file size, or incomplete hyperparameter dictionary
as a scientific cache identity. Compare a cached identity before consuming folds.
A changed baseline config/code/data is a new recipe requiring explicit replay
and attribution, not a silent modification to an old comparison.

## Development Feedback

`paired_feedback(y, candidate, reference, groups, scorer, ...)` takes aligned
development OOF predictions and a task-supplied scorer/direction. It resamples
whole groups, provides paired deltas, uncertainty and optional strata. This is
development evidence, not a confirmatory p value after adaptive model selection.

Save task-appropriate controls and error diagnostics in development_feedback.json
with `evidence_phase=development`. `feedback.py` reads validation-only evidence;
test poisoning must leave its strategy statistics, guidance and policy unchanged.
Search memory and parent summaries exclude nested heldout results and legacy
feedback that lacks a development provenance declaration.

Coverage, optimization and confirmation have separate budgets. The program
runner accepts `--coverage-rollouts` (default0) and `--confirmation-models`
(default2), records a frozen research_budget_plan.json and current usage. The
total selected-rollout budget includes coverage and optimization; coverage is
not counted as optimization success or given a giant score bonus.

`rank_hypotheses()` supports development expected gain, uncertainty and estimated
cost, without an artifact-present/implemented bonus. Active Codex proposals must
record numeric assumptions as assumptions, not measured gains. The classification
adapter also uses descriptive trained-family feedback and re-ranks retained
global candidates each iteration. Family statistics across different models are
not independent replicates or confidence intervals.

## Open Composition

Allowed research relationships include replace, feature_fusion, joint,
crossfit_residual, crossfit_stack and ablation. No relationship is compulsory.
`agent_defined_candidate` permits architecture implementation beyond named
templates. Its artifact contract must enumerate what the implementation really
consumes; an empty initial requirement list is not evidence that new dependencies
are present. Existing model.py is preserved, compiled and checked.

For continuous regression, `ResidualCore` fits on parent OOF errors.
`CrossFittedResidualRegressor` additionally uses nested grouped fits to train
combination weights without leaking a held-out group's labels through inner
residual targets. `CrossFittedStackingRegressor` fits its meta-estimator on grouped
OOF predictions. Insufficient groups cause an explicit error, never a fallback
to in-sample residuals. These helpers are regressors; a classification adapter
must implement an appropriate OOF-logit/probability combiner rather than stacking
arbitrary class IDs as if continuous.

## Confirmation Boundary

Native classification training defaults to development-only. Test DataLoader
iteration and test evaluation are deferred. A raw external static script is
confirmation-only until it has a separate, verified development-only adapter;
a boolean self-claim does not prove that it withholds test labels.

Freeze actual executed recipe fingerprints, not just a winning model name:

```json
{"recipe_fingerprints": {"selected_root": "<recorded fingerprint>",
                         "selected_child": "<recorded fingerprint>"}}
```

```bash
PYTHONPATH=src python -m vc_demo.harness.research_contract \
  --run-dir experiments/<run> --freeze-selection experiments/<run>/selected.json
```

This creates confirmation_lock.json, verifies original code/data and the declared
confirmation-model budget, and closes the run to further search/train_pending.
The confirmation call sets evaluation.phase=confirmation and passes the lock
path. The executor requires the same selected executable recipe; new settings
or another model cannot piggyback on a lock. Confirmation metrics are report-only.

No new-blind claim is permitted if the same groups were exposed previously.
Cannot-identify (for example no positive heldout long-term group) is a scientific
result, not permission to report100% recall or change the split.

## Acceptance Layers

1. Execution: interfaces, actual training, no fallback, no pruned/untrained reward.
2. Protocol: exact references, input/code identity, correct groups and time access.
3. Scientific: paired development evidence, frozen confirmation, fair controls.
4. Attribution: capacity/optimization versus artifact/temporal/interaction effects.
5. Transfer: independently specified new tasks and equal-resource comparisons.

Passing an earlier layer does not imply passing later layers. Unit/smoke scores
are never task results. This upgrade must be checked with CPU fixtures and must
not rewrite the historical T47D tree, rewards, figures or conclusions.
