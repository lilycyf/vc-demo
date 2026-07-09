# Official K562 Post-Run Audit

## Executive Summary
- Run dir: `experiments/official_k562_scientific_policy_run_50`
- Node status: trained `109`, blocked/acquisition `9`, failed `1`, pending `0`.
- Best validation node: `official_k562_native_p1_official_aido_string_fusion_66a588f9` val `0.488477`, test `0.518328`.
- Best test node: `official_k562_native_p1_official_target_gene_head_477d0ebb` val `0.455153`, test `0.526514`.
- Best root by validation: `official_k562_native_public_best_reimplementation` val `0.467945`, test `0.525642`.
- Best root by test: `official_k562_native_public_best_reimplementation` val `0.467945`, test `0.525642`.
- Strict artifact policy held: blocked branches remained acquisition/block; no fallback was used in the committed run summary.
- The run reached scale, but the best validation model was found at the first generated child; later expansions mostly stress-tested breadth/repeat handling.

## Key Interpretation
- Best overall is selected by validation Macro-F1, but the best root has higher held-out test Macro-F1; validation gains are not clearly test-dominant.
- The search became concentrated in official_aido_string_fusion repeats; this is useful as a pressure test but weak as broad scientific discovery evidence.
- Strict artifact blockers prevented scFoundation/scGPT/regulatory branches, so several paper-level biological prior families remain untested rather than underperforming.
- The external public best-node wrapper failed once; native/generated nodes are valid, but numerical comparison to the public static best node remains incomplete.
- The continue-to-75 phase relaxed repeat constraints to increase trained count, so results after that point should be labeled pressure/stress testing, not a clean fixed-policy search.
- The best validation reward appeared extremely early in the search; later expansions did not move the best frontier.

## Top Nodes By Validation Macro-F1
| node | family | val Macro-F1 | test Macro-F1 | parent |
|---|---|---:|---:|---|
| `official_k562_native_p1_official_aido_string_fusion_66a588f9` | `official_aido_string_fusion` | 0.488477 | 0.518328 | `official_k562_native_public_best_reimplementation` |
| `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | `official_aido_lora_adapter` | 0.474117 | 0.523304 | `official_k562_native_p1_official_string_gnn_attention_7ec267ae` |
| `official_k562_native_public_best_reimplementation` | `official_native_public_best_reimplementation` | 0.467945 | 0.525642 | `` |
| `official_k562_native_p1_official_target_gene_head_477d0ebb` | `official_target_gene_head` | 0.455153 | 0.526514 | `official_k562_native_p1_official_aido_lora_adapter_d757c78c` |
| `official_k562_native_p1_official_string_gnn_attention_18d05ea9` | `official_string_gnn_attention` | 0.442795 | 0.484715 | `official_k562_native_p1_official_native_public_best_reimplementation_f10eb662` |
| `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | `official_string_gnn_attention` | 0.441398 | 0.504627 | `official_k562_native_p1_official_aido_string_fusion_66a588f9` |
| `official_k562_native_p1_official_aido_string_fusion_5404c348` | `official_aido_string_fusion` | 0.441125 | 0.474044 | `official_k562_native_p1_official_aido_string_fusion_b7bcad75` |
| `official_k562_native_p1_official_aido_string_fusion_34dcef23` | `official_aido_string_fusion` | 0.440088 | 0.464265 | `official_k562_native_p1_official_aido_string_fusion_6a51b4f1` |
| `official_k562_native_p2_official_multimodal_mixture_of_experts_93125c64` | `official_multimodal_mixture_of_experts` | 0.438746 | 0.478014 | `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` |
| `official_k562_native_p1_official_aido_string_fusion_334b1eb4` | `official_aido_string_fusion` | 0.437173 | 0.484473 | `official_k562_native_p1_official_aido_string_fusion_3bc03a7b` |
| `official_k562_native_p1_official_aido_string_fusion_e283eea0` | `official_aido_string_fusion` | 0.435855 | 0.473530 | `official_k562_native_p1_official_aido_string_fusion_903c8f73` |
| `official_k562_native_p1_official_aido_string_fusion_697e7978` | `official_aido_string_fusion` | 0.435698 | 0.486076 | `official_k562_native_p1_official_aido_string_fusion_c3bb6a03` |

