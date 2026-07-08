# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: no improvement for 12 nodes
- Trained nodes: 21
- Failed nodes: 0
- Best node: `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` val=0.4961 test=0.5224
- Best root: `official_k562_native_public_best_reimplementation` val=0.4640 test=0.4924
- Improvement over best root: 0.0321 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `data/cell_lines/official_k562_cls` | custom_program | 0.4640 | 0.4924 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4129 | 0.4526 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4200 | 0.4644 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_native_public_best_reimplementation` | `` | root | root | native_train | program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 18.2 | custom_program | 0.4640 | 0.4924 |
| 0 | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 35.9 | external_static_node | 0.3333 | 0.3333 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 5.6 | gated_mlp | 0.4129 | 0.4526 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 7.8 | gated_mlp | 0.4200 | 0.4644 |
| 1 | `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | `official_k562_native_public_best_reimplementation` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 18.2 | custom_program | 0.4600 | 0.5082 |
| 2 | `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 18.2 | custom_program | 0.4644 | 0.5318 |
| 3 | `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.1 | custom_program | 0.4664 | 0.5300 |
| 4 | `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.7 | custom_program | 0.4926 | 0.5270 |
| 5 | `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 15.9 | custom_program | 0.4961 | 0.5224 |
| 6 | `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.6 | custom_program | 0.4812 | 0.5324 |
| 7 | `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.9 | custom_program | 0.4813 | 0.5307 |
| 8 | `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.0 | custom_program | 0.4940 | 0.5258 |
| 9 | `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 18.2 | custom_program | 0.4786 | 0.5297 |
| 10 | `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.2 | custom_program | 0.4878 | 0.5120 |
| 11 | `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.3 | custom_program | 0.4667 | 0.5070 |
| 12 | `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.2 | custom_program | 0.4666 | 0.5383 |
| 13 | `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.3 | custom_program | 0.4773 | 0.5204 |
| 14 | `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 15.9 | custom_program | 0.4648 | 0.5175 |
| 15 | `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.3 | custom_program | 0.4905 | 0.5189 |
| 16 | `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` | `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.8 | custom_program | 0.4960 | 0.5324 |
| 17 | `official_k562_native_p1_official_native_public_best_reimplementation_e9ade575` | `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.9 | custom_program | 0.4857 | 0.5383 |

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
| `official_k562_native_p1_official_native_public_best_reimplementation_e9ade575` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4640 |
| 0 | 0.4640 |
| 0 | 0.4640 |
| 0 | 0.4640 |
| 1 | 0.4640 |
| 2 | 0.4644 |
| 3 | 0.4664 |
| 4 | 0.4926 |
| 5 | 0.4961 |
| 6 | 0.4961 |
| 7 | 0.4961 |
| 8 | 0.4961 |
| 9 | 0.4961 |
| 10 | 0.4961 |
| 11 | 0.4961 |
| 12 | 0.4961 |
| 13 | 0.4961 |
| 14 | 0.4961 |
| 15 | 0.4961 |
| 16 | 0.4961 |
| 17 | 0.4961 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=1 val=0.4129 test=0.4526 backend=native_train artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=1 val=0.4200 test=0.4644 backend=native_train artifacts=perturbation_gene_or_context
- `official_k562_public_best_node2_1_1_1_1_1_smoke` status=trained visits=1 val=0.3333 test=0.3333 backend=external_static_node
- `official_k562_native_public_best_reimplementation` status=trained visits=18 val=0.4640 test=0.4924 backend=native_train artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_native_p1_official_native_public_best_reimplementation_4fc53048` status=trained visits=17 val=0.4600 test=0.5082 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_4fc53048/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
    - `official_k562_native_p1_official_native_public_best_reimplementation_f60cc825` status=trained visits=16 val=0.4644 test=0.5318 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_f60cc825/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
      - `official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10` status=trained visits=15 val=0.4664 test=0.5300 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_e49b7b10/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
        - `official_k562_native_p1_official_native_public_best_reimplementation_07f618d0` status=trained visits=14 val=0.4926 test=0.5270 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_07f618d0/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
          - `official_k562_native_p1_official_native_public_best_reimplementation_b620177f` status=trained visits=13 val=0.4961 test=0.5224 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_b620177f/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
            - `official_k562_native_p1_official_native_public_best_reimplementation_892db4d8` status=trained visits=12 val=0.4812 test=0.5324 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_892db4d8/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
              - `official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d` status=trained visits=11 val=0.4813 test=0.5307 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_9a556b9d/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                - `official_k562_native_p1_official_native_public_best_reimplementation_87202fb7` status=trained visits=10 val=0.4940 test=0.5258 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_87202fb7/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                  - `official_k562_native_p1_official_native_public_best_reimplementation_9c0544db` status=trained visits=9 val=0.4786 test=0.5297 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_9c0544db/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                    - `official_k562_native_p1_official_native_public_best_reimplementation_d267f027` status=trained visits=8 val=0.4878 test=0.5120 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_d267f027/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                      - `official_k562_native_p1_official_native_public_best_reimplementation_3db8e977` status=trained visits=7 val=0.4667 test=0.5070 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_3db8e977/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                        - `official_k562_native_p1_official_native_public_best_reimplementation_ab07539f` status=trained visits=6 val=0.4666 test=0.5383 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_ab07539f/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                          - `official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b` status=trained visits=5 val=0.4773 test=0.5204 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_ff68f01b/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                            - `official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20` status=trained visits=4 val=0.4648 test=0.5175 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_7d8c4b20/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                              - `official_k562_native_p1_official_native_public_best_reimplementation_495dc133` status=trained visits=3 val=0.4905 test=0.5189 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_495dc133/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                                - `official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af` status=trained visits=2 val=0.4960 test=0.5324 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_63b5a7af/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
                                  - `official_k562_native_p1_official_native_public_best_reimplementation_e9ade575` status=trained visits=1 val=0.4857 test=0.5383 strategy=official_native_public_best_reimplementation program=experiments/official_k562_gap_closing_small_50/programs/official_k562_native_p1_official_native_public_best_reimplementation_e9ade575/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
