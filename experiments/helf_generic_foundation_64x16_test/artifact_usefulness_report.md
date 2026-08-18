# Artifact Usefulness Report

- Run dir: `experiments/helf_generic_foundation_64x16_test`
- Artifact incremental gain proven: `False`
- Best child vs root val delta: `0.009577423334121704`
- Foundation vs root val delta: `0.006364971399307251`
- Foundation vs dense no-artifact val delta: `-0.003212451934814453`
- Foundation vs dense matched-control val delta: `-0.003212451934814453`

## Best Nodes

| Role | Node | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| Best root | `aivc_helf_perturb_root_residual_mlp` | 0.4117428958415985 | 0.4180757999420166 |
| Best generated child | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` | 0.4213203191757202 | 0.42448005080223083 |
| Best foundation artifact child | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_35285b7e` | 0.41810786724090576 | 0.41262853145599365 |
| Best dense no-artifact child | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` | 0.4213203191757202 | 0.42448005080223083 |
| Best dense matched control | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` | 0.4213203191757202 | 0.42448005080223083 |

## Paired Artifact Controls

| Artifact child | Control child | Artifact val | Control val | Incremental gain |
|---|---|---:|---:|---:|
| `aivc_helf_perturb_root_gated_mlp_p5_foundation_graph_laplacian_head_be22df66` | `aivc_helf_perturb_root_gated_mlp_p5_foundation_graph_laplacian_head_be22df66_p5_dense_matched_capacity_no_artifact_control_control_bceb59cb` | 0.41671648621559143 | 0.4162159264087677 | 0.0005005598068237305 |
| `aivc_helf_perturb_root_mlp_p9_foundation_pathway_pooling_encoder_c25a2ac3` | `aivc_helf_perturb_root_mlp_p9_foundation_pathway_pooling_encoder_c25a2ac3_p9_dense_matched_capacity_no_artifact_control_control_2fd2fbc4` | 0.41468608379364014 | 0.4172085225582123 | -0.0025224387645721436 |
| `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_35285b7e` | `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` | 0.41810786724090576 | 0.4213203191757202 | -0.003212451934814453 |

## Interpretation

A child can beat the root because of capacity, loss, optimization, or artifacts. This report only treats biological artifacts as useful when a source-backed artifact child beats the best available dense no-artifact or paired dense matched-capacity control under the same validation-only selection policy.
