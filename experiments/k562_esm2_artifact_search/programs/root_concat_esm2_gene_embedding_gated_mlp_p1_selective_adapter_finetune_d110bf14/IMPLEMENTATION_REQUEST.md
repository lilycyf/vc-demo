# Implementation Request: root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_d110bf14

## Parent

`root_concat_esm2_gene_embedding_gated_mlp_p1_mixture_of_experts_568d46e0`

## Blueprint

- id: `selective_adapter_finetune`
- status: `planned`
- category: `fine_tuning`
- role: Freeze a base encoder and train small adapters/LoRA-style modules.
- requires: pretrained_encoder

## Implementation Notes

Requires a pretrained encoder. Generate a request unless the encoder is already present in the repo.

## Required File

Create this file:

```text
experiments/k562_esm2_artifact_search/programs/root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_d110bf14/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits.

## Acceptance Criteria

- Documents frozen/trainable parameter groups
- Does not silently train a huge model

## Guardrails

Do not modify data, splits, or metric semantics. Keep the model compact enough for the current RunPod GPU.
