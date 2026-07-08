# Implementation Request: official_k562_root_aido_embedding_mlp_p2_official_multimodal_mixture_of_experts_db0e9af8

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_embedding_mlp_p1_official_aido_topk_layer_tuning_fa2d7be6`
- parent val Macro-F1: `0.39048025012016296`
- parent strategy: `official_aido_topk_layer_tuning`

## Blueprint

- id: `official_multimodal_mixture_of_experts`
- status: `planned`
- category: `multimodal_fusion`
- paper family: `multimodal_MoE`
- role: Route perturbations through experts specialized for expression, AIDO, STRING, and target-gene priors.
- requires: official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Experts may require artifacts; missing artifact experts must block or be explicitly inactive in non-strict runs only.

## Pipeline Grammar

```json
{
  "blueprint": "official_multimodal_mixture_of_experts",
  "representation": "unspecified",
  "perturbation_side": "unspecified",
  "target_side": "unspecified",
  "fusion": "unspecified",
  "prior": "unspecified",
  "head": "unspecified",
  "training_strategy": "unspecified",
  "fine_tuning": "unspecified",
  "required_artifacts": [],
  "paper_alignment": "blueprint not yet mapped into the grammar"
}
```

## Required File

Create this file:

```text
experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p2_official_multimodal_mixture_of_experts_db0e9af8/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Records router inputs
- Reports active experts
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
