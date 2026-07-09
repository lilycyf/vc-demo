# Implementation Request: official_k562_native_p4_official_regulatory_network_prior_beff5770

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_native_p1_official_string_neighborhood_attention_8885d36d`
- parent val Macro-F1: `0.4180651605129242`
- parent strategy: `official_string_neighborhood_attention`

## Blueprint

- id: `official_regulatory_network_prior`
- status: `planned`
- category: `network_prior`
- paper family: `regulatory_network_prior`
- role: Use gene regulatory network priors when an audited regulatory artifact is available.
- requires: regulatory_network_artifact, official_essential_deg_with_split_h5ad
- missing required artifacts now: regulatory_network_artifact

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

If no public regulatory artifact is available, create acquisition/blocker.

## Pipeline Grammar

```json
{
  "blueprint": "official_regulatory_network_prior",
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
experiments/official_k562_auto_impl_150/programs/official_k562_native_p4_official_regulatory_network_prior_beff5770/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Records regulatory source
- No fabricated edges
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
