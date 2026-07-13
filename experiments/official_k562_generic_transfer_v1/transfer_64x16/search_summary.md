# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, pruned, blocked for artifact acquisition, selected for training, pending implementation, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: requires artifact acquisition for official_aido_string_cross_attention: official_string_gnn_model_dir
- Proposal-like nodes: 46
- Trained nodes: 11
- Pruned proposals: 33
- Blocked/acquisition nodes: 2
- Pending implementation nodes: 0
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 2
- Best node: `official_k562_root_aido_gnn_embedding_mlp` val=0.4053 test=0.4486
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.4053 test=0.4486
- Improvement over best root: 0.0000 validation Macro-F1

## Automatic Implementation Loop

| Metric | Count |
|---|---:|
| Auto implementation records | 1 |
| Native smoke passed | 0 |
| Repair/implementation log rows | 9 |
| Repair failures | 0 |
| Requires external Codex | 10 |
| Blocked missing artifact | 0 |
| Trained and backpropagated | 0 |

| Item status | Count |
|---|---:|
| `requires_external_codex` | 1 |

| Decision event | Count |
|---|---:|
| `implementation_selected` | 9 |
| `requires_external_codex` | 9 |

- Implementation agent report: `experiments/official_k562_generic_transfer_v1/transfer_64x16/implementation_agent_report.json`
- Repair log: `experiments/official_k562_generic_transfer_v1/transfer_64x16/repair_log.jsonl`
- Agent decision trace: `experiments/official_k562_generic_transfer_v1/transfer_64x16/agent_decision_trace.jsonl`

## Search State Counts

