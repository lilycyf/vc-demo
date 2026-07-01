# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent is a task-aware rule policy: it uses K562 feature/model priors plus parent validation results to propose config-level child pipelines without changing data, splits, or metric semantics.

- Stop reason: no improvement for 8 nodes
- Trained nodes: 16
- Failed nodes: 0
- Best node: `root_concat_gated_mlp_c1_optimizer_refine_4a943707` val=0.6709 test=0.6134
- Best root: `root_concat_gated_mlp` val=0.6648 test=0.6101
- Improvement over best root: 0.0060 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `root_concat_gated_mlp` | `data/cell_lines/k562_concat` | gated_mlp | 0.6648 | 0.6101 |
| `root_concat_low_rank_mlp` | `data/cell_lines/k562_concat` | low_rank_mlp | 0.5604 | 0.5344 |
| `root_concat_mlp` | `data/cell_lines/k562_concat` | mlp | 0.6445 | 0.5802 |
| `root_concat_regularized_mlp` | `data/cell_lines/k562_concat` | mlp | 0.6086 | 0.5455 |
| `root_concat_residual_mlp` | `data/cell_lines/k562_concat` | residual_mlp | 0.6193 | 0.5600 |
| `root_delta_mlp` | `data/cell_lines/k562_delta` | mlp | 0.5981 | 0.5548 |
| `root_onehot_mlp` | `data/cell_lines/k562_onehot` | mlp | 0.5955 | 0.5352 |

## All Trained Nodes

| Iter | Node | Parent | Agent | Strategy | Data dir | Model | Hidden | Depth | Dropout | Rank | LR | WD | Val | Test |
|---:|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `root_concat_gated_mlp` | `` | root | root | `data/cell_lines/k562_concat` | gated_mlp | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6648 | 0.6101 |
| 0 | `root_concat_low_rank_mlp` | `` | root | root | `data/cell_lines/k562_concat` | low_rank_mlp | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5604 | 0.5344 |
| 0 | `root_concat_mlp` | `` | root | root | `data/cell_lines/k562_concat` | mlp | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6445 | 0.5802 |
| 0 | `root_concat_regularized_mlp` | `` | root | root | `data/cell_lines/k562_concat` | mlp | 384 | 3 | 0.2 |  | 0.0002 | 0.0005 | 0.6086 | 0.5455 |
| 0 | `root_concat_residual_mlp` | `` | root | root | `data/cell_lines/k562_concat` | residual_mlp | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6193 | 0.5600 |
| 0 | `root_delta_mlp` | `` | root | root | `data/cell_lines/k562_delta` | mlp | 256 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.5981 | 0.5548 |
| 0 | `root_onehot_mlp` | `` | root | root | `data/cell_lines/k562_onehot` | mlp | 256 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.5955 | 0.5352 |
| 1 | `root_concat_gated_mlp_c1_optimizer_refine_4a943707` | `root_concat_gated_mlp` | codex_task_aware_rule_agent | optimizer_refine | `data/cell_lines/k562_concat` | gated_mlp | 384 | 2 | 0.1 |  | 0.0005 | 1e-05 | 0.6709 | 0.6134 |
| 2 | `root_concat_mlp_c1_optimizer_refine_cc45c6cb` | `root_concat_mlp` | codex_task_aware_rule_agent | optimizer_refine | `data/cell_lines/k562_concat` | mlp | 384 | 2 | 0.1 |  | 0.0005 | 1e-05 | 0.6521 | 0.5847 |
| 3 | `root_concat_residual_mlp_c1_optimizer_refine_c49bd80c` | `root_concat_residual_mlp` | codex_task_aware_rule_agent | optimizer_refine | `data/cell_lines/k562_concat` | residual_mlp | 384 | 3 | 0.1 |  | 0.0005 | 1e-05 | 0.6348 | 0.5720 |
| 4 | `root_concat_regularized_mlp_c1_optimizer_refine_833289e9` | `root_concat_regularized_mlp` | codex_task_aware_rule_agent | optimizer_refine | `data/cell_lines/k562_concat` | mlp | 384 | 3 | 0.2 |  | 0.0005 | 1e-05 | 0.6253 | 0.5630 |
| 5 | `root_delta_mlp_c1_feature_to_concat_46d0e002` | `root_delta_mlp` | codex_task_aware_rule_agent | feature_to_concat | `data/cell_lines/k562_concat` | mlp | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6357 | 0.5843 |
| 6 | `root_onehot_mlp_c1_feature_to_concat_8546344c` | `root_onehot_mlp` | codex_task_aware_rule_agent | feature_to_concat | `data/cell_lines/k562_concat` | mlp | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6516 | 0.5774 |
| 7 | `root_concat_low_rank_mlp_c1_optimizer_refine_066955ab` | `root_concat_low_rank_mlp` | codex_task_aware_rule_agent | optimizer_refine | `data/cell_lines/k562_concat` | low_rank_mlp | 384 | 2 | 0.1 | 64 | 0.0005 | 1e-05 | 0.5840 | 0.5394 |
| 8 | `root_concat_gated_mlp_c1_optimizer_refine_4a943707_c1_optimizer_refine_4ecf6e16` | `root_concat_gated_mlp_c1_optimizer_refine_4a943707` | codex_task_aware_rule_agent | optimizer_refine | `data/cell_lines/k562_concat` | gated_mlp | 384 | 2 | 0.1 |  | 0.0008 | 0.0 | 0.6700 | 0.6210 |
| 9 | `root_concat_gated_mlp_c1_optimizer_refine_4a943707_c1_optimizer_refine_4ecf6e16_c1_optimizer_refine_0ba56c9c` | `root_concat_gated_mlp_c1_optimizer_refine_4a943707_c1_optimizer_refine_4ecf6e16` | codex_task_aware_rule_agent | optimizer_refine | `data/cell_lines/k562_concat` | gated_mlp | 384 | 2 | 0.1 |  | 0.0005 | 1e-05 | 0.6675 | 0.6205 |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.6648 |
| 0 | 0.6648 |
| 0 | 0.6648 |
| 0 | 0.6648 |
| 0 | 0.6648 |
| 0 | 0.6648 |
| 0 | 0.6648 |
| 1 | 0.6709 |
| 2 | 0.6709 |
| 3 | 0.6709 |
| 4 | 0.6709 |
| 5 | 0.6709 |
| 6 | 0.6709 |
| 7 | 0.6709 |
| 8 | 0.6709 |
| 9 | 0.6709 |

