# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, pruned, blocked for artifact acquisition, selected for training, pending implementation, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: requires artifact acquisition for official_scfoundation_top_layer_finetune: scfoundation_cell_embeddings
- Proposal-like nodes: 68
- Trained nodes: 18
- Pruned proposals: 49
- Blocked/acquisition nodes: 1
- Pending implementation nodes: 0
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 1
- Best node: `official_k562_native_p6_official_target_graph_conditioned_head_e7c293b6` val=0.4470 test=0.4829
- Best root: `official_k562_native_public_best_reimplementation` val=0.4221 test=0.4559
- Improvement over best root: 0.0249 validation Macro-F1

## Automatic Implementation Loop

| Metric | Count |
|---|---:|
| Auto implementation records | 1 |
| Native smoke passed | 10 |
| Repair/implementation log rows | 20 |
| Repair failures | 0 |
| Requires external Codex | 0 |
| Blocked missing artifact | 0 |
| Trained and backpropagated | 10 |

| Item status | Count |
|---|---:|
| `trained` | 1 |

| Decision event | Count |
|---|---:|
| `implementation_selected` | 10 |
| `trained_and_backpropagated` | 10 |

- Implementation agent report: `experiments/official_k562_auto_impl_150/implementation_agent_report.json`
- Repair log: `experiments/official_k562_auto_impl_150/repair_log.jsonl`
- Agent decision trace: `experiments/official_k562_auto_impl_150/agent_decision_trace.jsonl`

## Search State Counts

