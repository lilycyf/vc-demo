# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `official_k562_gap_closing_small_50`
- Trained nodes: 21
- Failed nodes: 0
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 51
- MCTS policy: uct
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

## MCTS Trace Summary

| Event | Count |
|---|---:|
| backpropagation | 17 |
| expansion | 17 |
| selection | 17 |

## Results

| Node | Parent | Backend | Strategy | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `` | native_train | root | 0.4640 | 0.4924 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | external_static_node | root | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root | 0.4129 | 0.4526 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root | 0.4200 | 0.4644 |
| `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | `official_k562_native_public_best_reimplementation` | native_train | official_native_public_best_reimplementation | 0.4600 | 0.5082 |
| `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | native_train | official_native_public_best_reimplementation | 0.4644 | 0.5318 |
| `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | native_train | official_native_public_best_reimplementation | 0.4664 | 0.5300 |
| `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | native_train | official_native_public_best_reimplementation | 0.4926 | 0.5270 |
| `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | native_train | official_native_public_best_reimplementation | 0.4961 | 0.5224 |
| `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | native_train | official_native_public_best_reimplementation | 0.4812 | 0.5324 |
| `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | native_train | official_native_public_best_reimplementation | 0.4813 | 0.5307 |
| `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | native_train | official_native_public_best_reimplementation | 0.4940 | 0.5258 |
| `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | native_train | official_native_public_best_reimplementation | 0.4786 | 0.5297 |
| `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | native_train | official_native_public_best_reimplementation | 0.4878 | 0.5120 |
| `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | native_train | official_native_public_best_reimplementation | 0.4667 | 0.5070 |
| `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | native_train | official_native_public_best_reimplementation | 0.4666 | 0.5383 |
| `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | native_train | official_native_public_best_reimplementation | 0.4773 | 0.5204 |
| `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | native_train | official_native_public_best_reimplementation | 0.4648 | 0.5175 |
| `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | native_train | official_native_public_best_reimplementation | 0.4905 | 0.5189 |
| `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` | `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | native_train | official_native_public_best_reimplementation | 0.4960 | 0.5324 |
| `official_k562_native_p1_official_native_public_best_reimplementation_e9ade575` | `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` | native_train | official_native_public_best_reimplementation | 0.4857 | 0.5383 |

## Best Node

- Best validation node: `official_k562_native_p1_official_native_public_best_reimplementation_b620177f`
- Validation Macro-F1: 0.4961
- Test Macro-F1: 0.5224

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Remaining gap: native implementations are compact proxies unless exact public static training recipe/checkpoints are run in benchmark mode.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.
