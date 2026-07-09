# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `official_k562_scientific_policy_run_50`
- Trained nodes: 109
- Failed nodes: 1
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 509
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 33
- Structural replicate nodes: 26
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 11
- Missing artifacts: esm2_k562_target_manifest, aido_gene_or_cell_embeddings, scfoundation_cell_embeddings, regulatory_network_artifact, single_cell_foundation_model_artifact
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
| AIDO_STRING_cross_attention | 4 |
| AIDO_STRING_fusion | 32 |
| AIDO_STRING_gated | 2 |
| AIDO_adapter | 5 |
| AIDO_cached_embedding | 3 |
| AIDO_full_finetune | 2 |
| AIDO_selective_finetune | 2 |
| Reactome_pathway_pooling | 4 |
| STRING_GNN_attention | 5 |
| STRING_GNN_frozen_cached | 3 |
| STRING_GNN_full_finetune | 2 |
| STRING_laplacian_prior | 2 |
| STRING_neighborhood_attention | 3 |
| checkpoint_ensemble_or_SWA | 1 |
| class_weighted_CE | 2 |
| focal_loss | 2 |
| gene_dropout_augmentation | 2 |
| layerwise_lr_decay | 2 |
| multimodal_MoE | 2 |
| official_deg_imbalance | 3 |
| public_static_tree_family | 2 |
| public_vcharness_best_path | 2 |
| public_vcharness_best_path_native_v1 | 1 |
| regulatory_network_prior | 3 |
| scFoundation_selective_finetune | 3 |
| scGPT_or_single_cell_encoder | 3 |
| target_bilinear_head | 2 |
| target_gene_aware_head | 5 |
| target_graph_conditioned_head | 3 |
| target_low_rank_head | 2 |
| temperature_calibration | 2 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| backpropagation | 52 |
| expansion | 115 |
| failure | 1 |
| pending_implementation | 62 |
| selection | 279 |

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
| `official_k562_p1_official_swa_or_checkpoint_ensemble_63c03f89` | `official_k562_p2_official_focal_loss_training_11ab1cb3` |  | official_swa_or_checkpoint_ensemble | structural_variant | 0.2942 | 0.3002 |
| `official_k562_p1_official_aido_string_fusion_f4155be3` | `official_k562_p3_official_aido_full_finetune_337e49b9` | native_train | official_aido_string_fusion | structural_variant | 0.3167 | 0.3241 |
| `official_k562_native_p1_official_native_public_best_reimplementation_f10eb662` | `official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f` | native_train | official_native_public_best_reimplementation | structural_variant | 0.4299 | 0.4618 |
| `official_k562_native_p1_official_string_gnn_attention_18d05ea9` | `official_k562_native_p1_official_native_public_best_reimplementation_f10eb662` | native_train | official_string_gnn_attention | structural_variant | 0.4428 | 0.4847 |
| `official_k562_native_p1_official_aido_lora_adapter_069eadbc` | `official_k562_native_p1_official_string_gnn_attention_18d05ea9` | native_train | official_aido_lora_adapter | structural_variant | 0.4029 | 0.4310 |
| `official_k562_native_p1_official_target_gene_head_9b50d297` | `official_k562_native_p1_official_aido_lora_adapter_069eadbc` | native_train | official_target_gene_head | structural_variant | 0.3902 | 0.4428 |
| `official_k562_native_p5_official_class_imbalance_training_e4044bff` | `official_k562_native_p1_official_target_gene_head_9b50d297` | native_train | official_class_imbalance_training | structural_variant | 0.3981 | 0.4165 |
| `official_k562_native_p5_official_target_graph_conditioned_head_47986c6a` | `official_k562_native_p5_official_class_imbalance_training_e4044bff` |  | official_target_graph_conditioned_head | structural_variant | 0.3506 | 0.3597 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_6be02781` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` | native_train | official_string_gnn_attention | structural_variant | 0.3480 | 0.3756 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_b55aad86` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_6be02781` | native_train | official_aido_string_fusion | structural_variant | 0.4120 | 0.4353 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_8625f823` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_b55aad86` | native_train | official_aido_lora_adapter | structural_variant | 0.3996 | 0.4148 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_03a94485` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_8625f823` | native_train | official_target_gene_head | structural_variant | 0.3763 | 0.4029 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_9a3ff6ec` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_03a94485` | native_train | official_aido_string_fusion | structural_variant | 0.4075 | 0.4493 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_gnn_attention_cb063325` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_9a3ff6ec` | native_train | official_string_gnn_attention | structural_variant | 0.3552 | 0.3870 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_4bce1ac6` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_gnn_attention_cb063325` | native_train | official_aido_lora_adapter | structural_variant | 0.4064 | 0.4275 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_37175f57` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_4bce1ac6` | native_train | official_target_gene_head | structural_variant | 0.3939 | 0.4299 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_c9e646ba` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_37175f57` | native_train | official_aido_string_fusion | structural_variant | 0.4113 | 0.4361 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_neighborhood_attention_8e3eed47` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_c9e646ba` |  | official_string_neighborhood_attention | structural_variant | 0.3337 | 0.3965 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_class_imbalance_training_badb57a0` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_c9e646ba` | native_train | official_class_imbalance_training | structural_variant | 0.3869 | 0.4079 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_81fc3097` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_class_imbalance_training_badb57a0` |  | official_pathway_pooling_reactome | structural_variant | 0.3491 | 0.3590 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_2c8ec64e` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_class_imbalance_training_badb57a0` | native_train | official_string_gnn_attention | structural_variant | 0.4043 | 0.4516 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_66952171` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_2c8ec64e` | native_train | official_aido_lora_adapter | structural_variant | 0.3416 | 0.3512 |
| `official_k562_native_p1_official_target_graph_conditioned_head_efba71d4` | `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` |  | official_target_graph_conditioned_head | structural_variant | 0.4251 | 0.4723 |
| `official_k562_native_p2_official_aido_string_cross_attention_f36612a4` | `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` |  | official_aido_string_cross_attention | structural_variant | 0.4107 | 0.4721 |
| `official_k562_native_p3_official_target_gene_head_80566b56` | `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` | native_train | official_target_gene_head | structural_variant | 0.4031 | 0.4301 |
| `official_k562_native_p1_official_aido_string_fusion_0ca95dd5` | `official_k562_native_p3_official_target_gene_head_80566b56` | native_train | official_aido_string_fusion | structural_variant | 0.3590 | 0.4310 |
| `official_k562_native_p1_official_aido_string_fusion_aeb536e0` | `official_k562_native_p1_official_aido_string_fusion_0ca95dd5` | native_train | official_aido_string_fusion | replicate | 0.4209 | 0.4662 |
| `official_k562_native_p1_official_aido_string_fusion_1462f243` | `official_k562_native_p1_official_aido_string_fusion_aeb536e0` | native_train | official_aido_string_fusion | replicate | 0.4335 | 0.4817 |
| `official_k562_native_p1_official_aido_string_fusion_153f19d3` | `official_k562_native_p1_official_aido_string_fusion_1462f243` | native_train | official_aido_string_fusion | replicate | 0.4342 | 0.4863 |
| `official_k562_native_p1_official_aido_string_fusion_903c8f73` | `official_k562_native_p1_official_aido_string_fusion_153f19d3` | native_train | official_aido_string_fusion | replicate | 0.4313 | 0.4761 |
| `official_k562_native_p1_official_aido_string_fusion_e283eea0` | `official_k562_native_p1_official_aido_string_fusion_903c8f73` | native_train | official_aido_string_fusion | replicate | 0.4359 | 0.4735 |
| `official_k562_native_p1_official_aido_string_fusion_8ab5038c` | `official_k562_native_p1_official_aido_string_fusion_e283eea0` | native_train | official_aido_string_fusion | replicate | 0.3818 | 0.4457 |
| `official_k562_native_p1_official_aido_string_fusion_453bde57` | `official_k562_native_p1_official_aido_string_fusion_8ab5038c` | native_train | official_aido_string_fusion | replicate | 0.4051 | 0.4663 |
| `official_k562_native_p1_official_aido_string_fusion_e41ea537` | `official_k562_native_p1_official_aido_string_fusion_453bde57` | native_train | official_aido_string_fusion | replicate | 0.4237 | 0.4721 |
| `official_k562_native_p1_official_aido_string_fusion_c3bb6a03` | `official_k562_native_p1_official_aido_string_fusion_e41ea537` | native_train | official_aido_string_fusion | replicate | 0.4030 | 0.4586 |
| `official_k562_native_p1_official_aido_string_fusion_697e7978` | `official_k562_native_p1_official_aido_string_fusion_c3bb6a03` | native_train | official_aido_string_fusion | replicate | 0.4357 | 0.4861 |
| `official_k562_native_p1_official_aido_string_fusion_6a51b4f1` | `official_k562_native_p1_official_aido_string_fusion_697e7978` | native_train | official_aido_string_fusion | replicate | 0.3794 | 0.4485 |
| `official_k562_native_p1_official_aido_string_fusion_34dcef23` | `official_k562_native_p1_official_aido_string_fusion_6a51b4f1` | native_train | official_aido_string_fusion | replicate | 0.4401 | 0.4643 |
| `official_k562_native_p1_official_aido_string_fusion_4d418087` | `official_k562_native_p1_official_aido_string_fusion_34dcef23` | native_train | official_aido_string_fusion | replicate | 0.3950 | 0.4655 |
| `official_k562_native_p1_official_aido_string_fusion_44ec01a4` | `official_k562_native_p1_official_aido_string_fusion_4d418087` | native_train | official_aido_string_fusion | replicate | 0.4049 | 0.4649 |
| `official_k562_native_p1_official_aido_string_fusion_cf14e3bf` | `official_k562_native_p1_official_aido_string_fusion_44ec01a4` | native_train | official_aido_string_fusion | replicate | 0.4289 | 0.4643 |
| `official_k562_native_p1_official_aido_string_fusion_3e3b60be` | `official_k562_native_p1_official_aido_string_fusion_cf14e3bf` | native_train | official_aido_string_fusion | replicate | 0.4170 | 0.4763 |
| `official_k562_native_p1_official_aido_string_fusion_ad422419` | `official_k562_native_p1_official_aido_string_fusion_3e3b60be` | native_train | official_aido_string_fusion | replicate | 0.3871 | 0.4468 |
| `official_k562_native_p1_official_aido_string_fusion_7ffa279e` | `official_k562_native_p1_official_aido_string_fusion_ad422419` | native_train | official_aido_string_fusion | replicate | 0.4272 | 0.4679 |
| `official_k562_native_p1_official_aido_string_fusion_8d97d3db` | `official_k562_native_p1_official_aido_string_fusion_7ffa279e` | native_train | official_aido_string_fusion | replicate | 0.3979 | 0.4589 |
| `official_k562_native_p1_official_aido_string_fusion_3bc03a7b` | `official_k562_native_p1_official_aido_string_fusion_8d97d3db` | native_train | official_aido_string_fusion | replicate | 0.3987 | 0.4587 |
| `official_k562_native_p1_official_aido_string_fusion_334b1eb4` | `official_k562_native_p1_official_aido_string_fusion_3bc03a7b` | native_train | official_aido_string_fusion | replicate | 0.4372 | 0.4845 |
| `official_k562_native_p1_official_aido_string_fusion_c881fe1c` | `official_k562_native_p1_official_aido_string_fusion_334b1eb4` | native_train | official_aido_string_fusion | replicate | 0.4129 | 0.4708 |
| `official_k562_native_p1_official_aido_string_fusion_b7bcad75` | `official_k562_native_p1_official_aido_string_fusion_c881fe1c` | native_train | official_aido_string_fusion | replicate | 0.4354 | 0.4753 |
| `official_k562_native_p1_official_aido_string_fusion_5404c348` | `official_k562_native_p1_official_aido_string_fusion_b7bcad75` | native_train | official_aido_string_fusion | replicate | 0.4411 | 0.4740 |
| `official_k562_native_p1_official_aido_string_fusion_dac145f0` | `official_k562_native_p1_official_aido_string_fusion_5404c348` | native_train | official_aido_string_fusion | replicate | 0.4008 | 0.4743 |
| `official_k562_native_p1_official_aido_string_fusion_406dbc47` | `official_k562_native_p1_official_aido_string_fusion_dac145f0` | native_train | official_aido_string_fusion | replicate | 0.4316 | 0.4660 |

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
