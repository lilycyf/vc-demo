# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: pending implementation limit reached (8)
- Trained nodes: 8
- Failed nodes: 0
- Best node: `official_k562_native_p1_official_aido_string_fusion_66a588f9` val=0.4885 test=0.5183
- Best root: `official_k562_native_public_best_reimplementation` val=0.4679 test=0.5256
- Improvement over best root: 0.0205 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `data/cell_lines/official_k562_cls` | custom_program | 0.4679 | 0.5256 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3333 | 0.3333 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4108 | 0.4533 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4128 | 0.4630 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_native_public_best_reimplementation` | `` | root | root | native_train | program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 16.8 | custom_program | 0.4679 | 0.5256 |
| 0 | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 36.7 | external_static_node | 0.3333 | 0.3333 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 6.0 | gated_mlp | 0.4108 | 0.4533 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 5.8 | gated_mlp | 0.4128 | 0.4630 |
| 1 | `official_k562_native_p1_official_aido_string_fusion_66a588f9` | `official_k562_native_public_best_reimplementation` | program_node | official_aido_string_fusion | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 17.4 | custom_program | 0.4885 | 0.5183 |
| 2 | `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | `official_k562_native_p1_official_aido_string_fusion_66a588f9` | program_node | official_string_gnn_attention | native_train | pipeline_program_node | weighted_cross_entropy | gene_graph,perturbation_gene_or_context |  | 16.7 | custom_program | 0.4414 | 0.5046 |
| 3 | `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | program_node | official_aido_lora_adapter | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,perturbation_gene_or_context |  | 10.3 | custom_program | 0.4741 | 0.5233 |
| 4 | `official_k562_native_p1_official_target_gene_head_477d0ebb` | `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 12.1 | custom_program | 0.4552 | 0.5265 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_native_public_best_reimplementation` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN,public_node_code |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_aido_string_fusion_66a588f9` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_string_gnn_attention_7ec267ae` | true | gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_aido_lora_adapter_d757c78c` | true | AIDO.Cell-100M,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_aido_cell_100m_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_target_gene_head_477d0ebb` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy | None |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4679 |
| 0 | 0.4679 |
| 0 | 0.4679 |
| 0 | 0.4679 |
| 1 | 0.4885 |
| 2 | 0.4885 |
| 3 | 0.4885 |
| 4 | 0.4885 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=1 val=0.4108 test=0.4533 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` status=needs_implementation visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` status=needs_implementation visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500/model.py pipeline=pipeline_program_node
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=1 val=0.4128 test=0.4630 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` status=needs_implementation visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` status=needs_implementation visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` status=needs_implementation visits=0 strategy=official_string_neighborhood_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1/model.py pipeline=pipeline_program_node
- `official_k562_public_best_node2_1_1_1_1_1_smoke` status=trained visits=1 val=0.3333 test=0.3333 backend=external_static_node
- `official_k562_native_public_best_reimplementation` status=trained visits=5 val=0.4679 test=0.5256 backend=native_train artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_native_p1_official_aido_string_fusion_66a588f9` status=trained visits=4 val=0.4885 test=0.5183 strategy=official_aido_string_fusion program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_aido_string_fusion_66a588f9/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
    - `official_k562_native_p1_official_string_gnn_attention_7ec267ae` status=trained visits=3 val=0.4414 test=0.5046 strategy=official_string_gnn_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_string_gnn_attention_7ec267ae/model.py backend=native_train pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context
      - `official_k562_native_p1_official_aido_lora_adapter_d757c78c` status=trained visits=2 val=0.4741 test=0.5233 strategy=official_aido_lora_adapter program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_aido_lora_adapter_d757c78c/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,perturbation_gene_or_context
        - `official_k562_native_p1_official_target_gene_head_477d0ebb` status=trained visits=1 val=0.4552 test=0.5265 strategy=official_target_gene_head program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_target_gene_head_477d0ebb/model.py backend=native_train pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
          - `official_k562_native_p1_official_pathway_pooling_reactome_b5af6810` status=needs_implementation visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p1_official_pathway_pooling_reactome_b5af6810/model.py pipeline=pipeline_program_node
          - `official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f` status=needs_implementation visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p2_official_aido_string_cross_attention_e44c7c9f/model.py pipeline=pipeline_program_node
          - `official_k562_native_p3_official_string_neighborhood_attention_0376ea72` status=needs_implementation visits=0 strategy=official_string_neighborhood_attention program=experiments/official_k562_scientific_policy_run_50/programs/official_k562_native_p3_official_string_neighborhood_attention_0376ea72/model.py pipeline=pipeline_program_node

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