| Status | Count |
|---|---:|
| `pruned_not_selected` | 33 |
| `requires_artifact_acquisition` | 2 |
| `trained` | 11 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3953 | 0.4122 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4053 | 0.4486 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 40.2 | gated_mlp | 0.3953 | 0.4122 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 40.6 | gated_mlp | 0.4053 | 0.4486 |
| 1 | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 55.7 | custom_program | 0.3428 | 0.3797 |
| 2 | `official_k562_root_aido_embedding_mlp_p3_official_string_neighborhood_attention_898d7103` | `official_k562_root_aido_embedding_mlp` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 126.9 | custom_program | 0.3552 | 0.3842 |
| 3 | `official_k562_root_aido_embedding_mlp_p7_official_aido_cached_embedding_fusion_7cfdea7c` | `official_k562_root_aido_embedding_mlp` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 53.2 | custom_program | 0.3268 | 0.3422 |
| 5 | `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_10827e49` | `official_k562_root_aido_embedding_mlp_p3_official_string_neighborhood_attention_898d7103` | program_node | official_target_graph_conditioned_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 126.0 | custom_program | 0.3554 | 0.3836 |
| 6 | `official_k562_root_aido_embedding_mlp_p1_official_string_laplacian_smoothing_dc9fe3d0` | `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_10827e49` | program_node | official_string_laplacian_smoothing | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 72.1 | custom_program | 0.3456 | 0.3749 |
| 7 | `official_k562_root_aido_embedding_mlp_p2_official_target_low_rank_head_a90e331d` | `official_k562_root_aido_embedding_mlp_p1_official_string_laplacian_smoothing_dc9fe3d0` | program_node | official_target_low_rank_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 52.4 | custom_program | 0.3535 | 0.3830 |
| 8 | `official_k562_root_aido_embedding_mlp_p1_official_temperature_calibrated_head_1f61c967` | `official_k562_root_aido_embedding_mlp_p2_official_target_low_rank_head_a90e331d` | program_node | official_temperature_calibrated_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 54.1 | custom_program | 0.3521 | 0.3783 |
| 9 | `official_k562_root_aido_embedding_mlp_p4_official_aido_lora_adapter_c468633e` | `official_k562_root_aido_embedding_mlp_p1_official_temperature_calibrated_head_1f61c967` | program_node | official_aido_lora_adapter | native_train | pipeline_program_node | weighted_cross_entropy | AIDO.Cell-100M,perturbation_gene_or_context |  | 54.3 | custom_program | 0.3328 | 0.3533 |
| 10 | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_649e5781` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | program_node | official_target_gene_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 56.8 | custom_program | 0.3535 | 0.3833 |

## Artifact And Pipeline Audit

| Node | Uses artifact | Artifact sides | Required artifacts | Missing required | Manifest | Loss | Test metric source |
|---|---:|---|---|---|---|---|---|
| `official_k562_root_aido_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp` | true | perturbation_gene_or_context |  |  | `` | weighted_cross_entropy | None |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p3_official_string_neighborhood_attention_898d7103` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p7_official_aido_cached_embedding_fusion_7cfdea7c` | true | perturbation_gene_or_context | official_aido_cell_100m_model_dir,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_10827e49` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p1_official_string_laplacian_smoothing_dc9fe3d0` | true | perturbation_gene_or_context | official_string_gnn_keep20_graph,official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p2_official_target_low_rank_head_a90e331d` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p1_official_temperature_calibrated_head_1f61c967` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_embedding_mlp_p4_official_aido_lora_adapter_c468633e` | true | AIDO.Cell-100M,perturbation_gene_or_context | official_essential_deg_with_split_h5ad,official_aido_cell_100m_model_dir |  | `` | weighted_cross_entropy |  |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_649e5781` | true | perturbation_gene_or_context | official_essential_deg_with_split_h5ad |  | `` | weighted_cross_entropy |  |

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.3953 |
| 0 | 0.4053 |
| 1 | 0.4053 |
| 2 | 0.4053 |
| 3 | 0.4053 |
| 5 | 0.4053 |
| 6 | 0.4053 |
| 7 | 0.4053 |
| 8 | 0.4053 |
| 9 | 0.4053 |
| 10 | 0.4053 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=8 val=0.3953 test=0.4122 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p4_official_class_imbalance_training_f1ee4c8d` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p2_official_aido_string_cross_attention_ac799500/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p3_official_string_neighborhood_attention_898d7103` status=trained visits=7 val=0.3552 test=0.3842 strategy=official_string_neighborhood_attention program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p3_official_string_neighborhood_attention_898d7103/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_embedding_mlp_p3_official_regulatory_network_prior_5c69a58d` status=pruned_not_selected visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p3_official_regulatory_network_prior_5c69a58d/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p4_official_focal_loss_training_46cb4208` status=pruned_not_selected visits=0 strategy=official_focal_loss_training program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p4_official_focal_loss_training_46cb4208/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_embedding_mlp_p2_official_public_best_node_3cf08432` status=pruned_not_selected visits=0 strategy=official_public_best_node pipeline=external_static_node
    - `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_10827e49` status=trained visits=6 val=0.3554 test=0.3836 strategy=official_target_graph_conditioned_head program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_10827e49/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_root_aido_embedding_mlp_p2_official_aido_string_concat_fusion_e1ed497a` status=pruned_not_selected visits=0 strategy=official_aido_string_concat_fusion program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p2_official_aido_string_concat_fusion_e1ed497a/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_embedding_mlp_p3_official_aido_string_gated_fusion_8488adda` status=pruned_not_selected visits=0 strategy=official_aido_string_gated_fusion program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p3_official_aido_string_gated_fusion_8488adda/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_embedding_mlp_p4_official_aido_string_bilinear_fusion_48b74f3d` status=pruned_not_selected visits=0 strategy=official_aido_string_bilinear_fusion program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p4_official_aido_string_bilinear_fusion_48b74f3d/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_embedding_mlp_p1_official_string_laplacian_smoothing_dc9fe3d0` status=trained visits=5 val=0.3456 test=0.3749 strategy=official_string_laplacian_smoothing program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p1_official_string_laplacian_smoothing_dc9fe3d0/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
        - `official_k562_root_aido_embedding_mlp_p3_official_target_bilinear_head_87ebf2db` status=pruned_not_selected visits=0 strategy=official_target_bilinear_head program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p3_official_target_bilinear_head_87ebf2db/model.py pipeline=pipeline_program_node
        - `official_k562_root_aido_embedding_mlp_p1_official_multimodal_mixture_of_experts_0892f485` status=pruned_not_selected visits=0 strategy=official_multimodal_mixture_of_experts program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p1_official_multimodal_mixture_of_experts_0892f485/model.py pipeline=pipeline_program_node
        - `official_k562_root_aido_embedding_mlp_p4_official_public_static_node_family_wrapper_ee1b2b4f` status=pruned_not_selected visits=0 strategy=official_public_static_node_family_wrapper program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p4_official_public_static_node_family_wrapper_ee1b2b4f/model.py pipeline=pipeline_program_node
        - `official_k562_root_aido_embedding_mlp_p2_official_target_low_rank_head_a90e331d` status=trained visits=4 val=0.3535 test=0.3830 strategy=official_target_low_rank_head program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p2_official_target_low_rank_head_a90e331d/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
          - `official_k562_root_aido_embedding_mlp_p2_official_gene_dropout_augmentation_02f005dc` status=pruned_not_selected visits=0 strategy=official_gene_dropout_augmentation program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p2_official_gene_dropout_augmentation_02f005dc/model.py pipeline=pipeline_program_node
          - `official_k562_root_aido_embedding_mlp_p3_official_layerwise_lr_schedule_0d6a63e8` status=pruned_not_selected visits=0 strategy=official_layerwise_lr_schedule program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p3_official_layerwise_lr_schedule_0d6a63e8/model.py pipeline=pipeline_program_node
          - `official_k562_root_aido_embedding_mlp_p4_official_swa_or_checkpoint_ensemble_81fb02a1` status=pruned_not_selected visits=0 strategy=official_swa_or_checkpoint_ensemble program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p4_official_swa_or_checkpoint_ensemble_81fb02a1/model.py pipeline=pipeline_program_node
          - `official_k562_root_aido_embedding_mlp_p1_official_temperature_calibrated_head_1f61c967` status=trained visits=3 val=0.3521 test=0.3783 strategy=official_temperature_calibrated_head program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p1_official_temperature_calibrated_head_1f61c967/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
            - `official_k562_root_aido_embedding_mlp_p3_official_string_gnn_attention_47e5808f` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p3_official_string_gnn_attention_47e5808f/model.py pipeline=pipeline_program_node
            - `official_k562_root_aido_embedding_mlp_p1_official_aido_string_fusion_bc76ecad` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p1_official_aido_string_fusion_bc76ecad/model.py pipeline=pipeline_program_node
            - `official_k562_root_aido_embedding_mlp_p2_official_native_public_best_reimplementation_2e08b7e4` status=pruned_not_selected visits=0 strategy=official_native_public_best_reimplementation program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p2_official_native_public_best_reimplementation_2e08b7e4/model.py pipeline=pipeline_program_node
            - `official_k562_root_aido_embedding_mlp_p4_official_aido_lora_adapter_c468633e` status=trained visits=2 val=0.3328 test=0.3533 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p4_official_aido_lora_adapter_c468633e/model.py pipeline=pipeline_program_node artifacts=AIDO.Cell-100M,perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p5_official_aido_full_finetune_3058c77a` status=pruned_not_selected visits=0 strategy=official_aido_full_finetune program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p5_official_aido_full_finetune_3058c77a/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p6_official_aido_topk_layer_tuning_6769f267` status=pruned_not_selected visits=0 strategy=official_aido_topk_layer_tuning program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p6_official_aido_topk_layer_tuning_6769f267/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p8_official_scfoundation_top_layer_finetune_2e7dd981` status=pruned_not_selected visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p8_official_scfoundation_top_layer_finetune_2e7dd981/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p7_official_aido_cached_embedding_fusion_7cfdea7c` status=trained visits=2 val=0.3268 test=0.3422 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_embedding_mlp_p7_official_aido_cached_embedding_fusion_7cfdea7c/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=3 val=0.4053 test=0.4486 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` status=trained visits=3 val=0.3428 test=0.3797 strategy=official_target_gene_head program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
    - `official_k562_root_aido_gnn_embedding_mlp_p3_official_pathway_pooling_reactome_809c59fc` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_pathway_pooling_reactome_809c59fc/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p4_official_string_gnn_attention_c802e42c` status=pruned_not_selected visits=0 strategy=official_string_gnn_attention program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_string_gnn_attention_c802e42c/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_fusion_df7d3b5c` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_fusion_df7d3b5c/model.py pipeline=pipeline_program_node
    - `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_649e5781` status=trained visits=2 val=0.3535 test=0.3833 strategy=official_target_gene_head program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_649e5781/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_root_aido_gnn_embedding_mlp_p3_official_target_gene_head_58c83acf` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_target_gene_head_58c83acf/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_47c95e70` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_47c95e70/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_gnn_embedding_mlp_p4_official_aido_string_fusion_a3d78906` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_aido_string_fusion_a3d78906/model.py pipeline=pipeline_program_node
      - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_ec2c0082` status=requires_artifact_acquisition visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_ec2c0082/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p6_official_string_gnn_frozen_cache_13e2bc96` status=pruned_not_selected visits=0 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p6_official_string_gnn_frozen_cache_13e2bc96/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p5_official_scgpt_cell_encoder_3141ef92` status=pruned_not_selected visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p5_official_scgpt_cell_encoder_3141ef92/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p7_official_string_gnn_full_finetune_969bb45b` status=pruned_not_selected visits=0 strategy=official_string_gnn_full_finetune program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p7_official_string_gnn_full_finetune_969bb45b/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p8_official_weighted_ce_training_2988ee3e` status=requires_artifact_acquisition visits=0 strategy=official_weighted_ce_training program=experiments/official_k562_generic_transfer_v1/transfer_64x16/programs/official_k562_root_aido_gnn_embedding_mlp_p8_official_weighted_ce_training_2988ee3e/model.py pipeline=pipeline_program_node

## Failures

| Node | Parent | Error |
|---|---|---|
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_weighted_ce_training_2988ee3e` | `official_k562_root_aido_gnn_embedding_mlp` | requires_artifact_acquisition |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_ec2c0082` | `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_649e5781` | requires_artifact_acquisition |

## Reproducibility Notes

- In paper-aligned mode, one node means one candidate program state, not necessarily one completed training run.
- `pruned_not_selected` proposals are deliberately not trained; they document the agent's search space and cheap-screen decision.
- `selected_for_training` is a transient rollout state written before execution; successful nodes become `trained`, failed nodes become `failed`.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
