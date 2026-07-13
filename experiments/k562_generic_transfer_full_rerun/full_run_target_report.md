# K562 Generic Transfer Full Rerun Target Report

- Branch: `k562-generic-transfer-full-rerun`
- Run dir: `experiments/k562_generic_transfer_full_rerun`
- Proposal selection mode: `global_queue`
- Stop reason: `proposal budget exhausted (300/300)`
- Target validation Macro-F1: `0.5`

## Counts
- `trained`: `2`
- `implementation_skipped`: `15`
- `requires_artifact_acquisition`: `14`
- `pruned_not_selected`: `271`
- Generated proposals: `300`
- Trained selected rollouts: `0`
- Implementation queue items: `0`
- Acquisition queue items: `14`

## Best Metrics
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=`0.4669579565525055` test=`0.523522138595581`
- Best generated child: `None` val=`None` test=`None`
- Delta child vs root: `None`
- Delta child vs target: `None`
- Root-beating achieved: `False`
- Target achieved: `False`

## Artifact Acquisition / Blockers
- `class_distribution`
- `official_string_gnn_model_dir`
- `pathway_memberships`
- `regulatory_network_artifact`
- `scfoundation_cell_embeddings`
- `single_cell_foundation_model_artifact`

## Audit Counters
- `fallback_count`: `0`
- `compact_proxy_count`: `0`
- `backprop_nontrained_count`: `0`
- `backend_anomaly_count`: `0`
- `backend_audit_status`: `passed`

## Conclusion
Mechanically completed the 300-proposal full run, but the scientific objective was not achieved: no generated child was trained because strict formal implementation rules skipped planned generated nodes instead of allowing compact/proxy implementations.
