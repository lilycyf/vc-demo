# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, pruned, blocked for artifact acquisition, selected for training, pending implementation, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: pending implementation trained
- Proposal-like nodes: 68
- Trained nodes: 12
- Pruned proposals: 55
- Blocked/acquisition nodes: 1
- Pending implementation nodes: 0
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 1
- Best node: `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2` val=0.4957 test=0.5347
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.4820 test=0.5395
- Improvement over best root: 0.0137 validation Macro-F1

## Automatic Implementation Loop

| Metric | Count |
|---|---:|
| Auto implementation records | 1 |
| Native smoke passed | 0 |
| Repair/implementation log rows | 10 |
| Repair failures | 0 |
| Requires external Codex | 11 |
| Blocked missing artifact | 0 |
| Trained and backpropagated | 0 |

| Item status | Count |
|---|---:|
| `requires_external_codex` | 1 |

| Decision event | Count |
|---|---:|
| `implementation_selected` | 10 |
| `requires_external_codex` | 10 |

- Implementation agent report: `experiments/official_k562_generic_transfer_v1/full_cellline_run/implementation_agent_report.json`
- Repair log: `experiments/official_k562_generic_transfer_v1/full_cellline_run/repair_log.jsonl`
- Agent decision trace: `experiments/official_k562_generic_transfer_v1/full_cellline_run/agent_decision_trace.jsonl`

## Search State Counts

