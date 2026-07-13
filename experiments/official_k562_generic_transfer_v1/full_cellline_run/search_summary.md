# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, pruned, blocked for artifact acquisition, selected for training, pending implementation, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: pending implementation trained
- Proposal-like nodes: 20
- Trained nodes: 5
- Pruned proposals: 15
- Blocked/acquisition nodes: 0
- Pending implementation nodes: 0
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 0
- Best node: `official_k562_root_aido_gnn_embedding_mlp_p8_official_temperature_calibrated_head_5df7fbe2` val=0.4845 test=0.5435
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.4795 test=0.5215
- Improvement over best root: 0.0049 validation Macro-F1

## Automatic Implementation Loop

| Metric | Count |
|---|---:|
| Auto implementation records | 1 |
| Native smoke passed | 0 |
| Repair/implementation log rows | 3 |
| Repair failures | 0 |
| Requires external Codex | 4 |
| Blocked missing artifact | 0 |
| Trained and backpropagated | 0 |

| Item status | Count |
|---|---:|
| `requires_external_codex` | 1 |

| Decision event | Count |
|---|---:|
| `implementation_selected` | 3 |
| `requires_external_codex` | 3 |

- Implementation agent report: `experiments/official_k562_generic_transfer_v1/full_cellline_run/implementation_agent_report.json`
- Repair log: `experiments/official_k562_generic_transfer_v1/full_cellline_run/repair_log.jsonl`
- Agent decision trace: `experiments/official_k562_generic_transfer_v1/full_cellline_run/agent_decision_trace.jsonl`

## Search State Counts

| Status | Count |
|---|---:|
| `pruned_not_selected` | 15 |
| `trained` | 5 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4410 | 0.5018 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4795 | 0.5215 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 138.1 | gated_mlp | 0.4410 | 0.5018 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 139.7 | gated_mlp | 0.4795 | 0.5215 |
| 1 | `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_gene_head_24be4a16` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 140.2 | custom_program | 0.4711 | 0.5259 |
| 2 | `official_k562_root_aido_embedding_mlp_p5_official_aido_cached_embedding_fusion_c6af2c45` | `official_k562_root_aido_embedding_mlp` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 136.4 | custom_program | 0.4587 | 0.4700 |
| 3 | `official_k562_root_aido_gnn_embedding_mlp_p8_official_temperature_calibrated_head_5df7fbe2` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_temperature_calibrated_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 137.3 | custom_program | 0.4845 | 0.5435 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_gene_head_24be4a16` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p5_official_aido_cached_embedding_fusion_c6af2c45` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_temperature_calibrated_head_5df7fbe2` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4410 |
| 0 | 0.4795 |
| 1 | 0.4795 |
| 2 | 0.4795 |
| 3 | 0.4845 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=2 val=0.4410 test=0.5018 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p3_official_aido_full_finetune_760f7427` status=pruned_not_selected visits=0 strategy=official_aido_full_finetune program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p3_official_aido_full_finetune_760f7427/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p4_official_aido_topk_layer_tuning_7b16df7b` status=pruned_not_selected visits=0 strategy=official_aido_topk_layer_tuning program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p4_official_aido_topk_layer_tuning_7b16df7b/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p1_official_regulatory_network_prior_9f8965ce` status=pruned_not_selected visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p1_official_regulatory_network_prior_9f8965ce/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p2_official_focal_loss_training_bb61fbf6` status=pruned_not_selected visits=0 strategy=official_focal_loss_training program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p2_official_focal_loss_training_bb61fbf6/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p6_official_scgpt_cell_encoder_9cdbf305` status=pruned_not_selected visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p6_official_scgpt_cell_encoder_9cdbf305/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p5_official_aido_cached_embedding_fusion_c6af2c45` status=trained visits=2 val=0.4587 test=0.4700 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p5_official_aido_cached_embedding_fusion_c6af2c45/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=3 val=0.4795 test=0.5215 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_83675661` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_83675661/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_string_neighborhood_attention_b063623e` status=pruned_not_selected visits=0 strategy=official_string_neighborhood_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_string_neighborhood_attention_b063623e/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p6_official_target_graph_conditioned_head_e840575e` status=pruned_not_selected visits=0 strategy=official_target_graph_conditioned_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_target_graph_conditioned_head_e840575e/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p5_official_class_imbalance_training_17860fe2` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_pathway_pooling_reactome_33626c6b` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_pathway_pooling_reactome_33626c6b/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_gene_head_24be4a16` status=trained visits=2 val=0.4711 test=0.5259 strategy=official_target_gene_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_target_gene_head_24be4a16/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p9_official_gene_dropout_augmentation_99ea864c` status=pruned_not_selected visits=0 strategy=official_gene_dropout_augmentation program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p9_official_gene_dropout_augmentation_99ea864c/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p10_official_layerwise_lr_schedule_dc1358f8` status=pruned_not_selected visits=0 strategy=official_layerwise_lr_schedule program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p10_official_layerwise_lr_schedule_dc1358f8/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p11_official_swa_or_checkpoint_ensemble_757ef51c` status=pruned_not_selected visits=0 strategy=official_swa_or_checkpoint_ensemble program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p11_official_swa_or_checkpoint_ensemble_757ef51c/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p7_official_public_static_node_family_wrapper_689ac261` status=pruned_not_selected visits=0 strategy=official_public_static_node_family_wrapper program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p7_official_public_static_node_family_wrapper_689ac261/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p12_official_string_neighborhood_attention_176da9c0` status=pruned_not_selected visits=0 strategy=official_string_neighborhood_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p12_official_string_neighborhood_attention_176da9c0/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p8_official_temperature_calibrated_head_5df7fbe2` status=trained visits=2 val=0.4845 test=0.5435 strategy=official_temperature_calibrated_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p8_official_temperature_calibrated_head_5df7fbe2/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context

## Reproducibility Notes

- In paper-aligned mode, one node means one candidate program state, not necessarily one completed training run.
- `pruned_not_selected` proposals are deliberately not trained; they document the agent's search space and cheap-screen decision.
- `selected_for_training` is a transient rollout state written before execution; successful nodes become `trained`, failed nodes become `failed`.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
