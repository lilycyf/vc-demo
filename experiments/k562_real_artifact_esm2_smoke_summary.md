# K562 ESM2 Artifact Smoke Summary

This smoke test verifies that the real ESM2 gene embedding artifact can be consumed by the existing K562 training path.

- Config: `configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json`
- Dataset: `data/cell_lines/k562_concat_esm2_gene_embedding`
- Feature dim: 2385 = 1105 K562 concat features + 1280 ESM2 features
- Device: `cuda`
- Epochs: 1
- Validation Macro-F1: 0.3560
- Test Macro-F1: 0.3511

This is a plumbing smoke only, not a scientific comparison, because it uses a one-epoch budget.