| Status | Count |
|---|---:|
| `pruned_not_selected` | 55 |
| `requires_artifact_acquisition` | 1 |
| `trained` | 12 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4354 | 0.4919 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4820 | 0.5395 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 132.9 | gated_mlp | 0.4354 | 0.4919 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 125.0 | gated_mlp | 0.4820 | 0.5395 |
| 1 | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 141.2 | custom_program | 0.4686 | 0.5171 |
| 2 | `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` | `official_k562_root_aido_embedding_mlp` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 152.8 | custom_program | 0.4505 | 0.4909 |
| 3 | `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_string_laplacian_smoothing | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 151.8 | custom_program | 0.4957 | 0.5347 |
| 4 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_c870de87` | `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 155.8 | custom_program | 0.4757 | 0.5339 |
| 5 | `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_low_rank_head_1814b770` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_c870de87` | program_node | official_target_low_rank_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 155.3 | custom_program | 0.4897 | 0.5453 |
| 6 | `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_99d67e4f` | `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_low_rank_head_1814b770` | program_node | official_layerwise_lr_schedule | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 155.4 | custom_program | 0.4810 | 0.5282 |
| 7 | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_10c0794d` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_99d67e4f` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 158.0 | custom_program | 0.4737 | 0.5226 |
| 8 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_10c0794d` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 157.7 | custom_program | 0.4796 | 0.5318 |
| 9 | `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_graph_conditioned_head_3894931a` | `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2` | program_node | official_target_graph_conditioned_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 171.8 | custom_program | 0.4640 | 0.5029 |
| 11 | `official_k562_root_aido_gnn_embedding_mlp_p11_official_string_laplacian_smoothing_c1bf6219` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | program_node | official_string_laplacian_smoothing | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 156.9 | custom_program | 0.4841 | 0.5302 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_c870de87` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_low_rank_head_1814b770` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_99d67e4f` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_10c0794d` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_graph_conditioned_head_3894931a` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_string_laplacian_smoothing_c1bf6219` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4354 |
| 0 | 0.4820 |
| 1 | 0.4820 |
| 2 | 0.4820 |
| 3 | 0.4957 |
| 4 | 0.4957 |
| 5 | 0.4957 |
| 6 | 0.4957 |
| 7 | 0.4957 |
| 8 | 0.4957 |
| 9 | 0.4957 |
| 11 | 0.4957 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=2 val=0.4354 test=0.4919 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` status=pruned_not_selected visits=0 strategy=official_target_graph_conditioned_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p5_official_regulatory_network_prior_046124cf` status=pruned_not_selected visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p5_official_regulatory_network_prior_046124cf/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p6_official_focal_loss_training_0342c716` status=pruned_not_selected visits=0 strategy=official_focal_loss_training program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p6_official_focal_loss_training_0342c716/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p4_official_public_best_node_dd0aeebb` status=pruned_not_selected visits=0 strategy=official_public_best_node pipeline=external_static_node
  - `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` status=trained visits=2 val=0.4505 test=0.4909 strategy=official_string_neighborhood_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=10 val=0.4820 test=0.5395 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_cross_attention_e2de701c` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_cross_attention_e2de701c/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` status=trained visits=3 val=0.4686 test=0.5171 strategy=official_target_gene_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_neighborhood_attention_60e073d0` status=pruned_not_selected visits=0 strategy=official_string_neighborhood_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_string_neighborhood_attention_60e073d0/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_lora_adapter_08a9a6e2` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_lora_adapter_08a9a6e2/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p3_official_class_imbalance_training_a6e9ba10` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p4_official_pathway_pooling_reactome_f9b457fb` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_pathway_pooling_reactome_f9b457fb/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p5_official_string_gnn_attention_6a196faa` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_string_gnn_attention_6a196faa/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p1_official_regulatory_network_prior_190f70aa` status=requires_artifact_acquisition visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_regulatory_network_prior_190f70aa/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p7_official_aido_full_finetune_ec4f8e7b` status=pruned_not_selected visits=0 strategy=official_aido_full_finetune program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p7_official_aido_full_finetune_ec4f8e7b/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p9_official_string_gnn_frozen_cache_db6789d4` status=pruned_not_selected visits=0 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p9_official_string_gnn_frozen_cache_db6789d4/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p8_official_scfoundation_top_layer_finetune_6a7046c6` status=pruned_not_selected visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p8_official_scfoundation_top_layer_finetune_6a7046c6/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p10_official_string_gnn_full_finetune_32b7629c` status=pruned_not_selected visits=0 strategy=official_string_gnn_full_finetune program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p10_official_string_gnn_full_finetune_32b7629c/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p12_official_regulatory_network_prior_7e8802ea` status=pruned_not_selected visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p12_official_regulatory_network_prior_7e8802ea/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p11_official_string_laplacian_smoothing_c1bf6219` status=trained visits=2 val=0.4841 test=0.5302 strategy=official_string_laplacian_smoothing program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p11_official_string_laplacian_smoothing_c1bf6219/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p9_official_weighted_ce_training_b1817b1a` status=pruned_not_selected visits=0 strategy=official_weighted_ce_training program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p9_official_weighted_ce_training_b1817b1a/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p10_official_aido_string_concat_fusion_16799795` status=pruned_not_selected visits=0 strategy=official_aido_string_concat_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p10_official_aido_string_concat_fusion_16799795/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p11_official_aido_string_gated_fusion_60845133` status=pruned_not_selected visits=0 strategy=official_aido_string_gated_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p11_official_aido_string_gated_fusion_60845133/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p12_official_aido_string_bilinear_fusion_a826dbcf` status=pruned_not_selected visits=0 strategy=official_aido_string_bilinear_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p12_official_aido_string_bilinear_fusion_a826dbcf/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p7_official_string_gnn_full_finetune_969bb45b` status=pruned_not_selected visits=0 strategy=official_string_gnn_full_finetune program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p7_official_string_gnn_full_finetune_969bb45b/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2` status=trained visits=8 val=0.4957 test=0.5347 strategy=official_string_laplacian_smoothing program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f2d4bffe` status=pruned_not_selected visits=0 strategy=official_aido_full_finetune program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f2d4bffe/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_bfadb62c` status=pruned_not_selected visits=0 strategy=official_aido_topk_layer_tuning program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_bfadb62c/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p6_official_string_gnn_frozen_cache_753eec9c` status=pruned_not_selected visits=0 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_string_gnn_frozen_cache_753eec9c/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p4_official_scgpt_cell_encoder_5e4af3ff` status=pruned_not_selected visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_scgpt_cell_encoder_5e4af3ff/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p5_official_scfoundation_top_layer_finetune_cf2d5e3c` status=pruned_not_selected visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_scfoundation_top_layer_finetune_cf2d5e3c/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_c870de87` status=trained visits=7 val=0.4757 test=0.5339 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_c870de87/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_root_aido_gnn_embedding_mlp_p3_official_target_bilinear_head_f8bb4b16` status=pruned_not_selected visits=0 strategy=official_target_bilinear_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_target_bilinear_head_f8bb4b16/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_gnn_embedding_mlp_p1_official_multimodal_mixture_of_experts_d0294429` status=pruned_not_selected visits=0 strategy=official_multimodal_mixture_of_experts program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_multimodal_mixture_of_experts_d0294429/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_gnn_embedding_mlp_p5_official_temperature_calibrated_head_bc0fc664` status=pruned_not_selected visits=0 strategy=official_temperature_calibrated_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_temperature_calibrated_head_bc0fc664/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_gnn_embedding_mlp_p6_official_gene_dropout_augmentation_7558f3c7` status=pruned_not_selected visits=0 strategy=official_gene_dropout_augmentation program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_gene_dropout_augmentation_7558f3c7/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_gnn_embedding_mlp_p4_official_public_static_node_family_wrapper_45211060` status=pruned_not_selected visits=0 strategy=official_public_static_node_family_wrapper program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_public_static_node_family_wrapper_45211060/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_low_rank_head_1814b770` status=trained visits=6 val=0.4897 test=0.5453 strategy=official_target_low_rank_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_target_low_rank_head_1814b770/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
        - `official_k562_root_aido_gnn_embedding_mlp_p2_official_swa_or_checkpoint_ensemble_24854586` status=pruned_not_selected visits=0 strategy=official_swa_or_checkpoint_ensemble program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_swa_or_checkpoint_ensemble_24854586/model.py pipeline=pipeline_program_node
        - `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_lora_adapter_3b8ba31b` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_lora_adapter_3b8ba31b/model.py pipeline=pipeline_program_node
        - `official_k562_root_aido_gnn_embedding_mlp_p5_official_string_gnn_attention_08c9d0bf` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_string_gnn_attention_08c9d0bf/model.py pipeline=pipeline_program_node
        - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_fusion_8602a9f4` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_fusion_8602a9f4/model.py pipeline=pipeline_program_node
        - `official_k562_root_aido_gnn_embedding_mlp_p4_official_native_public_best_reimplementation_312716fa` status=pruned_not_selected visits=0 strategy=official_native_public_best_reimplementation program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_native_public_best_reimplementation_312716fa/model.py pipeline=pipeline_program_node
        - `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_99d67e4f` status=trained visits=5 val=0.4810 test=0.5282 strategy=official_layerwise_lr_schedule program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_99d67e4f/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
          - `official_k562_root_aido_gnn_embedding_mlp_p5_official_aido_lora_adapter_d2bc664b` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_aido_lora_adapter_d2bc664b/model.py pipeline=pipeline_program_node
          - `official_k562_root_aido_gnn_embedding_mlp_p3_official_pathway_pooling_reactome_1c3f8802` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_pathway_pooling_reactome_1c3f8802/model.py pipeline=pipeline_program_node
          - `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_cross_attention_bf6c860c` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_cross_attention_bf6c860c/model.py pipeline=pipeline_program_node
          - `official_k562_root_aido_gnn_embedding_mlp_p4_official_string_gnn_attention_7a59a53a` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_string_gnn_attention_7a59a53a/model.py pipeline=pipeline_program_node
          - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_fusion_c2e04e52` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_fusion_c2e04e52/model.py pipeline=pipeline_program_node
          - `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_10c0794d` status=trained visits=4 val=0.4737 test=0.5226 strategy=official_target_gene_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_10c0794d/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
            - `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_69c1dde8` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_69c1dde8/model.py pipeline=pipeline_program_node
            - `official_k562_root_aido_gnn_embedding_mlp_p4_official_class_imbalance_training_c14b8a99` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
            - `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_59add227` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_59add227/model.py pipeline=pipeline_program_node
            - `official_k562_root_aido_gnn_embedding_mlp_p6_official_string_gnn_attention_760f955f` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_string_gnn_attention_760f955f/model.py pipeline=pipeline_program_node
            - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_fusion_44b7f2d1` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_fusion_44b7f2d1/model.py pipeline=pipeline_program_node
            - `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2` status=trained visits=3 val=0.4796 test=0.5318 strategy=official_string_neighborhood_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
              - `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_5386b216` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_5386b216/model.py pipeline=pipeline_program_node
              - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_1e07f298` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_1e07f298/model.py pipeline=pipeline_program_node
              - `official_k562_root_aido_gnn_embedding_mlp_p6_official_public_best_node_ec40a21b` status=pruned_not_selected visits=0 strategy=official_public_best_node pipeline=external_static_node
              - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_cross_attention_c04f3ba4` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_string_cross_attention_c04f3ba4/model.py pipeline=pipeline_program_node
              - `official_k562_root_aido_gnn_embedding_mlp_p5_official_aido_string_fusion_f73a8555` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_aido_string_fusion_f73a8555/model.py pipeline=pipeline_program_node
              - `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_graph_conditioned_head_3894931a` status=trained visits=2 val=0.4640 test=0.5029 strategy=official_target_graph_conditioned_head program=experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_target_graph_conditioned_head_3894931a/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context

## Failures

| Node | Parent | Error |
|---|---|---|
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_regulatory_network_prior_190f70aa` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | requires_artifact_acquisition |

## Reproducibility Notes

- In paper-aligned mode, one node means one candidate program state, not necessarily one completed training run.
- `pruned_not_selected` proposals are deliberately not trained; they document the agent's search space and cheap-screen decision.
- `selected_for_training` is a transient rollout state written before execution; successful nodes become `trained`, failed nodes become `failed`.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
