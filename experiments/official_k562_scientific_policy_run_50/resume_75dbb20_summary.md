# Official K562 Resume 75dbb20 Summary

Resume expanded new nodes: True
Stop reason: pending implementation limit reached (8), then 5 artifact-present STRING nodes trained and 3 scFoundation nodes blocked for missing artifact
Start counts: `{'trained': 28, 'needs_implementation': 0, 'requires_artifact_acquisition': 6, 'failed': 0}`
End counts: `{'trained': 33, 'requires_artifact_acquisition': 9}`
Implementation queue items: 0
Acquisition queue items: 9
Class distribution present: True (derived_from_train_labels_only_no_val_or_test)

## New Trained Nodes

- `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_47592563` (official_string_gnn_frozen_cache): val Macro-F1 0.3552, test Macro-F1 0.3845, backend `native_train`
- `official_k562_root_aido_embedding_mlp_p3_official_string_gnn_full_finetune_18414a9e` (official_string_gnn_full_finetune): val Macro-F1 0.4216, test Macro-F1 0.4352, backend `native_train`
- `official_k562_native_p2_official_string_gnn_frozen_cache_3d075b43` (official_string_gnn_frozen_cache): val Macro-F1 0.4171, test Macro-F1 0.4753, backend `native_train`
- `official_k562_native_p3_official_string_gnn_full_finetune_b09af07d` (official_string_gnn_full_finetune): val Macro-F1 0.4257, test Macro-F1 0.4638, backend `native_train`
- `official_k562_root_aido_embedding_mlp_p2_official_string_gnn_frozen_cache_a9964654` (official_string_gnn_frozen_cache): val Macro-F1 0.3552, test Macro-F1 0.3863, backend `native_train`

## Acquisition / Blockers

- `official_k562_p1_official_regulatory_network_prior_144a8b54` (official_regulatory_network_prior): missing `regulatory_network_artifact`; expected `data/artifacts/regulatory_network`
- `official_k562_root_aido_gnn_embedding_mlp_p1_official_regulatory_network_prior_d2e79373` (official_regulatory_network_prior): missing `regulatory_network_artifact`; expected `data/artifacts/regulatory_network`
- `official_k562_root_aido_embedding_mlp_p1_official_regulatory_network_prior_4cb71788` (official_regulatory_network_prior): missing `regulatory_network_artifact`; expected `data/artifacts/regulatory_network`
- `official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_c8a798ec` (official_scgpt_cell_encoder): missing `single_cell_foundation_model_artifact`; expected `data/artifacts/single_cell_foundation_model`
- `official_k562_native_p3_official_scgpt_cell_encoder_3e5cbefd` (official_scgpt_cell_encoder): missing `single_cell_foundation_model_artifact`; expected `data/artifacts/single_cell_foundation_model`
- `official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_d5b2bbc0` (official_scgpt_cell_encoder): missing `single_cell_foundation_model_artifact`; expected `data/artifacts/single_cell_foundation_model`
- `official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_229ce930` (official_scfoundation_top_layer_finetune): missing `scfoundation_cell_embeddings`; expected `data/artifacts/scfoundation`
- `official_k562_native_p1_official_scfoundation_top_layer_finetune_d20d4b0f` (official_scfoundation_top_layer_finetune): missing `scfoundation_cell_embeddings`; expected `data/artifacts/scfoundation`
- `official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_39582a38` (official_scfoundation_top_layer_finetune): missing `scfoundation_cell_embeddings`; expected `data/artifacts/scfoundation`

## Best Nodes

Best root: `official_k562_native_public_best_reimplementation` val 0.4679, test 0.5256
Best overall: `official_k562_native_p1_official_aido_string_fusion_66a588f9` val 0.4885, test 0.5183
Best changed: False

Backend routing anomalies: none
Fallback used: False
