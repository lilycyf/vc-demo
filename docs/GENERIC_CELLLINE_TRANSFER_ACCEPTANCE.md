# Generic Cell-Line Transfer Acceptance Criteria

Use this checklist for every generic cell-line transfer test.

## Required Inputs

- `CELL_LINE_ID` is explicit.
- `TEST_LEVEL` is one of `preflight`, `transfer_64x16`, or `transfer_150x40`.
- The run uses `scripts/run_generic_cellline_transfer_test.py` unless debugging the runner itself.
- The run branch is separate from the framework branch when producing experiment outputs.

## Task Contract

Pass only if:

- source-backed task contract exists for the selected cell line
- train/val/test split is fixed and auditable
- target gene order is fixed and auditable
- label semantics are documented
- validation Macro-F1 is the reward
- test Macro-F1 is report-only
- no K562 task files are used for a different cell line

## Artifact Contract

Pass only if:

- artifact registry exists for the selected cell line
- each artifact has provenance and status
- missing artifacts go through acquisition/block
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
- `blocked`: source-backed task/artifact could not be verified
- `failed`: implementation/search failed for a non-artifact reason
- `inconclusive`: run did not reach enough selected rollouts for the requested test level

Do not call a run passed if it only created configs or only reached preflight.
