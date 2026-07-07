# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: budget exhausted
- Trained nodes: 30
- Failed nodes: 0
- Best node: `root_concat_gated_mlp` val=0.6595 test=0.6149
- Best root: `root_concat_gated_mlp` val=0.6595 test=0.6149
- Improvement over best root: 0.0000 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `root_concat_gated_mlp` | `data/cell_lines/k562_concat` | gated_mlp | 0.6595 | 0.6149 |
| `root_concat_low_rank_mlp` | `data/cell_lines/k562_concat` | low_rank_mlp | 0.5406 | 0.5050 |
| `root_concat_mlp` | `data/cell_lines/k562_concat` | mlp | 0.6516 | 0.5932 |
| `root_concat_regularized_mlp` | `data/cell_lines/k562_concat` | mlp | 0.5937 | 0.5418 |
| `root_concat_residual_mlp` | `data/cell_lines/k562_concat` | residual_mlp | 0.6244 | 0.5599 |
| `root_delta_mlp` | `data/cell_lines/k562_delta` | mlp | 0.6138 | 0.5770 |
| `root_onehot_mlp` | `data/cell_lines/k562_onehot` | mlp | 0.6059 | 0.5532 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Agent | Strategy | Data dir | Model | Program | Hidden | Depth | Dropout | Rank | LR | WD | Val | Test |
|---:|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | `root_concat_gated_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | gated_mlp | `` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6595 | 0.6149 |
| 0 | `root_concat_low_rank_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | low_rank_mlp | `` | 384 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5406 | 0.5050 |
| 0 | `root_concat_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | mlp | `` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6516 | 0.5932 |
| 0 | `root_concat_regularized_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | mlp | `` | 384 | 3 | 0.2 |  | 0.0002 | 0.0005 | 0.5937 | 0.5418 |
| 0 | `root_concat_residual_mlp` | `` | root | root | root | `data/cell_lines/k562_concat` | residual_mlp | `` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6244 | 0.5599 |
| 0 | `root_delta_mlp` | `` | root | root | root | `data/cell_lines/k562_delta` | mlp | `` | 256 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6138 | 0.5770 |
| 0 | `root_onehot_mlp` | `` | root | root | root | `data/cell_lines/k562_onehot` | mlp | `` | 256 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6059 | 0.5532 |
| 1 | `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` | `root_concat_gated_mlp` | program_node | codex_program_node_agent | esm2_gene_projection | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.5562 | 0.5218 |
| 2 | `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53` | `root_concat_gated_mlp` | program_node | codex_program_node_agent | aido_embedding_fusion | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.6192 | 0.5914 |
| 3 | `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09` | `root_concat_mlp` | program_node | codex_program_node_agent | pathway_pooling_encoder | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.5210 | 0.4797 |
| 4 | `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d` | `root_concat_mlp` | program_node | codex_program_node_agent | cross_attention_gene_perturbation | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d/model.py` | 384 | 2 | 0.1 |  | 0.0003 | 0.0001 | 0.3158 | 0.3158 |
| 5 | `root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d` | `root_concat_residual_mlp` | program_node | codex_program_node_agent | uncertainty_calibrated_head | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.6559 | 0.5907 |
| 6 | `root_concat_residual_mlp_p2_selective_adapter_finetune_9ad96574` | `root_concat_residual_mlp` | program_node | codex_program_node_agent | selective_adapter_finetune | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p2_selective_adapter_finetune_9ad96574/model.py` | 384 | 3 | 0.1 |  | 0.0003 | 0.0001 | 0.3582 | 0.3716 |
| 7 | `root_delta_mlp_p1_dual_path_gated_low_rank_97d1cb9e` | `root_delta_mlp` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_97d1cb9e/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5593 | 0.5163 |
| 8 | `root_onehot_mlp_p1_dual_path_gated_low_rank_ac428951` | `root_onehot_mlp` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_onehot` | custom_program | `experiments/k562_program_node_agent_search/programs/root_onehot_mlp_p1_dual_path_gated_low_rank_ac428951/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5729 | 0.5231 |
| 9 | `root_concat_regularized_mlp_p1_mixture_of_experts_47d46756` | `root_concat_regularized_mlp` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_regularized_mlp_p1_mixture_of_experts_47d46756/model.py` | 384 | 3 | 0.2 |  | 0.0002 | 0.0001 | 0.6279 | 0.5721 |
| 10 | `root_concat_regularized_mlp_p1_mixture_of_experts_46004776` | `root_concat_regularized_mlp_p1_mixture_of_experts_47d46756` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_regularized_mlp_p1_mixture_of_experts_46004776/model.py` | 384 | 3 | 0.2 |  | 0.0002 | 0.0001 | 0.6259 | 0.5713 |
| 11 | `root_concat_regularized_mlp_p1_mixture_of_experts_51750e6b` | `root_concat_regularized_mlp_p1_mixture_of_experts_46004776` | program_node | codex_program_node_agent | mixture_of_experts | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_regularized_mlp_p1_mixture_of_experts_51750e6b/model.py` | 384 | 3 | 0.2 |  | 0.0002 | 0.0001 | 0.6244 | 0.5589 |
| 12 | `root_concat_regularized_mlp_p1_dual_path_gated_low_rank_1fb9482f` | `root_concat_regularized_mlp_p1_mixture_of_experts_51750e6b` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_concat` | custom_program | `experiments/k562_program_node_agent_search/programs/root_concat_regularized_mlp_p1_dual_path_gated_low_rank_1fb9482f/model.py` | 384 | 3 | 0.2 | 64 | 0.0002 | 0.0001 | 0.5213 | 0.4888 |
| 13 | `root_onehot_mlp_p1_dual_path_gated_low_rank_f0eebcdd` | `root_onehot_mlp_p1_dual_path_gated_low_rank_ac428951` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_onehot` | custom_program | `experiments/k562_program_node_agent_search/programs/root_onehot_mlp_p1_dual_path_gated_low_rank_f0eebcdd/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5515 | 0.5235 |
| 14 | `root_delta_mlp_p1_dual_path_gated_low_rank_cf0d972b` | `root_delta_mlp_p1_dual_path_gated_low_rank_97d1cb9e` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_cf0d972b/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5754 | 0.5090 |
| 15 | `root_delta_mlp_p1_dual_path_gated_low_rank_1ee05fa7` | `root_delta_mlp_p1_dual_path_gated_low_rank_cf0d972b` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_1ee05fa7/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5790 | 0.5327 |
| 16 | `root_delta_mlp_p1_dual_path_gated_low_rank_1dc0b3cd` | `root_delta_mlp_p1_dual_path_gated_low_rank_1ee05fa7` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_1dc0b3cd/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5762 | 0.5394 |
| 17 | `root_delta_mlp_p1_dual_path_gated_low_rank_18592b46` | `root_delta_mlp_p1_dual_path_gated_low_rank_1dc0b3cd` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_18592b46/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5589 | 0.5213 |
| 18 | `root_delta_mlp_p1_dual_path_gated_low_rank_0d01a52a` | `root_delta_mlp_p1_dual_path_gated_low_rank_18592b46` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_0d01a52a/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5666 | 0.5172 |
| 19 | `root_delta_mlp_p1_dual_path_gated_low_rank_418bc1b4` | `root_delta_mlp_p1_dual_path_gated_low_rank_0d01a52a` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_418bc1b4/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5646 | 0.5220 |
| 20 | `root_delta_mlp_p1_dual_path_gated_low_rank_d4e4ae1d` | `root_delta_mlp_p1_dual_path_gated_low_rank_418bc1b4` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_d4e4ae1d/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5612 | 0.5161 |
| 21 | `root_delta_mlp_p1_dual_path_gated_low_rank_f91ae8ef` | `root_delta_mlp_p1_dual_path_gated_low_rank_d4e4ae1d` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_f91ae8ef/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5773 | 0.5374 |
| 22 | `root_delta_mlp_p1_dual_path_gated_low_rank_cd7b4d1f` | `root_delta_mlp_p1_dual_path_gated_low_rank_f91ae8ef` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_cd7b4d1f/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5665 | 0.5248 |
| 23 | `root_delta_mlp_p1_dual_path_gated_low_rank_b25d1ab9` | `root_delta_mlp_p1_dual_path_gated_low_rank_cd7b4d1f` | program_node | codex_program_node_agent | dual_path_gated_low_rank | `data/cell_lines/k562_delta` | custom_program | `experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_b25d1ab9/model.py` | 256 | 2 | 0.1 | 64 | 0.0003 | 0.0001 | 0.5673 | 0.5250 |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.6595 |
| 0 | 0.6595 |
| 0 | 0.6595 |
| 0 | 0.6595 |
| 0 | 0.6595 |
| 0 | 0.6595 |
| 0 | 0.6595 |
| 1 | 0.6595 |
| 2 | 0.6595 |
| 3 | 0.6595 |
| 4 | 0.6595 |
| 5 | 0.6595 |
| 6 | 0.6595 |
| 7 | 0.6595 |
| 8 | 0.6595 |
| 9 | 0.6595 |
| 10 | 0.6595 |
| 11 | 0.6595 |
| 12 | 0.6595 |
| 13 | 0.6595 |
| 14 | 0.6595 |
| 15 | 0.6595 |
| 16 | 0.6595 |
| 17 | 0.6595 |
| 18 | 0.6595 |
| 19 | 0.6595 |
| 20 | 0.6595 |
| 21 | 0.6595 |
| 22 | 0.6595 |
| 23 | 0.6595 |

