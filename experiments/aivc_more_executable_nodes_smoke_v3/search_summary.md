# HELF_PERTURB_DEG Harness Demo Report

- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (8/8)`
- Generated proposals: `36`
- Trained selected rollouts: `8`
- Generated artifact-usefulness controls: `10`
- Trained foundation-artifact children: `8`
- Pruned not selected: `38`
- Requires artifact acquisition / blocked: `0`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.

## Best Root

- Val Macro-F1: `0.4123806655406952`
- Test Macro-F1: `0.400498628616333`

## Best Generated Child

- Strategy: `foundation_protein_embedding_fusion`
- Val Macro-F1: `0.42446669936180115`
- Test Macro-F1: `0.4096287786960602`

## Artifact Usefulness

- Best foundation-artifact child: `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion` val=0.42446669936180115
- Best dense matched no-artifact control: `` val=None
- Foundation vs root val gain: `0.012086033821105957`
- Foundation vs dense-control val gain: `None`
- Interpretation: `artifact gain not proven beyond dense matched-capacity control`
