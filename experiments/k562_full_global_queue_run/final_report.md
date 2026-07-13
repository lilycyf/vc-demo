# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `k562_full_global_queue_run`
- Trained nodes: 26
- Failed nodes: 4
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 450
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 33
- Structural replicate nodes: 2
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 8
- Missing artifacts: esm2_gene_embedding_h5ad, esm2_k562_target_manifest, aido_gene_or_cell_embeddings, scfoundation_cell_embeddings, official_string_gnn_model_dir
- Reconstructed compatibility artifacts: none
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
| AIDO_STRING_bilinear | 4 |
| AIDO_STRING_concat | 4 |
| AIDO_STRING_cross_attention | 11 |
| AIDO_STRING_fusion | 18 |
| AIDO_STRING_gated | 4 |
| AIDO_adapter | 16 |
| AIDO_cached_embedding | 5 |
| AIDO_full_finetune | 5 |
| AIDO_selective_finetune | 5 |
| Reactome_pathway_pooling | 15 |
| STRING_GNN_attention | 16 |
| STRING_GNN_frozen_cached | 5 |
| STRING_GNN_full_finetune | 4 |
| STRING_laplacian_prior | 4 |
| STRING_neighborhood_attention | 8 |
| checkpoint_ensemble_or_SWA | 3 |
| class_weighted_CE | 4 |
| focal_loss | 5 |
| gene_dropout_augmentation | 2 |
| layerwise_lr_decay | 3 |
| multimodal_MoE | 4 |
| official_deg_imbalance | 5 |
| public_static_tree_family | 4 |
| public_vcharness_best_path | 5 |
| public_vcharness_best_path_native_exact | 1 |
| regulatory_network_prior | 5 |
| scFoundation_selective_finetune | 5 |
| scGPT_or_single_cell_encoder | 5 |
| target_bilinear_head | 4 |
| target_gene_aware_head | 16 |
| target_graph_conditioned_head | 8 |
| target_low_rank_head | 4 |
| temperature_calibration | 3 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| artifact_acquisition_block_continued | 4 |
| expansion | 35 |
| global_queue_selected | 35 |
| implementation_loop_result | 32 |
| implementation_loop_start | 32 |
| pending_implementation | 32 |
| proposal_pool_generated | 35 |
| proposal_pruned | 145 |
| proposal_queued | 65 |
| selection | 35 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4381 | 0.4909 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4810 | 0.5259 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_gene_head | structural_variant | 0.4375 | 0.4994 |
| `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` | `official_k562_root_aido_embedding_mlp` |  | official_string_neighborhood_attention | structural_variant | 0.4148 | 0.4461 |
| `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` | `official_k562_root_aido_embedding_mlp` |  | official_target_graph_conditioned_head | structural_variant | 0.4195 | 0.4458 |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_target_low_rank_head_9dbf5d12` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_low_rank_head | structural_variant | 0.4557 | 0.5022 |
| `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_bilinear_head | structural_variant | 0.4456 | 0.4893 |
| `official_k562_root_aido_embedding_mlp_p8_official_string_laplacian_smoothing_c590de04` | `official_k562_root_aido_embedding_mlp` |  | official_string_laplacian_smoothing | structural_variant | 0.4292 | 0.4604 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_86a657ed` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_aido_cached_embedding_fusion | structural_variant | 0.4359 | 0.4985 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_multimodal_mixture_of_experts_32dc0d1a` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_multimodal_mixture_of_experts | structural_variant | 0.4562 | 0.4967 |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_temperature_calibrated_head_403896b2` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_temperature_calibrated_head | structural_variant | 0.4428 | 0.4994 |
| `official_k562_root_aido_gnn_embedding_mlp_p12_official_gene_dropout_augmentation_756bd70f` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_gene_dropout_augmentation | structural_variant | 0.4474 | 0.4934 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_04c620ff` | `official_k562_root_aido_gnn_embedding_mlp_p8_official_target_low_rank_head_9dbf5d12` |  | official_layerwise_lr_schedule | structural_variant | 0.4602 | 0.4992 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_swa_or_checkpoint_ensemble_889dddf0` | `official_k562_root_aido_gnn_embedding_mlp_p8_official_target_low_rank_head_9dbf5d12` |  | official_swa_or_checkpoint_ensemble | structural_variant | 0.4661 | 0.5070 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_4888e1ef` | `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85` |  | official_target_gene_head | structural_variant | 0.4828 | 0.5283 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_string_neighborhood_attention_08b2c770` | `official_k562_root_aido_gnn_embedding_mlp_p8_official_target_low_rank_head_9dbf5d12` |  | official_string_neighborhood_attention | structural_variant | 0.4809 | 0.5225 |
| `official_k562_root_aido_gnn_embedding_mlp_p5_official_target_graph_conditioned_head_e1a25a55` | `official_k562_root_aido_gnn_embedding_mlp_p7_official_multimodal_mixture_of_experts_32dc0d1a` |  | official_target_graph_conditioned_head | structural_variant | 0.4866 | 0.5290 |
| `official_k562_root_aido_gnn_embedding_mlp_p12_official_target_low_rank_head_e31f01a8` | `official_k562_root_aido_gnn_embedding_mlp_p7_official_multimodal_mixture_of_experts_32dc0d1a` |  | official_target_low_rank_head | structural_variant | 0.4474 | 0.5053 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_target_bilinear_head_8053bd8c` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_4888e1ef` |  | official_target_bilinear_head | structural_variant | 0.4898 | 0.5164 |
| `official_k562_root_aido_gnn_embedding_mlp_p9_official_aido_cached_embedding_fusion_0f75b97b` | `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85` |  | official_aido_cached_embedding_fusion | structural_variant | 0.4786 | 0.5303 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_laplacian_smoothing_87f46e76` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_swa_or_checkpoint_ensemble_889dddf0` |  | official_string_laplacian_smoothing | structural_variant | 0.4937 | 0.5194 |
| `official_k562_root_aido_gnn_embedding_mlp_p12_official_temperature_calibrated_head_841519b9` | `official_k562_root_aido_gnn_embedding_mlp_p12_official_gene_dropout_augmentation_756bd70f` |  | official_temperature_calibrated_head | structural_variant | 0.4901 | 0.5232 |
| `official_k562_root_aido_gnn_embedding_mlp_p6_official_gene_dropout_augmentation_368da237` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_target_graph_conditioned_head_e1a25a55` |  | official_gene_dropout_augmentation | structural_variant | 0.4947 | 0.5319 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_layerwise_lr_schedule_9c544c06` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_target_bilinear_head_8053bd8c` |  | official_layerwise_lr_schedule | structural_variant | 0.4702 | 0.5197 |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_multimodal_mixture_of_experts_4374052d` | `official_k562_root_aido_gnn_embedding_mlp_p7_official_multimodal_mixture_of_experts_32dc0d1a` |  | official_multimodal_mixture_of_experts | replicate | 0.4719 | 0.5336 |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_swa_or_checkpoint_ensemble_e29e9b6b` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_4888e1ef` |  | official_swa_or_checkpoint_ensemble | structural_variant | 0.4872 | 0.5291 |

## Best Node

- Best validation node: `official_k562_root_aido_gnn_embedding_mlp_p6_official_gene_dropout_augmentation_368da237`
- Validation Macro-F1: 0.4947
- Test Macro-F1: 0.5319

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Formal implementation rule: compact/proxy native stand-ins are forbidden; nodes must be exact public static execution or full artifact-backed implementations.
- Remaining gap: any historical compact/proxy nodes are excluded from paper-level conclusions and must be rerun after full implementation.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.
