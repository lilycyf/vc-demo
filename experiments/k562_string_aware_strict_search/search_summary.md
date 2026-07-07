# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, an agent-style proposal step, node execution, and report generation.
The proposal agent may generate config-level children or program-node children. Program nodes carry node-local Python model source and are dynamically loaded during training; data, splits, and metric semantics are unchanged.

- Stop reason: requires artifact acquisition for scfoundation_cell_encoder: scfoundation_cell_embeddings
- Trained nodes: 3
- Failed nodes: 1
- Best node: `root_concat_gated_mlp` val=0.6616 test=0.6123
- Best root: `root_concat_gated_mlp` val=0.6616 test=0.6123
- Improvement over best root: 0.0000 validation Macro-F1

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `root_concat_esm2_gene_embedding_gated_mlp` | `data/cell_lines/k562_concat_esm2_gene_embedding` | gated_mlp | 0.6512 | 0.6045 |
| `root_concat_esm2_target_aware_bilinear` | `data/cell_lines/k562_concat_esm2_gene_embedding` | target_aware_bilinear | 0.4156 | 0.4073 |
| `root_concat_gated_mlp` | `data/cell_lines/k562_concat` | gated_mlp | 0.6616 | 0.6123 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `root_concat_esm2_gene_embedding_gated_mlp` | `` | root | root | model_only | cross_entropy | perturbation_gene_or_context |  | 1.1 | gated_mlp | 0.6512 | 0.6045 |
| 0 | `root_concat_esm2_target_aware_bilinear` | `` | root | root | model_only | cross_entropy | perturbation_gene_or_context,target_gene |  | 2.0 | target_aware_bilinear | 0.4156 | 0.4073 |
| 0 | `root_concat_gated_mlp` | `` | root | root | model_only | cross_entropy | none |  | 3.1 | gated_mlp | 0.6616 | 0.6123 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss |
|---|---:|---|---|---|---|---|
| `root_concat_esm2_gene_embedding_gated_mlp` | true | perturbation_gene_or_context |  |  | `` | cross_entropy |
| `root_concat_esm2_target_aware_bilinear` | true | perturbation_gene_or_context,target_gene |  |  | `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` | cross_entropy |
| `root_concat_gated_mlp` | false | none |  |  | `` | cross_entropy |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.6512 |
| 0 | 0.6512 |
| 0 | 0.6616 |

## Tree

- `root_concat_gated_mlp` status=trained visits=1 val=0.6616 test=0.6123
  - `root_concat_gated_mlp_p1_scfoundation_cell_encoder_c117ca5e` status=requires_artifact_acquisition visits=0 strategy=scfoundation_cell_encoder program=experiments/k562_string_aware_strict_search/programs/root_concat_gated_mlp_p1_scfoundation_cell_encoder_c117ca5e/model.py pipeline=pipeline_program_node
- `root_concat_esm2_gene_embedding_gated_mlp` status=trained visits=1 val=0.6512 test=0.6045 artifacts=perturbation_gene_or_context
- `root_concat_esm2_target_aware_bilinear` status=trained visits=1 val=0.4156 test=0.4073 artifacts=perturbation_gene_or_context,target_gene

## Failures

| Node | Parent | Error |
|---|---|---|
| `root_concat_gated_mlp_p1_scfoundation_cell_encoder_c117ca5e` | `root_concat_gated_mlp` | requires_artifact_acquisition |

## Reproducibility Notes

- One node means one complete trainable candidate pipeline: data representation, model type, model hyperparameters, optimizer settings, and training run.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
