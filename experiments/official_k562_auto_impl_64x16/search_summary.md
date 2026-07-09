# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, pruned, blocked for artifact acquisition, selected for training, pending implementation, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: no improvement for 12 nodes
- Proposal-like nodes: 56
- Trained nodes: 17
- Pruned proposals: 39
- Blocked/acquisition nodes: 0
- Pending implementation nodes: 0
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 0
- Best node: `official_k562_native_p2_official_string_gnn_attention_c7b091ac` val=0.4421 test=0.4805
- Best root: `official_k562_native_public_best_reimplementation` val=0.4332 test=0.4702
- Improvement over best root: 0.0089 validation Macro-F1

## Automatic Implementation Loop

| Metric | Count |
|---|---:|
| Auto implementation records | 1 |
| Native smoke passed | 9 |
| Repair/implementation log rows | 18 |
| Repair failures | 0 |
| Requires external Codex | 0 |
| Blocked missing artifact | 0 |
| Trained and backpropagated | 9 |

| Item status | Count |
|---|---:|
| `trained` | 1 |

| Decision event | Count |
|---|---:|
| `implementation_selected` | 9 |
| `trained_and_backpropagated` | 9 |

- Implementation agent report: `experiments/official_k562_auto_impl_64x16/implementation_agent_report.json`
- Repair log: `experiments/official_k562_auto_impl_64x16/repair_log.jsonl`
- Agent decision trace: `experiments/official_k562_auto_impl_64x16/agent_decision_trace.jsonl`

## Search State Counts

