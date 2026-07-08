# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: no improvement for 12 nodes
- Trained nodes: 20
- Failed nodes: 0
- Best node: `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` val=0.4977 test=0.5260
- Best root: `official_k562_native_public_best_reimplementation` val=0.4637 test=0.4883
- Improvement over best root: 0.0339 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `data/cell_lines/official_k562_cls` | custom_program | 0.4637 | 0.4883 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4125 | 0.4529 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4155 | 0.4613 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_native_public_best_reimplementation` | `` | root | root | native_train | program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.7 | custom_program | 0.4637 | 0.4883 |
| 0 | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 35.0 | external_static_node | 0.3333 | 0.3333 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 6.9 | gated_mlp | 0.4125 | 0.4529 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 5.3 | gated_mlp | 0.4155 | 0.4613 |
| 1 | `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | `official_k562_native_public_best_reimplementation` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.8 | custom_program | 0.4763 | 0.5231 |
| 2 | `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 20.1 | custom_program | 0.4640 | 0.5391 |
| 3 | `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 19.7 | custom_program | 0.4805 | 0.5370 |
| 4 | `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.1 | custom_program | 0.4977 | 0.5260 |
| 5 | `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.9 | custom_program | 0.4724 | 0.5029 |
| 6 | `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 18.4 | custom_program | 0.4764 | 0.5103 |
| 7 | `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.5 | custom_program | 0.4636 | 0.5228 |
| 8 | `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.4 | custom_program | 0.4772 | 0.5104 |
| 9 | `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.9 | custom_program | 0.4762 | 0.5156 |
| 10 | `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 18.9 | custom_program | 0.4561 | 0.4759 |
| 11 | `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.1 | custom_program | 0.4508 | 0.5167 |
| 12 | `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.3 | custom_program | 0.4788 | 0.5034 |
| 13 | `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.0 | custom_program | 0.4839 | 0.5299 |
| 14 | `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 18.0 | custom_program | 0.4858 | 0.5126 |
| 15 | `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.6 | custom_program | 0.4565 | 0.5088 |
| 16 | `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` | `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 18.5 | custom_program | 0.4458 | 0.4796 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_native_public_best_reimplementation` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN,public_node_code |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4637 |
| 0 | 0.4637 |
| 0 | 0.4637 |
| 0 | 0.4637 |
| 1 | 0.4763 |
| 2 | 0.4763 |
| 3 | 0.4805 |
| 4 | 0.4977 |
| 5 | 0.4977 |
| 6 | 0.4977 |
| 7 | 0.4977 |
| 8 | 0.4977 |
| 9 | 0.4977 |
| 10 | 0.4977 |
| 11 | 0.4977 |
| 12 | 0.4977 |
| 13 | 0.4977 |
| 14 | 0.4977 |
| 15 | 0.4977 |
| 16 | 0.4977 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=1 val=0.4125 test=0.4529 backend=native_train artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=1 val=0.4155 test=0.4613 backend=native_train artifacts=perturbation_gene_or_context
- `official_k562_public_best_node2_1_1_1_1_1_smoke` status=trained visits=1 val=0.3333 test=0.3333 backend=external_static_node
- `official_k562_native_public_best_reimplementation` status=trained visits=17 val=0.4637 test=0.4883 backend=native_train artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` status=trained visits=16 val=0.4763 test=0.5231 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_4fc53048/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
    - `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` status=trained visits=15 val=0.4640 test=0.5391 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_f60cc825/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
      - `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` status=trained visits=14 val=0.4805 test=0.5370 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
        - `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` status=trained visits=13 val=0.4977 test=0.5260 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_07f618d0/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
          - `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` status=trained visits=12 val=0.4724 test=0.5029 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_b620177f/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
            - `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` status=trained visits=11 val=0.4764 test=0.5103 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_892db4d8/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
              - `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` status=trained visits=10 val=0.4636 test=0.5228 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                - `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` status=trained visits=9 val=0.4772 test=0.5104 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_87202fb7/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                  - `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` status=trained visits=8 val=0.4762 test=0.5156 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_9c0544db/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                    - `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` status=trained visits=7 val=0.4561 test=0.4759 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_d267f027/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                      - `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` status=trained visits=6 val=0.4508 test=0.5167 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_3db8e977/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                        - `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` status=trained visits=5 val=0.4788 test=0.5034 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_ab07539f/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                          - `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` status=trained visits=4 val=0.4839 test=0.5299 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                            - `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` status=trained visits=3 val=0.4858 test=0.5126 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                              - `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` status=trained visits=2 val=0.4565 test=0.5088 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_495dc133/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                                - `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` status=trained visits=1 val=0.4458 test=0.4796 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