## Top Nodes By Test Macro-F1
| node | family | val Macro-F1 | test Macro-F1 | parent |
|---|---|---:|---:|---|
| `official_k562_native_p1_official_target_gene_head_477d0ebb` | `official_target_gene_head` | 0.455153 | 0.526514 | `official_k562_native_p1_official_aido_lora_adapter_d757c78c` |
| `official_k562_native_public_best_reimplementation` | `official_native_public_best_reimplementation` | 0.467945 | 0.525642 | `` |
| `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | `official_aido_lora_adapter` | 0.474117 | 0.523304 | `official_k562_native_p1_official_string_gnn_attention_7ec267ae` |
| `official_k562_native_p1_official_aido_string_fusion_66a588f9` | `official_aido_string_fusion` | 0.488477 | 0.518328 | `official_k562_native_public_best_reimplementation` |
| `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | `official_string_gnn_attention` | 0.441398 | 0.504627 | `official_k562_native_p1_official_aido_string_fusion_66a588f9` |
| `official_k562_native_p1_official_aido_string_fusion_153f19d3` | `official_aido_string_fusion` | 0.434208 | 0.486328 | `official_k562_native_p1_official_aido_string_fusion_1462f243` |
| `official_k562_native_p1_official_aido_string_fusion_697e7978` | `official_aido_string_fusion` | 0.435698 | 0.486076 | `official_k562_native_p1_official_aido_string_fusion_c3bb6a03` |
| `official_k562_native_p1_official_string_gnn_attention_18d05ea9` | `official_string_gnn_attention` | 0.442795 | 0.484715 | `official_k562_native_p1_official_native_public_best_reimplementation_f10eb662` |
| `official_k562_native_p1_official_aido_string_fusion_334b1eb4` | `official_aido_string_fusion` | 0.437173 | 0.484473 | `official_k562_native_p1_official_aido_string_fusion_3bc03a7b` |
| `official_k562_native_p1_official_aido_string_fusion_1462f243` | `official_aido_string_fusion` | 0.433467 | 0.481672 | `official_k562_native_p1_official_aido_string_fusion_aeb536e0` |
| `official_k562_native_p2_official_multimodal_mixture_of_experts_93125c64` | `official_multimodal_mixture_of_experts` | 0.438746 | 0.478014 | `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` |
| `official_k562_native_p1_official_aido_string_fusion_3e3b60be` | `official_aido_string_fusion` | 0.417022 | 0.476265 | `official_k562_native_p1_official_aido_string_fusion_cf14e3bf` |

## Family Coverage And Concentration
| family | trained count | best val | mean val | best test | mean test |
|---|---:|---:|---:|---:|---:|
| `official_aido_string_fusion` | 32 | 0.488477 | 0.413606 | 0.518328 | 0.461494 |
| `official_aido_lora_adapter` | 5 | 0.474117 | 0.404916 | 0.523304 | 0.429564 |
| `official_string_gnn_attention` | 5 | 0.442795 | 0.398344 | 0.504627 | 0.440696 |
| `official_target_gene_head` | 5 | 0.455153 | 0.403731 | 0.526514 | 0.446429 |
| `official_pathway_pooling_reactome` | 4 | 0.408801 | 0.390298 | 0.447652 | 0.414366 |
| `official_aido_string_cross_attention` | 4 | 0.420698 | 0.401873 | 0.472137 | 0.449533 |
| `official_string_neighborhood_attention` | 3 | 0.357153 | 0.344482 | 0.422824 | 0.403517 |
| `official_class_imbalance_training` | 3 | 0.398138 | 0.389295 | 0.416518 | 0.407917 |
| `official_target_graph_conditioned_head` | 3 | 0.425073 | 0.390795 | 0.472302 | 0.416303 |
| `official_aido_cached_embedding_fusion` | 3 | 0.418051 | 0.413112 | 0.456214 | 0.436311 |
| `official_string_gnn_frozen_cache` | 3 | 0.417146 | 0.375868 | 0.475272 | 0.415363 |
| `official_native_public_best_reimplementation` | 2 | 0.467945 | 0.448915 | 0.525642 | 0.493697 |
| `official_public_best_node` | 2 | 0.333283 | 0.333283 | 0.333283 | 0.333283 |
| `root` | 2 | 0.412826 | 0.411835 | 0.462986 | 0.458120 |
| `official_focal_loss_training` | 2 | 0.378473 | 0.374490 | 0.416115 | 0.398278 |
| `official_aido_full_finetune` | 2 | 0.382536 | 0.373189 | 0.420003 | 0.398373 |
| `official_aido_topk_layer_tuning` | 2 | 0.391237 | 0.390858 | 0.426904 | 0.417501 |
| `official_string_gnn_full_finetune` | 2 | 0.425720 | 0.423664 | 0.463809 | 0.449486 |
| `official_string_laplacian_smoothing` | 2 | 0.411271 | 0.388375 | 0.438594 | 0.408738 |
| `official_weighted_ce_training` | 2 | 0.389370 | 0.372988 | 0.426967 | 0.395209 |