| Status | Count |
|---|---:|
| `pruned_not_selected` | 49 |
| `requires_artifact_acquisition` | 1 |
| `trained` | 18 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `data/cell_lines/official_k562_cls` | custom_program | 0.4221 | 0.4559 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3336 | 0.3336 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3936 | 0.4122 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3962 | 0.4113 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_native_public_best_reimplementation` | `` | root | root | native_train | program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 73.5 | custom_program | 0.4221 | 0.4559 |
| 0 | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 308.8 | external_static_node | 0.3336 | 0.3336 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 38.8 | gated_mlp | 0.3936 | 0.4122 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 38.5 | gated_mlp | 0.3962 | 0.4113 |
| 1 | `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | `official_k562_native_public_best_reimplementation` | program_node | official_string_gnn_attention | native_train | pipeline_program_node | weighted_cross_entropy | gene_graph,perturbation_gene_or_context |  | 70.1 | custom_program | 0.3383 | 0.3888 |
| 2 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 55.5 | custom_program | 0.3552 | 0.3885 |
| 3 | `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25` | `official_k562_root_aido_embedding_mlp` | program_node | official_target_graph_conditioned_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 53.4 | custom_program | 0.3559 | 0.3859 |
| 4 | `official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30` | `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 63.9 | custom_program | 0.4034 | 0.4329 |
| 5 | `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` | `official_k562_public_best_node2_1_1_1_1_1_smoke` | program_node | official_string_gnn_frozen_cache | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 46.3 | custom_program | 0.3501 | 0.4225 |
| 6 | `official_k562_native_p2_official_aido_string_concat_fusion_5570bf15` | `official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30` | program_node | official_aido_string_concat_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 75.9 | custom_program | 0.4188 | 0.4428 |
| 7 | `official_k562_native_p2_official_target_low_rank_head_ae932f98` | `official_k562_native_p2_official_aido_string_concat_fusion_5570bf15` | program_node | official_target_low_rank_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 66.4 | custom_program | 0.4029 | 0.4314 |
| 8 | `official_k562_native_p1_official_temperature_calibrated_head_ad83be07` | `official_k562_native_p2_official_target_low_rank_head_ae932f98` | program_node | official_temperature_calibrated_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 63.9 | custom_program | 0.4200 | 0.4462 |
| 9 | `official_k562_native_p2_official_native_public_best_reimplementation_4f343b3c` | `official_k562_native_p1_official_temperature_calibrated_head_ad83be07` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 77.1 | custom_program | 0.4411 | 0.4694 |
| 10 | `official_k562_native_p1_official_target_gene_head_46c4ee66` | `official_k562_native_p2_official_native_public_best_reimplementation_4f343b3c` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 66.9 | custom_program | 0.4067 | 0.4371 |
| 11 | `official_k562_native_p2_official_aido_string_cross_attention_5b1cf4f0` | `official_k562_native_p1_official_target_gene_head_46c4ee66` | program_node | official_aido_string_cross_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 76.3 | custom_program | 0.3823 | 0.4385 |
| 12 | `official_k562_native_p6_official_target_graph_conditioned_head_e7c293b6` | `official_k562_native_p1_official_target_gene_head_46c4ee66` | program_node | official_target_graph_conditioned_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 73.6 | custom_program | 0.4470 | 0.4829 |
| 13 | `official_k562_native_p1_official_string_neighborhood_attention_8885d36d` | `official_k562_native_p6_official_target_graph_conditioned_head_e7c293b6` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 73.1 | custom_program | 0.4181 | 0.4824 |
| 14 | `official_k562_native_p3_official_public_best_node_5f8e0610` | `official_k562_native_p1_official_string_neighborhood_attention_8885d36d` | program_node | official_public_best_node | external_static_node | program_node | external_static_node | external_public_best_node |  | 319.8 | custom_program | 0.3336 | 0.3336 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_native_public_best_reimplementation` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN,public_node_code |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | true | gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` | true | perturbation_gene_or_context | official_string_gnn_model_dir,official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p2_official_aido_string_concat_fusion_5570bf15` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_string_gnn_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p2_official_target_low_rank_head_ae932f98` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p1_official_temperature_calibrated_head_ad83be07` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p2_official_native_public_best_reimplementation_4f343b3c` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_target_gene_head_46c4ee66` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p2_official_aido_string_cross_attention_5b1cf4f0` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_string_gnn_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p6_official_target_graph_conditioned_head_e7c293b6` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p1_official_string_neighborhood_attention_8885d36d` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p3_official_public_best_node_5f8e0610` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4221 |
| 0 | 0.4221 |
| 0 | 0.4221 |
| 0 | 0.4221 |
| 1 | 0.4221 |
| 2 | 0.4221 |
| 3 | 0.4221 |
| 4 | 0.4221 |
| 5 | 0.4221 |
| 6 | 0.4221 |
| 7 | 0.4221 |
| 8 | 0.4221 |
| 9 | 0.4411 |
| 10 | 0.4411 |
| 11 | 0.4411 |
| 12 | 0.4470 |
| 13 | 0.4470 |
| 14 | 0.4470 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=2 val=0.3936 test=0.4122 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p2_official_public_best_node_0d39d5c6` status=pruned_not_selected visits=0 strategy=official_public_best_node pipeline=external_static_node
  - `official_k562_root_aido_embedding_mlp_p3_official_regulatory_network_prior_139ae582` status=pruned_not_selected visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_auto_impl_150/programs/official_k562_root_aido_embedding_mlp_p3_official_regulatory_network_prior_139ae582/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p4_official_focal_loss_training_29e824a9` status=pruned_not_selected visits=0 strategy=official_focal_loss_training program=experiments/official_k562_auto_impl_150/programs/official_k562_root_aido_embedding_mlp_p4_official_focal_loss_training_29e824a9/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25` status=trained visits=2 val=0.3559 test=0.3859 strategy=official_target_graph_conditioned_head program=experiments/official_k562_auto_impl_150/programs/official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=2 val=0.3962 test=0.4113 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_class_imbalance_training_fdd8ca75` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_auto_impl_150/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` status=trained visits=2 val=0.3552 test=0.3885 strategy=official_string_neighborhood_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_native_public_best_reimplementation` status=trained visits=12 val=0.4221 test=0.4559 backend=native_train artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_native_p4_official_target_gene_head_bb439915` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_target_gene_head_bb439915/model.py pipeline=pipeline_program_node
  - `official_k562_native_p1_official_aido_string_fusion_66a588f9` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_aido_string_fusion_66a588f9/model.py pipeline=pipeline_program_node
  - `official_k562_native_p3_official_aido_lora_adapter_9d77b24d` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_aido_lora_adapter_9d77b24d/model.py pipeline=pipeline_program_node
  - `official_k562_native_p2_official_string_gnn_attention_c7b091ac` status=trained visits=11 val=0.3383 test=0.3888 strategy=official_string_gnn_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_string_gnn_attention_c7b091ac/model.py backend=native_train pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context
    - `official_k562_native_p1_official_aido_full_finetune_253d0020` status=pruned_not_selected visits=0 strategy=official_aido_full_finetune program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_aido_full_finetune_253d0020/model.py pipeline=pipeline_program_node
    - `official_k562_native_p2_official_aido_topk_layer_tuning_1543d9b3` status=pruned_not_selected visits=0 strategy=official_aido_topk_layer_tuning program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_aido_topk_layer_tuning_1543d9b3/model.py pipeline=pipeline_program_node
    - `official_k562_native_p4_official_scgpt_cell_encoder_6dea72bd` status=pruned_not_selected visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_scgpt_cell_encoder_6dea72bd/model.py pipeline=pipeline_program_node
    - `official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30` status=trained visits=11 val=0.4034 test=0.4329 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_native_p3_official_aido_string_gated_fusion_d3b6aa98` status=pruned_not_selected visits=0 strategy=official_aido_string_gated_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_aido_string_gated_fusion_d3b6aa98/model.py pipeline=pipeline_program_node
      - `official_k562_native_p4_official_aido_string_bilinear_fusion_6d5f4458` status=pruned_not_selected visits=0 strategy=official_aido_string_bilinear_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_aido_string_bilinear_fusion_6d5f4458/model.py pipeline=pipeline_program_node
      - `official_k562_native_p1_official_weighted_ce_training_1147ed60` status=pruned_not_selected visits=0 strategy=official_weighted_ce_training program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_weighted_ce_training_1147ed60/model.py pipeline=pipeline_program_node
      - `official_k562_native_p2_official_aido_string_concat_fusion_5570bf15` status=trained visits=10 val=0.4188 test=0.4428 strategy=official_aido_string_concat_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_aido_string_concat_fusion_5570bf15/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
        - `official_k562_native_p3_official_target_bilinear_head_17b86b22` status=pruned_not_selected visits=0 strategy=official_target_bilinear_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_target_bilinear_head_17b86b22/model.py pipeline=pipeline_program_node
        - `official_k562_native_p1_official_multimodal_mixture_of_experts_0b2158d0` status=pruned_not_selected visits=0 strategy=official_multimodal_mixture_of_experts program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_multimodal_mixture_of_experts_0b2158d0/model.py pipeline=pipeline_program_node
        - `official_k562_native_p4_official_public_static_node_family_wrapper_d783bafb` status=pruned_not_selected visits=0 strategy=official_public_static_node_family_wrapper program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_public_static_node_family_wrapper_d783bafb/model.py pipeline=pipeline_program_node
        - `official_k562_native_p2_official_target_low_rank_head_ae932f98` status=trained visits=9 val=0.4029 test=0.4314 strategy=official_target_low_rank_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_target_low_rank_head_ae932f98/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
          - `official_k562_native_p2_official_gene_dropout_augmentation_c2c80ae6` status=pruned_not_selected visits=0 strategy=official_gene_dropout_augmentation program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_gene_dropout_augmentation_c2c80ae6/model.py pipeline=pipeline_program_node
          - `official_k562_native_p3_official_layerwise_lr_schedule_c026facb` status=pruned_not_selected visits=0 strategy=official_layerwise_lr_schedule program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_layerwise_lr_schedule_c026facb/model.py pipeline=pipeline_program_node
          - `official_k562_native_p4_official_swa_or_checkpoint_ensemble_4a7aad6e` status=pruned_not_selected visits=0 strategy=official_swa_or_checkpoint_ensemble program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_swa_or_checkpoint_ensemble_4a7aad6e/model.py pipeline=pipeline_program_node
          - `official_k562_native_p1_official_temperature_calibrated_head_ad83be07` status=trained visits=8 val=0.4200 test=0.4462 strategy=official_temperature_calibrated_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_temperature_calibrated_head_ad83be07/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
            - `official_k562_native_p3_official_string_gnn_attention_ad963783` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_string_gnn_attention_ad963783/model.py pipeline=pipeline_program_node
            - `official_k562_native_p1_official_aido_string_fusion_dad31ac2` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_aido_string_fusion_dad31ac2/model.py pipeline=pipeline_program_node
            - `official_k562_native_p4_official_aido_lora_adapter_f41b61bf` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_aido_lora_adapter_f41b61bf/model.py pipeline=pipeline_program_node
            - `official_k562_native_p2_official_native_public_best_reimplementation_4f343b3c` status=trained visits=6 val=0.4411 test=0.4694 strategy=official_native_public_best_reimplementation program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_native_public_best_reimplementation_4f343b3c/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
              - `official_k562_native_p4_official_string_gnn_attention_8db070ee` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_string_gnn_attention_8db070ee/model.py pipeline=pipeline_program_node
              - `official_k562_native_p2_official_aido_string_fusion_4ff632f4` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_aido_string_fusion_4ff632f4/model.py pipeline=pipeline_program_node
              - `official_k562_native_p3_official_pathway_pooling_reactome_85de1bf0` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_pathway_pooling_reactome_85de1bf0/model.py pipeline=pipeline_program_node
              - `official_k562_native_p1_official_target_gene_head_46c4ee66` status=trained visits=5 val=0.4067 test=0.4371 strategy=official_target_gene_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_target_gene_head_46c4ee66/model.py backend=native_train pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
                - `official_k562_native_p3_official_target_gene_head_f22d5b45` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_target_gene_head_f22d5b45/model.py pipeline=pipeline_program_node
                - `official_k562_native_p1_official_aido_lora_adapter_cd6e7f54` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_aido_lora_adapter_cd6e7f54/model.py pipeline=pipeline_program_node
                - `official_k562_native_p4_official_aido_string_fusion_6f862340` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_aido_string_fusion_6f862340/model.py pipeline=pipeline_program_node
                - `official_k562_native_p2_official_aido_string_cross_attention_5b1cf4f0` status=trained visits=2 val=0.3823 test=0.4385 strategy=official_aido_string_cross_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_aido_string_cross_attention_5b1cf4f0/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
                - `official_k562_native_p5_official_aido_lora_adapter_3bcecf73` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p5_official_aido_lora_adapter_3bcecf73/model.py pipeline=pipeline_program_node
                - `official_k562_native_p7_official_aido_string_cross_attention_43c56efd` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p7_official_aido_string_cross_attention_43c56efd/model.py pipeline=pipeline_program_node
                - `official_k562_native_p8_official_focal_loss_training_7972766c` status=pruned_not_selected visits=0 strategy=official_focal_loss_training program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p8_official_focal_loss_training_7972766c/model.py pipeline=pipeline_program_node
                - `official_k562_native_p6_official_target_graph_conditioned_head_e7c293b6` status=trained visits=4 val=0.4470 test=0.4829 strategy=official_target_graph_conditioned_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p6_official_target_graph_conditioned_head_e7c293b6/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
                  - `official_k562_native_p4_official_string_gnn_attention_9c8fcb57` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_string_gnn_attention_9c8fcb57/model.py pipeline=pipeline_program_node
                  - `official_k562_native_p2_official_class_imbalance_training_8fa9c1f8` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
                  - `official_k562_native_p3_official_pathway_pooling_reactome_ade166c5` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_pathway_pooling_reactome_ade166c5/model.py pipeline=pipeline_program_node
                  - `official_k562_native_p1_official_string_neighborhood_attention_8885d36d` status=trained visits=3 val=0.4181 test=0.4824 strategy=official_string_neighborhood_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_string_neighborhood_attention_8885d36d/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
                    - `official_k562_native_p1_official_target_gene_head_3f327172` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_target_gene_head_3f327172/model.py pipeline=pipeline_program_node
                    - `official_k562_native_p2_official_aido_string_fusion_1c5de481` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p2_official_aido_string_fusion_1c5de481/model.py pipeline=pipeline_program_node
                    - `official_k562_native_p4_official_regulatory_network_prior_beff5770` status=pruned_not_selected visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_regulatory_network_prior_beff5770/model.py pipeline=pipeline_program_node
                    - `official_k562_native_p3_official_public_best_node_5f8e0610` status=trained visits=1 val=0.3336 test=0.3336 strategy=official_public_best_node backend=external_static_node pipeline=external_static_node artifacts=perturbation_gene_or_context
                      - `official_k562_native_p4_official_string_gnn_attention_cc5f8148` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_string_gnn_attention_cc5f8148/model.py pipeline=pipeline_program_node
                      - `official_k562_native_p1_official_string_neighborhood_attention_32154c60` status=pruned_not_selected visits=0 strategy=official_string_neighborhood_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p1_official_string_neighborhood_attention_32154c60/model.py pipeline=pipeline_program_node
                      - `official_k562_native_p2_official_class_imbalance_training_b58afcb4` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
                      - `official_k562_native_p3_official_pathway_pooling_reactome_89e22836` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p3_official_pathway_pooling_reactome_89e22836/model.py pipeline=pipeline_program_node
                      - `official_k562_native_p5_official_aido_lora_adapter_8493b1ef` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p5_official_aido_lora_adapter_8493b1ef/model.py pipeline=pipeline_program_node
                      - `official_k562_native_p6_official_target_graph_conditioned_head_1465dc85` status=pruned_not_selected visits=0 strategy=official_target_graph_conditioned_head program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p6_official_target_graph_conditioned_head_1465dc85/model.py pipeline=pipeline_program_node
                      - `official_k562_native_p7_official_aido_string_cross_attention_2f81e817` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p7_official_aido_string_cross_attention_2f81e817/model.py pipeline=pipeline_program_node
                      - `official_k562_native_p8_official_scfoundation_top_layer_finetune_ba26b0e0` status=requires_artifact_acquisition visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_auto_impl_150/programs/official_k562_native_p8_official_scfoundation_top_layer_finetune_ba26b0e0/model.py pipeline=pipeline_program_node
