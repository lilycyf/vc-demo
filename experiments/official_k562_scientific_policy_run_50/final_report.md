# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `official_k562_scientific_policy_run_50`
- Trained nodes: 57
- Failed nodes: 0
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 186
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 31
- Structural replicate nodes: 0
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 12
- Missing artifacts: aido_gene_or_cell_embeddings, scfoundation_cell_embeddings, regulatory_network_artifact, single_cell_foundation_model_artifact
- Reconstructed compatibility artifacts: official_string_gnn_model_dir
- STRING_GNN compatibility caveat: reconstructed artifacts must not be claimed as numerically equivalent to unpublished original checkpoints.

## Public Static Tree Alignment

- Family groups mapped: 4
- The public static scaffold is benchmark/reference only; it is not counted as local search output.

| Public family | Node count | Local equivalent blueprints |
|---|---:|---|
| aido_lora_adapter | 6 | official_aido_lora_adapter |
| aido_string_fusion | 68 | official_aido_string_fusion |
| official_training_or_head_variant | 1 | official_target_gene_head |
| string_gnn_attention | 79 | official_string_gnn_attention |

## Scientific Search Coverage

| Family | Count |
|---|---:|
| AIDO_STRING_bilinear | 2 |
| AIDO_STRING_concat | 2 |
| AIDO_STRING_cross_attention | 3 |
| AIDO_STRING_fusion | 1 |
| AIDO_STRING_gated | 2 |
| AIDO_adapter | 1 |
| AIDO_cached_embedding | 3 |
| AIDO_full_finetune | 2 |
| AIDO_selective_finetune | 2 |
| Reactome_pathway_pooling | 3 |
| STRING_GNN_attention | 1 |
| STRING_GNN_frozen_cached | 3 |
| STRING_GNN_full_finetune | 2 |
| STRING_laplacian_prior | 2 |
| STRING_neighborhood_attention | 2 |
| class_weighted_CE | 2 |
| focal_loss | 2 |
| gene_dropout_augmentation | 2 |
| layerwise_lr_decay | 2 |
| multimodal_MoE | 2 |
| official_deg_imbalance | 1 |
| public_static_tree_family | 2 |
| public_vcharness_best_path | 1 |
| regulatory_network_prior | 3 |
| scFoundation_selective_finetune | 3 |
| scGPT_or_single_cell_encoder | 3 |
| target_bilinear_head | 2 |
| target_gene_aware_head | 1 |
| target_graph_conditioned_head | 1 |
| target_low_rank_head | 2 |
| temperature_calibration | 2 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| backpropagation | 6 |
| expansion | 62 |
| pending_implementation | 56 |
| selection | 62 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `` | native_train | root |  | 0.4679 | 0.5256 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | external_static_node | root |  | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4108 | 0.4533 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4128 | 0.4630 |
| `official_k562_native_p1_official_aido_string_fusion_66a588f9` | `official_k562_native_public_best_reimplementation` | native_train | official_aido_string_fusion | structural_variant | 0.4885 | 0.5183 |
| `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | `official_k562_native_p1_official_aido_string_fusion_66a588f9` | native_train | official_string_gnn_attention | structural_variant | 0.4414 | 0.5046 |
| `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | native_train | official_aido_lora_adapter | structural_variant | 0.4741 | 0.5233 |
| `official_k562_native_p1_official_target_gene_head_477d0ebb` | `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | native_train | official_target_gene_head | structural_variant | 0.4552 | 0.5265 |
| `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` | `official_k562_native_p1_official_target_gene_head_477d0ebb` |  | official_pathway_pooling_reactome | structural_variant | 0.4088 | 0.4477 |
| `official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f` | `official_k562_native_p1_official_target_gene_head_477d0ebb` |  | official_aido_string_cross_attention | structural_variant | 0.3578 | 0.4436 |
| `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` | `official_k562_native_p1_official_target_gene_head_477d0ebb` |  | official_string_neighborhood_attention | structural_variant | 0.3426 | 0.4228 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_pathway_pooling_reactome | structural_variant | 0.3979 | 0.4254 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_aido_string_cross_attention | structural_variant | 0.4207 | 0.4469 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_string_neighborhood_attention | structural_variant | 0.3572 | 0.3912 |
| `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` | `official_k562_root_aido_embedding_mlp` |  | official_pathway_pooling_reactome | structural_variant | 0.4054 | 0.4254 |
| `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` | `official_k562_root_aido_embedding_mlp` |  | official_aido_string_cross_attention | structural_variant | 0.4183 | 0.4355 |
| `official_k562_p1_official_class_imbalance_training_fde536bb` | `official_k562_public_best_node2_1_1_1_1_1_smoke` |  | official_class_imbalance_training | structural_variant | 0.3828 | 0.3993 |
| `official_k562_p1_official_target_graph_conditioned_head_ab86336c` | `official_k562_p1_official_class_imbalance_training_fde536bb` |  | official_target_graph_conditioned_head | structural_variant | 0.3967 | 0.4169 |
| `official_k562_p2_official_public_best_node_0f24e30a` | `official_k562_p1_official_class_imbalance_training_fde536bb` | external_static_node | official_public_best_node | structural_variant | 0.3333 | 0.3333 |
| `official_k562_p2_official_focal_loss_training_11ab1cb3` | `official_k562_p2_official_public_best_node_0f24e30a` |  | official_focal_loss_training | structural_variant | 0.3705 | 0.3804 |
| `official_k562_p3_official_aido_full_finetune_337e49b9` | `official_k562_p2_official_public_best_node_0f24e30a` |  | official_aido_full_finetune | structural_variant | 0.3638 | 0.3767 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` |  | official_focal_loss_training | structural_variant | 0.3785 | 0.4161 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` |  | official_aido_full_finetune | structural_variant | 0.3825 | 0.4200 |
| `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` | `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` |  | official_aido_cached_embedding_fusion | structural_variant | 0.4181 | 0.4311 |
| `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` | `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` |  | official_aido_topk_layer_tuning | structural_variant | 0.3912 | 0.4269 |
| `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` | `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` |  | official_aido_cached_embedding_fusion | structural_variant | 0.4161 | 0.4562 |
| `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` | `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` |  | official_aido_topk_layer_tuning | structural_variant | 0.3905 | 0.4081 |
| `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_9e4940c9` | `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` |  | official_aido_cached_embedding_fusion | structural_variant | 0.4052 | 0.4216 |
| `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_47592563` | `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` |  | official_string_gnn_frozen_cache | structural_variant | 0.3552 | 0.3845 |
| `official_k562_root_aido_embedding_mlp_p3_official_string_gnn_full_finetune_18414a9e` | `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` |  | official_string_gnn_full_finetune | structural_variant | 0.4216 | 0.4352 |
| `official_k562_native_p2_official_string_gnn_frozen_cache_3d075b43` | `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` |  | official_string_gnn_frozen_cache | structural_variant | 0.4171 | 0.4753 |
| `official_k562_native_p3_official_string_gnn_full_finetune_b09af07d` | `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` |  | official_string_gnn_full_finetune | structural_variant | 0.4257 | 0.4638 |
| `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_a9964654` | `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_9e4940c9` |  | official_string_gnn_frozen_cache | structural_variant | 0.3552 | 0.3863 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_laplacian_smoothing_300cae7b` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` |  | official_string_laplacian_smoothing | structural_variant | 0.4113 | 0.4386 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_weighted_ce_training_4f8db4e3` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` |  | official_weighted_ce_training | structural_variant | 0.3894 | 0.4270 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_concat_fusion_4ecbbcfc` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` |  | official_aido_string_concat_fusion | structural_variant | 0.4075 | 0.4358 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_aido_string_gated_fusion_e45402bd` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` |  | official_aido_string_gated_fusion | structural_variant | 0.4150 | 0.4405 |
| `official_k562_p1_official_string_laplacian_smoothing_cacb16db` | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` |  | official_string_laplacian_smoothing | structural_variant | 0.3655 | 0.3789 |
| `official_k562_p2_official_weighted_ce_training_d9dfeac6` | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` |  | official_weighted_ce_training | structural_variant | 0.3566 | 0.3635 |
| `official_k562_p3_official_aido_string_concat_fusion_857f5a22` | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` |  | official_aido_string_concat_fusion | structural_variant | 0.3546 | 0.3731 |
| `official_k562_p4_official_aido_string_gated_fusion_1fe27291` | `official_k562_p1_official_target_graph_conditioned_head_ab86336c` |  | official_aido_string_gated_fusion | structural_variant | 0.3564 | 0.3684 |
| `official_k562_native_p1_official_aido_string_bilinear_fusion_e2f0a399` | `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` |  | official_aido_string_bilinear_fusion | structural_variant | 0.4145 | 0.4332 |
| `official_k562_native_p2_official_multimodal_mixture_of_experts_93125c64` | `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` |  | official_multimodal_mixture_of_experts | structural_variant | 0.4387 | 0.4780 |
| `official_k562_native_p3_official_target_low_rank_head_0ae2d7d8` | `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` |  | official_target_low_rank_head | structural_variant | 0.4232 | 0.4425 |
| `official_k562_native_p4_official_target_bilinear_head_5a491322` | `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` |  | official_target_bilinear_head | structural_variant | 0.4053 | 0.4315 |
| `official_k562_root_aido_embedding_mlp_p1_official_aido_string_bilinear_fusion_15f82887` | `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` |  | official_aido_string_bilinear_fusion | structural_variant | 0.3830 | 0.4038 |
| `official_k562_root_aido_embedding_mlp_p2_official_multimodal_mixture_of_experts_db0e9af8` | `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` |  | official_multimodal_mixture_of_experts | structural_variant | 0.4260 | 0.4394 |
| `official_k562_root_aido_embedding_mlp_p3_official_target_low_rank_head_2e5e7df5` | `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` |  | official_target_low_rank_head | structural_variant | 0.4061 | 0.4246 |
| `official_k562_root_aido_embedding_mlp_p4_official_target_bilinear_head_7539101a` | `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` |  | official_target_bilinear_head | structural_variant | 0.4117 | 0.4263 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_public_static_node_family_wrapper_34241d65` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287` |  | official_public_static_node_family_wrapper | structural_variant | 0.4108 | 0.4408 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_temperature_calibrated_head_d4f4664c` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287` |  | official_temperature_calibrated_head | structural_variant | 0.3971 | 0.4194 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_gene_dropout_augmentation_11602380` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287` |  | official_gene_dropout_augmentation | structural_variant | 0.3707 | 0.4125 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_layerwise_lr_schedule_e7171cc9` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287` |  | official_layerwise_lr_schedule | structural_variant | 0.4093 | 0.4310 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_public_static_node_family_wrapper_cc540ff7` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87` |  | official_public_static_node_family_wrapper | structural_variant | 0.4151 | 0.4350 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_temperature_calibrated_head_c9bd0eba` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87` |  | official_temperature_calibrated_head | structural_variant | 0.3695 | 0.4080 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_gene_dropout_augmentation_d60de428` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87` |  | official_gene_dropout_augmentation | structural_variant | 0.4020 | 0.4355 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_layerwise_lr_schedule_77aee7f1` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87` |  | official_layerwise_lr_schedule | structural_variant | 0.3909 | 0.4237 |

## Best Node

- Best validation node: `official_k562_native_p1_official_aido_string_fusion_66a588f9`
- Validation Macro-F1: 0.4885
- Test Macro-F1: 0.5183

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Remaining gap: native implementations are compact proxies unless exact public static training recipe/checkpoints are run in benchmark mode.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.
