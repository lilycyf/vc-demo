# HELF_PERTURB_DEG Generic Foundation-Artifact Harness Report

- Cell line: `HELF`
- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (16/16)`
- Generated proposals: `64`
- Trained selected rollouts: `16`
- Generated artifact-usefulness controls: `16`
- Trained foundation-artifact children: `3`
- Pruned not selected: `60`
- Requires artifact acquisition / blocked: `4`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.

## Best Root

- Val Macro-F1: `0.4117428958415985`
- Test Macro-F1: `0.4180757999420166`

## Best Generated Child

- Strategy: `dense_matched_capacity_no_artifact_control`
- Val Macro-F1: `0.4213203191757202`
- Test Macro-F1: `0.42448005080223083`

## Artifact Usefulness

- Best foundation-artifact child: `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_35285b7e` val=0.41810786724090576
- Best dense matched no-artifact control: `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` val=0.4213203191757202
- Foundation vs root val gain: `0.006364971399307251`
- Foundation vs dense-control val gain: `-0.003212451934814453`
- Interpretation: `artifact gain not proven beyond dense matched-capacity control`

| Artifact child | Dense control | Artifact val | Control val | Incremental val gain |
|---|---|---:|---:|---:|
| `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_35285b7e` | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` | 0.41810786724090576 | 0.4213203191757202 | -0.003212451934814453 |
| `aivc_helf_perturb_root_gated_mlp_p5_foundation_graph_laplacian_head_be22df66` | `aivc_helf_perturb_root_gated_mlp_p5_foundation_graph_laplacian_head_be22df66_p5_dense_matched_capacity_no_artifact_control_control_bceb59cb` | 0.41671648621559143 | 0.4162159264087677 | 0.0005005598068237305 |
| `aivc_helf_perturb_root_mlp_p9_foundation_pathway_pooling_encoder_c25a2ac3` | `aivc_helf_perturb_root_mlp_p9_foundation_pathway_pooling_encoder_c25a2ac3_p9_dense_matched_capacity_no_artifact_control_control_2fd2fbc4` | 0.41468608379364014 | 0.4172085225582123 | -0.0025224387645721436 |

## Acquisition / Blocker Summary

- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
