# K562 Official Generic Full Cell-Line Run

- Run dir: `experiments/official_k562_generic_transfer_v1/full_cellline_run`
- Entrypoint: `scripts/run_generic_cellline_transfer_test.py --cell-line K562 --run-type full_cellline_run --level full_cellline_run --execute`
- Budget requested by full level: 300 proposals / 100 trained rollouts / 8 epochs.
- Stop policy for this stage: stopped after the primary root-beating objective was achieved; implementation and acquisition queues are empty.

## Result

- Best root: `official_k562_root_aido_gnn_embedding_mlp` val Macro-F1 `0.479533`, test Macro-F1 `0.521490`
- Best generated child: `official_k562_root_aido_gnn_embedding_mlp_p8_official_temperature_calibrated_head_5df7fbe2` (`official_temperature_calibrated_head`) val Macro-F1 `0.484467`, test Macro-F1 `0.543527`
- Delta child-vs-root val: `+0.004933`
- Delta child-vs-root test: `+0.022038`
- Root-beating objective achieved: `true`

## Counts

| Metric | Count |
|---|---:|
| total_nodes | 20 |
| generated_proposals | 18 |
| trained_total | 5 |
| trained_generated_children | 3 |
| pruned_not_selected | 15 |
| selected_for_training | 0 |
| pending | 0 |
| blocked_or_acquisition | 0 |
| failed | 0 |

## Trained Generated Children

| Node | Strategy | Parent | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_temperature_calibrated_head_5df7fbe2` | `official_temperature_calibrated_head` | `official_k562_root_aido_gnn_embedding_mlp` | 0.484467 | 0.543527 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_target_gene_head_24be4a16` | `official_target_gene_head` | `official_k562_root_aido_gnn_embedding_mlp` | 0.471070 | 0.525905 |
| `official_k562_root_aido_embedding_mlp_p5_official_aido_cached_embedding_fusion_c6af2c45` | `official_aido_cached_embedding_fusion` | `official_k562_root_aido_embedding_mlp` | 0.458740 | 0.469956 |

## Artifact-Constrained Exclusions

The full run excluded blueprints requiring artifacts already proven unavailable from public/source-backed acquisition, rather than training a substitute.

- Excluded count: `10`
- Blocked artifacts: `official_string_gnn_model_dir`

## Hard Counters

| Counter | Value |
|---|---:|
| fallback_policy_mentions | 1 |
| model_source_proxy_violations | 0 |
| backprop_nontrained | 0 |
| backend_anomaly_generated_external_static | 0 |

Notes:
- `fallback_policy_mentions` counts policy/report text mentions, not trained fallback behavior.
- `model_source_proxy_violations` is the enforced source-code guardrail counter and is expected to be 0.
- No generated child used `external_static_node`; that backend remains reserved for public wrappers.
- Test Macro-F1 was used for reporting only, not reward selection.
