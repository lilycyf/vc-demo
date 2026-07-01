# B Handoff: Real Cell-Line Data

## Goal

Move from the synthetic A demo to one real cell-line experiment while preserving the same harness shape:

```text
config -> train/evaluate node -> metrics.json -> MCTS updates tree -> next config
```

This commit prepares the framework. It does not download or commit real Perturb-seq data.

## Prepared Interfaces

- `dataset_type: "synthetic"` keeps the A demo path unchanged.
- `dataset_type: "real_npz"` enables a real one-cell-line NPZ dataset.
- `configs/real_k562_template.json` is the template for a real K562 run.
- `configs/real_k562_demo_fixture.json` exercises the real-data path with a tiny generated fixture.
- `scripts/validate_real_dataset.py` checks shape, split availability, and label ranges.
- `scripts/make_fake_real_dataset.py` creates a tiny fixture for framework validation only.
- `data/README.md` defines the expected manifest and NPZ layout.

## Required Real Data Contract

Place data under:

```text
data/cell_lines/k562/
```

Required files:

```text
manifest.json
train.npz
val.npz
test.npz
```

Each NPZ must contain:

- `features`: `float32`, shape `[n_perturbations, n_features]`
- `labels`: `int64`, shape `[n_perturbations, n_target_genes]`

Label convention:

- `0`: down-regulated
- `1`: unchanged
- `2`: up-regulated

The feature matrix can initially be simple perturbation features such as one-hot or precomputed embeddings. Later it can be replaced by foundation-model, STRING/GNN, or multimodal features without changing `train.py`.

## Validate The Framework

Run this before using real data:

```bash
python scripts/make_fake_real_dataset.py --data-dir data/cell_lines/k562_demo
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562_demo
python -m vc_demo.train \
  --config configs/real_k562_demo_fixture.json \
  --output-dir experiments/nodes/real_k562_demo_fixture \
  --max-epochs 1
```

Expected result:

```text
experiments/nodes/real_k562_demo_fixture/metrics.json
```

## Next Codex Task

1. Pull the latest repo on RunPod.
2. Read `data/README.md` and this handoff.
3. Obtain or generate one real cell-line perturbation dataset, preferably K562 first.
4. Convert it into the `real_npz` contract.
5. Run:

```bash
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562
python -m vc_demo.train \
  --config configs/real_k562_template.json \
  --output-dir experiments/nodes/real_k562_template_mlp \
  --max-epochs 1
```

6. If the single-node real-data run succeeds, point `vc_demo.mcts` at a real-data root config and run a short 3-5 candidate search.

## Do Not Commit

- `data/cell_lines/*`
- `experiments/nodes/*`
- `*.pt`
- `*.ckpt`
- `__pycache__`
- `.egg-info`

These are ignored by `.gitignore`.

## Current Limitation

The real-data loader currently expects precomputed perturbation-level features and DEG class labels. It does not yet implement raw single-cell preprocessing, DEG calling, or foundation-model embedding generation. Those are intentionally left as the next B-stage data-preparation step.
