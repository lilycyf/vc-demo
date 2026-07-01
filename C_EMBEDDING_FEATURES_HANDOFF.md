# C Handoff: Replace One-Hot Perturbation Features

## Why This Is The Next Step

The current B-stage K562 run is a real-data harness demo, not a paper-level reproduction.
It uses real Norman/Weissman K562 perturbation data, but the model input is still a simple
perturbation one-hot vector. This proves that the training/MCTS loop can run on a real
cell-line dataset, but it does not yet test the main VCHarness idea of composing stronger
biological representation modules.

The next Codex should replace or augment the one-hot `features` matrix with precomputed
biological features while keeping the same `real_npz` data contract.

## Current Real K562 Baseline

Current local RunPod dataset:

```text
data/cell_lines/k562/
  manifest.json
  train.npz
  val.npz
  test.npz
```

Current feature definition:

- `features`: perturbation one-hot vector
- `feature_dim`: 105
- `labels`: 1000 target-gene DEG classes
- label rule: per-perturbation delta vs control mean expression, bottom/top 5 percent as down/up

Current short run summary:

- baseline val Macro-F1: 0.3207
- baseline test Macro-F1: 0.3188
- best 3-step MCTS val Macro-F1: 0.5107
- best 3-step MCTS test Macro-F1: 0.4778

## Target Upgrade

Create a new dataset directory, for example:

```text
data/cell_lines/k562_gene_features/
  manifest.json
  train.npz
  val.npz
  test.npz
```

Keep the same label matrices and splits, but replace `features` with one of:

1. Gene identity features for the perturbed gene, such as ESM2/protein embeddings.
2. Network features, such as STRING/GNN embeddings for the perturbed gene.
3. Concatenated features, such as one-hot + gene embedding + network embedding.
4. A small learned embedding table keyed by perturbation, if external embeddings are unavailable.

The training code already supports any 2-D float32 feature matrix. If `model.input_dim` is
`"auto"`, it will infer feature dimension from the NPZ file.

## Suggested Commands

First audit the current one-hot dataset:

```bash
python scripts/audit_real_dataset.py \
  --data-dir data/cell_lines/k562 \
  --output experiments/real_k562_dataset_audit.json
```

Then build an upgraded feature dataset. The exact script depends on the available embedding
source. It should preserve perturbation order within each split and write the same keys:

```text
features: float32 [n_perturbations, new_feature_dim]
labels: int64 [n_perturbations, n_target_genes]
perturbations: optional string array
 target_genes: optional string array
```

Validate:

```bash
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562_gene_features
python scripts/audit_real_dataset.py --data-dir data/cell_lines/k562_gene_features
```

Train:

```bash
python -m vc_demo.train \
  --config configs/real_k562_template.json \
  --output-dir experiments/nodes/real_k562_gene_features_mlp \
  --max-epochs 1
```

For the upgraded dataset, make a copied config whose `data_dir` points to the new directory
and whose `node_name` is distinct.

## What To Commit

Commit only code/config/docs/summaries:

- feature-building script
- new config JSON
- audit summary markdown or JSON if small
- training summary markdown
- README/HANDOFF updates

Do not commit:

- `data/cell_lines/*`
- `data/raw/*`
- `experiments/nodes/*`
- checkpoint files

## Acceptance Criteria

The C-stage handoff is complete when:

1. `validate_real_dataset.py` passes on the upgraded feature dataset.
2. `audit_real_dataset.py` shows `all_splits_one_hot_features: false` or explicitly documents a learned-embedding baseline.
3. One upgraded-feature baseline trains for at least 1 epoch on CUDA.
4. A short MCTS run with `--root-config` completes for 3-5 candidates.
5. A summary compares one-hot baseline vs upgraded-feature baseline.
