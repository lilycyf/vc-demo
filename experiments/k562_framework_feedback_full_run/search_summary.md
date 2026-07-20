# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, queued, pruned, blocked for artifact acquisition, selected for training, skipped when realtime implementation cannot safely produce a real model, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: pending implementation trained
- Proposal-like nodes: 20
- Trained nodes: 5
- Queued proposals: 15
- Pruned proposals: 0
- Blocked/acquisition nodes: 0
- Pending implementation nodes: 0
- Implementation-skipped nodes: 0
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 0
- Best node: `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` val=0.5025 test=0.5389
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.4792 test=0.5464
- Improvement over best root: 0.0233 validation Macro-F1

## Automatic Implementation Loop

| Metric | Count |
|---|---:|
| Auto implementation records | 1 |
| Native smoke passed | 0 |
| Repair/implementation log rows | 3 |
| Repair failures | 0 |
| Implementation skipped | 0 |
| Blocked missing artifact | 0 |
| Trained and backpropagated | 0 |

| Item status | Count |
|---|---:|
| `requires_realtime_implementation` | 1 |

| Decision event | Count |
|---|---:|
| `implementation_selected` | 3 |
| `requires_realtime_implementation` | 3 |

- Implementation agent report: `experiments/k562_framework_feedback_full_run/implementation_agent_report.json`
- Repair log: `experiments/k562_framework_feedback_full_run/repair_log.jsonl`
- Agent decision trace: `experiments/k562_framework_feedback_full_run/agent_decision_trace.jsonl`

## Search State Counts

| Status | Count |
|---|---:|
| `candidate_queued` | 15 |
| `trained` | 5 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4324 | 0.4885 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4792 | 0.5464 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 144.8 | gated_mlp | 0.4324 | 0.4885 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 145.2 | gated_mlp | 0.4792 | 0.5464 |
| 1 | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 164.2 | custom_program | 0.5025 | 0.5389 |
| 2 | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | `official_k562_root_aido_embedding_mlp` | program_node | official_class_imbalance_training | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 143.5 | gated_mlp | 0.4124 | 0.4342 |
| 3 | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_pathway_pooling_reactome | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 156.5 | custom_program | 0.4758 | 0.5426 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad,class_distribution |  | `` | focal_loss | None |
| `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` | true | perturbation_gene_or_context | pathway_membership_matrix,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4324 |
| 0 | 0.4792 |
| 1 | 0.5025 |
| 2 | 0.5025 |
| 3 | 0.5025 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=2 val=0.4324 test=0.4885 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` status=trained visits=1 val=0.4124 test=0.4342 strategy=official_class_imbalance_training backend=native_train pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_embedding_mlp_p1_official_focal_loss_training_6c9f7ffb` status=candidate_queued visits=0 strategy=official_focal_loss_training program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p1_official_focal_loss_training_6c9f7ffb/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p4_official_aido_cached_embedding_fusion_de24d28a` status=candidate_queued visits=0 strategy=official_aido_cached_embedding_fusion program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p4_official_aido_cached_embedding_fusion_de24d28a/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p2_official_aido_full_finetune_b9963e8c` status=candidate_queued visits=0 strategy=official_aido_full_finetune program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p2_official_aido_full_finetune_b9963e8c/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p3_official_aido_topk_layer_tuning_d2501a66` status=candidate_queued visits=0 strategy=official_aido_topk_layer_tuning program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p3_official_aido_topk_layer_tuning_d2501a66/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p5_official_scgpt_cell_encoder_d39d6d57` status=candidate_queued visits=0 strategy=official_scgpt_cell_encoder program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p5_official_scgpt_cell_encoder_d39d6d57/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p6_official_scfoundation_top_layer_finetune_2a622fba` status=candidate_queued visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p6_official_scfoundation_top_layer_finetune_2a622fba/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` status=candidate_queued visits=0 strategy=official_string_neighborhood_attention program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` status=candidate_queued visits=0 strategy=official_target_graph_conditioned_head program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p6_official_weighted_ce_training_8ced18b7` status=candidate_queued visits=0 strategy=official_weighted_ce_training program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p6_official_weighted_ce_training_8ced18b7/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p5_official_regulatory_network_prior_046124cf` status=candidate_queued visits=0 strategy=official_regulatory_network_prior program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_embedding_mlp_p5_official_regulatory_network_prior_046124cf/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p4_official_public_best_node_dd0aeebb` status=candidate_queued visits=0 strategy=official_public_best_node pipeline=external_static_node
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=3 val=0.4792 test=0.5464 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` status=trained visits=2 val=0.5025 test=0.5389 strategy=official_target_gene_head program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` status=trained visits=2 val=0.4758 test=0.5426 strategy=official_pathway_pooling_reactome program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` status=candidate_queued visits=0 strategy=official_string_gnn_attention program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` status=candidate_queued visits=0 strategy=official_aido_string_fusion program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` status=candidate_queued visits=0 strategy=official_aido_lora_adapter program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_cross_attention_e2de701c` status=candidate_queued visits=0 strategy=official_aido_string_cross_attention program=experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_cross_attention_e2de701c/model.py pipeline=pipeline_program_node

## Reproducibility Notes

- In paper-aligned mode, one node means one candidate program state, not necessarily one completed training run.
- `candidate_queued` proposals remain globally eligible for rollout training until selected, blocked, failed, or budget ends.
- `pruned_not_selected` proposals are deliberately not trained; in full-cellline global-queue mode they should mainly represent duplicate/dominated candidates rather than local-pool losers.
- `selected_for_training` is a transient rollout state written before execution; successful nodes become `trained`, failed nodes become `failed`.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
