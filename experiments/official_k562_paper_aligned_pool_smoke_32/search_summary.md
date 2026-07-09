# VCHarness-Style K562 Search Summary

This run separates the search loop into MCTS parent selection, proposal-pool generation, cheap screening/pruning, selected rollout execution, and reward backpropagation.
In paper-aligned mode, a node may be proposed, pruned, blocked for artifact acquisition, selected for training, pending implementation, failed, or trained. Only trained rollout nodes backpropagate reward to MCTS.

- Stop reason: proposal budget exhausted (32/32)
- Proposal-like nodes: 36
- Trained nodes: 11
- Pruned proposals: 25
- Blocked/acquisition nodes: 0
- Pending implementation nodes: 0
- Selected-for-training nodes: 0
- Failed nodes: 0
- Failure/acquisition records: 0
- Best node: `official_k562_native_p2_official_aido_string_concat_fusion_5570bf15` val=0.4258 test=0.4831
- Best root: `official_k562_native_public_best_reimplementation` val=0.4032 test=0.4749
- Improvement over best root: 0.0226 validation Macro-F1

## Search State Counts

| Status | Count |
|---|---:|
| `pruned_not_selected` | 25 |
| `trained` | 11 |

## Root Baselines

| Node | Data dir | Model | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_native_public_best_reimplementation` | `data/cell_lines/official_k562_cls` | custom_program | 0.4032 | 0.4749 |
| `official_k562_public_best_node2_1_1_1_1_1_smoke` | `data/cell_lines/official_k562_cls` | external_static_node | 0.3336 | 0.3336 |
| `official_k562_root_aido_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.3936 | 0.4068 |
| `official_k562_root_aido_gnn_embedding_mlp` | `data/cell_lines/official_k562_cls` | gated_mlp | 0.4011 | 0.4302 |

## All Trained Nodes

| Iter | Node | Parent | Kind | Strategy | Backend | Pipeline | Loss | Artifact sides | Missing req. | Sec | Model | Val | Test |
|---:|---|---|---|---|---|---|---|---|---|---:|---|---:|---:|
| 0 | `official_k562_native_public_best_reimplementation` | `` | root | root | native_train | program_node | weighted_cross_entropy | AIDO.Cell-100M,gene_graph,perturbation_gene_or_context |  | 75.4 | custom_program | 0.4032 | 0.4749 |
| 0 | `official_k562_public_best_node2_1_1_1_1_1_smoke` | `` | root | root | external_static_node | program_node | external_static_node | external_public_best_node |  | 310.7 | external_static_node | 0.3336 | 0.3336 |
| 0 | `official_k562_root_aido_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 38.8 | gated_mlp | 0.3936 | 0.4068 |
| 0 | `official_k562_root_aido_gnn_embedding_mlp` | `` | root | root | native_train | model_only | weighted_cross_entropy | perturbation_gene_or_context |  | 39.3 | gated_mlp | 0.4011 | 0.4302 |
| 1 | `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | `official_k562_native_public_best_reimplementation` | program_node | official_string_gnn_attention | native_train | pipeline_program_node | weighted_cross_entropy | gene_graph,perturbation_gene_or_context |  | 71.4 | custom_program | 0.3702 | 0.4450 |
| 2 | `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` | `official_k562_root_aido_gnn_embedding_mlp` | program_node | official_string_neighborhood_attention | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 67.7 | custom_program | 0.3552 | 0.3817 |
| 3 | `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25` | `official_k562_root_aido_embedding_mlp` | program_node | official_target_graph_conditioned_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 72.0 | custom_program | 0.3505 | 0.3744 |
| 4 | `official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30` | `official_k562_native_p2_official_string_gnn_attention_c7b091ac` | program_node | official_aido_cached_embedding_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 61.5 | custom_program | 0.4116 | 0.4840 |
| 5 | `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` | `official_k562_public_best_node2_1_1_1_1_1_smoke` | program_node | official_string_gnn_frozen_cache | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 50.8 | custom_program | 0.3778 | 0.4404 |
| 6 | `official_k562_native_p2_official_aido_string_concat_fusion_5570bf15` | `official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30` | program_node | official_aido_string_concat_fusion | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 61.9 | custom_program | 0.4258 | 0.4831 |
| 7 | `official_k562_native_p2_official_target_low_rank_head_ae932f98` | `official_k562_native_p2_official_aido_string_concat_fusion_5570bf15` | program_node | official_target_low_rank_head | native_train | pipeline_program_node | weighted_cross_entropy | perturbation_gene_or_context |  | 61.4 | custom_program | 0.4215 | 0.4424 |

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

## Best-So-Far Curve

