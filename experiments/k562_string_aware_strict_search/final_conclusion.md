# K562 STRING-Aware Strict Search Conclusion

## Setup

- Experiment: `k562_string_aware_strict_search`
- Branch: `k562-string-aware-strict-search`
- Search policy: UCT, `exploration = 1.4142135623730951`
- Dataset/split: existing K562 `real_npz` train/validation/test splits, unchanged
- Reward: validation Macro-F1; test Macro-F1 reported for trained nodes
- Strict artifact mode: no fallback models implemented or trained
- STRING artifact: present at `data/artifacts/string/k562_target_graph_edges.tsv`

Formal command:

```bash
python -m vc_demo.harness.program_run \
  --experiment k562_string_aware_strict_search \
  --root-configs \
    configs/k562_roots/root_concat_gated_mlp.json \
    configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json \
    configs/k562_roots/root_concat_esm2_target_aware_bilinear.json \
  --run-dir experiments/k562_string_aware_strict_search \
  --budget-nodes 40 \
  --max-epochs 4 \
  --max-children 4 \
  --stop-no-improve 12 \
  --exploration 1.4142135623730951 \
  --selection-policy uct \
  --artifact-registry configs/artifacts/k562_registry.json \
  --seed 41 \
  --allow-planned-blueprints \
  --max-pending-implementations 2 \
  --reset
```

## Stop Reason

The run stopped with `requires_artifact_acquisition` before any child implementation or fallback training. The selected planned node was:

- Node: `root_concat_gated_mlp_p1_scfoundation_cell_encoder_c117ca5e`
- Blueprint: `scfoundation_cell_encoder`
- Missing artifact: `scfoundation_cell_embeddings`
- Expected path: `data/artifacts/scfoundation`

`acquisition_queue.json` requests acquiring `scfoundation_cell_embeddings` from `precomputed scFoundation cell-state embedding or approved encoder output` and then resuming strict search.

## Root Results

| Root | val Macro-F1 | test Macro-F1 | Artifact usage |
|---|---:|---:|---|
| `root_concat_gated_mlp` | 0.6616 | 0.6123 | none |
| `root_concat_esm2_gene_embedding_gated_mlp` | 0.6512 | 0.6045 | perturbation-side ESM2 row features |
| `root_concat_esm2_target_aware_bilinear` | 0.4156 | 0.4073 | target-gene ESM2 manifest |

Best root: `root_concat_gated_mlp` with val Macro-F1 `0.6616` and test Macro-F1 `0.6123`.

Best overall trained node: `root_concat_gated_mlp` with val Macro-F1 `0.6616` and test Macro-F1 `0.6123`.

## STRING Graph Status

STRING graph node searched: `False`.

No `ppi_graph_message_passing` or `string_gnn_perturbation_propagator` node was selected before the run stopped for scFoundation acquisition. Therefore no STRING graph-aware node was implemented or trained in this run.

The STRING graph artifact itself is present and audit-backed:

- Path: `data/artifacts/string/k562_target_graph_edges.tsv`
- Source: `https://version-12-0.string-db.org/api/tsv/network`
- Version: `STRING 12.0`
- Edges: `36550` retained from `135802` raw API edges
- Nodes: `1054`
- Perturbation coverage: `0.9048`
- Target coverage: `0.9660`

Because no graph node was trained, graph-node comparisons are not applicable:

- Graph node exceeds non-artifact root: not evaluated
- Graph node exceeds ESM2 root: not evaluated
- Graph node truly used `k562_target_graph_edges.tsv`: no graph node was selected, so no

## Artifact State

Present artifacts:

- `esm2_gene_embedding_h5ad`
- `esm2_k562_target_manifest`
- `string_k562_gene_graph`

Missing artifacts:

- `aido_gene_or_cell_embeddings`
- `scfoundation_cell_embeddings`
- `pathway_membership_matrix`

## Next Artifact To Acquire

The immediate blocker is `scfoundation_cell_embeddings`, because MCTS selected `scfoundation_cell_encoder` before any STRING/PPI blueprint. The next step should be to acquire or produce a real scFoundation cell-state embedding or approved encoder output at `data/artifacts/scfoundation`, then update `configs/artifacts/k562_registry.json`, rerun the artifact audit, and resume strict search without fallback.

After scFoundation is resolved, STRING/PPI graph-aware nodes are now unblocked by the registry and should be trainable if selected.

## Files

- Tree: `experiments/k562_string_aware_strict_search/tree.json`
- Search summary: `experiments/k562_string_aware_strict_search/search_summary.md`
- Failures: `experiments/k562_string_aware_strict_search/failures.json`
- Acquisition queue: `experiments/k562_string_aware_strict_search/acquisition_queue.json`
- Artifact audit: `experiments/k562_string_aware_strict_search/artifact_registry_audit.json`
