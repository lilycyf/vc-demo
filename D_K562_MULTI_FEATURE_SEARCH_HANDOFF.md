# D Handoff: K562 Multi-Feature Automated Search

## Goal

Run a single-cell-line K562 search that is closer to the VCHarness paper shape:

```text
real K562 data -> multiple biological feature datasets -> multiple root configs -> MCTS-style search -> best node report
```

This is still not the full paper reproduction. It is a one-cell-line, compact-budget search with rule-based child generation rather than an AI coding agent that edits model code.

## Prepared Code

- `scripts/build_k562_feature_datasets.py`
  - Builds `k562_onehot`, `k562_delta`, and `k562_concat` datasets from the current K562 NPZ files.
- `scripts/make_k562_root_configs.py`
  - Writes root configs under `configs/k562_roots/`.
- `src/vc_demo/search.py`
  - Multi-root search entrypoint with budget, stop-no-improve, failure recording, best-so-far summary.

## Data Products To Build On RunPod

```bash
python scripts/build_k562_feature_datasets.py \
  --source-dir data/cell_lines/k562 \
  --output-root data/cell_lines

python scripts/make_k562_root_configs.py \
  --output-dir configs/k562_roots
```

Expected ignored local datasets:

```text
data/cell_lines/k562_onehot/
data/cell_lines/k562_delta/
data/cell_lines/k562_concat/
```

## Validate Feature Datasets

```bash
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562_onehot
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562_delta
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562_concat

python scripts/audit_real_dataset.py --data-dir data/cell_lines/k562_onehot
python scripts/audit_real_dataset.py --data-dir data/cell_lines/k562_delta
python scripts/audit_real_dataset.py --data-dir data/cell_lines/k562_concat
```

Expected audit behavior:

- `k562_onehot`: `all_splits_one_hot_features=true`
- `k562_delta`: `all_splits_one_hot_features=false`
- `k562_concat`: `all_splits_one_hot_features=false`

## Full Experiment Command

Run this after validation:

```bash
python -m vc_demo.search \
  --root-configs configs/k562_roots/*.json \
  --run-dir experiments/k562_real_features \
  --summary experiments/k562_real_features/search_summary.md \
  --budget-nodes 20 \
  --max-epochs 2 \
  --max-children 3 \
  --stop-no-improve 6 \
  --reset
```

## Expected Summary

The search writes:

```text
experiments/k562_real_features/tree.json
experiments/k562_real_features/search_summary.md
experiments/k562_real_features/proposals/*.json
```

The summary should answer:

- Which root feature dataset performed best?
- Did MCTS improve over the best root?
- Which feature type won: onehot, delta, or concat?
- What was the best validation Macro-F1 and test Macro-F1?
- Did the search stop by budget or no-improve condition?
- What failures occurred, if any?

## Do Not Commit

Do not commit large or generated local artifacts:

```text
data/cell_lines/*
data/raw/*
experiments/*/nodes/*
*.pt
*.ckpt
__pycache__
*.egg-info
```

Commit only:

- code changes
- root config JSON files
- proposal config JSON files if small and useful
- `tree.json` and summary markdown if small
- audit JSON summaries if small
- README/HANDOFF updates

## Current Gap After This Stage

Even after this search, remaining paper-level gaps are:

- no AI coding agent yet; child generation is rule-based mutation
- no ESM2/AIDO/scFoundation/STRING embeddings yet; `delta` and `concat` are stronger local biological features but not foundation-model modules
- only K562, not four cell lines
- simplified DEG label rule and target-gene selection
