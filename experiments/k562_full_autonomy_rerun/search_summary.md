# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, queued, pruned, blocked for artifact acquisition, selected for training, skipped when realtime implementation cannot safely produce a real model, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: pending implementation trained
- Proposal-like nodes: 32
- Trained nodes: 7
- Queued proposals: 25
- Pruned proposals: 0
- Blocked/acquisition nodes: 0
- Pending implementation nodes: 0
- Implementation-skipped nodes: 0
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 0
- Best node: `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` val=0.5010 test=0.5180
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.4833 test=0.5374
- Improvement over best root: 0.0177 validation Macro-F1

## Automatic Implementation Loop

| Metric | Count |
|---|---:|
| Auto implementation records | 1 |
| Native smoke passed | 0 |
| Repair/implementation log rows | 4 |
| Repair failures | 0 |
| Implementation skipped | 0 |
| Blocked missing artifact | 0 |
| Trained and backpropagated | 0 |

| Item status | Count |
|---|---:|
| `requires_realtime_implementation` | 1 |

| Decision event | Count |
|---|---:|
| `implementation_selected` | 4 |
| `requires_realtime_implementation` | 4 |

- Implementation agent report: `experiments/k562_full_autonomy_rerun/implementation_agent_report.json`
- Repair log: `experiments/k562_full_autonomy_rerun/repair_log.jsonl`
- Agent decision trace: `experiments/k562_full_autonomy_rerun/agent_decision_trace.jsonl`

## Search State Counts

