# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: pending implementation trained
- Trained nodes: 34
- Failed nodes: 0
- Best node: `root_concat_gated_mlp` val=0.6499 test=0.6127
- Best root: `root_concat_gated_mlp` val=0.6499 test=0.6127
- Improvement over best root: 0.0000 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `root_concat_gated_mlp` | `data/cell_lines/k562_concat` | gated_mlp | 0.6499 | 0.6127 |
| `root_concat_low_rank_mlp` | `data/cell_lines/k562_concat` | low_rank_mlp | 0.5878 | 0.5460 |
| `root_concat_mlp` | `data/cell_lines/k562_concat` | mlp | 0.6403 | 0.5818 |
| `root_concat_regularized_mlp` | `data/cell_lines/k562_concat` | mlp | 0.6107 | 0.5753 |
| `root_concat_residual_mlp` | `data/cell_lines/k562_concat` | residual_mlp | 0.6283 | 0.5798 |
| `root_delta_mlp` | `data/cell_lines/k562_delta` | mlp | 0.6074 | 0.5711 |
| `root_onehot_mlp` | `data/cell_lines/k562_onehot` | mlp | 0.6150 | 0.5594 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Agent | Strategy | Data dir | Model | Program | Hidden | Depth | Dropout | Rank | LR | WD | Val | Test |
|---:|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `root_concat_gated_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | gated_mlp | `` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6499 | 0.6127 |
| 0 | `root_concat_low_rank_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | low_rank_mlp | `` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5878 | 0.5460 |
| 0 | `root_concat_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | mlp | `` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6403 | 0.5818 |
| 0 | `root_concat_regularized_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | mlp | `` | 384 | 3 | 0.2 |  | 0.0002 | 0.0005 | 0.6107 | 0.5753 |
| 0 | `root_concat_residual_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | residual_mlp | `` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6283 | 0.5798 |
| 0 | `root_delta_mlp` | `` | root | root | root | `data/cell_lines/k562_delta` | mlp | `` | 256 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6074 | 0.5711 |
| 0 | `root_onehot_mlp` | `` | root | root | root | `data/cell_lines/k562_onehot` | mlp | `` | 256 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6150 | 0.5594 |
| 1 | `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` | `root_concat_gated_mlp` | program_node | codex_program_node_agent | esm2_gene_projection | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.5510 | 0.5189 |
| 2 | `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53` | `root_concat_gated_mlp` | program_node | codex_program_node_agent | aido_embedding_fusion | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6313 | 0.5749 |
| 3 | `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09` | `root_concat_mlp` | program_node | codex_program_node_agent | pathway_pooling_encoder | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.3498 | 0.3477 |
| 4 | `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d` | `root_concat_mlp` | program_node | codex_program_node_agent | cross_attention_gene_perturbation | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.3158 | 0.3158 |
| 5 | `root_concat_residual_mlp_p1_mixture_of_experts_bb507bf4` | `root_concat_residual_mlp` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_bb507bf4/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6270 | 0.5711 |
| 6 | `root_concat_residual_mlp_p1_mixture_of_experts_df7b769f` | `root_concat_residual_mlp_p1_mixture_of_experts_bb507bf4` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_df7b769f/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6359 | 0.5687 |
| 7 | `root_concat_residual_mlp_p1_mixture_of_experts_f4f761d6` | `root_concat_residual_mlp_p1_mixture_of_experts_df7b769f` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_f4f761d6/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6330 | 0.5736 |
| 8 | `root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88` | `root_concat_residual_mlp_p1_mixture_of_experts_f4f761d6` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6376 | 0.5692 |
| 9 | `root_concat_residual_mlp_p1_mixture_of_experts_8464479d` | `root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_8464479d/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6258 | 0.5631 |
| 10 | `root_concat_residual_mlp_p1_mixture_of_experts_a03c1399` | `root_concat_residual_mlp_p1_mixture_of_experts_8464479d` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_a03c1399/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6304 | 0.5706 |
| 11 | `root_concat_residual_mlp_p1_mixture_of_experts_513b5884` | `root_concat_residual_mlp_p1_mixture_of_experts_a03c1399` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_513b5884/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6414 | 0.5693 |
| 12 | `root_concat_residual_mlp_p1_mixture_of_experts_49d84667` | `root_concat_residual_mlp_p1_mixture_of_experts_513b5884` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_49d84667/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6276 | 0.5634 |
| 13 | `root_concat_residual_mlp_p1_mixture_of_experts_a86cd846` | `root_concat_residual_mlp_p1_mixture_of_experts_49d84667` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_a86cd846/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6318 | 0.5680 |
| 14 | `root_concat_residual_mlp_p1_mixture_of_experts_269135c2` | `root_concat_residual_mlp_p1_mixture_of_experts_a86cd846` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_269135c2/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6338 | 0.5751 |
| 15 | `root_concat_residual_mlp_p1_mixture_of_experts_7f846804` | `root_concat_residual_mlp_p1_mixture_of_experts_269135c2` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_7f846804/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6300 | 0.5579 |
| 16 | `root_concat_residual_mlp_p1_mixture_of_experts_214c9d4c` | `root_concat_residual_mlp_p1_mixture_of_experts_7f846804` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_214c9d4c/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6325 | 0.5658 |
| 17 | `root_concat_residual_mlp_p1_mixture_of_experts_be9104eb` | `root_concat_residual_mlp_p1_mixture_of_experts_214c9d4c` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_be9104eb/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6222 | 0.5672 |
| 18 | `root_concat_residual_mlp_p1_mixture_of_experts_5796a973` | `root_concat_residual_mlp_p1_mixture_of_experts_be9104eb` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_5796a973/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6318 | 0.5612 |
| 19 | `root_concat_residual_mlp_p1_mixture_of_experts_060f6a76` | `root_concat_residual_mlp_p1_mixture_of_experts_5796a973` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_060f6a76/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6346 | 0.5799 |
| 20 | `root_concat_residual_mlp_p1_mixture_of_experts_2f0b1109` | `root_concat_residual_mlp_p1_mixture_of_experts_060f6a76` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_2f0b1109/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6298 | 0.5679 |
| 21 | `root_concat_residual_mlp_p1_mixture_of_experts_03075c2a` | `root_concat_residual_mlp_p1_mixture_of_experts_2f0b1109` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_03075c2a/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6388 | 0.5718 |
| 22 | `root_concat_residual_mlp_p1_mixture_of_experts_9d8fdcfd` | `root_concat_residual_mlp_p1_mixture_of_experts_03075c2a` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_9d8fdcfd/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6319 | 0.5621 |
| 23 | `root_concat_residual_mlp_p1_mixture_of_experts_492850ca` | `root_concat_residual_mlp_p1_mixture_of_experts_9d8fdcfd` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_492850ca/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6400 | 0.5733 |
| 24 | `root_concat_residual_mlp_p1_mixture_of_experts_c60eb670` | `root_concat_residual_mlp_p1_mixture_of_experts_492850ca` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_c60eb670/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6305 | 0.5640 |
| 25 | `root_concat_residual_mlp_p1_mixture_of_experts_85dd45d1` | `root_concat_residual_mlp_p1_mixture_of_experts_c60eb670` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_85dd45d1/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6322 | 0.5646 |
| 26 | `root_concat_residual_mlp_p1_mixture_of_experts_223a10cb` | `root_concat_residual_mlp_p1_mixture_of_experts_85dd45d1` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_223a10cb/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6327 | 0.5631 |
| 27 | `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97` | `root_concat_residual_mlp_p1_mixture_of_experts_223a10cb` | program_node | codex_program_node_agent | gated_multimodal_fusion | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6439 | 0.5841 |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.6499 |
| 0 | 0.6499 |
| 0 | 0.6499 |
| 0 | 0.6499 |
| 0 | 0.6499 |
| 0 | 0.6499 |
| 0 | 0.6499 |
| 1 | 0.6499 |
| 2 | 0.6499 |
| 3 | 0.6499 |
| 4 | 0.6499 |
| 5 | 0.6499 |
| 6 | 0.6499 |
| 7 | 0.6499 |
| 8 | 0.6499 |
| 9 | 0.6499 |
| 10 | 0.6499 |
| 11 | 0.6499 |
| 12 | 0.6499 |
| 13 | 0.6499 |
| 14 | 0.6499 |
| 15 | 0.6499 |
| 16 | 0.6499 |
| 17 | 0.6499 |
| 18 | 0.6499 |
| 19 | 0.6499 |
| 20 | 0.6499 |
| 21 | 0.6499 |
| 22 | 0.6499 |
| 23 | 0.6499 |
| 24 | 0.6499 |
| 25 | 0.6499 |
| 26 | 0.6499 |
| 27 | 0.6499 |

