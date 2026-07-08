# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `official_k562_gap_closing_small_50`
- Trained nodes: 20
- Failed nodes: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- MCTS policy: UCT unless run manifest says otherwise
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 11
- Missing artifacts: aido_gene_or_cell_embeddings, scfoundation_cell_embeddings
- Reconstructed compatibility artifacts: official_string_gnn_model_dir
- STRING_GNN compatibility caveat: reconstructed artifacts must not be claimed as numerically equivalent to unpublished original checkpoints.

## Results

| Node | Parent | Backend | Strategy | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `` | native_train | root | 0.4637 | 0.4883 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | external_static_node | root | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root | 0.4125 | 0.4529 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root | 0.4155 | 0.4613 |
| `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | `official_k562_native_public_best_reimplementation` | native_train | official_native_public_best_reimplementation | 0.4763 | 0.5231 |
| `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | native_train | official_native_public_best_reimplementation | 0.4640 | 0.5391 |
| `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | native_train | official_native_public_best_reimplementation | 0.4805 | 0.5370 |
| `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | native_train | official_native_public_best_reimplementation | 0.4977 | 0.5260 |
| `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | native_train | official_native_public_best_reimplementation | 0.4724 | 0.5029 |
| `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | native_train | official_native_public_best_reimplementation | 0.4764 | 0.5103 |
| `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | native_train | official_native_public_best_reimplementation | 0.4636 | 0.5228 |
| `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | native_train | official_native_public_best_reimplementation | 0.4772 | 0.5104 |
| `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | native_train | official_native_public_best_reimplementation | 0.4762 | 0.5156 |
| `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | native_train | official_native_public_best_reimplementation | 0.4561 | 0.4759 |
| `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | native_train | official_native_public_best_reimplementation | 0.4508 | 0.5167 |
| `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | native_train | official_native_public_best_reimplementation | 0.4788 | 0.5034 |
| `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | native_train | official_native_public_best_reimplementation | 0.4839 | 0.5299 |
| `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | native_train | official_native_public_best_reimplementation | 0.4858 | 0.5126 |
| `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | native_train | official_native_public_best_reimplementation | 0.4565 | 0.5088 |
| `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` | `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | native_train | official_native_public_best_reimplementation | 0.4458 | 0.4796 |

## Best Node

- Best validation node: `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0`
- Validation Macro-F1: 0.4977
- Test Macro-F1: 0.5260

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Remaining gap: native implementations are compact proxies unless exact public static training recipe/checkpoints are run in benchmark mode.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: smoke runs validate the loop; 50/150-node runs are required for paper-level search pressure.

## Next Commands

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_gap_closing_small_50 \
  --experiment official_k562_gap_closing_small_50 \
  --root-configs \
    configs/official_k562_root_aido_embedding_mlp.json \
    configs/official_k562_root_aido_gnn_embedding_mlp.json \
    configs/official_k562_public_best_node_smoke.json \
    configs/official_k562_native_public_best_reimplementation.json \
  --budget-nodes 50 --max-epochs 3 --max-children 3 --stop-no-improve 12 \
  --selection-policy uct --official-blueprint-space --strict-artifacts \
  --allow-planned-blueprints --enable-repair-loop --enable-acquisition-loop --reset
```
