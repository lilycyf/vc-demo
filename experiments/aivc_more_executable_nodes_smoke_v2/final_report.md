# HELF_PERTURB_DEG Harness Demo Report

- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (8/8)`
- Generated proposals: `36`
- Trained selected rollouts: `8`
- Generated artifact-usefulness controls: `10`
- Trained foundation-artifact children: `6`
- Pruned not selected: `38`
- Requires artifact acquisition / blocked: `0`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.

## Best Root

- Val Macro-F1: `0.4011034667491913`
- Test Macro-F1: `0.3975583612918854`

## Best Generated Child

- Strategy: `foundation_protein_embedding_fusion`
- Val Macro-F1: `0.42144325375556946`
- Test Macro-F1: `0.4116392433643341`

## Artifact Usefulness

- Best foundation-artifact child: `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion` val=0.42144325375556946
- Best dense matched no-artifact control: `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p18_foundation_chemberta_drug_encoder_dense_control` val=0.4025525152683258
- Foundation vs root val gain: `0.020339787006378174`
- Foundation vs dense-control val gain: `0.018890738487243652`
- Interpretation: `artifact useful beyond capacity`

| Artifact child | Dense control | Artifact val | Control val | Incremental val gain |
|---|---|---:|---:|---:|
| `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p17_foundation_rdkit_drug_fingerprint_fusion` | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p17_foundation_rdkit_drug_fingerprint_fusion_dense_control` | 0.3924606740474701 | 0.397737592458725 | -0.005276918411254883 |
| `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p18_foundation_chemberta_drug_encoder` | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p18_foundation_chemberta_drug_encoder_dense_control` | 0.3951749801635742 | 0.4025525152683258 | -0.007377535104751587 |
