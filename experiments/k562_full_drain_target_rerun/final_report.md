# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `k562_full_drain_target_rerun`
- Trained nodes: 32
- Failed nodes: 1
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 481
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 33
- Structural replicate nodes: 4
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 8
- Missing artifacts: esm2_gene_embedding_h5ad, esm2_k562_target_manifest, aido_gene_or_cell_embeddings, scfoundation_cell_embeddings, official_aido_cell_100m_model_dir, official_string_gnn_model_dir, regulatory_network_artifact, single_cell_foundation_model_artifact
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
| AIDO_STRING_cross_attention | 9 |
| AIDO_STRING_fusion | 17 |
| AIDO_STRING_gated | 4 |
| AIDO_adapter | 15 |
| AIDO_cached_embedding | 4 |
| AIDO_full_finetune | 4 |
| AIDO_selective_finetune | 4 |
| Reactome_pathway_pooling | 11 |
| STRING_GNN_attention | 15 |
| STRING_GNN_frozen_cached | 4 |
| STRING_GNN_full_finetune | 4 |
| STRING_laplacian_prior | 4 |
| STRING_neighborhood_attention | 5 |
| checkpoint_ensemble_or_SWA | 4 |
| class_weighted_CE | 5 |
| focal_loss | 4 |
| gene_dropout_augmentation | 4 |
| layerwise_lr_decay | 3 |
| multimodal_MoE | 4 |
| official_deg_imbalance | 5 |
| public_static_tree_family | 4 |
| public_vcharness_best_path | 5 |
| public_vcharness_best_path_native_exact | 1 |
| regulatory_network_prior | 4 |
| scFoundation_selective_finetune | 4 |
| scGPT_or_single_cell_encoder | 4 |
| target_bilinear_head | 4 |
| target_gene_aware_head | 15 |
| target_graph_conditioned_head | 6 |
| target_low_rank_head | 4 |
| temperature_calibration | 4 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| artifact_acquisition_block_continued | 1 |
| backpropagation | 1 |
| expansion | 33 |
| failure | 1 |
| global_queue_selected | 33 |
| implementation_loop_result | 29 |
| implementation_loop_start | 29 |
| implementation_skipped_continued | 1 |
| manual_train_pending_backpropagation | 29 |
| pending_implementation | 29 |
| proposal_pool_generated | 33 |
| proposal_pruned | 132 |
| proposal_queued | 66 |
| realtime_implementation_required | 29 |
| selected_for_training | 2 |
| selection | 33 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4277 | 0.4866 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4881 | 0.5437 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_gene_head | structural_variant | 0.4458 | 0.4914 |
| `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | `official_k562_root_aido_embedding_mlp` | native_train | official_class_imbalance_training | structural_variant | 0.4194 | 0.4395 |
| `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_pathway_pooling_reactome | structural_variant | 0.4795 | 0.5350 |
| `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` | `official_k562_root_aido_embedding_mlp` |  | official_string_neighborhood_attention | structural_variant | 0.4550 | 0.4876 |
| `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` | `official_k562_root_aido_embedding_mlp` |  | official_target_graph_conditioned_head | structural_variant | 0.4527 | 0.4874 |
| `official_k562_root_aido_embedding_mlp_p6_official_target_low_rank_head_f28a1bc1` | `official_k562_root_aido_embedding_mlp` |  | official_target_low_rank_head | structural_variant | 0.4390 | 0.4643 |
| `official_k562_root_aido_embedding_mlp_p1_official_target_bilinear_head_217a17b9` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_target_bilinear_head | structural_variant | 0.3599 | 0.3717 |
| `official_k562_root_aido_embedding_mlp_p2_official_focal_loss_training_37672209` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_focal_loss_training | structural_variant | 0.4309 | 0.4468 |
| `official_k562_root_aido_gnn_embedding_mlp_p5_official_weighted_ce_training_ea636995` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_weighted_ce_training | structural_variant | 0.4757 | 0.5193 |
| `official_k562_root_aido_embedding_mlp_p10_official_gene_dropout_augmentation_ed174d61` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_gene_dropout_augmentation | structural_variant | 0.3953 | 0.4151 |
| `official_k562_root_aido_embedding_mlp_p11_official_temperature_calibrated_head_ddceef70` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_temperature_calibrated_head | structural_variant | 0.4307 | 0.4473 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_string_laplacian_smoothing_dbe5f678` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_string_laplacian_smoothing | structural_variant | 0.4791 | 0.5261 |
| `official_k562_root_aido_embedding_mlp_p9_official_multimodal_mixture_of_experts_4c5d0049` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_multimodal_mixture_of_experts | structural_variant | 0.3612 | 0.3741 |
| `official_k562_root_aido_embedding_mlp_p2_official_layerwise_lr_schedule_331b00bd` | `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` |  | official_layerwise_lr_schedule | structural_variant | 0.4407 | 0.4991 |
| `official_k562_root_aido_embedding_mlp_p3_official_swa_or_checkpoint_ensemble_7fe2d86a` | `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` |  | official_swa_or_checkpoint_ensemble | structural_variant | 0.4431 | 0.4732 |
| `official_k562_root_aido_embedding_mlp_p4_official_target_gene_head_e22830d2` | `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` |  | official_target_gene_head | structural_variant | 0.4320 | 0.4703 |
| `official_k562_root_aido_embedding_mlp_p9_official_class_imbalance_training_a61b5a31` | `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` |  | official_class_imbalance_training | structural_variant | 0.4103 | 0.4252 |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_neighborhood_attention_62af14f5` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_string_neighborhood_attention | structural_variant | 0.4948 | 0.5218 |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_pathway_pooling_reactome_6cb04fc4` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_pathway_pooling_reactome | replicate | 0.4744 | 0.5412 |
| `official_k562_root_aido_gnn_embedding_mlp_p10_official_target_graph_conditioned_head_cc233d73` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_target_graph_conditioned_head | structural_variant | 0.4747 | 0.5262 |
| `official_k562_root_aido_embedding_mlp_p8_official_target_bilinear_head_25775217` | `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` |  | official_target_bilinear_head | structural_variant | 0.4267 | 0.4736 |
| `official_k562_root_aido_gnn_embedding_mlp_p6_official_target_low_rank_head_4ca91b75` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_string_laplacian_smoothing_dbe5f678` |  | official_target_low_rank_head | structural_variant | 0.4507 | 0.4877 |
| `official_k562_root_aido_embedding_mlp_p11_official_focal_loss_training_e2939124` | `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` |  | official_focal_loss_training | structural_variant | 0.4412 | 0.4763 |
| `official_k562_root_aido_embedding_mlp_p8_official_weighted_ce_training_9bd1864b` | `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` |  | official_weighted_ce_training | structural_variant | 0.4391 | 0.4986 |
| `official_k562_root_aido_embedding_mlp_p6_official_gene_dropout_augmentation_14862a55` | `official_k562_root_aido_embedding_mlp_p3_official_swa_or_checkpoint_ensemble_7fe2d86a` |  | official_gene_dropout_augmentation | structural_variant | 0.4361 | 0.4968 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_temperature_calibrated_head_382161c4` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_temperature_calibrated_head | structural_variant | 0.4885 | 0.5373 |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_string_laplacian_smoothing_fbb33084` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_weighted_ce_training_ea636995` |  | official_string_laplacian_smoothing | structural_variant | 0.4913 | 0.5396 |
| `official_k562_root_aido_embedding_mlp_p12_official_multimodal_mixture_of_experts_004fa9ff` | `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` |  | official_multimodal_mixture_of_experts | structural_variant | 0.4389 | 0.4773 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_swa_or_checkpoint_ensemble_9bb25b02` | `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_neighborhood_attention_62af14f5` |  | official_swa_or_checkpoint_ensemble | structural_variant | 0.4774 | 0.5339 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_layerwise_lr_schedule_ffa8e759` | `official_k562_root_aido_gnn_embedding_mlp_p11_official_pathway_pooling_reactome_6cb04fc4` |  | official_layerwise_lr_schedule | structural_variant | 0.4901 | 0.5234 |

## Best Node

- Best validation node: `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_neighborhood_attention_62af14f5`
- Validation Macro-F1: 0.4948
- Test Macro-F1: 0.5218

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Formal implementation rule: compact/proxy native stand-ins are forbidden; nodes must be exact public static execution or full artifact-backed implementations.
- Remaining gap: any historical compact/proxy nodes are excluded from paper-level conclusions and must be rerun after full implementation.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.
