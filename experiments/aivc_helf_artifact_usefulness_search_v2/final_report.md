# HELF_PERTURB_DEG Harness Demo Report

- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (100/100)`
- Generated proposals: `300`
- Trained selected rollouts: `100`
- Generated artifact-usefulness controls: `50`
- Trained foundation-artifact children: `11`
- Pruned not selected: `168`
- Requires artifact acquisition / blocked: `82`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.

## Best Root

- Val Macro-F1: `0.4292716979980469`
- Test Macro-F1: `0.4248248040676117`

## Best Generated Child

- Strategy: `dense_matched_capacity_no_artifact_control`
- Val Macro-F1: `0.44976553320884705`
- Test Macro-F1: `0.4499788284301758`

## Artifact Usefulness

- Best foundation-artifact child: `aivc_helf_perturb_root_low_rank_mlp_p25_foundation_graph_laplacian_head_734aadb9` val=0.4375234842300415
- Best dense matched no-artifact control: `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f_p31_dense_matched_capacity_no_artifact_control_control_8950845e` val=0.44976553320884705
- Foundation vs root val gain: `0.008251786231994629`
- Foundation vs dense-control val gain: `-0.012242048978805542`
- Interpretation: `artifact gain not proven beyond dense matched-capacity control`

| Artifact child | Dense control | Artifact val | Control val | Incremental val gain |
|---|---|---:|---:|---:|
| `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_35285b7e` | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` | 0.43020787835121155 | 0.44018325209617615 | -0.0099753737449646 |
| `aivc_helf_perturb_root_mlp_p7_foundation_string_graph_message_passing_d8dd1066` | `aivc_helf_perturb_root_mlp_p7_foundation_string_graph_message_passing_d8dd106_p7_dense_matched_capacity_no_artifact_control_control_b0835292` | 0.42982712388038635 | 0.4493443965911865 | -0.01951727271080017 |
| `aivc_helf_perturb_root_gated_mlp_p13_foundation_string_graph_message_passing_a17c2d5f` | `aivc_helf_perturb_root_gated_mlp_p13_foundation_string_graph_message_passing_p13_dense_matched_capacity_no_artifact_control_control_2ccd4e84` | 0.4312750995159149 | 0.4467560946941376 | -0.015480995178222656 |
| `aivc_helf_perturb_root_low_rank_mlp_p19_foundation_string_graph_message_passing_0c38fb5a` | `aivc_helf_perturb_root_low_rank_mlp_p19_foundation_string_graph_message_pass_p19_dense_matched_capacity_no_artifact_control_control_1819a082` | 0.4262031614780426 | 0.4442417621612549 | -0.01803860068321228 |
| `aivc_helf_perturb_root_low_rank_mlp_p25_foundation_graph_laplacian_head_734aadb9` | `aivc_helf_perturb_root_low_rank_mlp_p25_foundation_graph_laplacian_head_734a_p25_dense_matched_capacity_no_artifact_control_control_3b51d371` | 0.4375234842300415 | 0.44029712677001953 | -0.0027736425399780273 |
| `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f` | `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f_p31_dense_matched_capacity_no_artifact_control_control_8950845e` | 0.4298115670681 | 0.44976553320884705 | -0.01995396614074707 |
| `aivc_helf_perturb_root_gated_mlp_p37_foundation_graph_laplacian_head_cd81f606` | `aivc_helf_perturb_root_gated_mlp_p37_foundation_graph_laplacian_head_cd81f60_p37_dense_matched_capacity_no_artifact_control_control_ebe15993` | 0.43241938948631287 | 0.43852365016937256 | -0.006104260683059692 |
| `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_3_p43_foundation_graph_laplacian_head_3c7eac46` | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passi_p43_dense_matched_capacity_no_artifact_control_control_0e0eeb2d` | 0.4360891282558441 | 0.4379824697971344 | -0.0018933415412902832 |
| `aivc_helf_perturb_root_low_rank_mlp_p49_foundation_graph_laplacian_head_dd485df6` | `aivc_helf_perturb_root_low_rank_mlp_p49_foundation_graph_laplacian_head_dd48_p49_dense_matched_capacity_no_artifact_control_control_7c3f411f` | 0.42725589871406555 | 0.4459019601345062 | -0.018646061420440674 |
| `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_3_p55_foundation_pathway_pooling_encoder_e0d74e07` | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passi_p55_dense_matched_capacity_no_artifact_control_control_1f5b0f0c` | 0.4281359612941742 | 0.44513341784477234 | -0.016997456550598145 |
| `aivc_helf_perturb_root_low_rank_mlp_p61_foundation_pathway_pooling_encoder_a97102c4` | `aivc_helf_perturb_root_low_rank_mlp_p61_foundation_pathway_pooling_encoder_a_p61_dense_matched_capacity_no_artifact_control_control_4ae062d1` | 0.4303874969482422 | 0.4478359520435333 | -0.017448455095291138 |

## Acquisition / Blocker Summary

- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_cell_encoder` blocked for `scgpt_whole_human_checkpoint`.
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
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
- `foundation_scgpt_adapter_finetune` blocked for `scgpt_whole_human_checkpoint`.
