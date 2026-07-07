# Implementation Request: root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53

## Parent

`root_concat_gated_mlp`

## Blueprint

- id: `aido_embedding_fusion`
- status: `planned`
- category: `foundation_model_fusion`
- role: Fuse AIDO-style biological foundation embeddings with perturbation and expression features.
- requires: aido_embeddings

## Implementation Notes

Requires precomputed AIDO embeddings or an approved loader. Missing artifacts must be reported explicitly.

## Required File

Create this file:

```text
experiments/k562_esm2_artifact_search/programs/root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits.

## Acceptance Criteria

- Documents AIDO artifact source
- Does not silently substitute random embeddings
- Keeps large foundation model frozen unless task allows fine-tuning

## Guardrails

Do not modify data, splits, or metric semantics. Keep the model compact enough for the current RunPod GPU.
