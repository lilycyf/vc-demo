# Official K562 Paper-Scale Search Space Audit

- Official selectable blueprints: 33
- Estimated combinatorial candidate count: 94500
- Reaches 600+ search-space target: true
- Status counts: `{"implemented": 7, "planned": 26}`

## Dimensions

- backbone: AIDO.Cell-100M, AIDO cached embedding, single-cell foundation encoder, STRING_GNN, public static wrapper, native public-best reimplementation
- adapter: LoRA, frozen adapter, selective layer tuning, full fine-tune, cached embedding projection
- graph_prior: STRING frozen embedding, K-hop attention, message passing, Laplacian smoothing, graph-conditioned head
- fusion: concat, gated, bilinear, cross-attention, mixture-of-experts, late fusion, residual fusion
- target_head: shared head, target-specific head, low-rank head, bilinear head, calibrated head
- training_strategy: weighted CE, focal loss, class-balanced loss, layerwise LR, SWA, checkpoint ensemble
- biological_prior: pathway membership, Reactome pooling, regulatory network prior

## Blueprint Contract

| Blueprint | Status | Family | Cost | Required artifacts |
|---|---|---|---|---|
| `official_native_public_best_reimplementation` | implemented | public_vcharness_best_path_native_v1 | medium | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_public_best_node` | implemented | public_vcharness_best_path | expensive | official_public_best_node_code, official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_lora_adapter` | implemented | AIDO_adapter | expensive | official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad |
| `official_string_gnn_attention` | implemented | STRING_GNN_attention | medium | official_string_gnn_model_dir, official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_aido_string_fusion` | implemented | AIDO_STRING_fusion | expensive | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_target_gene_head` | implemented | target_gene_aware_head | cheap | official_essential_deg_with_split_h5ad |
| `official_class_imbalance_training` | implemented | official_deg_imbalance | cheap | official_essential_deg_with_split_h5ad, class_distribution |
| `official_aido_full_finetune` | planned | AIDO_full_finetune | expensive | official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_topk_layer_tuning` | planned | AIDO_selective_finetune | expensive | official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_cached_embedding_fusion` | planned | AIDO_cached_embedding | medium | official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad |
| `official_scgpt_cell_encoder` | planned | scGPT_or_single_cell_encoder | expensive | single_cell_foundation_model_artifact, official_essential_deg_with_split_h5ad |
| `official_scfoundation_top_layer_finetune` | planned | scFoundation_selective_finetune | expensive | scfoundation_cell_embeddings, official_essential_deg_with_split_h5ad |
| `official_string_gnn_frozen_cache` | planned | STRING_GNN_frozen_cached | medium | official_string_gnn_model_dir, official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_string_gnn_full_finetune` | planned | STRING_GNN_full_finetune | expensive | official_string_gnn_model_dir, official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_string_neighborhood_attention` | planned | STRING_neighborhood_attention | medium | official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_string_laplacian_smoothing` | planned | STRING_laplacian_prior | medium | official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_aido_string_concat_fusion` | planned | AIDO_STRING_concat | medium | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_string_gated_fusion` | planned | AIDO_STRING_gated | medium | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_string_cross_attention` | planned | AIDO_STRING_cross_attention | expensive | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_aido_string_bilinear_fusion` | planned | AIDO_STRING_bilinear | medium | official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad |
| `official_multimodal_mixture_of_experts` | planned | multimodal_MoE | medium | official_essential_deg_with_split_h5ad |
| `official_target_low_rank_head` | planned | target_low_rank_head | cheap | official_essential_deg_with_split_h5ad |
| `official_target_bilinear_head` | planned | target_bilinear_head | cheap | official_essential_deg_with_split_h5ad |
| `official_target_graph_conditioned_head` | planned | target_graph_conditioned_head | medium | official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad |
| `official_pathway_pooling_reactome` | planned | Reactome_pathway_pooling | medium | pathway_memberships, official_essential_deg_with_split_h5ad |
| `official_regulatory_network_prior` | planned | regulatory_network_prior | medium | regulatory_network_artifact, official_essential_deg_with_split_h5ad |
| `official_weighted_ce_training` | planned | class_weighted_CE | cheap | official_essential_deg_with_split_h5ad, class_distribution |
| `official_focal_loss_training` | planned | focal_loss | cheap | official_essential_deg_with_split_h5ad, class_distribution |
| `official_layerwise_lr_schedule` | planned | layerwise_lr_decay | cheap | official_essential_deg_with_split_h5ad |
| `official_swa_or_checkpoint_ensemble` | planned | checkpoint_ensemble_or_SWA | medium | official_essential_deg_with_split_h5ad |
| `official_temperature_calibrated_head` | planned | temperature_calibration | cheap | official_essential_deg_with_split_h5ad |
| `official_gene_dropout_augmentation` | planned | gene_dropout_augmentation | cheap | official_essential_deg_with_split_h5ad |
| `official_public_static_node_family_wrapper` | planned | public_static_tree_family | expensive | official_public_best_node_code, official_essential_deg_with_split_h5ad |