- `official_k562_public_best_node2_1_1_1_1_1_smoke` status=trained visits=2 val=0.3336 test=0.3336 backend=external_static_node
  - `official_k562_p4_official_string_laplacian_smoothing_208df089` status=pruned_not_selected visits=0 strategy=official_string_laplacian_smoothing program=experiments/official_k562_auto_impl_150/programs/official_k562_p4_official_string_laplacian_smoothing_208df089/model.py pipeline=pipeline_program_node
  - `official_k562_p3_official_string_gnn_full_finetune_1881d60a` status=pruned_not_selected visits=0 strategy=official_string_gnn_full_finetune program=experiments/official_k562_auto_impl_150/programs/official_k562_p3_official_string_gnn_full_finetune_1881d60a/model.py pipeline=pipeline_program_node
  - `official_k562_p1_official_scfoundation_top_layer_finetune_2a9665c5` status=pruned_not_selected visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_auto_impl_150/programs/official_k562_p1_official_scfoundation_top_layer_finetune_2a9665c5/model.py pipeline=pipeline_program_node
  - `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` status=trained visits=2 val=0.3501 test=0.4225 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_auto_impl_150/programs/official_k562_p2_official_string_gnn_frozen_cache_38234ef6/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context

## Failures

| Node | Parent | Error |
|---|---|---|
| `official_k562_native_p8_official_scfoundation_top_layer_finetune_ba26b0e0` | `official_k562_native_p3_official_public_best_node_5f8e0610` | requires_artifact_acquisition |

## Reproducibility Notes

- In paper-aligned mode, one node means one candidate program state, not necessarily one completed training run.
- `pruned_not_selected` proposals are deliberately not trained; they document the agent's search space and cheap-screen decision.
- `selected_for_training` is a transient rollout state written before execution; successful nodes become `trained`, failed nodes become `failed`.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