| Status | Count |
|---|---:|
| `pruned_not_selected` | 39 |
| `trained` | 17 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `data/cell_lines/official_k562_cls` | custom_program | 0.4332 | 0.4702 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3336 | 0.3336 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4007 | 0.4221 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3923 | 0.4209 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_native_public_best_reimplementation` | `` | root | root | native_train | program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 73.5 | custom_program | 0.4332 | 0.4702 |
| 0 | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 317.7 | external_static_node | 0.3336 | 0.3336 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 39.0 | gated_mlp | 0.4007 | 0.4221 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 39.6 | gated_mlp | 0.3923 | 0.4209 |
| 1 | `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | `official_k562_native_public_best_reimplementation` | program_node | official_string_gnn_attention | native_train | pipeline_program_node | weighted_cross_entropy | gene_graph,perturbation_gene_or_context |  | 71.5 | custom_program | 0.4421 | 0.4805 |
| 2 | `official_k562_native_p3_official_string_neighborhood_attention_68e48066` | `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 72.6 | custom_program | 0.3748 | 0.4426 |
| 3 | `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25` | `official_k562_root_aido_embedding_mlp` | program_node | official_target_graph_conditioned_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 51.9 | custom_program | 0.3544 | 0.3751 |
| 4 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_10091559` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 46.6 | custom_program | 0.3819 | 0.4228 |
| 5 | `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` | `official_k562_public_best_node2_1_1_1_1_1_smoke` | program_node | official_string_gnn_frozen_cache | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 43.1 | custom_program | 0.4276 | 0.4820 |
| 6 | `official_k562_p2_official_aido_string_concat_fusion_2507f645` | `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` | program_node | official_aido_string_concat_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 49.0 | custom_program | 0.3505 | 0.4051 |
| 7 | `official_k562_native_p5_official_temperature_calibrated_head_62cb9d93` | `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | program_node | official_temperature_calibrated_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 61.7 | custom_program | 0.4216 | 0.4556 |
| 8 | `official_k562_native_p2_official_target_low_rank_head_6e80c4ef` | `official_k562_native_p5_official_temperature_calibrated_head_62cb9d93` | program_node | official_target_low_rank_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 61.5 | custom_program | 0.4177 | 0.4408 |
| 9 | `official_k562_native_p2_official_native_public_best_reimplementation_75191c6f` | `official_k562_native_p2_official_target_low_rank_head_6e80c4ef` | program_node | official_native_public_best_reimplementation | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 73.8 | custom_program | 0.4285 | 0.4470 |
| 10 | `official_k562_native_p1_official_target_gene_head_49b66848` | `official_k562_native_p2_official_native_public_best_reimplementation_75191c6f` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 60.4 | custom_program | 0.4164 | 0.4415 |
| 11 | `official_k562_native_p2_official_aido_string_cross_attention_46d7a5a9` | `official_k562_native_p1_official_target_gene_head_49b66848` | program_node | official_aido_string_cross_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 72.3 | custom_program | 0.3841 | 0.4429 |
| 12 | `official_k562_native_p6_official_target_graph_conditioned_head_445330d7` | `official_k562_native_p1_official_target_gene_head_49b66848` | program_node | official_target_graph_conditioned_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 70.7 | custom_program | 0.3869 | 0.4465 |
| 13 | `official_k562_root_aido_gnn_embedding_mlp_p7_official_public_best_node_35cba159` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_public_best_node | external_static_node | program_node | external_static_node | external_public_best_node |  | 309.7 | gated_mlp | 0.3336 | 0.3336 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_native_public_best_reimplementation` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN,public_node_code |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | true | gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p3_official_string_neighborhood_attention_68e48066` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_10091559` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` | true | perturbation_gene_or_context | official_string_gnn_model_dir,official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_p2_official_aido_string_concat_fusion_2507f645` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_string_gnn_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p5_official_temperature_calibrated_head_62cb9d93` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p2_official_target_low_rank_head_6e80c4ef` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p2_official_native_public_best_reimplementation_75191c6f` | true | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_string_gnn_keep20_graph,official_aido_cell_100m_model_dir,official_string_gnn_model_dir |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p1_official_target_gene_head_49b66848` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy | None |
| `official_k562_native_p2_official_aido_string_cross_attention_46d7a5a9` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_string_gnn_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_native_p6_official_target_graph_conditioned_head_445330d7` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_public_best_node_35cba159` | true | external_public_best_node | AIDO.Cell-100M,STRING_GNN |  | `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` | external_static_node | missing_or_val_fallback |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4332 |
| 0 | 0.4332 |
| 0 | 0.4332 |
| 0 | 0.4332 |
| 1 | 0.4421 |
| 2 | 0.4421 |
| 3 | 0.4421 |
| 4 | 0.4421 |
| 5 | 0.4421 |
| 6 | 0.4421 |
| 7 | 0.4421 |
| 8 | 0.4421 |
| 9 | 0.4421 |
| 10 | 0.4421 |
| 11 | 0.4421 |
| 12 | 0.4421 |
| 13 | 0.4421 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=2 val=0.4007 test=0.4221 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p2_official_public_best_node_0d39d5c6` status=pruned_not_selected visits=0 strategy=official_public_best_node pipeline=external_static_node
  - `official_k562_root_aido_embedding_mlp_p3_official_regulatory_network_prior_139ae582` status=pruned_not_selected visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_embedding_mlp_p3_official_regulatory_network_prior_139ae582/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p4_official_focal_loss_training_29e824a9` status=pruned_not_selected visits=0 strategy=official_focal_loss_training program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_embedding_mlp_p4_official_focal_loss_training_29e824a9/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25` status=trained visits=2 val=0.3544 test=0.3751 strategy=official_target_graph_conditioned_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=3 val=0.3923 test=0.4209 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_37668cf6` status=pruned_not_selected visits=0 strategy=official_aido_full_finetune program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_37668cf6/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_2e347318` status=pruned_not_selected visits=0 strategy=official_aido_topk_layer_tuning program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_2e347318/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_scgpt_cell_encoder_e689f05c` status=pruned_not_selected visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_scgpt_cell_encoder_e689f05c/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_10091559` status=trained visits=2 val=0.3819 test=0.4228 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_10091559/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p5_official_target_gene_head_439f47d4` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_target_gene_head_439f47d4/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_fusion_27f8af13` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_string_fusion_27f8af13/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p8_official_aido_full_finetune_34c61d98` status=pruned_not_selected visits=0 strategy=official_aido_full_finetune program=experiments/official_k562_auto_impl_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p8_official_aido_full_finetune_34c61d98/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p7_official_public_best_node_35cba159` status=trained visits=1 val=0.3336 test=0.3336 strategy=official_public_best_node backend=external_static_node pipeline=external_static_node artifacts=perturbation_gene_or_context
- `official_k562_native_public_best_reimplementation` status=trained visits=9 val=0.4332 test=0.4702 backend=native_train artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_native_p4_official_target_gene_head_bb439915` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p4_official_target_gene_head_bb439915/model.py pipeline=pipeline_program_node
  - `official_k562_native_p1_official_aido_string_fusion_66a588f9` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p1_official_aido_string_fusion_66a588f9/model.py pipeline=pipeline_program_node
  - `official_k562_native_p3_official_aido_lora_adapter_9d77b24d` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p3_official_aido_lora_adapter_9d77b24d/model.py pipeline=pipeline_program_node
  - `official_k562_native_p2_official_string_gnn_attention_c7b091ac` status=trained visits=8 val=0.4421 test=0.4805 strategy=official_string_gnn_attention program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p2_official_string_gnn_attention_c7b091ac/model.py backend=native_train pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context
    - `official_k562_native_p2_official_aido_string_cross_attention_a9d31401` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p2_official_aido_string_cross_attention_a9d31401/model.py pipeline=pipeline_program_node
    - `official_k562_native_p4_official_class_imbalance_training_306c7695` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
    - `official_k562_native_p1_official_pathway_pooling_reactome_a3a9a35d` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p1_official_pathway_pooling_reactome_a3a9a35d/model.py pipeline=pipeline_program_node
    - `official_k562_native_p3_official_string_neighborhood_attention_68e48066` status=trained visits=2 val=0.3748 test=0.4426 strategy=official_string_neighborhood_attention program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p3_official_string_neighborhood_attention_68e48066/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_native_p6_official_gene_dropout_augmentation_33f7ea45` status=pruned_not_selected visits=0 strategy=official_gene_dropout_augmentation program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p6_official_gene_dropout_augmentation_33f7ea45/model.py pipeline=pipeline_program_node
    - `official_k562_native_p7_official_layerwise_lr_schedule_38120bc4` status=pruned_not_selected visits=0 strategy=official_layerwise_lr_schedule program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p7_official_layerwise_lr_schedule_38120bc4/model.py pipeline=pipeline_program_node
    - `official_k562_native_p8_official_swa_or_checkpoint_ensemble_32cd2370` status=pruned_not_selected visits=0 strategy=official_swa_or_checkpoint_ensemble program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p8_official_swa_or_checkpoint_ensemble_32cd2370/model.py pipeline=pipeline_program_node
    - `official_k562_native_p5_official_temperature_calibrated_head_62cb9d93` status=trained visits=7 val=0.4216 test=0.4556 strategy=official_temperature_calibrated_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p5_official_temperature_calibrated_head_62cb9d93/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_native_p3_official_target_bilinear_head_69c529c3` status=pruned_not_selected visits=0 strategy=official_target_bilinear_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p3_official_target_bilinear_head_69c529c3/model.py pipeline=pipeline_program_node
      - `official_k562_native_p1_official_multimodal_mixture_of_experts_a3975739` status=pruned_not_selected visits=0 strategy=official_multimodal_mixture_of_experts program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p1_official_multimodal_mixture_of_experts_a3975739/model.py pipeline=pipeline_program_node
      - `official_k562_native_p4_official_public_static_node_family_wrapper_c8b4298c` status=pruned_not_selected visits=0 strategy=official_public_static_node_family_wrapper program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p4_official_public_static_node_family_wrapper_c8b4298c/model.py pipeline=pipeline_program_node
      - `official_k562_native_p2_official_target_low_rank_head_6e80c4ef` status=trained visits=6 val=0.4177 test=0.4408 strategy=official_target_low_rank_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p2_official_target_low_rank_head_6e80c4ef/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
        - `official_k562_native_p3_official_string_gnn_attention_13271107` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p3_official_string_gnn_attention_13271107/model.py pipeline=pipeline_program_node
        - `official_k562_native_p1_official_aido_string_fusion_f2b3ebbf` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p1_official_aido_string_fusion_f2b3ebbf/model.py pipeline=pipeline_program_node
        - `official_k562_native_p4_official_aido_lora_adapter_5d95e7b7` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p4_official_aido_lora_adapter_5d95e7b7/model.py pipeline=pipeline_program_node
        - `official_k562_native_p2_official_native_public_best_reimplementation_75191c6f` status=trained visits=4 val=0.4285 test=0.4470 strategy=official_native_public_best_reimplementation program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p2_official_native_public_best_reimplementation_75191c6f/model.py backend=native_train pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
          - `official_k562_native_p4_official_string_gnn_attention_babc98da` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p4_official_string_gnn_attention_babc98da/model.py pipeline=pipeline_program_node
          - `official_k562_native_p2_official_aido_string_fusion_77966388` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p2_official_aido_string_fusion_77966388/model.py pipeline=pipeline_program_node
          - `official_k562_native_p3_official_pathway_pooling_reactome_fb339f7d` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p3_official_pathway_pooling_reactome_fb339f7d/model.py pipeline=pipeline_program_node
          - `official_k562_native_p1_official_target_gene_head_49b66848` status=trained visits=3 val=0.4164 test=0.4415 strategy=official_target_gene_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p1_official_target_gene_head_49b66848/model.py backend=native_train pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
            - `official_k562_native_p3_official_target_gene_head_0431e395` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p3_official_target_gene_head_0431e395/model.py pipeline=pipeline_program_node
            - `official_k562_native_p1_official_aido_lora_adapter_a70dea63` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p1_official_aido_lora_adapter_a70dea63/model.py pipeline=pipeline_program_node
            - `official_k562_native_p4_official_aido_string_fusion_1a0a335f` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p4_official_aido_string_fusion_1a0a335f/model.py pipeline=pipeline_program_node
            - `official_k562_native_p2_official_aido_string_cross_attention_46d7a5a9` status=trained visits=2 val=0.3841 test=0.4429 strategy=official_aido_string_cross_attention program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p2_official_aido_string_cross_attention_46d7a5a9/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
            - `official_k562_native_p5_official_aido_lora_adapter_22e1b0b9` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p5_official_aido_lora_adapter_22e1b0b9/model.py pipeline=pipeline_program_node
            - `official_k562_native_p7_official_aido_string_cross_attention_0f7c7520` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p7_official_aido_string_cross_attention_0f7c7520/model.py pipeline=pipeline_program_node
            - `official_k562_native_p8_official_focal_loss_training_7a4d9d97` status=pruned_not_selected visits=0 strategy=official_focal_loss_training program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p8_official_focal_loss_training_7a4d9d97/model.py pipeline=pipeline_program_node
            - `official_k562_native_p6_official_target_graph_conditioned_head_445330d7` status=trained visits=2 val=0.3869 test=0.4465 strategy=official_target_graph_conditioned_head program=experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p6_official_target_graph_conditioned_head_445330d7/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_public_best_node2_1_1_1_1_1_smoke` status=trained visits=3 val=0.3336 test=0.3336 backend=external_static_node
  - `official_k562_p4_official_string_laplacian_smoothing_208df089` status=pruned_not_selected visits=0 strategy=official_string_laplacian_smoothing program=experiments/official_k562_auto_impl_64x16/programs/official_k562_p4_official_string_laplacian_smoothing_208df089/model.py pipeline=pipeline_program_node
  - `official_k562_p3_official_string_gnn_full_finetune_1881d60a` status=pruned_not_selected visits=0 strategy=official_string_gnn_full_finetune program=experiments/official_k562_auto_impl_64x16/programs/official_k562_p3_official_string_gnn_full_finetune_1881d60a/model.py pipeline=pipeline_program_node
  - `official_k562_p1_official_scfoundation_top_layer_finetune_2a9665c5` status=pruned_not_selected visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_auto_impl_64x16/programs/official_k562_p1_official_scfoundation_top_layer_finetune_2a9665c5/model.py pipeline=pipeline_program_node
  - `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` status=trained visits=3 val=0.4276 test=0.4820 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_auto_impl_64x16/programs/official_k562_p2_official_string_gnn_frozen_cache_38234ef6/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_p3_official_aido_string_gated_fusion_5ce43b05` status=pruned_not_selected visits=0 strategy=official_aido_string_gated_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_p3_official_aido_string_gated_fusion_5ce43b05/model.py pipeline=pipeline_program_node
    - `official_k562_p4_official_aido_string_bilinear_fusion_ca398bbe` status=pruned_not_selected visits=0 strategy=official_aido_string_bilinear_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_p4_official_aido_string_bilinear_fusion_ca398bbe/model.py pipeline=pipeline_program_node
    - `official_k562_p1_official_weighted_ce_training_abea1e53` status=pruned_not_selected visits=0 strategy=official_weighted_ce_training program=experiments/official_k562_auto_impl_64x16/programs/official_k562_p1_official_weighted_ce_training_abea1e53/model.py pipeline=pipeline_program_node
    - `official_k562_p2_official_aido_string_concat_fusion_2507f645` status=trained visits=2 val=0.3505 test=0.4051 strategy=official_aido_string_concat_fusion program=experiments/official_k562_auto_impl_64x16/programs/official_k562_p2_official_aido_string_concat_fusion_2507f645/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context

## Reproducibility Notes

- In paper-aligned mode, one node means one candidate program state, not necessarily one completed training run.
- `pruned_not_selected` proposals are deliberately not trained; they document the agent's search space and cheap-screen decision.
- `selected_for_training` is a transient rollout state written before execution; successful nodes become `trained`, failed nodes become `failed`.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