| Status | Count |
|---|---:|
| `candidate_queued` | 25 |
| `trained` | 7 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4295 | 0.4801 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4833 | 0.5374 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 139.2 | gated_mlp | 0.4295 | 0.4801 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 139.1 | gated_mlp | 0.4833 | 0.5374 |
| 1 | `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_string_gnn_attention | native_train | pipeline_program_node | weighted_cross_entropy | gene_graph,perturbation_gene_or_context |  | 191.7 | custom_program | 0.4644 | 0.5000 |
| 2 | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 156.1 | custom_program | 0.5010 | 0.5180 |
| 3 | `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_aido_string_fusion | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 160.3 | custom_program | 0.4782 | 0.5253 |
| 4 | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | `official_k562_root_aido_embedding_mlp` | program_node | official_class_imbalance_training | native_train | pipeline_program_node | focal_loss | perturbation_gene_or_context |  | 137.0 | gated_mlp | 0.4344 | 0.4585 |
| 5 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_aido_lora_adapter | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,perturbation_gene_or_context |  | 158.6 | custom_program | 0.4765 | 0.5044 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` | true | gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_string_gnn_model_dir |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad,class_distribution |  | `` | focal_loss | None |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` | true | AIDO.Cell-100M,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_aido_cell_100m_model_dir |  | `` | weighted_cross_entropy |  |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4295 |
| 0 | 0.4833 |
| 1 | 0.4833 |
| 2 | 0.5010 |
| 3 | 0.5010 |
| 4 | 0.5010 |
| 5 | 0.5010 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=2 val=0.4295 test=0.4801 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` status=trained visits=1 val=0.4344 test=0.4585 strategy=official_class_imbalance_training backend=native_train pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_embedding_mlp_p2_official_target_low_rank_head_f46fa489` status=candidate_queued visits=0 strategy=official_target_low_rank_head program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p2_official_target_low_rank_head_f46fa489/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p3_official_target_bilinear_head_00844437` status=candidate_queued visits=0 strategy=official_target_bilinear_head program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p3_official_target_bilinear_head_00844437/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p1_official_multimodal_mixture_of_experts_3f805895` status=candidate_queued visits=0 strategy=official_multimodal_mixture_of_experts program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p1_official_multimodal_mixture_of_experts_3f805895/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p5_official_temperature_calibrated_head_e9cf2fea` status=candidate_queued visits=0 strategy=official_temperature_calibrated_head program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p5_official_temperature_calibrated_head_e9cf2fea/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p6_official_gene_dropout_augmentation_a46e2c38` status=candidate_queued visits=0 strategy=official_gene_dropout_augmentation program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p6_official_gene_dropout_augmentation_a46e2c38/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p4_official_public_static_node_family_wrapper_b9d08e78` status=candidate_queued visits=0 strategy=official_public_static_node_family_wrapper program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p4_official_public_static_node_family_wrapper_b9d08e78/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` status=candidate_queued visits=0 strategy=official_string_neighborhood_attention program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` status=candidate_queued visits=0 strategy=official_target_graph_conditioned_head program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p4_official_public_best_node_dd0aeebb` status=candidate_queued visits=0 strategy=official_public_best_node pipeline=external_static_node
  - `official_k562_root_aido_embedding_mlp_p6_official_focal_loss_training_0342c716` status=candidate_queued visits=0 strategy=official_focal_loss_training program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p6_official_focal_loss_training_0342c716/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p5_official_regulatory_network_prior_046124cf` status=candidate_queued visits=0 strategy=official_regulatory_network_prior program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p5_official_regulatory_network_prior_046124cf/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p9_official_weighted_ce_training_7034fb0a` status=candidate_queued visits=0 strategy=official_weighted_ce_training program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p9_official_weighted_ce_training_7034fb0a/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p8_official_string_laplacian_smoothing_c590de04` status=candidate_queued visits=0 strategy=official_string_laplacian_smoothing program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p8_official_string_laplacian_smoothing_c590de04/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p10_official_aido_string_concat_fusion_0ac4de80` status=candidate_queued visits=0 strategy=official_aido_string_concat_fusion program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p10_official_aido_string_concat_fusion_0ac4de80/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p11_official_aido_string_gated_fusion_e6ec34ac` status=candidate_queued visits=0 strategy=official_aido_string_gated_fusion program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p11_official_aido_string_gated_fusion_e6ec34ac/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p12_official_aido_string_bilinear_fusion_1cf22a64` status=candidate_queued visits=0 strategy=official_aido_string_bilinear_fusion program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p12_official_aido_string_bilinear_fusion_1cf22a64/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p7_official_string_gnn_full_finetune_4d8c27c4` status=candidate_queued visits=0 strategy=official_string_gnn_full_finetune program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_embedding_mlp_p7_official_string_gnn_full_finetune_4d8c27c4/model.py pipeline=pipeline_program_node
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=5 val=0.4833 test=0.5374 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` status=trained visits=2 val=0.4644 test=0.5000 strategy=official_string_gnn_attention program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d/model.py pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` status=trained visits=2 val=0.5010 test=0.5180 strategy=official_target_gene_head program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_86a657ed` status=candidate_queued visits=0 strategy=official_aido_cached_embedding_fusion program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_86a657ed/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p6_official_string_gnn_frozen_cache_39095dbe` status=candidate_queued visits=0 strategy=official_string_gnn_frozen_cache program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_string_gnn_frozen_cache_39095dbe/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f54f7d63` status=candidate_queued visits=0 strategy=official_aido_full_finetune program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f54f7d63/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_73e7b933` status=candidate_queued visits=0 strategy=official_aido_topk_layer_tuning program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_73e7b933/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p4_official_scgpt_cell_encoder_1554684b` status=candidate_queued visits=0 strategy=official_scgpt_cell_encoder program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_scgpt_cell_encoder_1554684b/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p5_official_scfoundation_top_layer_finetune_a5471728` status=candidate_queued visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_scfoundation_top_layer_finetune_a5471728/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` status=trained visits=2 val=0.4782 test=0.5253 strategy=official_aido_string_fusion program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d/model.py pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` status=trained visits=2 val=0.4765 test=0.5044 strategy=official_aido_lora_adapter program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28/model.py pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` status=candidate_queued visits=0 strategy=official_pathway_pooling_reactome program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_cross_attention_e2de701c` status=candidate_queued visits=0 strategy=official_aido_string_cross_attention program=experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_cross_attention_e2de701c/model.py pipeline=pipeline_program_node

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