## Tree

- `root_concat_gated_mlp` status=trained visits=3 val=0.6595 test=0.6149
  - `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` status=trained visits=2 val=0.5562 test=0.5218 strategy=esm2_gene_projection program=experiments/k562_program_node_agent_search/programs/root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460/model.py
  - `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53` status=trained visits=2 val=0.6192 test=0.5914 strategy=aido_embedding_fusion program=experiments/k562_program_node_agent_search/programs/root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53/model.py
- `root_concat_low_rank_mlp` status=trained visits=1 val=0.5406 test=0.5050
- `root_concat_mlp` status=trained visits=3 val=0.6516 test=0.5932
  - `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09` status=trained visits=2 val=0.5210 test=0.4797 strategy=pathway_pooling_encoder program=experiments/k562_program_node_agent_search/programs/root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09/model.py
  - `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d` status=trained visits=2 val=0.3158 test=0.3158 strategy=cross_attention_gene_perturbation program=experiments/k562_program_node_agent_search/programs/root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d/model.py
- `root_concat_regularized_mlp` status=trained visits=5 val=0.5937 test=0.5418
  - `root_concat_regularized_mlp_p1_mixture_of_experts_47d46756` status=trained visits=4 val=0.6279 test=0.5721 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_regularized_mlp_p1_mixture_of_experts_47d46756/model.py
    - `root_concat_regularized_mlp_p1_mixture_of_experts_46004776` status=trained visits=3 val=0.6259 test=0.5713 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_regularized_mlp_p1_mixture_of_experts_46004776/model.py
      - `root_concat_regularized_mlp_p1_mixture_of_experts_51750e6b` status=trained visits=2 val=0.6244 test=0.5589 strategy=mixture_of_experts program=experiments/k562_program_node_agent_search/programs/root_concat_regularized_mlp_p1_mixture_of_experts_51750e6b/model.py
        - `root_concat_regularized_mlp_p1_dual_path_gated_low_rank_1fb9482f` status=trained visits=1 val=0.5213 test=0.4888 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_concat_regularized_mlp_p1_dual_path_gated_low_rank_1fb9482f/model.py
