# K562 Generic Cell-Line Transfer 64x16 Report

- final decision: `blocked`
- cell line: `K562`
- test level: `transfer_64x16`
- run dir: `experiments/official_k562_generic_transfer_v1/transfer_64x16`
- stop reason: `see run_manifest/search_summary`
- generated proposals: `None`
- proposal budget: `None`
- trained rollout budget: `None`

## Counts
- pruned_not_selected: `33`
- requires_artifact_acquisition: `2`
- trained: `11`
- implementation queue count: `0`
- acquisition queue count: `2`
- failures reported by manifest: `None`

## Hard Counters
- fallback_count: `0`
- compact_proxy_count: `0`
- backprop_nontrained_count: `0`
- backend_anomaly_count: `0`
- k562_leakage_count: `0` (CELL_LINE_ID=K562 self-instantiation test)
- forbidden_committed_file_count: `0` after staged guard check

## Best Nodes
- best root: `official_k562_root_aido_gnn_embedding_mlp` val `0.4053276479244232` test `0.4485529363155365`
- best trained rollout overall: `official_k562_root_aido_gnn_embedding_mlp` strategy `root` val `0.4053276479244232` test `0.4485529363155365`

## Trained Nodes
| node | strategy | val Macro-F1 | test Macro-F1 |
|---|---|---:|---:|
| `official_k562_root_aido_gnn_embedding_mlp` | `root` | `0.4053276479244232` | `0.4485529363155365` |
| `official_k562_root_aido_embedding_mlp` | `root` | `0.39528778195381165` | `0.412227988243103` |
| `official_k562_root_aido_embedding_mlp_p1_official_target_graph_conditioned_head_10827e49` | `official_target_graph_conditioned_head` | `0.35537660121917725` | `0.3836159408092499` |
| `official_k562_root_aido_embedding_mlp_p3_official_string_neighborhood_attention_898d7103` | `official_string_neighborhood_attention` | `0.35522815585136414` | `0.3842289447784424` |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_649e5781` | `official_target_gene_head` | `0.3535339832305908` | `0.38332605361938477` |
| `official_k562_root_aido_embedding_mlp_p2_official_target_low_rank_head_a90e331d` | `official_target_low_rank_head` | `0.3534698188304901` | `0.38302621245384216` |
| `official_k562_root_aido_embedding_mlp_p1_official_temperature_calibrated_head_1f61c967` | `official_temperature_calibrated_head` | `0.35207679867744446` | `0.3783244788646698` |
| `official_k562_root_aido_embedding_mlp_p1_official_string_laplacian_smoothing_dc9fe3d0` | `official_string_laplacian_smoothing` | `0.3455764949321747` | `0.37493762373924255` |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_target_gene_head` | `0.3427940309047699` | `0.37970054149627686` |
| `official_k562_root_aido_embedding_mlp_p4_official_aido_lora_adapter_c468633e` | `official_aido_lora_adapter` | `0.3328036665916443` | `0.35330188274383545` |
| `official_k562_root_aido_embedding_mlp_p7_official_aido_cached_embedding_fusion_7cfdea7c` | `official_aido_cached_embedding_fusion` | `0.32680580019950867` | `0.34223854541778564` |

## Blocker
The run is blocked by strict artifact policy, not by model/training failure.
- artifact: `official_string_gnn_model_dir`
- node: `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_string_cross_attention_ec2c0082`
- strategy: `official_aido_string_cross_attention`
- expected path: `/home/Models/STRING_GNN`
- source note: Exact model directory expected by public VCHarness node code; not equivalent to STRING graph edge file.
- acquisition status: `requires_codex_research_download_or_build`
- acquisition task: `experiments/official_k562_generic_transfer_v1/transfer_64x16/artifact_acquisition/ACQUIRE_official_string_gnn_model_dir.md`

## Search Semantics
- Proposal-pool generation occurred across multiple resume cycles.
- Unselected proposals are recorded as `pruned_not_selected` and were not trained.
- Selected planned nodes were implemented only after required artifacts were present, then compiled, smoked, trained, and backpropagated as trained nodes.
- The run stopped before 16 trained rollouts because `official_string_gnn_model_dir` lacks a source-backed automatic resolver and cannot be replaced by the STRING edge file.

## Acquisition
- acquisition report: `experiments/official_k562_generic_transfer_v1/transfer_64x16/artifact_acquisition/artifact_acquisition_report.json`
- STRING_GNN blocker evidence: `experiments/official_k562_generic_transfer_v1/transfer_64x16/artifact_acquisition/official_string_gnn_model_dir_blocker_report.md`
- `class_distribution`: `already_present` action `verified_existing_file`
- `official_string_gnn_model_dir`: `requires_codex_research_download_or_build` action `generated_codex_research_task`

## Acceptance Decision
`blocked`: source-backed task and many artifacts are verified, the loop trained selected rollouts without fallback, but the requested 64x16 test cannot complete until the exact `/home/Models/STRING_GNN` model directory is acquired or verifiably built.
