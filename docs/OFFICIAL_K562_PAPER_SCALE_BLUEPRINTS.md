# Official K562 Paper-Scale Blueprint Space

This is the explicit official K562 MCTS search-space checklist. It intentionally separates selectable blueprint definitions from pre-implementation. Formal paper-level runs forbid fallback models and compact/proxy/simplified native stand-ins.

- Paper-scale K562 budget target: 600+ candidate nodes.
- Public benchmark scaffold: 154 public K562 static nodes.
- Official selectable blueprint count: 33.
- Implemented now: 2.
- Planned for Codex on demand: 31.

| ID | Status | Family | Level | Cost | Codex action when selected | Required artifacts |
|---|---|---|---:|---|---|---|
| `official_native_public_best_reimplementation` | `planned` | `public_vcharness_best_path_native_exact` | 5 | `expensive` | implement full public-static recipe port on selection; proxy forbidden | official_public_best_node_code, official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_public_best_node` | `implemented` | `public_vcharness_best_path` | 5 | `expensive` | run immediately | official_public_best_node_code, official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_lora_adapter` | `planned` | `AIDO_adapter` | 5 | `expensive` | implement full artifact-backed model.py/config patch on selection | official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad |
| `official_string_gnn_attention` | `planned` | `STRING_GNN_attention` | 5 | `medium` | implement full artifact-backed model.py/config patch on selection | official_string_gnn_model_dir, official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_aido_string_fusion` | `planned` | `AIDO_STRING_fusion` | 5 | `expensive` | implement full artifact-backed model.py/config patch on selection | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_target_gene_head` | `planned` | `target_gene_aware_head` | 4 | `cheap` | implement full artifact-backed model.py/config patch on selection | official_essential_deg_with_split_h5ad |
| `official_class_imbalance_training` | `implemented` | `official_deg_imbalance` | 1 | `cheap` | run immediately | official_essential_deg_with_split_h5ad, class_distribution |
| `official_aido_full_finetune` | `planned` | `AIDO_full_finetune` | 5 | `expensive` | planned_for_codex_on_selection | official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_topk_layer_tuning` | `planned` | `AIDO_selective_finetune` | 5 | `expensive` | planned_for_codex_on_selection | official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_cached_embedding_fusion` | `planned` | `AIDO_cached_embedding` | 5 | `medium` | planned_for_codex_on_selection | official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad |
| `official_scgpt_cell_encoder` | `planned` | `scGPT_or_single_cell_encoder` | 5 | `expensive` | planned_for_codex_on_selection | single_cell_foundation_model_artifact, official_essential_deg_with_split_h5ad |
| `official_scfoundation_top_layer_finetune` | `planned` | `scFoundation_selective_finetune` | 5 | `expensive` | planned_for_codex_on_selection | scfoundation_cell_embeddings, official_essential_deg_with_split_h5ad |
| `official_string_gnn_frozen_cache` | `planned` | `STRING_GNN_frozen_cached` | 5 | `medium` | planned_for_codex_on_selection | official_string_gnn_model_dir, official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_string_gnn_full_finetune` | `planned` | `STRING_GNN_full_finetune` | 5 | `expensive` | planned_for_codex_on_selection | official_string_gnn_model_dir, official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_string_neighborhood_attention` | `planned` | `STRING_neighborhood_attention` | 5 | `medium` | planned_for_codex_on_selection | official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_string_laplacian_smoothing` | `planned` | `STRING_laplacian_prior` | 5 | `medium` | planned_for_codex_on_selection | official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_aido_string_concat_fusion` | `planned` | `AIDO_STRING_concat` | 4 | `medium` | planned_for_codex_on_selection | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_string_gated_fusion` | `planned` | `AIDO_STRING_gated` | 4 | `medium` | planned_for_codex_on_selection | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_string_cross_attention` | `planned` | `AIDO_STRING_cross_attention` | 4 | `expensive` | planned_for_codex_on_selection | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_string_bilinear_fusion` | `planned` | `AIDO_STRING_bilinear` | 4 | `medium` | planned_for_codex_on_selection | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_multimodal_mixture_of_experts` | `planned` | `multimodal_MoE` | 4 | `medium` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad |
| `official_target_low_rank_head` | `planned` | `target_low_rank_head` | 4 | `cheap` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad |
| `official_target_bilinear_head` | `planned` | `target_bilinear_head` | 4 | `cheap` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad |
| `official_target_graph_conditioned_head` | `planned` | `target_graph_conditioned_head` | 5 | `medium` | planned_for_codex_on_selection | official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_pathway_pooling_reactome` | `planned` | `Reactome_pathway_pooling` | 5 | `medium` | planned_for_codex_on_selection | pathway_membership_matrix, official_essential_deg_with_split_h5ad |
| `official_regulatory_network_prior` | `planned` | `regulatory_network_prior` | 5 | `medium` | planned_for_codex_on_selection | regulatory_network_artifact, official_essential_deg_with_split_h5ad |
| `official_weighted_ce_training` | `planned` | `class_weighted_CE` | 1 | `cheap` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad, class_distribution |
| `official_focal_loss_training` | `planned` | `focal_loss` | 1 | `cheap` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad, class_distribution |
| `official_layerwise_lr_schedule` | `planned` | `layerwise_lr_decay` | 1 | `cheap` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad |
| `official_swa_or_checkpoint_ensemble` | `planned` | `checkpoint_ensemble_or_SWA` | 1 | `medium` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad |
| `official_temperature_calibrated_head` | `planned` | `temperature_calibration` | 2 | `cheap` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad |
| `official_gene_dropout_augmentation` | `planned` | `gene_dropout_augmentation` | 2 | `cheap` | planned_for_codex_on_selection | official_essential_deg_with_split_h5ad |
| `official_public_static_node_family_wrapper` | `planned` | `public_static_tree_family` | 5 | `expensive` | planned_for_codex_on_selection | official_public_best_node_code, official_essential_deg_with_split_h5ad |

## Formal Policy

- Planned blueprints are selectable but must produce `IMPLEMENTATION_REQUEST.md` and then a full artifact-backed implementation before training.
- Compact/proxy/simplified native stand-ins are forbidden in formal K562 search.
- Missing required artifacts must go through acquisition or block; do not train fallback models.
