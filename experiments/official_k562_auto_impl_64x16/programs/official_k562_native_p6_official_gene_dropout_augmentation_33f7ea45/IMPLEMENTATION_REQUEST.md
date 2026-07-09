# Implementation Request: official_k562_native_p6_official_gene_dropout_augmentation_33f7ea45

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_native_p2_official_string_gnn_attention_c7b091ac`
- parent val Macro-F1: `0.44208720326423645`
- parent strategy: `official_string_gnn_attention`

## Blueprint

- id: `official_gene_dropout_augmentation`
- status: `planned`
- category: `regularization`
- paper family: `gene_dropout_augmentation`
- role: Use gene/feature dropout augmentation for robustness under K562 perturbation features.
- requires: official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex records augmentation probability and affected feature groups.

## Pipeline Grammar

```json
{
  "blueprint": "official_gene_dropout_augmentation",
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
experiments/official_k562_auto_impl_64x16/programs/official_k562_native_p6_official_gene_dropout_augmentation_33f7ea45/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Does not alter labels
- Records augmentation
- Reports Macro-F1

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
