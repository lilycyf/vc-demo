# Official K562 Resume Pressure Summary

Rounds completed: 1 (requested 2-3 unless early stop condition triggers)
Stop reason: requires artifact acquisition for class_distribution, regulatory_network_artifact, and single_cell_foundation_model_artifact
Early stop: artifact blockers could not be automatically resolved; stopped before expanding search further

## Round 1

Start counts: `{'trained': 23, 'needs_implementation': 8, 'requires_artifact_acquisition': 3}`
End counts: `{'trained': 27, 'requires_artifact_acquisition': 7}`

### Implemented / Trained Nodes

- `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e` (official_aido_cached_embedding_fusion): val Macro-F1 0.4181, test Macro-F1 0.4311, backend `native_train`
- `official_k562_native_p1_official_aido_topk_layer_tuning_f7c2702a` (official_aido_topk_layer_tuning): val Macro-F1 0.3912, test Macro-F1 0.4269, backend `native_train`
- `official_k562_native_p2_official_aido_cached_embedding_fusion_58fcc751` (official_aido_cached_embedding_fusion): val Macro-F1 0.4161, test Macro-F1 0.4562, backend `native_train`
- `official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6` (official_aido_topk_layer_tuning): val Macro-F1 0.3905, test Macro-F1 0.4081, backend `native_train`
- `official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_9e4940c9` (official_aido_cached_embedding_fusion): val Macro-F1 0.4052, test Macro-F1 0.4216, backend `native_train`

### Invalidated Nodes

- `official_k562_p1_official_class_imbalance_training_fde536bb`: invalid external_static_node backend for generated child plus missing `class_distribution`; moved to acquisition/block.

### Acquisition / Blockers

- `official_k562_p1_official_class_imbalance_training_fde536bb` (official_class_imbalance_training): missing `class_distribution`; source `derive only from official train labels with documented split/provenance before retraining; not currently registered`
- `official_k562_p1_official_regulatory_network_prior_144a8b54` (official_regulatory_network_prior): missing `regulatory_network_artifact`; source `definition/source required before acquisition; do not fabricate regulatory edges`
- `official_k562_root_aido_gnn_embedding_mlp_p1_official_regulatory_network_prior_d2e79373` (official_regulatory_network_prior): missing `regulatory_network_artifact`; source `definition/source required before acquisition; do not fabricate regulatory edges`
- `official_k562_root_aido_embedding_mlp_p1_official_regulatory_network_prior_4cb71788` (official_regulatory_network_prior): missing `regulatory_network_artifact`; source `definition/source required before acquisition; do not fabricate regulatory edges`
- `official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_c8a798ec` (official_scgpt_cell_encoder): missing `single_cell_foundation_model_artifact`; source `definition/source required before acquisition; no verified official scGPT/scFoundation K562 artifact configured`
- `official_k562_native_p3_official_scgpt_cell_encoder_3e5cbefd` (official_scgpt_cell_encoder): missing `single_cell_foundation_model_artifact`; source `definition/source required before acquisition; no verified official scGPT/scFoundation K562 artifact configured`
- `official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_d5b2bbc0` (official_scgpt_cell_encoder): missing `single_cell_foundation_model_artifact`; source `definition/source required before acquisition; no verified official scGPT/scFoundation K562 artifact configured`

## Best Nodes

Best root: `official_k562_native_public_best_reimplementation` val 0.4679, test 0.5256
Best overall: `official_k562_native_p1_official_aido_string_fusion_66a588f9` val 0.4885, test 0.5183
Best changed this round: False

Backend routing anomalies: none
Repeated selection anomaly: none detected in this round; no additional search expansion was run after unresolved acquisition blockers
Fallback used: False
