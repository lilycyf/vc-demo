# HELF_PERTURB_DEG Harness Demo Report

- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (16/16)`
- Generated proposals: `64`
- Trained selected rollouts: `16`
- Trained foundation-artifact children: `3`
- Pruned not selected: `40`
- Requires artifact acquisition / blocked: `8`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.

## Best Root

- Val Macro-F1: `0.4296294152736664`
- Test Macro-F1: `0.4275474548339844`

## Best Generated Child

- Strategy: `focal_loss`
- Val Macro-F1: `0.4455164968967438`
- Test Macro-F1: `0.43781033158302307`

## Acquisition / Blocker Summary

- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