## Tree

- `root_concat_gated_mlp` status=trained visits=4 val=0.6648 test=0.6101
  - `root_concat_gated_mlp_c1_optimizer_refine_4a943707` status=trained visits=4 val=0.6709 test=0.6134 strategy=optimizer_refine
    - `root_concat_gated_mlp_c1_optimizer_refine_4a943707_c1_optimizer_refine_4ecf6e16` status=trained visits=3 val=0.6700 test=0.6210 strategy=optimizer_refine
      - `root_concat_gated_mlp_c1_optimizer_refine_4a943707_c1_optimizer_refine_4ecf6e16_c1_optimizer_refine_0ba56c9c` status=trained visits=2 val=0.6675 test=0.6205 strategy=optimizer_refine
- `root_concat_low_rank_mlp` status=trained visits=2 val=0.5604 test=0.5344
  - `root_concat_low_rank_mlp_c1_optimizer_refine_066955ab` status=trained visits=2 val=0.5840 test=0.5394 strategy=optimizer_refine
- `root_concat_mlp` status=trained visits=2 val=0.6445 test=0.5802
  - `root_concat_mlp_c1_optimizer_refine_cc45c6cb` status=trained visits=2 val=0.6521 test=0.5847 strategy=optimizer_refine
- `root_concat_regularized_mlp` status=trained visits=2 val=0.6086 test=0.5455
  - `root_concat_regularized_mlp_c1_optimizer_refine_833289e9` status=trained visits=2 val=0.6253 test=0.5630 strategy=optimizer_refine
- `root_concat_residual_mlp` status=trained visits=2 val=0.6193 test=0.5600
  - `root_concat_residual_mlp_c1_optimizer_refine_c49bd80c` status=trained visits=2 val=0.6348 test=0.5720 strategy=optimizer_refine
- `root_delta_mlp` status=trained visits=2 val=0.5981 test=0.5548
  - `root_delta_mlp_c1_feature_to_concat_46d0e002` status=trained visits=2 val=0.6357 test=0.5843 strategy=feature_to_concat
- `root_onehot_mlp` status=trained visits=2 val=0.5955 test=0.5352
  - `root_onehot_mlp_c1_feature_to_concat_8546344c` status=trained visits=2 val=0.6516 test=0.5774 strategy=feature_to_concat

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next using UCT.
- The proposal agent decides how to modify that parent into one executable child config.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
