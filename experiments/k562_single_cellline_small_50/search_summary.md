# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: no improvement for 10 nodes
- Trained nodes: 13
- Failed nodes: 0
- Best node: `root_concat_esm2_gene_embedding_gated_mlp` val=0.6685 test=0.6137
- Best root: `root_concat_esm2_gene_embedding_gated_mlp` val=0.6685 test=0.6137
- Improvement over best root: 0.0000 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `root_concat_esm2_gene_embedding_gated_mlp` | `data/cell_lines/k562_concat_esm2_gene_embedding` | gated_mlp | 0.6685 | 0.6137 |
| `root_concat_esm2_target_aware_bilinear` | `data/cell_lines/k562_concat_esm2_gene_embedding` | target_aware_bilinear | 0.4103 | 0.3937 |
| `root_concat_gated_mlp` | `data/cell_lines/k562_concat` | gated_mlp | 0.6556 | 0.6020 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `root_concat_esm2_gene_embedding_gated_mlp` | `` | root | root | model_only | cross_entropy | perturbation_gene_or_context |  | 0.5 | gated_mlp | 0.6685 | 0.6137 |
| 0 | `root_concat_esm2_target_aware_bilinear` | `` | root | root | model_only | cross_entropy | perturbation_gene_or_context,target_gene |  | 0.5 | target_aware_bilinear | 0.4103 | 0.3937 |
| 0 | `root_concat_gated_mlp` | `` | root | root | model_only | cross_entropy | none |  | 1.3 | gated_mlp | 0.6556 | 0.6020 |
| 1 | `root_concat_esm2_gene_embedding_gated_mlp_p1_ppi_graph_message_passing_28553456` | `root_concat_esm2_gene_embedding_gated_mlp` | program_node | ppi_graph_message_passing | pipeline_program_node | cross_entropy | gene_graph,perturbation_gene_or_context |  | 1.4 | custom_program | 0.4037 | 0.3838 |
| 2 | `root_concat_gated_mlp_p1_ppi_graph_message_passing_a20f1392` | `root_concat_gated_mlp` | program_node | ppi_graph_message_passing | pipeline_program_node | cross_entropy | gene_graph |  | 2.1 | custom_program | 0.3846 | 0.3704 |
| 3 | `root_concat_esm2_target_aware_bilinear_p2_string_gnn_perturbation_propagator_8c1fa841` | `root_concat_esm2_target_aware_bilinear` | program_node | string_gnn_perturbation_propagator | pipeline_program_node | cross_entropy | gene_graph,perturbation_gene_or_context,target_gene |  | 2.0 | custom_program | 0.3593 | 0.3723 |
| 4 | `root_concat_esm2_gene_embedding_gated_mlp_p2_string_gnn_perturbation_propagator_77f9aa50` | `root_concat_esm2_gene_embedding_gated_mlp_p1_ppi_graph_message_passing_28553456` | program_node | string_gnn_perturbation_propagator | pipeline_program_node | cross_entropy | gene_graph,perturbation_gene_or_context |  | 1.3 | custom_program | 0.3786 | 0.3639 |
| 5 | `root_concat_gated_mlp_p3_target_gene_embedding_bilinear_b5f6cd6b` | `root_concat_gated_mlp_p1_ppi_graph_message_passing_a20f1392` | program_node | target_gene_embedding_bilinear | pipeline_program_node | cross_entropy | perturbation_gene_or_context,target_gene |  | 0.4 | custom_program | 0.4142 | 0.3961 |
| 6 | `root_concat_gated_mlp_p3_target_gene_embedding_bilinear_c0efe558` | `root_concat_gated_mlp_p3_target_gene_embedding_bilinear_b5f6cd6b` | program_node | target_gene_embedding_bilinear | pipeline_program_node | cross_entropy | perturbation_gene_or_context,target_gene |  | 0.5 | custom_program | 0.4142 | 0.4111 |
| 7 | `root_concat_gated_mlp_p4_esm2_gene_projection_c51f3ec3` | `root_concat_gated_mlp_p3_target_gene_embedding_bilinear_c0efe558` | program_node | esm2_gene_projection | pipeline_program_node | cross_entropy | perturbation_gene_or_context,target_gene |  | 0.8 | custom_program | 0.6442 | 0.5890 |
| 8 | `root_concat_gated_mlp_p4_esm2_gene_projection_b3c74ee2` | `root_concat_gated_mlp_p4_esm2_gene_projection_c51f3ec3` | program_node | esm2_gene_projection | pipeline_program_node | cross_entropy | perturbation_gene_or_context,target_gene |  | 0.5 | custom_program | 0.6582 | 0.5915 |
| 9 | `root_concat_gated_mlp_p5_pathway_pooling_encoder_985689b7` | `root_concat_gated_mlp_p4_esm2_gene_projection_b3c74ee2` | program_node | pathway_pooling_encoder | pipeline_program_node | cross_entropy | pathway_membership,perturbation_gene_or_context,target_gene |  | 0.8 | custom_program | 0.5395 | 0.4986 |
| 10 | `root_concat_gated_mlp_p5_pathway_pooling_encoder_6a5480b0` | `root_concat_gated_mlp_p5_pathway_pooling_encoder_985689b7` | program_node | pathway_pooling_encoder | pipeline_program_node | cross_entropy | pathway_membership,perturbation_gene_or_context,target_gene |  | 0.8 | custom_program | 0.5491 | 0.5140 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss |
|---|---:|---|---|---|---|---|
| `root_concat_esm2_gene_embedding_gated_mlp` | true | perturbation_gene_or_context |  |  | `` | cross_entropy |
| `root_concat_esm2_target_aware_bilinear` | true | perturbation_gene_or_context,target_gene |  |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |
| `root_concat_gated_mlp` | false | none |  |  | `` | cross_entropy |
| `root_concat_esm2_gene_embedding_gated_mlp_p1_ppi_graph_message_passing_28553456` | true | gene_graph,perturbation_gene_or_context | string_k562_gene_graph |  | `` | cross_entropy |
| `root_concat_gated_mlp_p1_ppi_graph_message_passing_a20f1392` | true | gene_graph | string_k562_gene_graph |  | `` | cross_entropy |
| `root_concat_esm2_target_aware_bilinear_p2_string_gnn_perturbation_propagator_8c1fa841` | true | gene_graph,perturbation_gene_or_context,target_gene | string_k562_gene_graph |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |
| `root_concat_esm2_gene_embedding_gated_mlp_p2_string_gnn_perturbation_propagator_77f9aa50` | true | gene_graph,perturbation_gene_or_context | string_k562_gene_graph |  | `` | cross_entropy |
| `root_concat_gated_mlp_p3_target_gene_embedding_bilinear_b5f6cd6b` | true | perturbation_gene_or_context,target_gene | esm2_gene_embedding_h5ad,esm2_k562_target_manifest |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |
| `root_concat_gated_mlp_p3_target_gene_embedding_bilinear_c0efe558` | true | perturbation_gene_or_context,target_gene | esm2_gene_embedding_h5ad,esm2_k562_target_manifest |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |
| `root_concat_gated_mlp_p4_esm2_gene_projection_c51f3ec3` | true | perturbation_gene_or_context,target_gene | esm2_gene_embedding_h5ad |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |
| `root_concat_gated_mlp_p4_esm2_gene_projection_b3c74ee2` | true | perturbation_gene_or_context,target_gene | esm2_gene_embedding_h5ad |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |
| `root_concat_gated_mlp_p5_pathway_pooling_encoder_985689b7` | true | pathway_membership,perturbation_gene_or_context,target_gene | pathway_membership_matrix |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |
| `root_concat_gated_mlp_p5_pathway_pooling_encoder_6a5480b0` | true | pathway_membership,perturbation_gene_or_context,target_gene | pathway_membership_matrix |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.6685 |
| 0 | 0.6685 |
| 0 | 0.6685 |
| 1 | 0.6685 |
| 2 | 0.6685 |
| 3 | 0.6685 |
| 4 | 0.6685 |
| 5 | 0.6685 |
| 6 | 0.6685 |
| 7 | 0.6685 |
| 8 | 0.6685 |
| 9 | 0.6685 |
| 10 | 0.6685 |

