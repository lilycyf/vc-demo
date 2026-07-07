# Target-Aware Artifact Model Space

This repository now separates two levels of biological artifact use.

## Level 1: Perturbation-Side Artifact Features

The existing ESM2 dataset appends a real frozen ESM2 vector for the perturbed gene to the row-level input features. This is useful but limited: a dense head can still treat all target genes as anonymous output columns.

## Level 2: Perturbation + Target Artifact Geometry

The upgraded contract adds a dataset-local artifact manifest:

```text
data/cell_lines/<dataset>/artifact_manifest.json
```

The manifest points to aligned arrays such as:

```text
target_gene_embeddings.npz::target_gene_embeddings
```

Models can now use row-level perturbation/context features, perturbation-gene embeddings already present in `gene_embedding_features`, and target-gene embeddings as the geometry of the prediction head.

The first executable model using this contract is:

```text
model_type: target_aware_bilinear
```

It encodes each perturbation/context row, projects target-gene ESM2 vectors, and scores each target through a bilinear factorized classifier. This is closer to a paper-style biological-prior node than appending ESM2 to tabular features.

## Agent Rules

A Codex program-node agent may implement new children from the model-space list, but it must obey these rules:

- Real artifacts must be documented by path and coverage.
- Missing AIDO, scFoundation, STRING, or pathway artifacts must be reported as missing, not silently replaced.
- Random embeddings or synthetic graph edges may only be described as ablations, never as paper-aligned biological artifacts.
- The train/validation/test split and label semantics must remain unchanged.
- Program-node `model.py` files may read `spec.artifact_manifest_path` and `spec.artifacts`.

## Current Executable Upgrade

Use:

```text
configs/k562_roots/root_concat_esm2_target_aware_bilinear.json
```

This config expects the ESM2 perturbation-side dataset plus a target-side artifact manifest built by:

```bash
python scripts/build_target_gene_artifact.py \
  --data-dir data/cell_lines/k562_concat_esm2_gene_embedding \
  --embedding-h5ad data/artifacts/gene_embeddings/ESM2_D1280.h5ad \
  --artifact-name ESM2_D1280 \
  --gene-column symbol
```

## No-Fallback Formal Testing

For formal tests, missing AIDO, scFoundation, STRING, pathway, pretrained encoder, or other required artifacts must produce a blocked node, not a fallback model. A fallback can be useful for engineering ablations, but it must be run separately and labeled as non-paper-aligned.
