# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: no improvement for 1 nodes
- Trained nodes: 3
- Failed nodes: 0
- Best node: `official_k562_root_aido_gnn_embedding_mlp` val=0.4108 test=0.4432
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.4108 test=0.4432
- Improvement over best root: 0.0000 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4068 | 0.4306 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4108 | 0.4432 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 5.8 | gated_mlp | 0.4068 | 0.4306 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 6.7 | gated_mlp | 0.4108 | 0.4432 |
| 1 | `official_k562_root_aido_gnn_embedding_mlp_p1_dual_path_gated_low_rank_4c85c6a0` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | dual_path_gated_low_rank | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 4.1 | custom_program | 0.4064 | 0.4284 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss |
|---|---:|---|---|---|---|---|
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |
| `official_k562_root_aido_gnn_embedding_mlp_p1_dual_path_gated_low_rank_4c85c6a0` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4068 |
| 0 | 0.4108 |
| 1 | 0.4108 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=1 val=0.4068 test=0.4306 artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=2 val=0.4108 test=0.4432 artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p1_dual_path_gated_low_rank_4c85c6a0` status=trained visits=1 val=0.4064 test=0.4284 strategy=dual_path_gated_low_rank program=experiments/official_k562_harness_backend_smoke/programs/official_k562_root_aido_gnn_embedding_mlp_p1_dual_path_gated_low_rank_4c85c6a0/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