## Tree

- `root_concat_gated_mlp` status=trained visits=8 val=0.6556 test=0.6020
  - `root_concat_gated_mlp_p1_ppi_graph_message_passing_a20f1392` status=trained visits=7 val=0.3846 test=0.3704 strategy=ppi_graph_message_passing program=experiments/k562_single_cellline_small_50/programs/root_concat_gated_mlp_p1_ppi_graph_message_passing_a20f1392/model.py pipeline=pipeline_program_node artifacts=gene_graph
    - `root_concat_gated_mlp_p3_target_gene_embedding_bilinear_b5f6cd6b` status=trained visits=6 val=0.4142 test=0.3961 strategy=target_gene_embedding_bilinear program=experiments/k562_single_cellline_small_50/programs/root_concat_gated_mlp_p3_target_gene_embedding_bilinear_b5f6cd6b/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context,target_gene
      - `root_concat_gated_mlp_p3_target_gene_embedding_bilinear_c0efe558` status=trained visits=5 val=0.4142 test=0.4111 strategy=target_gene_embedding_bilinear program=experiments/k562_single_cellline_small_50/programs/root_concat_gated_mlp_p3_target_gene_embedding_bilinear_c0efe558/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context,target_gene
        - `root_concat_gated_mlp_p4_esm2_gene_projection_c51f3ec3` status=trained visits=4 val=0.6442 test=0.5890 strategy=esm2_gene_projection program=experiments/k562_single_cellline_small_50/programs/root_concat_gated_mlp_p4_esm2_gene_projection_c51f3ec3/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context,target_gene
          - `root_concat_gated_mlp_p4_esm2_gene_projection_b3c74ee2` status=trained visits=3 val=0.6582 test=0.5915 strategy=esm2_gene_projection program=experiments/k562_single_cellline_small_50/programs/root_concat_gated_mlp_p4_esm2_gene_projection_b3c74ee2/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context,target_gene
            - `root_concat_gated_mlp_p5_pathway_pooling_encoder_985689b7` status=trained visits=2 val=0.5395 test=0.4986 strategy=pathway_pooling_encoder program=experiments/k562_single_cellline_small_50/programs/root_concat_gated_mlp_p5_pathway_pooling_encoder_985689b7/model.py pipeline=pipeline_program_node artifacts=pathway_membership,perturbation_gene_or_context,target_gene
              - `root_concat_gated_mlp_p5_pathway_pooling_encoder_6a5480b0` status=trained visits=1 val=0.5491 test=0.5140 strategy=pathway_pooling_encoder program=experiments/k562_single_cellline_small_50/programs/root_concat_gated_mlp_p5_pathway_pooling_encoder_6a5480b0/model.py pipeline=pipeline_program_node artifacts=pathway_membership,perturbation_gene_or_context,target_gene