- `root_concat_residual_mlp` status=trained visits=3 val=0.6244 test=0.5599
  - `root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d` status=trained visits=2 val=0.6559 test=0.5907 strategy=uncertainty_calibrated_head program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d/model.py
  - `root_concat_residual_mlp_p2_selective_adapter_finetune_9ad96574` status=trained visits=2 val=0.3582 test=0.3716 strategy=selective_adapter_finetune program=experiments/k562_program_node_agent_search/programs/root_concat_residual_mlp_p2_selective_adapter_finetune_9ad96574/model.py
- `root_delta_mlp` status=trained visits=12 val=0.6138 test=0.5770
  - `root_delta_mlp_p1_dual_path_gated_low_rank_97d1cb9e` status=trained visits=11 val=0.5593 test=0.5163 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_97d1cb9e/model.py
    - `root_delta_mlp_p1_dual_path_gated_low_rank_cf0d972b` status=trained visits=10 val=0.5754 test=0.5090 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_cf0d972b/model.py
      - `root_delta_mlp_p1_dual_path_gated_low_rank_1ee05fa7` status=trained visits=9 val=0.5790 test=0.5327 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_1ee05fa7/model.py
        - `root_delta_mlp_p1_dual_path_gated_low_rank_1dc0b3cd` status=trained visits=8 val=0.5762 test=0.5394 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_1dc0b3cd/model.py
          - `root_delta_mlp_p1_dual_path_gated_low_rank_18592b46` status=trained visits=7 val=0.5589 test=0.5213 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_18592b46/model.py
            - `root_delta_mlp_p1_dual_path_gated_low_rank_0d01a52a` status=trained visits=6 val=0.5666 test=0.5172 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_0d01a52a/model.py
              - `root_delta_mlp_p1_dual_path_gated_low_rank_418bc1b4` status=trained visits=5 val=0.5646 test=0.5220 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_418bc1b4/model.py
                - `root_delta_mlp_p1_dual_path_gated_low_rank_d4e4ae1d` status=trained visits=4 val=0.5612 test=0.5161 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_d4e4ae1d/model.py
                  - `root_delta_mlp_p1_dual_path_gated_low_rank_f91ae8ef` status=trained visits=3 val=0.5773 test=0.5374 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_f91ae8ef/model.py
                    - `root_delta_mlp_p1_dual_path_gated_low_rank_cd7b4d1f` status=trained visits=2 val=0.5665 test=0.5248 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_cd7b4d1f/model.py
                      - `root_delta_mlp_p1_dual_path_gated_low_rank_b25d1ab9` status=trained visits=1 val=0.5673 test=0.5250 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_delta_mlp_p1_dual_path_gated_low_rank_b25d1ab9/model.py
- `root_onehot_mlp` status=trained visits=3 val=0.6059 test=0.5532
  - `root_onehot_mlp_p1_dual_path_gated_low_rank_ac428951` status=trained visits=2 val=0.5729 test=0.5231 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_onehot_mlp_p1_dual_path_gated_low_rank_ac428951/model.py
    - `root_onehot_mlp_p1_dual_path_gated_low_rank_f0eebcdd` status=trained visits=1 val=0.5515 test=0.5235 strategy=dual_path_gated_low_rank program=experiments/k562_program_node_agent_search/programs/root_onehot_mlp_p1_dual_path_gated_low_rank_f0eebcdd/model.py

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.

## Paper-Aligned UCT Addendum

- Selection policy: UCT
- Exploration: sqrt(2) = 1.4142135623730951
- PUCT used: no
- Trained nodes: 30
- Planned blueprints implemented on demand: 6
- Level 4/5 trained children: 8
- Failed nodes: 0
- Pending nodes: 0
- Best root: `root_concat_gated_mlp` val=0.6595 test=0.6149
- Best overall: `root_concat_gated_mlp` val=0.6595 test=0.6149
- Improvement over best root: 0.0000

See `final_conclusion.md` for missing-artifact fallbacks and paper-alignment notes.
