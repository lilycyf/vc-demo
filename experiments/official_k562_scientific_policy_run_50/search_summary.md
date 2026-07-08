# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: pending implementation trained
- Trained nodes: 41
- Failed nodes: 0
- Best node: `official_k562_native_p1_official_aido_string_fusion_66a588f9` val=0.4885 test=0.5183
- Best root: `official_k562_native_public_best_reimplementation` val=0.4679 test=0.5256
- Improvement over best root: 0.0205 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `data/cell_lines/official_k562_cls` | custom_program | 0.4679 | 0.5256 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4108 | 0.4533 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4128 | 0.4630 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_native_public_best_reimplementation` | `` | root | root | native_train | program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.8 | custom_program | 0.4679 | 0.5256 |
| 0 | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 36.7 | external_static_node | 0.3333 | 0.3333 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 6.0 | gated_mlp | 0.4108 | 0.4533 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 5.8 | gated_mlp | 0.4128 | 0.4630 |
| 1 | `official_k562_native_p1_official_aido_string_fusion_66a588f9` | `official_k562_native_public_best_reimplementation` | program_node | official_aido_string_fusion | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.4 | custom_program | 0.4885 | 0.5183 |
| 2 | `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | `official_k562_native_p1_official_aido_string_fusion_66a588f9` | program_node | official_string_gnn_attention | native_train | pipeline_program_node | weighted_cross_entropy | gene_graph,perturbation_gene_or_context |  | 16.7 | custom_program | 0.4414 | 0.5046 |
| 3 | `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | program_node | official_aido_lora_adapter | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,perturbation_gene_or_context |  | 10.3 | custom_program | 0.4741 | 0.5233 |
| 4 | `official_k562_native_p1_official_target_gene_head_477d0ebb` | `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 12.1 | custom_program | 0.4552 | 0.5265 |
| 5 | `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` | `official_k562_native_p1_official_target_gene_head_477d0ebb` | program_node | official_pathway_pooling_reactome | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 15.0 | custom_program | 0.4088 | 0.4477 |
| 6 | `official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f` | `official_k562_native_p1_official_target_gene_head_477d0ebb` | program_node | official_aido_string_cross_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 23.8 | custom_program | 0.3578 | 0.4436 |
| 7 | `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` | `official_k562_native_p1_official_target_gene_head_477d0ebb` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 12.7 | custom_program | 0.3426 | 0.4228 |
| 8 | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_pathway_pooling_reactome | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 13.3 | custom_program | 0.3979 | 0.4254 |
| 9 | `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_aido_string_cross_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 15.3 | custom_program | 0.4207 | 0.4469 |
| 10 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 13.2 | custom_program | 0.3572 | 0.3912 |
| 11 | `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` | `official_k562_root_aido_embedding_mlp` | program_node | official_pathway_pooling_reactome | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 9.5 | custom_program | 0.4054 | 0.4254 |
| 12 | `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` | `official_k562_root_aido_embedding_mlp` | program_node | official_aido_string_cross_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 14.1 | custom_program | 0.4183 | 0.4355 |
| 13 | `official_k562_p1_official_class_imbalance_training_fde536bb` | `official_k562_public_best_node2_1_1_1_1_1_smoke` | program_node | official_class_imbalance_training | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 11.8 | custom_program | 0.3828 | 0.3993 |
| 14 | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` | `official_k562_p1_official_class_imbalance_training_fde536bb` | program_node | official_target_graph_conditioned_head | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 27.0 | custom_program | 0.3967 | 0.4169 |
| 15 | `official_k562_p2_official_public_best_node_0f24e30a` | `official_k562_p1_official_class_imbalance_training_fde536bb` | program_node | official_public_best_node | external_static_node | program_node | external_static_node | external_public_best_node |  | 36.0 | external_static_node | 0.3333 | 0.3333 |
| 17 | `official_k562_p2_official_focal_loss_training_11ab1cb3` | `official_k562_p2_official_public_best_node_0f24e30a` | program_node | official_focal_loss_training | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 11.2 | custom_program | 0.3705 | 0.3804 |
| 18 | `official_k562_p3_official_aido_full_finetune_337e49b9` | `official_k562_p2_official_public_best_node_0f24e30a` | program_node | official_aido_full_finetune | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 11.7 | custom_program | 0.3638 | 0.3767 |
| 20 | `official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` | program_node | official_focal_loss_training | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 18.6 | custom_program | 0.3785 | 0.4161 |
| 21 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` | program_node | official_aido_full_finetune | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 10.4 | custom_program | 0.3825 | 0.4200 |
| 23 | `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` | `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 18.7 | custom_program | 0.4181 | 0.4311 |
| 25 | `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` | `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` | program_node | official_aido_topk_layer_tuning | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 15.9 | custom_program | 0.3912 | 0.4269 |
| 26 | `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` | `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 13.1 | custom_program | 0.4161 | 0.4562 |
| 28 | `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` | `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` | program_node | official_aido_topk_layer_tuning | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 9.2 | custom_program | 0.3905 | 0.4081 |
| 29 | `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_9e4940c9` | `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 14.3 | custom_program | 0.4052 | 0.4216 |
| 32 | `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_47592563` | `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` | program_node | official_string_gnn_frozen_cache | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 18.7 | custom_program | 0.3552 | 0.3845 |
| 33 | `official_k562_root_aido_embedding_mlp_p3_official_string_gnn_full_finetune_18414a9e` | `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` | program_node | official_string_gnn_full_finetune | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 11.8 | custom_program | 0.4216 | 0.4352 |
| 35 | `official_k562_native_p2_official_string_gnn_frozen_cache_3d075b43` | `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` | program_node | official_string_gnn_frozen_cache | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 16.1 | custom_program | 0.4171 | 0.4753 |
| 36 | `official_k562_native_p3_official_string_gnn_full_finetune_b09af07d` | `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` | program_node | official_string_gnn_full_finetune | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 13.8 | custom_program | 0.4257 | 0.4638 |
| 38 | `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_a9964654` | `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_9e4940c9` | program_node | official_string_gnn_frozen_cache | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 12.2 | custom_program | 0.3552 | 0.3863 |
| 39 | `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_laplacian_smoothing_300cae7b` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` | program_node | official_string_laplacian_smoothing | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 15.2 | custom_program | 0.4113 | 0.4386 |
| 40 | `official_k562_root_aido_gnn_embedding_mlp_p2_official_weighted_ce_training_4f8db4e3` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` | program_node | official_weighted_ce_training | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 8.4 | custom_program | 0.3894 | 0.4270 |
| 41 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_concat_fusion_4ecbbcfc` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` | program_node | official_aido_string_concat_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 12.4 | custom_program | 0.4075 | 0.4358 |
| 42 | `official_k562_root_aido_gnn_embedding_mlp_p4_official_aido_string_gated_fusion_e45402bd` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` | program_node | official_aido_string_gated_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 12.9 | custom_program | 0.4150 | 0.4405 |
| 43 | `official_k562_p1_official_string_laplacian_smoothing_cacb16db` | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` | program_node | official_string_laplacian_smoothing | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 20.2 | custom_program | 0.3655 | 0.3789 |
| 44 | `official_k562_p2_official_weighted_ce_training_d9dfeac6` | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` | program_node | official_weighted_ce_training | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 11.8 | custom_program | 0.3566 | 0.3635 |
| 45 | `official_k562_p3_official_aido_string_concat_fusion_857f5a22` | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` | program_node | official_aido_string_concat_fusion | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 16.5 | custom_program | 0.3546 | 0.3731 |
| 46 | `official_k562_p4_official_aido_string_gated_fusion_1fe27291` | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` | program_node | official_aido_string_gated_fusion | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 17.2 | custom_program | 0.3564 | 0.3684 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_native_public_best_reimplementation` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN,public_node_code |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_aido_string_fusion_66a588f9` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | true | gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | true | AIDO.Cell-100M,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_aido_cell_100m_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_target_gene_head_477d0ebb` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` | true | perturbation_gene_or_context | pathway_memberships |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` | true | perturbation_gene_or_context | pathway_memberships |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` | true | perturbation_gene_or_context | pathway_memberships |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_p1_official_class_imbalance_training_fde536bb` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad,class_distribution |  | `` | focal_loss | missing_or_val_fallback |
| `official_k562_p1_official_target_graph_conditioned_head_ab86336c` | true | perturbation_gene_or_context |  |  | `` | focal_loss |  |
| `official_k562_p2_official_public_best_node_0f24e30a` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |
| `official_k562_p2_official_focal_loss_training_11ab1cb3` | true | perturbation_gene_or_context |  |  | `` | focal_loss |  |
| `official_k562_p3_official_aido_full_finetune_337e49b9` | true | perturbation_gene_or_context |  |  | `` | focal_loss |  |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_9e4940c9` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_47592563` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p3_official_string_gnn_full_finetune_18414a9e` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p2_official_string_gnn_frozen_cache_3d075b43` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p3_official_string_gnn_full_finetune_b09af07d` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_a9964654` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_laplacian_smoothing_300cae7b` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_weighted_ce_training_4f8db4e3` | true | perturbation_gene_or_context | class_distribution |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_concat_fusion_4ecbbcfc` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_aido_string_gated_fusion_e45402bd` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |  |
| `official_k562_p1_official_string_laplacian_smoothing_cacb16db` | true | perturbation_gene_or_context |  |  | `` | focal_loss |  |
| `official_k562_p2_official_weighted_ce_training_d9dfeac6` | true | perturbation_gene_or_context | class_distribution |  | `` | focal_loss |  |
| `official_k562_p3_official_aido_string_concat_fusion_857f5a22` | true | perturbation_gene_or_context |  |  | `` | focal_loss |  |
| `official_k562_p4_official_aido_string_gated_fusion_1fe27291` | true | perturbation_gene_or_context |  |  | `` | focal_loss |  |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4679 |
| 0 | 0.4679 |
| 0 | 0.4679 |
| 0 | 0.4679 |
| 1 | 0.4885 |
| 2 | 0.4885 |
| 3 | 0.4885 |
| 4 | 0.4885 |
| 5 | 0.4885 |
| 6 | 0.4885 |
| 7 | 0.4885 |
| 8 | 0.4885 |
| 9 | 0.4885 |
| 10 | 0.4885 |
| 11 | 0.4885 |
| 12 | 0.4885 |
| 13 | 0.4885 |
| 14 | 0.4885 |
| 15 | 0.4885 |
| 17 | 0.4885 |
| 18 | 0.4885 |
| 20 | 0.4885 |
| 21 | 0.4885 |
| 23 | 0.4885 |
| 25 | 0.4885 |
| 26 | 0.4885 |
| 28 | 0.4885 |
| 29 | 0.4885 |
| 32 | 0.4885 |
| 33 | 0.4885 |
| 35 | 0.4885 |
| 36 | 0.4885 |
| 38 | 0.4885 |
| 39 | 0.4885 |
| 40 | 0.4885 |
| 41 | 0.4885 |
| 42 | 0.4885 |
| 43 | 0.4885 |
| 44 | 0.4885 |
| 45 | 0.4885 |
| 46 | 0.4885 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=9 val=0.4108 test=0.4533 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` status=trained visits=4 val=0.4054 test=0.4254 strategy=official_pathway_pooling_reactome program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` status=trained visits=1 val=0.3905 test=0.4081 strategy=official_aido_topk_layer_tuning program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_9e4940c9` status=trained visits=2 val=0.4052 test=0.4216 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_9e4940c9/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_39582a38` status=requires_artifact_acquisition visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_39582a38/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_a9964654` status=trained visits=2 val=0.3552 test=0.3863 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_a9964654/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_d5b2bbc0` status=requires_artifact_acquisition visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_d5b2bbc0/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` status=trained visits=4 val=0.4183 test=0.4355 strategy=official_aido_string_cross_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_embedding_mlp_p1_official_regulatory_network_prior_4cb71788` status=requires_artifact_acquisition visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p1_official_regulatory_network_prior_4cb71788/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` status=trained visits=3 val=0.4181 test=0.4311 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_229ce930` status=requires_artifact_acquisition visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_229ce930/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_47592563` status=trained visits=2 val=0.3552 test=0.3845 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_47592563/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_root_aido_embedding_mlp_p3_official_string_gnn_full_finetune_18414a9e` status=trained visits=2 val=0.4216 test=0.4352 strategy=official_string_gnn_full_finetune program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p3_official_string_gnn_full_finetune_18414a9e/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_c8a798ec` status=requires_artifact_acquisition visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_c8a798ec/model.py pipeline=pipeline_program_node
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=10 val=0.4128 test=0.4630 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` status=trained visits=5 val=0.3979 test=0.4254 strategy=official_pathway_pooling_reactome program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_laplacian_smoothing_300cae7b` status=trained visits=2 val=0.4113 test=0.4386 strategy=official_string_laplacian_smoothing program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_string_laplacian_smoothing_300cae7b/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p2_official_weighted_ce_training_4f8db4e3` status=trained visits=2 val=0.3894 test=0.4270 strategy=official_weighted_ce_training program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_weighted_ce_training_4f8db4e3/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_concat_fusion_4ecbbcfc` status=trained visits=2 val=0.4075 test=0.4358 strategy=official_aido_string_concat_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_concat_fusion_4ecbbcfc/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p4_official_aido_string_gated_fusion_e45402bd` status=trained visits=2 val=0.4150 test=0.4405 strategy=official_aido_string_gated_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_aido_string_gated_fusion_e45402bd/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` status=trained visits=3 val=0.4207 test=0.4469 strategy=official_aido_string_cross_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p1_official_regulatory_network_prior_d2e79373` status=requires_artifact_acquisition visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_regulatory_network_prior_d2e79373/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87` status=trained visits=1 val=0.3785 test=0.4161 strategy=official_focal_loss_training program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287` status=trained visits=1 val=0.3825 test=0.4200 strategy=official_aido_full_finetune program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` status=trained visits=1 val=0.3572 test=0.3912 strategy=official_string_neighborhood_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_public_best_node2_1_1_1_1_1_smoke` status=trained visits=10 val=0.3333 test=0.3333 backend=external_static_node
  - `official_k562_p1_official_class_imbalance_training_fde536bb` status=trained visits=6 val=0.3828 test=0.3993 strategy=official_class_imbalance_training pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_p1_official_target_graph_conditioned_head_ab86336c` status=trained visits=5 val=0.3967 test=0.4169 strategy=official_target_graph_conditioned_head program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_p1_official_target_graph_conditioned_head_ab86336c/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_p1_official_string_laplacian_smoothing_cacb16db` status=trained visits=2 val=0.3655 test=0.3789 strategy=official_string_laplacian_smoothing program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_p1_official_string_laplacian_smoothing_cacb16db/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_p2_official_weighted_ce_training_d9dfeac6` status=trained visits=2 val=0.3566 test=0.3635 strategy=official_weighted_ce_training program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_p2_official_weighted_ce_training_d9dfeac6/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_p3_official_aido_string_concat_fusion_857f5a22` status=trained visits=2 val=0.3546 test=0.3731 strategy=official_aido_string_concat_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_p3_official_aido_string_concat_fusion_857f5a22/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_p4_official_aido_string_gated_fusion_1fe27291` status=trained visits=2 val=0.3564 test=0.3684 strategy=official_aido_string_gated_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_p4_official_aido_string_gated_fusion_1fe27291/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_p2_official_public_best_node_0f24e30a` status=trained visits=3 val=0.3333 test=0.3333 strategy=official_public_best_node backend=external_static_node pipeline=external_static_node
      - `official_k562_p1_official_regulatory_network_prior_144a8b54` status=requires_artifact_acquisition visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_p1_official_regulatory_network_prior_144a8b54/model.py pipeline=pipeline_program_node
      - `official_k562_p2_official_focal_loss_training_11ab1cb3` status=trained visits=1 val=0.3705 test=0.3804 strategy=official_focal_loss_training program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_p2_official_focal_loss_training_11ab1cb3/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_p3_official_aido_full_finetune_337e49b9` status=trained visits=1 val=0.3638 test=0.3767 strategy=official_aido_full_finetune program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_p3_official_aido_full_finetune_337e49b9/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_native_public_best_reimplementation` status=trained visits=12 val=0.4679 test=0.5256 backend=native_train artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_native_p1_official_aido_string_fusion_66a588f9` status=trained visits=11 val=0.4885 test=0.5183 strategy=official_aido_string_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_aido_string_fusion_66a588f9/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
    - `official_k562_native_p1_official_string_gnn_attention_7ec267ae` status=trained visits=10 val=0.4414 test=0.5046 strategy=official_string_gnn_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_string_gnn_attention_7ec267ae/model.py backend=native_train pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context
      - `official_k562_native_p1_official_aido_lora_adapter_d757c78c` status=trained visits=9 val=0.4741 test=0.5233 strategy=official_aido_lora_adapter program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_aido_lora_adapter_d757c78c/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,perturbation_gene_or_context
        - `official_k562_native_p1_official_target_gene_head_477d0ebb` status=trained visits=8 val=0.4552 test=0.5265 strategy=official_target_gene_head program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_target_gene_head_477d0ebb/model.py backend=native_train pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
          - `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` status=trained visits=5 val=0.4088 test=0.4477 strategy=official_pathway_pooling_reactome program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_pathway_pooling_reactome_b5af6810/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
            - `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` status=trained visits=1 val=0.3912 test=0.4269 strategy=official_aido_topk_layer_tuning program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
            - `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` status=trained visits=3 val=0.4161 test=0.4562 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
              - `official_k562_native_p1_official_scfoundation_top_layer_finetune_d20d4b0f` status=requires_artifact_acquisition visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_scfoundation_top_layer_finetune_d20d4b0f/model.py pipeline=pipeline_program_node
              - `official_k562_native_p2_official_string_gnn_frozen_cache_3d075b43` status=trained visits=2 val=0.4171 test=0.4753 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p2_official_string_gnn_frozen_cache_3d075b43/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
              - `official_k562_native_p3_official_string_gnn_full_finetune_b09af07d` status=trained visits=2 val=0.4257 test=0.4638 strategy=official_string_gnn_full_finetune program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p3_official_string_gnn_full_finetune_b09af07d/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
            - `official_k562_native_p3_official_scgpt_cell_encoder_3e5cbefd` status=requires_artifact_acquisition visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p3_official_scgpt_cell_encoder_3e5cbefd/model.py pipeline=pipeline_program_node
          - `official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f` status=trained visits=1 val=0.3578 test=0.4436 strategy=official_aido_string_cross_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
          - `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` status=trained visits=1 val=0.3426 test=0.4228 strategy=official_string_neighborhood_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p3_official_string_neighborhood_attention_0376ea72/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