| Iter | Best val Macro-F1 |
|---:|---:|
| 0 | 0.4032 |
| 0 | 0.4032 |
| 0 | 0.4032 |
| 0 | 0.4032 |
| 1 | 0.4032 |
| 2 | 0.4032 |
| 3 | 0.4032 |
| 4 | 0.4116 |
| 5 | 0.4116 |
| 6 | 0.4258 |
| 7 | 0.4258 |

## Tree

- `official_k562_root_aido_embedding_mlp` status=trained visits=2 val=0.3936 test=0.4068 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_embedding_mlp_p2_official_public_best_node_0d39d5c6` status=pruned_not_selected visits=0 strategy=official_public_best_node pipeline=external_static_node
  - `official_k562_root_aido_embedding_mlp_p3_official_regulatory_network_prior_139ae582` status=pruned_not_selected visits=0 strategy=official_regulatory_network_prior program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_root_aido_embedding_mlp_p3_official_regulatory_network_prior_139ae582/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p4_official_focal_loss_training_29e824a9` status=pruned_not_selected visits=0 strategy=official_focal_loss_training program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_root_aido_embedding_mlp_p4_official_focal_loss_training_29e824a9/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25` status=trained visits=2 val=0.3505 test=0.3744 strategy=official_target_graph_conditioned_head program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_4405dd25/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_root_aido_gnn_embedding_mlp` status=trained visits=2 val=0.4011 test=0.4302 backend=native_train artifacts=perturbation_gene_or_context
  - `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15` status=pruned_not_selected visits=0 strategy=official_aido_string_cross_attention program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_76c8dc15/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p4_official_class_imbalance_training_fdd8ca75` status=pruned_not_selected visits=0 strategy=official_class_imbalance_training pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab` status=pruned_not_selected visits=0 strategy=official_pathway_pooling_reactome program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_6cfe87ab/model.py pipeline=pipeline_program_node
  - `official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1` status=trained visits=2 val=0.3552 test=0.3817 strategy=official_string_neighborhood_attention program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_8f579df1/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
- `official_k562_native_public_best_reimplementation` status=trained visits=5 val=0.4032 test=0.4749 backend=native_train artifacts=AIDO.Cell-100M,gene_graph,perturbation_gene_or_context
  - `official_k562_native_p4_official_target_gene_head_bb439915` status=pruned_not_selected visits=0 strategy=official_target_gene_head program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p4_official_target_gene_head_bb439915/model.py pipeline=pipeline_program_node
  - `official_k562_native_p1_official_aido_string_fusion_66a588f9` status=pruned_not_selected visits=0 strategy=official_aido_string_fusion program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p1_official_aido_string_fusion_66a588f9/model.py pipeline=pipeline_program_node
  - `official_k562_native_p3_official_aido_lora_adapter_9d77b24d` status=pruned_not_selected visits=0 strategy=official_aido_lora_adapter program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p3_official_aido_lora_adapter_9d77b24d/model.py pipeline=pipeline_program_node
  - `official_k562_native_p2_official_string_gnn_attention_c7b091ac` status=trained visits=4 val=0.3702 test=0.4450 strategy=official_string_gnn_attention program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p2_official_string_gnn_attention_c7b091ac/model.py backend=native_train pipeline=pipeline_program_node artifacts=gene_graph,perturbation_gene_or_context
    - `official_k562_native_p1_official_aido_full_finetune_253d0020` status=pruned_not_selected visits=0 strategy=official_aido_full_finetune program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p1_official_aido_full_finetune_253d0020/model.py pipeline=pipeline_program_node
    - `official_k562_native_p2_official_aido_topk_layer_tuning_1543d9b3` status=pruned_not_selected visits=0 strategy=official_aido_topk_layer_tuning program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p2_official_aido_topk_layer_tuning_1543d9b3/model.py pipeline=pipeline_program_node
    - `official_k562_native_p4_official_scgpt_cell_encoder_6dea72bd` status=pruned_not_selected visits=0 strategy=official_scgpt_cell_encoder program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p4_official_scgpt_cell_encoder_6dea72bd/model.py pipeline=pipeline_program_node
    - `official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30` status=trained visits=4 val=0.4116 test=0.4840 strategy=official_aido_cached_embedding_fusion program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
      - `official_k562_native_p3_official_aido_string_gated_fusion_d3b6aa98` status=pruned_not_selected visits=0 strategy=official_aido_string_gated_fusion program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p3_official_aido_string_gated_fusion_d3b6aa98/model.py pipeline=pipeline_program_node
      - `official_k562_native_p4_official_aido_string_bilinear_fusion_6d5f4458` status=pruned_not_selected visits=0 strategy=official_aido_string_bilinear_fusion program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p4_official_aido_string_bilinear_fusion_6d5f4458/model.py pipeline=pipeline_program_node
      - `official_k562_native_p1_official_weighted_ce_training_1147ed60` status=pruned_not_selected visits=0 strategy=official_weighted_ce_training program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p1_official_weighted_ce_training_1147ed60/model.py pipeline=pipeline_program_node
      - `official_k562_native_p2_official_aido_string_concat_fusion_5570bf15` status=trained visits=3 val=0.4258 test=0.4831 strategy=official_aido_string_concat_fusion program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p2_official_aido_string_concat_fusion_5570bf15/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
        - `official_k562_native_p3_official_target_bilinear_head_17b86b22` status=pruned_not_selected visits=0 strategy=official_target_bilinear_head program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p3_official_target_bilinear_head_17b86b22/model.py pipeline=pipeline_program_node
        - `official_k562_native_p1_official_multimodal_mixture_of_experts_0b2158d0` status=pruned_not_selected visits=0 strategy=official_multimodal_mixture_of_experts program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p1_official_multimodal_mixture_of_experts_0b2158d0/model.py pipeline=pipeline_program_node
        - `official_k562_native_p4_official_public_static_node_family_wrapper_d783bafb` status=pruned_not_selected visits=0 strategy=official_public_static_node_family_wrapper program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p4_official_public_static_node_family_wrapper_d783bafb/model.py pipeline=pipeline_program_node
        - `official_k562_native_p2_official_target_low_rank_head_ae932f98` status=trained visits=2 val=0.4215 test=0.4424 strategy=official_target_low_rank_head program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p2_official_target_low_rank_head_ae932f98/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context
          - `official_k562_native_p2_official_gene_dropout_augmentation_c2c80ae6` status=pruned_not_selected visits=0 strategy=official_gene_dropout_augmentation program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p2_official_gene_dropout_augmentation_c2c80ae6/model.py pipeline=pipeline_program_node
          - `official_k562_native_p3_official_layerwise_lr_schedule_c026facb` status=pruned_not_selected visits=0 strategy=official_layerwise_lr_schedule program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p3_official_layerwise_lr_schedule_c026facb/model.py pipeline=pipeline_program_node
          - `official_k562_native_p4_official_swa_or_checkpoint_ensemble_4a7aad6e` status=pruned_not_selected visits=0 strategy=official_swa_or_checkpoint_ensemble program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p4_official_swa_or_checkpoint_ensemble_4a7aad6e/model.py pipeline=pipeline_program_node
          - `official_k562_native_p1_official_temperature_calibrated_head_ad83be07` status=pruned_not_selected visits=0 strategy=official_temperature_calibrated_head program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p1_official_temperature_calibrated_head_ad83be07/model.py pipeline=pipeline_program_node