## MCTS Trace
- Trace events: `{'selection': 279, 'expansion': 115, 'backpropagation': 52, 'pending_implementation': 62, 'failure': 1}`
- Top selected parents: `{'official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1': 169, 'official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab': 12, 'official_k562_p1_official_target_graph_conditioned_head_ab86336c': 12, 'official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a': 12, 'official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6': 12, 'official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_full_finetune_6db85287': 12, 'official_k562_root_aido_gnn_embedding_mlp_p2_official_focal_loss_training_0f4a1b87': 12, 'official_k562_native_p1_official_target_gene_head_477d0ebb': 9, 'official_k562_root_aido_gnn_embedding_mlp': 9, 'official_k562_p2_official_public_best_node_0f24e30a': 9}`
- Top chosen blueprints: `{'official_aido_string_fusion': 32, 'official_pathway_pooling_reactome': 8, 'official_aido_string_cross_attention': 8, 'official_string_neighborhood_attention': 6, 'official_target_graph_conditioned_head': 6, 'official_regulatory_network_prior': 6, 'official_aido_cached_embedding_fusion': 6, 'official_scgpt_cell_encoder': 6, 'official_scfoundation_top_layer_finetune': 6, 'official_string_gnn_frozen_cache': 6}`
- Best-value timeline:
  - iteration `1` leaf `official_k562_native_p1_official_aido_string_fusion_66a588f9` reward `0.488477` test `0.518328`

## Blockers And Failure
- Acquisition queue count: `9`
- Blocked artifact ids observed: `['regulatory_network_artifact', 'scfoundation_cell_embeddings', 'single_cell_foundation_model_artifact']`
- Failures: `{"failures": [{"node": "official_k562_root_aido_gnn_embedding_mlp_p5_official_public_best_node_bf9cc47e", "parent": "official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1", "error": "RuntimeError: external static node failed with exit code 1; see experiments/official_k562_scientific_policy_run_50/nodes/official_k562_root_aido_gnn_embedding_mlp_p5_official_public_best_node_bf9cc47e/external_stdout.txt", "strategy": "official_public_best_node"}]}`

- External public-best failure detail: failed before training because Lightning TensorBoardLogger could not find `tensorboard` or `tensorboardX`; this is an environment dependency gap for the wrapper benchmark, not a native-model training failure.

## Recommended Next Actions
1. Do not jump straight to 150-node discovery from this exact state; first fix or quarantine the external public best-node wrapper so public-static comparison is clean.
2. Separate reports into two phases: fixed-policy search up to the first no-improvement stop, and relaxed-repeat pressure test after repeat limits were loosened.
3. If the goal is stronger scientific discovery, reduce repeat concentration in `official_aido_string_fusion` and force broader family coverage rather than more repeats.
4. If the goal is paper alignment, prioritize real acquisition/definition for scFoundation/scGPT/regulatory artifacts; these are currently blocked, not evaluated.
5. For model selection, report both best validation and best test root/generated node because the best validation node does not dominate the best root on test.
