# HELF Perturbation Harness Demo

This demo keeps the VCHarness-style loop but changes the task from drug identity classification to a smaller perturbation-response problem.

## Prediction Problem

`HELF_PERTURB_DEG` predicts how a drug perturbation changes target-gene expression direction in HELF cells.

- Unit: bootstrap pseudobulk pair `(drug-treated cells, control cells)`.
- Input: treated-control expression delta over feature genes plus perturbation drug one-hot.
- Output: `[batch, n_target_genes, 3]` logits.
- Classes: `down`, `unchanged`, `up`.
- Reward: validation Macro-F1.
- Test Macro-F1: final report only.
- Split: drug-level train/val/test split before bootstrap generation, so validation/test drugs are held-out perturbations.

This is perturbation-related because the model predicts the transcriptional response direction caused by a perturbing drug, rather than identifying the drug label directly from single cells.

## Why This Is Smaller Than The Paper Task

The paper-scale VCHarness task predicts CRISPR perturbation DEG labels with large biological foundation artifacts. This demo intentionally avoids unavailable foundation checkpoints and uses only the provided h5ad to create a runnable, auditable harness loop.

## Prepare Data

```bash
python3 scripts/prepare_helf_perturbation_demo.py   --input data/raw/merged_data.h5ad   --output-dir data/cell_lines/helf_perturb_deg_cls   --feature-genes 1024   --target-genes 512   --bootstraps-per-drug 64   --cells-per-bootstrap 96   --deg-threshold 0.25   --seed 19
```

## Smoke Run

```bash
VC_DEMO_FORCE_CPU=1 PYTHONPATH=src python3 scripts/run_helf_drug_harness_demo.py   --root-configs     configs/helf_perturb_roots/root_mlp.json     configs/helf_perturb_roots/root_residual_mlp.json     configs/helf_perturb_roots/root_gated_mlp.json     configs/helf_perturb_roots/root_low_rank_mlp.json   --run-dir experiments/helf_perturb_harness_demo_smoke   --experiment helf_perturb_harness_demo_smoke   --budget-proposals 16   --budget-trained-nodes 4   --candidate-pool-size 4   --max-epochs 1   --reset
```

## Fuller Demo Run

```bash
VC_DEMO_FORCE_CPU=1 PYTHONPATH=src python3 scripts/run_helf_drug_harness_demo.py   --root-configs     configs/helf_perturb_roots/root_mlp.json     configs/helf_perturb_roots/root_residual_mlp.json     configs/helf_perturb_roots/root_gated_mlp.json     configs/helf_perturb_roots/root_low_rank_mlp.json   --run-dir experiments/helf_perturb_harness_demo_full   --experiment helf_perturb_harness_demo_full   --budget-proposals 96   --budget-trained-nodes 24   --candidate-pool-size 4   --max-epochs 6   --reset
```

## Search Space

The open-source search space includes MLP, residual MLP, gated MLP, FiLM residual MLP, mixture-of-experts MLP, dense heads, low-rank target heads, temperature-calibrated heads, weighted CE, focal loss, dropout, width, depth, and learning-rate variants.

## Guardrails

- No foundation model checkpoint is required.
- No fallback artifact is allowed or needed.
- Test metrics are report-only.
- Generated proposals not selected by the proposal pool are pruned and not trained.
- Data outputs and node checkpoints must not be committed.
