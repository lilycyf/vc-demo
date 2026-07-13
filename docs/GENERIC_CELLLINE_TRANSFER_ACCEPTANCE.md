# Generic Cell-Line Transfer Acceptance Criteria

Use this checklist for every generic cell-line transfer test.

## Required Inputs

- `CELL_LINE_ID` is explicit.
- `RUN_TYPE` is explicit: `loop_self_test` or `full_cellline_run`.
- `TEST_LEVEL` is one of `preflight`, `transfer_64x16`, `transfer_150x40`, or `full_cellline_run`.
- The run uses `scripts/run_generic_cellline_transfer_test.py` unless debugging the runner itself.
- The run branch is separate from the framework branch when producing experiment outputs.


## Run Type Acceptance

Pass only if the run type is explicit:

- `RUN_TYPE=loop_self_test` is for wiring/proposal/acquisition/implementation-loop validation only.
- `RUN_TYPE=full_cellline_run` is for real model-quality cell-line experiments.
- `full_cellline_run` must use `--level full_cellline_run`.
- `full_cellline_run` must use `max_epochs >= 8`.
- `full_cellline_run` must explicitly set `target_val_macro_f1`.
- `transfer_64x16` and `transfer_150x40` must not be described as full model-quality runs.
- Full runs must apply artifact-constrained blueprint filtering before training and report excluded blueprint families.
- Full runs must train at least 100 selected rollouts unless stopped by a source-backed blocker.
- Full runs must generate at least 300 proposals unless stopped by a source-backed blocker.
- Full runs must explicitly report whether best generated child beats best root on validation Macro-F1.
- Full runs must explicitly report whether best generated child reaches `target_val_macro_f1`.

## Task Contract

Pass only if:

- source-backed task contract exists for the selected cell line
- train/val/test split is fixed and auditable
- target gene order is fixed and auditable
- label semantics are documented
- validation Macro-F1 is the reward
- test Macro-F1 is report-only
- no K562 task files are used for a different cell line

## Root-Beating Acceptance

For `RUN_TYPE=full_cellline_run`, the primary scientific objective is:

```text
best_generated_child_val_macro_f1 > best_root_val_macro_f1
best_generated_child_val_macro_f1 >= target_val_macro_f1
```

The run is not a scientific success unless both conditions are true. If either is false, the final report must mark the full-run objective as not achieved and include root-dominance / target-gap attribution.

## Artifact Contract

Pass only if:

- artifact registry exists for the selected cell line
- each artifact has provenance and status
- missing artifacts go through acquisition before block
- `requires_codex_research_download_or_build` has a completed Codex research acquisition report before final blocked status
- no fake/random/generated artifact is used as fallback
- row order, shape, vocabulary, and source are verified before marking present

## Search Semantics

Pass only if:

- MCTS/proposal-pool generates multiple candidates per expansion
- unselected proposals are pruned and not trained
- selected rollout is trained before reward backpropagation
- validation Macro-F1 is the only reward used for selection
- test Macro-F1 does not affect selection

## Implementation Semantics

Pass only if:

- selected planned node reads node-local contracts
- `model.py` is written only after required artifacts are present
- compile passes
- native smoke passes
- `train_pending` passes or records a real failure
- no compact/proxy/fallback implementation is used in formal transfer tests

## Audit Counters

Required final counters:

```text
fallback_count = 0
compact_proxy_count = 0
backprop_nontrained_count = 0
backend_anomaly_count = 0
k562_leakage_count = 0
forbidden_committed_file_count = 0
```

## Forbidden Commit Paths

The commit must not include:

```text
data/
*/nodes/*
checkpoint files
*.pt
*.pth
*.ckpt
*.bin
*.npz
*.h5ad
/home/Models
/workspace/_external
__pycache__
*.egg-info
```

## Final Decision

The final report must state one of:

- `passed`: generic transfer loop completed with all hard counters at zero
- `blocked`: source-backed task/artifact could not be verified after acquisition resolver and Codex research acquisition were attempted
- `failed`: implementation/search failed for a non-artifact reason
- `inconclusive`: run did not reach enough selected rollouts for the requested test level

Do not call a run passed if it only created configs or only reached preflight.
