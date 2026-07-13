# K562 Full Global-Queue Run Target Report

- Proposal selection mode: `global_queue`
- Target validation Macro-F1: `0.5`
- Root-beating achieved: `True`
- Score target achieved: `False`

## Counts

```json
{
  "trained": 26,
  "requires_artifact_acquisition": 11,
  "candidate_queued": 30,
  "pruned_not_selected": 145
}
```

## Best Root

```json
{
  "node": "official_k562_root_aido_gnn_embedding_mlp",
  "strategy": "root",
  "val_macro_f1": 0.48099008202552795,
  "test_macro_f1": 0.5259189009666443,
  "status": "trained"
}
```

## Best Generated Child

```json
{
  "node": "official_k562_root_aido_gnn_embedding_mlp_p6_official_gene_dropout_augmentation_368da237",
  "strategy": "official_gene_dropout_augmentation",
  "val_macro_f1": 0.4946935474872589,
  "test_macro_f1": 0.5318608283996582,
  "status": "trained"
}
```

- Delta child vs root: `0.013703465461730957`
- Delta child vs target: `-0.005306452512741089`

## Blocked Artifacts
- `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` strategy=official_aido_lora_adapter artifact=None status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` strategy=official_string_gnn_attention artifact=None status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` strategy=official_aido_string_fusion artifact=None status=requires_artifact_acquisition
- `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` strategy=official_class_imbalance_training artifact=None status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p10_official_public_static_node_family_wrapper_786354b6` strategy=official_public_static_node_family_wrapper artifact=official_string_gnn_model_dir status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f54f7d63` strategy=official_aido_full_finetune artifact=official_aido_cell_100m_model_dir status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_73e7b933` strategy=official_aido_topk_layer_tuning artifact=official_aido_cell_100m_model_dir status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_lora_adapter_b31381fd` strategy=official_aido_lora_adapter artifact=official_aido_cell_100m_model_dir status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p12_official_aido_full_finetune_2b5b9d0c` strategy=official_aido_full_finetune artifact=official_aido_cell_100m_model_dir status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p8_official_aido_topk_layer_tuning_4f258bf5` strategy=official_aido_topk_layer_tuning artifact=official_aido_cell_100m_model_dir status=requires_artifact_acquisition
- `official_k562_root_aido_gnn_embedding_mlp_p8_official_public_static_node_family_wrapper_79d19c4b` strategy=official_public_static_node_family_wrapper artifact=official_string_gnn_model_dir status=requires_artifact_acquisition

## Audit
- fallback_count: `0`
- backprop_nontrained_count: `0`
- Strict blockers were recorded for unavailable/unverifiable AIDO.Cell-100M model interface and STRING_GNN model directory; no fallback/proxy training was used for those nodes.
