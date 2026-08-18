# HELF_PERTURB_DEG Generic Foundation-Artifact Harness Report

- Cell line: `HELF`
- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (2/2)`
- Generated proposals: `8`
- Trained selected rollouts: `2`
- Generated artifact-usefulness controls: `2`
- Trained foundation-artifact children: `2`
- Pruned not selected: `8`
- Requires artifact acquisition / blocked: `0`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.

## Best Root

- Val Macro-F1: `0.4011065661907196`
- Test Macro-F1: `0.4000442326068878`

## Best Generated Child

- Strategy: `foundation_graph_laplacian_head`
- Val Macro-F1: `0.41547608375549316`
- Test Macro-F1: `0.41339072585105896`

## Artifact Usefulness

- Best foundation-artifact child: `aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_457c4213` val=0.41547608375549316
- Best dense matched no-artifact control: `` val=None
- Foundation vs root val gain: `0.01436951756477356`
- Foundation vs dense-control val gain: `None`
- Interpretation: `artifact gain not proven beyond dense matched-capacity control`
