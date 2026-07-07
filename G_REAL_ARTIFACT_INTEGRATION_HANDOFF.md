# G Handoff: Real External Artifact Integration

## What Changed

This branch adds a reusable path for consuming real external biological artifacts in the K562 VCHarness-style loop.

New framework pieces:

- `scripts/download_foundation_artifact.py`: lists/downloads public artifacts from `genbio-ai/foundation-models-perturbation` on HuggingFace.
- `scripts/build_gene_embedding_dataset.py`: reads a real H5AD gene embedding artifact with `h5py`, aligns perturbation gene symbols to `obs/<gene_column>`, and writes a new split-file `real_npz` dataset.
- `configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json`: root config for K562 concat features plus real ESM2 gene embeddings.
- `configs/k562_roots/root_concat_pca_fair_gene_embedding_gated_mlp.json`: lower-coverage PCA_Fair artifact root config retained for comparison/debugging.
- `TASK_K562_ESM2_ARTIFACT_SEARCH.md`: concrete next-run instructions.

## Artifact Results On RunPod

Downloaded but not committed:

```text
data/artifacts/gene_embeddings/PCA_Fair_essential_K-562_controls_D128.h5ad
data/artifacts/gene_embeddings/ESM2_D1280.h5ad
```

Built but not committed:

```text
data/cell_lines/k562_concat_pca_fair_gene_embedding
data/cell_lines/k562_concat_esm2_gene_embedding
```

Committed small audit/summary files document the generated datasets.

## Coverage

PCA_Fair K562 controls D=128:

- feature dim: 1233 = 1105 + 128
- coverage: 28.57 percent
- conclusion: real artifact but poor overlap with the current Norman K562 perturbation set

ESM2 D=1280:

- feature dim: 2385 = 1105 + 1280
- coverage: 96.19 percent
- missing perturbations: `ELMSAN1`, `KIAA1804`, `C19orf26`, `C3orf72`
- conclusion: best current artifact for the next search

## Smoke Result

The ESM2 artifact root trains on CUDA for one epoch:

```text
val Macro-F1: 0.3560
test Macro-F1: 0.3511
```

This confirms the data/model plumbing. It is not a scientific result because it is only one epoch.

## Next Step

Run `TASK_K562_ESM2_ARTIFACT_SEARCH.md` in a fresh Codex run. The important comparison is no longer architecture-only child nodes versus root. It is:

1. non-artifact best root
2. ESM2 artifact root
3. children that truly consume ESM2-augmented features

A child should not be called a foundation-model node unless it uses this real artifact or another documented external artifact.
