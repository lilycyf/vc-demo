# K562 Full Cell-Line Run Target Report

## Decision

- Final decision: `blocked` for full-budget completion because `regulatory_network_artifact` lacks a source-backed artifact contract.
- Root-beating objective: `achieved`
- Target validation Macro-F1 >= 0.50: `not achieved`
- Both primary objectives: `not achieved`

## Counts

| Metric | Count |
|---|---:|
| `generated_proposals` | 66 |
| `trained_total` | 12 |
| `trained_generated_children` | 10 |
| `pruned_not_selected` | 55 |
| `blocked_or_acquisition` | 1 |
| `failed` | 0 |
| `pending` | 0 |

## Best Root

- Node: `official_k562_root_aido_gnn_embedding_mlp`
- Validation Macro-F1: `0.482001`
- Test Macro-F1: `0.539478`

## Best Generated Child

- Node: `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_laplacian_smoothing_81b813c2`
- Strategy: `official_string_laplacian_smoothing`
- Validation Macro-F1: `0.495657`
- Test Macro-F1: `0.534659`
- Delta child vs root validation: `+0.013656`
- Delta child vs target validation: `-0.004343`

## Artifact Blocker

- `regulatory_network_artifact`: blocked after source-backed acquisition research; no fallback/proxy trained.
- Blocker report: `artifact_acquisition/regulatory_network_artifact_blocker.md`

## Guardrail Counters

| Counter | Value |
|---|---:|
| fallback_count | 0 |
| compact_proxy_count | 0 |
| backprop_nontrained_count | 0 |
| backend_anomaly_count | 0 |
