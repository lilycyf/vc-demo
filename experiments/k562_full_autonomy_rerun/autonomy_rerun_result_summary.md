# K562 Full Autonomy Rerun Summary

Run dir: `experiments/k562_full_autonomy_rerun`

Objective achieved: **True**

## Best Results

Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.483300, test=0.537383
Best generated child: `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` val=0.500979, test=0.518027
Delta child-vs-root: 0.017679
Delta child-vs-target: 0.000979

## Counts

```json
{
  "status_counts": {
    "trained": 7,
    "candidate_queued": 25
  },
  "generated_proposals": 30,
  "trained_selected_rollouts": 5,
  "pruned": 0,
  "skipped": 25,
  "blocked": 0,
  "failed": 0,
  "implementation_queue_items": 0,
  "acquisition_queue_items": 0,
  "fallback_count_trace_scan": 0,
  "backprop_nontrained_count_trace_scan": 0,
  "backend_anomaly_count_trace_scan": 0
}
```

## Trained Nodes

| Node | Strategy | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | official_target_gene_head | 0.5009788274765015 | 0.5180274248123169 |
| `official_k562_root_aido_gnn_embedding_mlp` | None | 0.48330000042915344 | 0.5373832583427429 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_3afacf8d` | official_aido_string_fusion | 0.47817835211753845 | 0.525343120098114 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` | official_aido_lora_adapter | 0.4764595329761505 | 0.5043745040893555 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d` | official_string_gnn_attention | 0.46437814831733704 | 0.5000032782554626 |
| `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | official_class_imbalance_training | 0.43443652987480164 | 0.45848551392555237 |
| `official_k562_root_aido_embedding_mlp` | None | 0.4295100271701813 | 0.4801298677921295 |
