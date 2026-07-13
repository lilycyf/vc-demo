# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, pruned, blocked for artifact acquisition, selected for training, pending implementation, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: pending implementation limit reached (1)
- Proposal-like nodes: 6
- Trained nodes: 2
- Pruned proposals: 3
- Blocked/acquisition nodes: 0
- Pending implementation nodes: 1
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 0
- Best node: `official_k562_root_aido_gnn_embedding_mlp` val=0.3883 test=0.3996
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.3883 test=0.3996
- Improvement over best root: 0.0000 validation Macro-F1

## Automatic Implementation Loop

| Metric | Count |
|---|---:|
| Auto implementation records | 1 |
| Native smoke passed | 0 |
| Repair/implementation log rows | 1 |
| Repair failures | 0 |
| Requires external Codex | 2 |
| Blocked missing artifact | 0 |
| Trained and backpropagated | 0 |

| Item status | Count |
|---|---:|
| `requires_external_codex` | 1 |

| Decision event | Count |
|---|---:|
| `implementation_selected` | 1 |
| `requires_external_codex` | 1 |

- Implementation agent report: `experiments/official_k562_self_transfer_loop_64x16/implementation_agent_report.json`
- Repair log: `experiments/official_k562_self_transfer_loop_64x16/repair_log.jsonl`
- Agent decision trace: `experiments/official_k562_self_transfer_loop_64x16/agent_decision_trace.jsonl`

## Search State Counts

| Status | Count |
|---|---:|
| `needs_implementation` | 1 |
| `pruned_not_selected` | 3 |
| `trained` | 2 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3844 | 0.3975 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3883 | 0.3996 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 41.1 | gated_mlp | 0.3844 | 0.3975 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 42.2 | gated_mlp | 0.3883 | 0.3996 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.3844 |
| 0 | 0.3883 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=1 val=0.3844 test=0.3975 backend=native_train artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=1 val=0.3883 test=0.3996 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_self_transfer_loop_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_self_transfer_loop_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_self_transfer_loop_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` status=needs_implementation visits=0 strategy=official_target_gene_head program=experiments/official_k562_self_transfer_loop_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042/model.py pipeline=pipeline_program_node

## Reproducibility Notes

- In paper-aligned mode, one node means one candidate program state, not necessarily one completed training run.
- `pruned_not_selected` proposals are deliberately not trained; they document the agent's search space and cheap-screen decision.
- `selected_for_training` is a transient rollout state written before execution; successful nodes become `trained`, failed nodes become `failed`.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
