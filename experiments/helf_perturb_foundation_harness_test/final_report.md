# HELF_PERTURB_DEG Harness Demo Report

- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (24/24)`
- Generated proposals: `96`
- Trained selected rollouts: `24`
- Pruned not selected: `26`
- Requires artifact acquisition / blocked: `46`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority, but selected blueprints are blocked unless required artifacts have source-backed, shape/order/provenance-verifiable files. Lightweight PyTorch transforms are the executable baseline path for this demo.

## Best Root

- Val Macro-F1: `0.34924936294555664`
- Test Macro-F1: `0.35048195719718933`

## Best Generated Child

- Strategy: `focal_loss`
- Val Macro-F1: `0.3694060742855072`
- Test Macro-F1: `0.36407771706581116`

## Acquisition / Blocker Summary

- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
