# Implementation Request: root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460

## Parent

`root_concat_gated_mlp`

## Blueprint

- id: `esm2_gene_projection`
- status: `planned`
- category: `foundation_model_fusion`
- role: Project frozen ESM2 protein embeddings into the perturbation-response predictor.
- requires: protein_sequences_or_esm2_embeddings

## Implementation Notes

This repo now has a real ESM2 H5AD artifact path convention: data/artifacts/gene_embeddings/ESM2_D1280.h5ad. Build aligned K562 features with scripts/build_gene_embedding_dataset.py before selecting this blueprint. Do not fabricate embeddings; if the artifact is absent, request download via scripts/download_foundation_artifact.py.

## Required File

Create this file:

```text
experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits.

## Acceptance Criteria

- Documents ESM2 artifact source
- Reports perturbation-gene coverage
- Keeps embeddings frozen by default
- Records fallback if embeddings are missing

## Guardrails

Do not modify data, splits, or metric semantics. Keep the model compact enough for the current RunPod GPU.