## Tree

- `root_concat_gated_mlp` status=trained visits=3 val=0.6499 test=0.6127
  - `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` status=trained visits=2 val=0.5510 test=0.5189 strategy=esm2_gene_projection program=experiments/k562_program_node_agent_search/programs/root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460/model.py
  - `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53` status=trained visits=2 val=0.6313 test=0.5749 strategy=aido_embedding_fusion program=experiments/k562_program_node_agent_search/programs/root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53/model.py
- `root_concat_low_rank_mlp` status=trained visits=1 val=0.5878 test=0.5460
- `root_concat_mlp` status=trained visits=3 val=0.6403 test=0.5818
  - `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09` status=trained visits=2 val=0.3498 test=0.3477 strategy=pathway_pooling_encoder program=experiments/k562_program_node_agent_search/programs/root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09/model.py
  - `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d` status=trained visits=2 val=0.3158 test=0.3158 strategy=cross_attention_gene_perturbation program=experiments/k562_program_node_agent_search/programs/root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d/model.py
- `root_concat_regularized_mlp` status=trained visits=1 val=0.6107 test=0.5753
- `root_concat_residual_mlp` status=trained visits=24 val=0.6283 test=0.5798
  - `root_concat_residual_mlp_p1_mixture_of_experts_bb507bf4` status=trained visits=23 val=0.6270 test=0.5711 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_bb507bf4/model.py
    - `root_concat_residual_mlp_p1_mixture_of_experts_df7b769f` status=trained visits=22 val=0.6359 test=0.5687 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_df7b769f/model.py
      - `root_concat_residual_mlp_p1_mixture_of_experts_f4f761d6` status=trained visits=21 val=0.6330 test=0.5736 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_f4f761d6/model.py
        - `root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88` status=trained visits=20 val=0.6376 test=0.5692 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88/model.py
          - `root_concat_residual_mlp_p1_mixture_of_experts_8464479d` status=trained visits=19 val=0.6258 test=0.5631 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_8464479d/model.py
            - `root_concat_residual_mlp_p1_mixture_of_experts_a03c1399` status=trained visits=18 val=0.6304 test=0.5706 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_a03c1399/model.py
              - `root_concat_residual_mlp_p1_mixture_of_experts_513b5884` status=trained visits=17 val=0.6414 test=0.5693 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_513b5884/model.py
                - `root_concat_residual_mlp_p1_mixture_of_experts_49d84667` status=trained visits=16 val=0.6276 test=0.5634 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_49d84667/model.py
                  - `root_concat_residual_mlp_p1_mixture_of_experts_a86cd846` status=trained visits=15 val=0.6318 test=0.5680 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_a86cd846/model.py
                    - `root_concat_residual_mlp_p1_mixture_of_experts_269135c2` status=trained visits=14 val=0.6338 test=0.5751 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_269135c2/model.py
                      - `root_concat_residual_mlp_p1_mixture_of_experts_7f846804` status=trained visits=13 val=0.6300 test=0.5579 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_7f846804/model.py
                        - `root_concat_residual_mlp_p1_mixture_of_experts_214c9d4c` status=trained visits=12 val=0.6325 test=0.5658 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_214c9d4c/model.py
                          - `root_concat_residual_mlp_p1_mixture_of_experts_be9104eb` status=trained visits=11 val=0.6222 test=0.5672 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_be9104eb/model.py
                            - `root_concat_residual_mlp_p1_mixture_of_experts_5796a973` status=trained visits=10 val=0.6318 test=0.5612 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_5796a973/model.py
                              - `root_concat_residual_mlp_p1_mixture_of_experts_060f6a76` status=trained visits=9 val=0.6346 test=0.5799 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_060f6a76/model.py
                                - `root_concat_residual_mlp_p1_mixture_of_experts_2f0b1109` status=trained visits=8 val=0.6298 test=0.5679 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_2f0b1109/model.py
                                  - `root_concat_residual_mlp_p1_mixture_of_experts_03075c2a` status=trained visits=7 val=0.6388 test=0.5718 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_03075c2a/model.py
                                    - `root_concat_residual_mlp_p1_mixture_of_experts_9d8fdcfd` status=trained visits=6 val=0.6319 test=0.5621 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_9d8fdcfd/model.py
                                      - `root_concat_residual_mlp_p1_mixture_of_experts_492850ca` status=trained visits=5 val=0.6400 test=0.5733 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_492850ca/model.py
                                        - `root_concat_residual_mlp_p1_mixture_of_experts_c60eb670` status=trained visits=4 val=0.6305 test=0.5640 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_c60eb670/model.py
                                          - `root_concat_residual_mlp_p1_mixture_of_experts_85dd45d1` status=trained visits=3 val=0.6322 test=0.5646 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_85dd45d1/model.py
                                            - `root_concat_residual_mlp_p1_mixture_of_experts_223a10cb` status=trained visits=2 val=0.6327 test=0.5631 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_mixture_of_experts_223a10cb/model.py
                                              - `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97` status=trained visits=2 val=0.6439 test=0.5841 strategy=gated_multimodal_fusion program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97/model.py
- `root_delta_mlp` status=trained visits=1 val=0.6074 test=0.5711
- `root_onehot_mlp` status=trained visits=1 val=0.6150 test=0.5594

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next using UCT/PUCT.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.

## Paper-Level Addendum

- Trained nodes: 34
- Planned blueprints implemented on demand: 5
- Level 4/5 trained children: 27
- Selection policy: PUCT
- Pending nodes: 0
- Failed nodes: 0
- Best root: `root_concat_gated_mlp` val=0.6499 test=0.6127
- Best overall: `root_concat_gated_mlp` val=0.6499 test=0.6127
- Improvement over best root: 0.0000
- GPU wall-time lower-bound estimate: 13.1 minutes / 0.217 GPU-hours

See `final_conclusion.md` for missing artifact fallbacks and limitations.