- `official_k562_public_best_node2_1_1_1_1_1_smoke` status=trained visits=2 val=0.3336 test=0.3336 backend=external_static_node
  - `official_k562_p4_official_string_laplacian_smoothing_208df089` status=pruned_not_selected visits=0 strategy=official_string_laplacian_smoothing program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_p4_official_string_laplacian_smoothing_208df089/model.py pipeline=pipeline_program_node
  - `official_k562_p3_official_string_gnn_full_finetune_1881d60a` status=pruned_not_selected visits=0 strategy=official_string_gnn_full_finetune program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_p3_official_string_gnn_full_finetune_1881d60a/model.py pipeline=pipeline_program_node
  - `official_k562_p1_official_scfoundation_top_layer_finetune_2a9665c5` status=pruned_not_selected visits=0 strategy=official_scfoundation_top_layer_finetune program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_p1_official_scfoundation_top_layer_finetune_2a9665c5/model.py pipeline=pipeline_program_node
  - `official_k562_p2_official_string_gnn_frozen_cache_38234ef6` status=trained visits=2 val=0.3778 test=0.4404 strategy=official_string_gnn_frozen_cache program=experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_p2_official_string_gnn_frozen_cache_38234ef6/model.py pipeline=pipeline_program_node artifacts=perturbation_gene_or_context

## Reproducibility Notes

- In paper-aligned mode, one node means one candidate program state, not necessarily one completed training run.
- `pruned_not_selected` proposals are deliberately not trained; they document the agent's search space and cheap-screen decision.
- `selected_for_training` is a transient rollout state written before execution; successful nodes become `trained`, failed nodes become `failed`.
- MCTS decides which already-trained parent is worth expanding next. The paper-aligned default is UCT; PUCT is retained only as an optional implementation extension/ablation.
- Tree/proposal records preserve UCT-style audit fields when available: visits, Q_v, Exploitation, Exploration, uct, stage, and selected-parent candidates.
- Pipeline records preserve model, training/loss, artifact requirements, artifact usage claims, duration, and missing-artifact status for each node.
- The proposal agent decides how to modify that parent into one executable child config or node-local model program.
- The node workspace under `nodes/` is intentionally ignored by git; committed summaries live in `tree.json`, `search_summary.md`, and `proposals/`.
