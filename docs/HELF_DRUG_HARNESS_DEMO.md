# HELF Drug Harness Demo

This branch defines a smaller VCHarness-style demo from `merged_data.h5ad`.

## Task

- `CELL_LINE_ID`: `HELF_DRUG`
- Input: single-cell HELF expression from `merged_data.h5ad`
- Label: 12-way `Drug` identity
- Output shape: `[batch, 1, 12]`
- Reward: validation Macro-F1
- Test Macro-F1: report only

This is intentionally smaller than the original Virtual Cell perturbation-response task. It tests whether the harness can automate model engineering around a real single-cell dataset without requiring unavailable foundation-model artifacts.

## Data Contract

Run:

```bash
python3 scripts/prepare_helf_drug_demo.py \
  --input data/raw/merged_data.h5ad \
  --output-dir data/cell_lines/helf_drug_cls \
  --top-genes 2000 \
  --seed 13
```

The script writes ignored data files under `data/cell_lines/helf_drug_cls`:

- `train.npz`
- `val.npz`
- `test.npz`
- `manifest.json`
- `task_contract.md`

## Search Space

See `configs/helf_drug_search_space.json`.

The search space uses open-source PyTorch modules only: MLP, residual MLP, gated MLP, low-rank head, FiLM residual, mixture-of-experts, feature dropout, temperature calibration, weighted CE, and focal loss.

## Demo Run

```bash
PYTHONPATH=src python3 scripts/run_helf_drug_harness_demo.py \
  --root-configs configs/helf_drug_roots/root_mlp.json configs/helf_drug_roots/root_residual_mlp.json configs/helf_drug_roots/root_gated_mlp.json \
  --run-dir experiments/helf_drug_harness_demo_smoke \
  --experiment helf_drug_harness_demo_smoke \
  --budget-proposals 48 \
  --budget-trained-nodes 12 \
  --candidate-pool-size 4 \
  --max-epochs 4 \
  --reset
```

## Guardrails

- Do not commit `data/`, `nodes/`, checkpoints, `.h5ad`, or `.npz` files.
- Do not use `Drug`, `Sample`, `Well`, or split labels as model input features.
- Validation Macro-F1 is the reward; test Macro-F1 is not used for model selection.
