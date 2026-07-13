# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `k562_generic_transfer_full_rerun`
- Trained nodes: 2
- Failed nodes: 14
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 532
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 24
- Structural replicate nodes: 0
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
| AIDO_STRING_cross_attention | 1 |
| AIDO_STRING_fusion | 1 |
| AIDO_adapter | 2 |
| AIDO_cached_embedding | 10 |
| AIDO_full_finetune | 9 |
| Reactome_pathway_pooling | 2 |
| STRING_GNN_attention | 1 |
| STRING_GNN_frozen_cached | 2 |
| STRING_GNN_full_finetune | 1 |
| STRING_neighborhood_attention | 2 |
| focal_loss | 234 |
| gene_dropout_augmentation | 1 |
| multimodal_MoE | 1 |
| official_deg_imbalance | 1 |
| public_static_tree_family | 2 |
| public_vcharness_best_path | 1 |
| regulatory_network_prior | 2 |
| scFoundation_selective_finetune | 10 |
| scGPT_or_single_cell_encoder | 10 |
| target_bilinear_head | 1 |
| target_gene_aware_head | 2 |
| target_graph_conditioned_head | 2 |
| target_low_rank_head | 1 |
| temperature_calibration | 1 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| artifact_acquisition_block_continued | 14 |
| expansion | 29 |
| global_queue_selected | 29 |
| implementation_loop_result | 15 |
| implementation_loop_start | 15 |
| implementation_skipped_continued | 15 |
| pending_implementation | 15 |
| proposal_pool_generated | 50 |
| proposal_pruned | 271 |
| proposal_queued | 29 |
| selection | 50 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4331 | 0.4944 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4670 | 0.5235 |

## Best Node

- Best validation node: `official_k562_root_aido_gnn_embedding_mlp`
- Validation Macro-F1: 0.4670
- Test Macro-F1: 0.5235

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Formal implementation rule: compact/proxy native stand-ins are forbidden; nodes must be exact public static execution or full artifact-backed implementations.
- Remaining gap: any historical compact/proxy nodes are excluded from paper-level conclusions and must be rerun after full implementation.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.
