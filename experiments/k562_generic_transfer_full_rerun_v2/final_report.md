# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `k562_generic_transfer_full_rerun_v2`
- Trained nodes: 16
- Failed nodes: 1
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 252
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 33
- Structural replicate nodes: 4
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 9
- Missing artifacts: esm2_gene_embedding_h5ad, esm2_k562_target_manifest, aido_gene_or_cell_embeddings, scfoundation_cell_embeddings
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
| AIDO_STRING_cross_attention | 5 |
| AIDO_STRING_fusion | 9 |
| AIDO_STRING_gated | 2 |
| AIDO_adapter | 7 |
| AIDO_cached_embedding | 3 |
| AIDO_full_finetune | 3 |
| AIDO_selective_finetune | 3 |
| Reactome_pathway_pooling | 5 |
| STRING_GNN_attention | 7 |
| STRING_GNN_frozen_cached | 2 |
| STRING_GNN_full_finetune | 2 |
| STRING_laplacian_prior | 3 |
| STRING_neighborhood_attention | 5 |
| checkpoint_ensemble_or_SWA | 1 |
| class_weighted_CE | 2 |
| focal_loss | 3 |
| gene_dropout_augmentation | 2 |
| layerwise_lr_decay | 1 |
| multimodal_MoE | 2 |
| official_deg_imbalance | 4 |
| public_static_tree_family | 2 |
| public_vcharness_best_path | 4 |
| public_vcharness_best_path_native_exact | 1 |
| regulatory_network_prior | 4 |
| scFoundation_selective_finetune | 3 |
| scGPT_or_single_cell_encoder | 3 |
| target_bilinear_head | 2 |
| target_gene_aware_head | 6 |
| target_graph_conditioned_head | 4 |
| target_low_rank_head | 2 |
| temperature_calibration | 2 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| expansion | 18 |
| global_queue_selected | 18 |
| implementation_loop_result | 18 |
| implementation_loop_start | 18 |
| pending_implementation | 18 |
| proposal_pool_generated | 18 |
| proposal_pruned | 44 |
| proposal_queued | 64 |
| realtime_implementation_required | 18 |
| selection | 18 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4467 | 0.4956 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4823 | 0.5491 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_gene_head | structural_variant | 0.4491 | 0.4960 |
| `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` | `official_k562_root_aido_embedding_mlp` |  | official_string_neighborhood_attention | structural_variant | 0.3879 | 0.3909 |
| `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` | `official_k562_root_aido_embedding_mlp` |  | official_target_graph_conditioned_head | structural_variant | 0.3772 | 0.4111 |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_target_low_rank_head_9dbf5d12` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_low_rank_head | structural_variant | 0.4183 | 0.4933 |
| `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_bilinear_head | structural_variant | 0.4474 | 0.5011 |
| `official_k562_root_aido_embedding_mlp_p8_official_string_laplacian_smoothing_c590de04` | `official_k562_root_aido_embedding_mlp` |  | official_string_laplacian_smoothing | structural_variant | 0.3729 | 0.3924 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_86a657ed` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_aido_cached_embedding_fusion | structural_variant | 0.3991 | 0.4434 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_multimodal_mixture_of_experts_32dc0d1a` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_multimodal_mixture_of_experts | structural_variant | 0.3438 | 0.3496 |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_temperature_calibrated_head_403896b2` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_temperature_calibrated_head | structural_variant | 0.4460 | 0.4990 |
| `official_k562_root_aido_gnn_embedding_mlp_p12_official_gene_dropout_augmentation_756bd70f` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_gene_dropout_augmentation | structural_variant | 0.4435 | 0.4965 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_6ad83af7` | `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85` |  | official_layerwise_lr_schedule | structural_variant | 0.4608 | 0.5071 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_swa_or_checkpoint_ensemble_e558308b` | `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85` |  | official_swa_or_checkpoint_ensemble | structural_variant | 0.3791 | 0.4492 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_target_gene_head_c258d8f6` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_target_gene_head | replicate | 0.4435 | 0.4886 |
| `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_gene_head_adb9fcb6` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_target_gene_head | replicate | 0.4266 | 0.5058 |

## Best Node

- Best validation node: `official_k562_root_aido_gnn_embedding_mlp`
- Validation Macro-F1: 0.4823
- Test Macro-F1: 0.5491

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Formal implementation rule: compact/proxy native stand-ins are forbidden; nodes must be exact public static execution or full artifact-backed implementations.
- Remaining gap: any historical compact/proxy nodes are excluded from paper-level conclusions and must be rerun after full implementation.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.
