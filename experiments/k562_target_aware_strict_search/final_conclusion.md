# K562 Target-Aware Strict Artifact Search Conclusion

## Setup

- Experiment: `k562_target_aware_strict_search`
- Branch: `k562-target-aware-strict-search`
- Selection: paper-aligned UCT, `exploration = sqrt(2) = 1.4142135623730951`
- Dataset/split: existing K562 `real_npz` train/validation/test splits, unchanged
- Reward metric: validation Macro-F1; test Macro-F1 reported only for final comparison
- Strict artifact mode: enabled. No fallback model was implemented or trained for missing-artifact planned nodes.

Formal command used:

```bash
python -m vc_demo.harness.program_run \
  --experiment k562_target_aware_strict_search \
  --root-configs \
    configs/k562_roots/root_concat_gated_mlp.json \
    configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json \
    configs/k562_roots/root_concat_esm2_target_aware_bilinear.json \
  --run-dir experiments/k562_target_aware_strict_search \
  --budget-nodes 32 \
  --max-epochs 4 \
  --max-children 3 \
  --stop-no-improve 10 \
  --exploration 1.4142135623730951 \
  --selection-policy uct \
  --artifact-registry configs/artifacts/k562_registry.json \
  --seed 31 \
  --allow-planned-blueprints \
  --max-pending-implementations 2 \
  --reset
```

## Stop Reason

Stop reason: `blocked_missing_artifact`.

The harness first reported `pending implementation limit reached (2)`. Under the strict artifact rule, the selected planned node `root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_8e61c57f` requires `pretrained_encoder`, which is not present in the artifact registry or run artifacts. I therefore did not implement or train a fallback model. The run was recorded as blocked.

Blocked records:

- `root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_8e61c57f` / `selective_adapter_finetune` blocked by missing: pretrained_encoder

## Root Results

| Root | val Macro-F1 | test Macro-F1 | artifact use |
|---|---:|---:|---|
| `root_concat_gated_mlp` | 0.6622 | 0.6164 | none |
| `root_concat_esm2_gene_embedding_gated_mlp` | 0.6644 | 0.6208 | perturbation-side ESM2 row features |
| `root_concat_esm2_target_aware_bilinear` | 0.3805 | 0.3723 | target-gene ESM2 manifest |


Best root: `root_concat_esm2_gene_embedding_gated_mlp` with validation Macro-F1 `0.6644` and test Macro-F1 `0.6208`.

Best overall trained node: `root_concat_esm2_gene_embedding_gated_mlp` with validation Macro-F1 `0.6644` and test Macro-F1 `0.6208`.

## Required Comparisons

- Exceeds non-artifact root (`root_concat_gated_mlp`): `True`.
- Exceeds perturbation-only ESM2 root (`root_concat_esm2_gene_embedding_gated_mlp`): `False`.
- Exceeds target-aware ESM2 root (`root_concat_esm2_target_aware_bilinear`): `True`.

The target-aware ESM2 root did not beat the non-artifact or perturbation-only ESM2 roots in this strict run.

## Artifact Usage

Nodes that truly used the target-gene artifact:

- `root_concat_esm2_target_aware_bilinear` consumed `data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json` and `target_gene_embeddings.npz`.

Nodes that used only perturbation-side ESM2 row features:

- `root_concat_esm2_gene_embedding_gated_mlp`.

No child node was trained after the roots, because the first queued planned implementation requiring a missing artifact triggered strict blocking.

Present artifacts:

- `esm2_gene_embedding_h5ad`
- `esm2_k562_target_manifest`

Missing artifacts:

- `aido_gene_or_cell_embeddings`
- `scfoundation_cell_embeddings`
- `string_k562_gene_graph`
- `pathway_membership_matrix`

Target-gene ESM2 coverage from the audit: `0.921` over `1000` target genes, with `79` missing target genes.

## Interpretation

This strict run does not support continuing by training fallback models. The best model remained the perturbation-side ESM2 root, not the target-aware bilinear root. The immediate blocker was a selected selective-adapter blueprint that requires a real pretrained encoder. The next step should be to add a real, registry-declared `pretrained_encoder` artifact if selective adapter fine-tuning is desired. For broader target-aware biological search, the most useful artifacts to add next are STRING/PPI graph edges and pathway membership matrices aligned to the K562 target genes, because those unblock graph/pathway blueprints without contaminating the formal result with fallback behavior.

## Reproducibility Artifacts

- Tree: `experiments/k562_target_aware_strict_search/tree.json`
- Failures/block records: `experiments/k562_target_aware_strict_search/failures.json`
- Implementation queue: `experiments/k562_target_aware_strict_search/implementation_queue.json`
- Artifact audit: `experiments/k562_target_aware_strict_search/artifact_registry_audit.json`
- Summary: `experiments/k562_target_aware_strict_search/search_summary.md`
