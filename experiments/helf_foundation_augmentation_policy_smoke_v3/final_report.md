# HELF_PERTURB_DEG Harness Demo Report

- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (6/6)`
- Generated proposals: `32`
- Trained selected rollouts: `6`
- Trained foundation-artifact children: `5`
- Pruned not selected: `26`
- Requires artifact acquisition / blocked: `0`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.

## Best Root

- Val Macro-F1: `0.40055227279663086`
- Test Macro-F1: `0.39280009269714355`

## Best Generated Child

- Strategy: `foundation_graph_laplacian_head`
- Val Macro-F1: `0.4183642864227295`
- Test Macro-F1: `0.40721526741981506`
