# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: no improvement for 1 nodes
- Trained nodes: 5
- Failed nodes: 0
- Best node: `official_k562_native_public_best_reimplementation` val=0.4336 test=0.4599
- Best root: `official_k562_native_public_best_reimplementation` val=0.4336 test=0.4599
- Improvement over best root: 0.0000 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `data/cell_lines/official_k562_cls` | custom_program | 0.4336 | 0.4599 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3944 | 0.4200 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4009 | 0.4232 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_native_public_best_reimplementation` | `` | root | root | native_train | program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 10.1 | custom_program | 0.4336 | 0.4599 |
| 0 | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 34.8 | external_static_node | 0.3333 | 0.3333 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 7.0 | gated_mlp | 0.3944 | 0.4200 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 5.3 | gated_mlp | 0.4009 | 0.4232 |
| 1 | `official_k562_native_p1_official_target_gene_head_31044876` | `official_k562_native_public_best_reimplementation` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 6.9 | custom_program | 0.4169 | 0.4478 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_native_public_best_reimplementation` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN,public_node_code |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_target_gene_head_31044876` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy | None |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4336 |
| 0 | 0.4336 |
| 0 | 0.4336 |
| 0 | 0.4336 |
| 1 | 0.4336 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=1 val=0.3944 test=0.4200 backend=native_train artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=1 val=0.4009 test=0.4232 backend=native_train artifacts=perturbation_gene_or_context
- `official_k562_public_best_node2_1_1_1_1_1_smoke` status=trained visits=1 val=0.3333 test=0.3333 backend=external_static_node
- `official_k562_native_public_best_reimplementation` status=trained visits=2 val=0.4336 test=0.4599 backend=native_train artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_native_p1_official_target_gene_head_31044876` status=trained visits=1 val=0.4169 test=0.4478 strategy=official_target_gene_head program=experiments/official_k562_gap_closing_smoke/programs/official_k562_native_p1_official_target_gene_head_31044876/model.py backend=native_train pipeline=pipeline_program_node artifacts=perturbation_gene_or_context

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
