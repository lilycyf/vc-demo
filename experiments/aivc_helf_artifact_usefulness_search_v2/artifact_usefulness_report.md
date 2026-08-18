# Artifact Usefulness Report

- Run dir: `experiments/aivc_helf_artifact_usefulness_search_v2`
- Artifact incremental gain proven: `False`
- Best child vs root val delta: `0.02049383521080017`
- Foundation vs root val delta: `0.008251786231994629`
- Foundation vs dense no-artifact val delta: `-0.012242048978805542`
- Foundation vs dense matched-control val delta: `-0.012242048978805542`

## Best Nodes

| Role | Node | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| Best root | `aivc_helf_perturb_root_residual_mlp` | 0.4292716979980469 | 0.4248248040676117 |
| Best generated child | `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f_p31_dense_matched_capacity_no_artifact_control_control_8950845e` | 0.44976553320884705 | 0.4499788284301758 |
| Best foundation artifact child | `aivc_helf_perturb_root_low_rank_mlp_p25_foundation_graph_laplacian_head_734aadb9` | 0.4375234842300415 | 0.4299347698688507 |
| Best dense no-artifact child | `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f_p31_dense_matched_capacity_no_artifact_control_control_8950845e` | 0.44976553320884705 | 0.4499788284301758 |
| Best dense matched control | `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f_p31_dense_matched_capacity_no_artifact_control_control_8950845e` | 0.44976553320884705 | 0.4499788284301758 |

## Paired Artifact Controls

| Artifact child | Control child | Artifact val | Control val | Incremental gain |
|---|---|---:|---:|---:|
| `aivc_helf_perturb_root_gated_mlp_p13_foundation_string_graph_message_passing_a17c2d5f` | `aivc_helf_perturb_root_gated_mlp_p13_foundation_string_graph_message_passing_p13_dense_matched_capacity_no_artifact_control_control_2ccd4e84` | 0.4312750995159149 | 0.4467560946941376 | -0.015480995178222656 |
| `aivc_helf_perturb_root_gated_mlp_p37_foundation_graph_laplacian_head_cd81f606` | `aivc_helf_perturb_root_gated_mlp_p37_foundation_graph_laplacian_head_cd81f60_p37_dense_matched_capacity_no_artifact_control_control_ebe15993` | 0.43241938948631287 | 0.43852365016937256 | -0.006104260683059692 |
| `aivc_helf_perturb_root_low_rank_mlp_p19_foundation_string_graph_message_passing_0c38fb5a` | `aivc_helf_perturb_root_low_rank_mlp_p19_foundation_string_graph_message_pass_p19_dense_matched_capacity_no_artifact_control_control_1819a082` | 0.4262031614780426 | 0.4442417621612549 | -0.01803860068321228 |
| `aivc_helf_perturb_root_low_rank_mlp_p25_foundation_graph_laplacian_head_734aadb9` | `aivc_helf_perturb_root_low_rank_mlp_p25_foundation_graph_laplacian_head_734a_p25_dense_matched_capacity_no_artifact_control_control_3b51d371` | 0.4375234842300415 | 0.44029712677001953 | -0.0027736425399780273 |
| `aivc_helf_perturb_root_low_rank_mlp_p49_foundation_graph_laplacian_head_dd485df6` | `aivc_helf_perturb_root_low_rank_mlp_p49_foundation_graph_laplacian_head_dd48_p49_dense_matched_capacity_no_artifact_control_control_7c3f411f` | 0.42725589871406555 | 0.4459019601345062 | -0.018646061420440674 |
| `aivc_helf_perturb_root_low_rank_mlp_p61_foundation_pathway_pooling_encoder_a97102c4` | `aivc_helf_perturb_root_low_rank_mlp_p61_foundation_pathway_pooling_encoder_a_p61_dense_matched_capacity_no_artifact_control_control_4ae062d1` | 0.4303874969482422 | 0.4478359520435333 | -0.017448455095291138 |
| `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f` | `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f_p31_dense_matched_capacity_no_artifact_control_control_8950845e` | 0.4298115670681 | 0.44976553320884705 | -0.01995396614074707 |
| `aivc_helf_perturb_root_mlp_p7_foundation_string_graph_message_passing_d8dd1066` | `aivc_helf_perturb_root_mlp_p7_foundation_string_graph_message_passing_d8dd106_p7_dense_matched_capacity_no_artifact_control_control_b0835292` | 0.42982712388038635 | 0.4493443965911865 | -0.01951727271080017 |
| `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_3_p43_foundation_graph_laplacian_head_3c7eac46` | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passi_p43_dense_matched_capacity_no_artifact_control_control_0e0eeb2d` | 0.4360891282558441 | 0.4379824697971344 | -0.0018933415412902832 |
| `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_3_p55_foundation_pathway_pooling_encoder_e0d74e07` | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passi_p55_dense_matched_capacity_no_artifact_control_control_1f5b0f0c` | 0.4281359612941742 | 0.44513341784477234 | -0.016997456550598145 |
| `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_35285b7e` | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` | 0.43020787835121155 | 0.44018325209617615 | -0.0099753737449646 |

## Interpretation

A child can beat the root because of capacity, loss, optimization, or artifacts. This report only treats biological artifacts as useful when a source-backed artifact child beats the best available dense no-artifact or paired dense matched-capacity control under the same validation-only selection policy.
