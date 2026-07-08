# Continue K562 Resume Pressure Test to 50+ Nodes

- Start trained nodes: 41
- End statuses: {'trained': 57, 'requires_artifact_acquisition': 9}
- Implementation queue items: 0
- Acquisition queue items: 9
- Blocked artifacts: regulatory_network_artifact, scfoundation_cell_embeddings, single_cell_foundation_model_artifact
- class_distribution present: True
- Fallback used: False
- Backend anomalies: 0
- Family coverage count: 31
- Blocked-aware policy effective this turn: True

## New Trained Nodes

| node | strategy | val Macro-F1 | test Macro-F1 |
|---|---|---:|---:|
| `official_k562_native_p1_official_aido_string_bilinear_fusion_e2f0a399` | `official_aido_string_bilinear_fusion` | 0.414450 | 0.433233 |
| `official_k562_native_p2_official_multimodal_mixture_of_experts_93125c64` | `official_multimodal_mixture_of_experts` | 0.438746 | 0.478014 |
| `official_k562_native_p3_official_target_low_rank_head_0ae2d7d8` | `official_target_low_rank_head` | 0.423233 | 0.442457 |
| `official_k562_native_p4_official_target_bilinear_head_5a491322` | `official_target_bilinear_head` | 0.405315 | 0.431491 |
| `official_k562_root_aido_embedding_mlp_p1_official_aido_string_bilinear_fusion_15f82887` | `official_aido_string_bilinear_fusion` | 0.383050 | 0.403847 |
| `official_k562_root_aido_embedding_mlp_p2_official_multimodal_mixture_of_experts_db0e9af8` | `official_multimodal_mixture_of_experts` | 0.425995 | 0.439431 |
| `official_k562_root_aido_embedding_mlp_p3_official_target_low_rank_head_2e5e7df5` | `official_target_low_rank_head` | 0.406058 | 0.424615 |
| `official_k562_root_aido_embedding_mlp_p4_official_target_bilinear_head_7539101a` | `official_target_bilinear_head` | 0.411658 | 0.426301 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_public_static_node_family_wrapper_34241d65` | `official_public_static_node_family_wrapper` | 0.410822 | 0.440790 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_temperature_calibrated_head_d4f4664c` | `official_temperature_calibrated_head` | 0.397095 | 0.419372 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_gene_dropout_augmentation_11602380` | `official_gene_dropout_augmentation` | 0.370729 | 0.412535 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_layerwise_lr_schedule_e7171cc9` | `official_layerwise_lr_schedule` | 0.409310 | 0.431007 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_public_static_node_family_wrapper_cc540ff7` | `official_public_static_node_family_wrapper` | 0.415128 | 0.434952 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_temperature_calibrated_head_c9bd0eba` | `official_temperature_calibrated_head` | 0.369454 | 0.408046 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_gene_dropout_augmentation_d60de428` | `official_gene_dropout_augmentation` | 0.402017 | 0.435548 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_layerwise_lr_schedule_77aee7f1` | `official_layerwise_lr_schedule` | 0.390883 | 0.423664 |

## New Blockers

- None in this continuation turn.

## Best Nodes

- Best root: `official_k562_native_public_best_reimplementation` val=0.467945 test=0.525642
- Best overall: `official_k562_native_p1_official_aido_string_fusion_66a588f9` val=0.488477 test=0.518328
- Exceeded previous best overall: False
