# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: no improvement for 8 nodes
- Trained nodes: 15
- Failed nodes: 0
- Best node: `root_concat_gated_mlp` val=0.6628 test=0.6275
- Best root: `root_concat_gated_mlp` val=0.6628 test=0.6275
- Improvement over best root: 0.0000 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `root_concat_esm2_gene_embedding_gated_mlp` | `data/cell_lines/k562_concat_esm2_gene_embedding` | gated_mlp | 0.6520 | 0.6107 |
| `root_concat_gated_mlp` | `data/cell_lines/k562_concat` | gated_mlp | 0.6628 | 0.6275 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Agent | Strategy | Data dir | Model | Program | Hidden | Depth | Dropout | Rank | LR | WD | Val | Test |
|---:|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `root_concat_esm2_gene_embedding_gated_mlp` | `` | root | root | root | `data/cell_lines/k562_concat_esm2_gene_embedding` | gated_mlp | `` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6520 | 0.6107 |
| 0 | `root_concat_gated_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | gated_mlp | `` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6628 | 0.6275 |
| 1 | `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` | `root_concat_gated_mlp` | program_node | codex_program_node_agent | esm2_gene_projection | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6591 | 0.5801 |
| 2 | `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53` | `root_concat_gated_mlp` | program_node | codex_program_node_agent | aido_embedding_fusion | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.5114 | 0.5106 |
| 3 | `root_concat_esm2_gene_embedding_gated_mlp_p1_mixture_of_experts_568d46e0` | `root_concat_esm2_gene_embedding_gated_mlp` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_esm2_gene_embedding_gated_mlp_p1_mixture_of_experts_568d46e0/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6454 | 0.5710 |
| 4 | `root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_d110bf14` | `root_concat_esm2_gene_embedding_gated_mlp_p1_mixture_of_experts_568d46e0` | program_node | codex_program_node_agent | selective_adapter_finetune | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_d110bf14/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6092 | 0.5563 |
| 5 | `root_concat_esm2_gene_embedding_gated_mlp_p2_focal_loss_training_strategy_28b52bf3` | `root_concat_esm2_gene_embedding_gated_mlp_p1_mixture_of_experts_568d46e0` | program_node | codex_program_node_agent | focal_loss_training_strategy | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_esm2_gene_embedding_gated_mlp_p2_focal_loss_training_strategy_28b52bf3/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6170 | 0.5913 |
| 6 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_2fd693aa` | `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_2fd693aa/model.py` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5546 | 0.5173 |
| 7 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_f7a63806` | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_2fd693aa` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_f7a63806/model.py` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5609 | 0.5209 |
| 8 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_d587fd09` | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_f7a63806` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_d587fd09/model.py` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5636 | 0.5240 |
| 9 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_632e7a18` | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_d587fd09` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_632e7a18/model.py` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5509 | 0.5223 |
| 10 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_59171b80` | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_632e7a18` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_59171b80/model.py` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5714 | 0.5319 |
| 11 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_398e085c` | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_59171b80` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_398e085c/model.py` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5640 | 0.5153 |
| 12 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_7c4d116f` | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_398e085c` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_7c4d116f/model.py` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5417 | 0.5064 |
| 13 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_60828c40` | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_7c4d116f` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat_esm2_gene_embedding` | custom_program | `experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_60828c40/model.py` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5652 | 0.5270 |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.6520 |
| 0 | 0.6628 |
| 1 | 0.6628 |
| 2 | 0.6628 |
| 3 | 0.6628 |
| 4 | 0.6628 |
| 5 | 0.6628 |
| 6 | 0.6628 |
| 7 | 0.6628 |
| 8 | 0.6628 |
| 9 | 0.6628 |
| 10 | 0.6628 |
| 11 | 0.6628 |
| 12 | 0.6628 |
| 13 | 0.6628 |

## Tree

- `root_concat_gated_mlp` status=trained visits=11 val=0.6628 test=0.6275
  - `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` status=trained visits=10 val=0.6591 test=0.5801 strategy=esm2_gene_projection program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460/model.py
    - `root_concat_gated_mlp_p1_dual_path_gated_low_rank_2fd693aa` status=trained visits=8 val=0.5546 test=0.5173 strategy=dual_path_gated_low_rank program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_2fd693aa/model.py
      - `root_concat_gated_mlp_p1_dual_path_gated_low_rank_f7a63806` status=trained visits=7 val=0.5609 test=0.5209 strategy=dual_path_gated_low_rank program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_f7a63806/model.py
        - `root_concat_gated_mlp_p1_dual_path_gated_low_rank_d587fd09` status=trained visits=6 val=0.5636 test=0.5240 strategy=dual_path_gated_low_rank program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_d587fd09/model.py
          - `root_concat_gated_mlp_p1_dual_path_gated_low_rank_632e7a18` status=trained visits=5 val=0.5509 test=0.5223 strategy=dual_path_gated_low_rank program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_632e7a18/model.py
            - `root_concat_gated_mlp_p1_dual_path_gated_low_rank_59171b80` status=trained visits=4 val=0.5714 test=0.5319 strategy=dual_path_gated_low_rank program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_59171b80/model.py
              - `root_concat_gated_mlp_p1_dual_path_gated_low_rank_398e085c` status=trained visits=3 val=0.5640 test=0.5153 strategy=dual_path_gated_low_rank program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_398e085c/model.py
                - `root_concat_gated_mlp_p1_dual_path_gated_low_rank_7c4d116f` status=trained visits=2 val=0.5417 test=0.5064 strategy=dual_path_gated_low_rank program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_7c4d116f/model.py
                  - `root_concat_gated_mlp_p1_dual_path_gated_low_rank_60828c40` status=trained visits=1 val=0.5652 test=0.5270 strategy=dual_path_gated_low_rank program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_dual_path_gated_low_rank_60828c40/model.py
  - `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53` status=trained visits=2 val=0.5114 test=0.5106 strategy=aido_embedding_fusion program=experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53/model.py
- `root_concat_esm2_gene_embedding_gated_mlp` status=trained visits=4 val=0.6520 test=0.6107
  - `root_concat_esm2_gene_embedding_gated_mlp_p1_mixture_of_experts_568d46e0` status=trained visits=3 val=0.6454 test=0.5710 strategy=mixture_of_experts program=experiments/k562_esm2_artifact_search/programs/root_concat_esm2_gene_embedding_gated_mlp_p1_mixture_of_experts_568d46e0/model.py
    - `root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_d110bf14` status=trained visits=2 val=0.6092 test=0.5563 strategy=selective_adapter_finetune program=experiments/k562_esm2_artifact_search/programs/root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_d110bf14/model.py
    - `root_concat_esm2_gene_embedding_gated_mlp_p2_focal_loss_training_strategy_28b52bf3` status=trained visits=2 val=0.6170 test=0.5913 strategy=focal_loss_training_strategy program=experiments/k562_esm2_artifact_search/programs/root_concat_esm2_gene_embedding_gated_mlp_p2_focal_loss_training_strategy_28b52bf3/model.py

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
