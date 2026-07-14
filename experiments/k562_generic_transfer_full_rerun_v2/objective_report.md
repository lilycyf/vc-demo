# K562 Generic Transfer Full Rerun v2 Objective Report

## Run
- run_dir: `experiments/k562_generic_transfer_full_rerun_v2`
- proposal_selection_mode: `unknown`
- target validation Macro-F1: `0.50`
- latest stop reason: `manual_report_after_selected_rollouts`

## Counts
- generated proposals: `108`
- trained selected rollouts: `14`
- pruned: `44`
- skipped: `0`
- blocked/acquisition/framework blockers: `4`
- failed entries: `0`
- pending implementation: `0`
- acquisition queue items: `1`
- status counts: `{'trained': 16, 'requires_artifact_acquisition': 3, 'candidate_queued': 46, 'requires_framework_materialization': 1, 'pruned_not_selected': 44}`

## Best Metrics
- best root: `official_k562_root_aido_gnn_embedding_mlp` val `0.482341` test `0.549099`
- best generated child: `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_6ad83af7` strategy `root` val `0.460818` test `0.507110`
- delta child-vs-root val: `-0.021523`
- delta child-vs-target val: `-0.039182`
- objective achieved: `False`

## Safety Audit
- fallback count: `0`
- compact/proxy count: `0`
- backprop_nontrained count: `0`
- backend anomaly count: `0`
- generated public-static family wrapper was blocked rather than proxied because it lacked concrete external_static materialization.

## Blockers
- `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` artifact `official_aido_cell_100m_model_dir` status `None` reason: 
- `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28` strategy `root`: 
- `official_k562_root_aido_gnn_embedding_mlp_p10_official_public_static_node_family_wrapper_786354b6` strategy `root`: blocked_incomplete_public_static_materialization: generated public static family wrapper lacks a specific public node id/external_static_node execution config; writing a PyTorch model.py would be a proxy, so strict mode blocks
- `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f54f7d63` strategy `root`: blocked_missing_loadable_aido_interface: /home/Models/AIDO.Cell-100M exists but lacks a verified cellfoundation AutoModel/AutoTokenizer loading interface; strict full-finetune cannot use cached embeddings or fallback
- `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_73e7b933` strategy `root`: blocked_missing_loadable_aido_interface: selected AIDO top-k layer tuning requires a verified loadable AIDO.Cell-100M architecture/tokenizer interface; existing /home/Models/AIDO.Cell-100M files are not sufficient for strict fine-tuning

## Trained Generated Children
| node | strategy | val Macro-F1 | test Macro-F1 |
|---|---|---:|---:|
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_layerwise_lr_schedule_6ad83af7` | `root` | 0.460818 | 0.507110 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `root` | 0.449065 | 0.496006 |
| `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85` | `root` | 0.447419 | 0.501116 |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_temperature_calibrated_head_403896b2` | `root` | 0.445968 | 0.499009 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_target_gene_head_c258d8f6` | `root` | 0.443534 | 0.488589 |
| `official_k562_root_aido_gnn_embedding_mlp_p12_official_gene_dropout_augmentation_756bd70f` | `root` | 0.443473 | 0.496489 |
| `official_k562_root_aido_gnn_embedding_mlp_p9_official_target_gene_head_adb9fcb6` | `root` | 0.426564 | 0.505789 |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_target_low_rank_head_9dbf5d12` | `root` | 0.418333 | 0.493323 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_cached_embedding_fusion_86a657ed` | `root` | 0.399118 | 0.443385 |
| `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` | `root` | 0.387926 | 0.390896 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_swa_or_checkpoint_ensemble_e558308b` | `root` | 0.379113 | 0.449194 |
| `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` | `root` | 0.377207 | 0.411136 |
| `official_k562_root_aido_embedding_mlp_p8_official_string_laplacian_smoothing_c590de04` | `root` | 0.372883 | 0.392381 |
| `official_k562_root_aido_gnn_embedding_mlp_p7_official_multimodal_mixture_of_experts_32dc0d1a` | `root` | 0.343810 | 0.349625 |
