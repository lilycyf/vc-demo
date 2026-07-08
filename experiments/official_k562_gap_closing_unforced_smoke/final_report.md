# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `official_k562_gap_closing_unforced_smoke`
- Trained nodes: 6
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
| `official_k562_native_public_best_reimplementation` | `` | native_train | root | 0.4394 | 0.4800 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | external_static_node | root | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root | 0.3762 | 0.3852 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root | 0.3912 | 0.4284 |
| `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | `official_k562_native_public_best_reimplementation` | native_train | official_native_public_best_reimplementation | 0.4004 | 0.4549 |
| `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | native_train | official_native_public_best_reimplementation | 0.4159 | 0.4641 |

## Best Node

- Best validation node: `official_k562_native_public_best_reimplementation`
- Validation Macro-F1: 0.4394
- Test Macro-F1: 0.4800

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