- `root_concat_esm2_gene_embedding_gated_mlp` status=trained visits=3 val=0.6685 test=0.6137 artifacts=perturbation_gene_or_context
  - `root_concat_esm2_gene_embedding_gated_mlp_p1_ppi_graph_message_passing_28553456` status=trained visits=2 val=0.4037 test=0.3838 strategy=ppi_graph_message_passing program=experiments/k562_single_cellline_small_50/programs/root_concat_esm2_gene_embedding_gated_mlp_p1_ppi_graph_message_passing_28553456/model.py pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context
    - `root_concat_esm2_gene_embedding_gated_mlp_p2_string_gnn_perturbation_propagator_77f9aa50` status=trained visits=1 val=0.3786 test=0.3639 strategy=string_gnn_perturbation_propagator program=experiments/k562_single_cellline_small_50/programs/root_concat_esm2_gene_embedding_gated_mlp_p2_string_gnn_perturbation_propagator_77f9aa50/model.py pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context
- `root_concat_esm2_target_aware_bilinear` status=trained visits=2 val=0.4103 test=0.3937 artifacts=perturbation_gene_or_context,target_gene
  - `root_concat_esm2_target_aware_bilinear_p2_string_gnn_perturbation_propagator_8c1fa841` status=trained visits=1 val=0.3593 test=0.3723 strategy=string_gnn_perturbation_propagator program=experiments/k562_single_cellline_small_50/programs/root_concat_esm2_target_aware_bilinear_p2_string_gnn_perturbation_propagator_8c1fa841/model.py pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context,target_gene

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
