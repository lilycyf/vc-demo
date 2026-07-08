# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `official_k562_scientific_policy_run_50`
- Trained nodes: 15
- Failed nodes: 0
- Pending implementations: 8
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 66
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 13
- Structural replicate nodes: 0
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 11
- Missing artifacts: aido_gene_or_cell_embeddings, scfoundation_cell_embeddings
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
| AIDO_STRING_cross_attention | 3 |
| AIDO_STRING_fusion | 1 |
| AIDO_adapter | 1 |
| AIDO_full_finetune | 2 |
| Reactome_pathway_pooling | 3 |
| STRING_GNN_attention | 1 |
| STRING_neighborhood_attention | 2 |
| focal_loss | 2 |
| official_deg_imbalance | 1 |
| public_vcharness_best_path | 1 |
| regulatory_network_prior | 3 |
| target_gene_aware_head | 1 |
| target_graph_conditioned_head | 1 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| backpropagation | 6 |
| expansion | 22 |
| pending_implementation | 16 |
| selection | 22 |

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
| `official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f` | `official_k562_native_p1_official_target_gene_head_477d0ebb` |  | official_aido_string_cross_attention | structural_variant | 0.3578 | 0.4436 |
| `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` | `official_k562_native_p1_official_target_gene_head_477d0ebb` |  | official_string_neighborhood_attention | structural_variant | 0.3426 | 0.4228 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_aido_string_cross_attention | structural_variant | 0.4207 | 0.4469 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_string_neighborhood_attention | structural_variant | 0.3572 | 0.3912 |
| `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` | `official_k562_root_aido_embedding_mlp` |  | official_aido_string_cross_attention | structural_variant | 0.4183 | 0.4355 |
| `official_k562_p1_official_class_imbalance_training_fde536bb` | `official_k562_public_best_node2_1_1_1_1_1_smoke` | external_static_node | official_class_imbalance_training | structural_variant | 0.3333 | 0.3333 |
| `official_k562_p2_official_public_best_node_0f24e30a` | `official_k562_p1_official_class_imbalance_training_fde536bb` | external_static_node | official_public_best_node | structural_variant | 0.3333 | 0.3333 |

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
