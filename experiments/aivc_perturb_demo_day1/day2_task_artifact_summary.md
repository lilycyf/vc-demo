# Day 2 Task Artifacts: AIVC HELF Perturbation Response Demo

## What Was Built

Generated a trainable real-NPZ perturbation response task from data/raw/merged_data.h5ad.

The task is scoped to HELF, 10umol, 48h, heldout-drug perturbation response prediction. It does not claim dose, time, or cross-cell-line generalization.

## Output Data Directory

data/cell_lines/aivc_helf_perturb_deg_cls

This directory is a generated data artifact and should not be committed to Git.

## Dataset Contract

- task_id: HELF_PERTURB_DEG
- task_type: drug_perturbation_target_gene_deg_direction_prediction
- n_cells: 9156
- n_genes_original: 31942
- n_feature_genes: 1024
- n_drug_onehot_features: 10
- n_features: 1034
- n_targets: 512
- n_classes: 3

## Drug-Level Split

- train (7 drugs): HY-16405-PR-104; HY-75800-Lomibuvir; HY-10443-Balapiravir; HY-N0112-Dihydromyricetin; HY-13543-Tretazicar; HY-B0021-Doxifluridine; HY-108969-Pyrazoloacridine
- val (2 drugs): HY-16209-Forodesine (hydrochloride); HY-13744-Rubitecan
- test (1 drugs): HY-16503-Treosulfan

## Rows By Split

- train: 448 bootstrap pseudobulk rows
- val: 128 bootstrap pseudobulk rows
- test: 64 bootstrap pseudobulk rows

## Label Balance

| Split | Down | Unchanged | Up |
|---|---:|---:|---:|
| train | 8501 | 178987 | 41888 |
| val | 2319 | 53016 | 10201 |
| test | 1820 | 24618 | 6330 |

## Root Baseline Check

Ran a real 2-epoch residual_mlp root baseline using configs/aivc_helf_perturb_roots/root_residual_mlp.json.

- best validation Macro-F1: 0.397407
- test Macro-F1: 0.392861
- device: cpu

Checkpoint and node outputs are under experiments/aivc_perturb_demo_day2_root_check/nodes/ and should not be committed.

## Generated Root Configs

- configs/aivc_helf_perturb_roots/root_mlp.json
- configs/aivc_helf_perturb_roots/root_residual_mlp.json
- configs/aivc_helf_perturb_roots/root_gated_mlp.json
- configs/aivc_helf_perturb_roots/root_low_rank_mlp.json

## Next Step

Run the first harness search over this real task using the AIVC root configs, then add source-backed artifact children: Reactome pathway membership, STRING target-gene graph, and RDKit/ChemBERTa drug embedding only if drug-name-to-SMILES mapping validates.

Suggested baseline command:

    PYTHONPATH=src python -m vc_demo.train --config configs/aivc_helf_perturb_roots/root_residual_mlp.json --output-dir experiments/aivc_perturb_demo_root_baseline/nodes/root_residual_mlp --max-epochs 8

## Guardrails

- No random-cell split claim.
- Validation Macro-F1 drives search; test Macro-F1 is report-only.
- Generated data, NPZ, H5AD, checkpoints, and node weights are not committed.
- Foundation models may be used only as verified embedding artifacts, not as proxy response predictors.
