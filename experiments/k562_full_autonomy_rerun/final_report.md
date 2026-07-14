# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `k562_full_autonomy_rerun`
- Trained nodes: 7
- Failed nodes: 0
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 68
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 30
- Structural replicate nodes: 0
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 10
- Missing artifacts: esm2_gene_embedding_h5ad, esm2_k562_target_manifest, aido_gene_or_cell_embeddings, scfoundation_cell_embeddings, regulatory_network_artifact, single_cell_foundation_model_artifact
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
| AIDO_STRING_bilinear | 1 |
| AIDO_STRING_concat | 1 |
| AIDO_STRING_cross_attention | 1 |
| AIDO_STRING_fusion | 1 |
| AIDO_STRING_gated | 1 |
| AIDO_adapter | 1 |
| AIDO_cached_embedding | 1 |
| AIDO_full_finetune | 1 |
| AIDO_selective_finetune | 1 |
| Reactome_pathway_pooling | 1 |
| STRING_GNN_attention | 1 |
| STRING_GNN_frozen_cached | 1 |
| STRING_GNN_full_finetune | 1 |
| STRING_laplacian_prior | 1 |
| STRING_neighborhood_attention | 1 |
| class_weighted_CE | 1 |
| focal_loss | 1 |
| gene_dropout_augmentation | 1 |
| multimodal_MoE | 1 |
| official_deg_imbalance | 1 |
| public_static_tree_family | 1 |
| public_vcharness_best_path | 1 |
| regulatory_network_prior | 1 |
| scFoundation_selective_finetune | 1 |
| scGPT_or_single_cell_encoder | 1 |
| target_bilinear_head | 1 |
| target_gene_aware_head | 1 |
| target_graph_conditioned_head | 1 |
| target_low_rank_head | 1 |
| temperature_calibration | 1 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| backpropagation | 1 |
| expansion | 5 |
| global_queue_selected | 5 |
| implementation_loop_result | 4 |
| implementation_loop_start | 4 |
| pending_implementation | 4 |
| proposal_pool_generated | 5 |
| proposal_queued | 30 |
| realtime_implementation_required | 4 |
| selected_for_training | 1 |
| selection | 5 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4295 | 0.4801 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4833 | 0.5374 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_string_gnn_attention | structural_variant | 0.4644 | 0.5000 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_gene_head | structural_variant | 0.5010 | 0.5180 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_aido_string_fusion | structural_variant | 0.4782 | 0.5253 |
| `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | `official_k562_root_aido_embedding_mlp` | native_train | official_class_imbalance_training | structural_variant | 0.4344 | 0.4585 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_aido_lora_adapter | structural_variant | 0.4765 | 0.5044 |

## Best Node

- Best validation node: `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042`
- Validation Macro-F1: 0.5010
- Test Macro-F1: 0.5180

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Formal implementation rule: compact/proxy native stand-ins are forbidden; nodes must be exact public static execution or full artifact-backed implementations.
- Remaining gap: any historical compact/proxy nodes are excluded from paper-level conclusions and must be rerun after full implementation.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.
