# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `official_k562_full_cellline_run`
- Trained nodes: 12
- Failed nodes: 1
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 119
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 33
- Structural replicate nodes: 1
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
| AIDO_STRING_bilinear | 1 |
| AIDO_STRING_concat | 1 |
| AIDO_STRING_cross_attention | 3 |
| AIDO_STRING_fusion | 5 |
| AIDO_STRING_gated | 1 |
| AIDO_adapter | 5 |
| AIDO_cached_embedding | 1 |
| AIDO_full_finetune | 2 |
| AIDO_selective_finetune | 1 |
| Reactome_pathway_pooling | 4 |
| STRING_GNN_attention | 5 |
| STRING_GNN_frozen_cached | 2 |
| STRING_GNN_full_finetune | 2 |
| STRING_laplacian_prior | 2 |
| STRING_neighborhood_attention | 3 |
| checkpoint_ensemble_or_SWA | 1 |
| class_weighted_CE | 1 |
| focal_loss | 1 |
| gene_dropout_augmentation | 1 |
| layerwise_lr_decay | 1 |
| multimodal_MoE | 1 |
| official_deg_imbalance | 3 |
| public_static_tree_family | 1 |
| public_vcharness_best_path | 2 |
| public_vcharness_best_path_native_exact | 1 |
| regulatory_network_prior | 3 |
| scFoundation_selective_finetune | 2 |
| scGPT_or_single_cell_encoder | 1 |
| target_bilinear_head | 1 |
| target_gene_aware_head | 4 |
| target_graph_conditioned_head | 2 |
| target_low_rank_head | 1 |
| temperature_calibration | 1 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| artifact_acquisition_block | 1 |
| expansion | 11 |
| implementation_loop_result | 10 |
| implementation_loop_start | 10 |
| pending_implementation | 10 |
| proposal_pool_generated | 11 |
| proposal_pruned | 55 |
| selection | 11 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4354 | 0.4919 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4820 | 0.5395 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_gene_head | structural_variant | 0.4686 | 0.5171 |
| `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` | `official_k562_root_aido_embedding_mlp` |  | official_string_neighborhood_attention | structural_variant | 0.4505 | 0.4909 |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_string_laplacian_smoothing | structural_variant | 0.4957 | 0.5347 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_c870de87` | `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2` |  | official_aido_cached_embedding_fusion | structural_variant | 0.4757 | 0.5339 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_low_rank_head_1814b770` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_c870de87` |  | official_target_low_rank_head | structural_variant | 0.4897 | 0.5453 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_99d67e4f` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_low_rank_head_1814b770` |  | official_layerwise_lr_schedule | structural_variant | 0.4810 | 0.5282 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_10c0794d` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_99d67e4f` |  | official_target_gene_head | structural_variant | 0.4737 | 0.5226 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_10c0794d` |  | official_string_neighborhood_attention | structural_variant | 0.4796 | 0.5318 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_graph_conditioned_head_3894931a` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2` |  | official_target_graph_conditioned_head | structural_variant | 0.4640 | 0.5029 |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_string_laplacian_smoothing_c1bf6219` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_string_laplacian_smoothing | structural_variant | 0.4841 | 0.5302 |

## Best Node

- Best validation node: `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2`
- Validation Macro-F1: 0.4957
- Test Macro-F1: 0.5347

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Formal implementation rule: compact/proxy native stand-ins are forbidden; nodes must be exact public static execution or full artifact-backed implementations.
- Remaining gap: any historical compact/proxy nodes are excluded from paper-level conclusions and must be rerun after full implementation.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.
