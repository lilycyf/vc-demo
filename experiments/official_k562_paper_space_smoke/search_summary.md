# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: no improvement for 1 nodes
- Trained nodes: 4
- Failed nodes: 0
- Best node: `official_k562_root_aido_gnn_embedding_mlp` val=0.3919 test=0.4206
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.3919 test=0.4206
- Improvement over best root: 0.0000 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_public_best_node2_1_1_1_1_1` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3861 | 0.3914 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3919 | 0.4206 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_public_best_node2_1_1_1_1_1` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 36.9 | external_static_node | 0.3333 | 0.3333 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 5.5 | gated_mlp | 0.3861 | 0.3914 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 5.8 | gated_mlp | 0.3919 | 0.4206 |
| 1 | `official_k562_root_aido_gnn_embedding_mlp_p1_official_class_imbalance_training_f6a6bb2d` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_class_imbalance_training | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 5.5 | gated_mlp | 0.3890 | 0.4069 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss |
|---|---:|---|---|---|---|---|
| `official_k562_public_best_node2_1_1_1_1_1` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN,public_node_code |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node |
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_class_imbalance_training_f6a6bb2d` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | focal_loss |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.3333 |
| 0 | 0.3861 |
| 0 | 0.3919 |
| 1 | 0.3919 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=1 val=0.3861 test=0.3914 backend=native_train artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=2 val=0.3919 test=0.4206 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_class_imbalance_training_f6a6bb2d` status=trained visits=1 val=0.3890 test=0.4069 strategy=official_class_imbalance_training backend=native_train pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_public_best_node2_1_1_1_1_1` status=trained visits=1 val=0.3333 test=0.3333 backend=external_static_node

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
