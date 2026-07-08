# Implementation Request: official_k562_p3_official_aido_full_finetune_337e49b9

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_p2_official_public_best_node_0f24e30a`
- parent val Macro-F1: `0.33328312635421753`
- parent strategy: `official_public_best_node`

## Blueprint

- id: `official_aido_full_finetune`
- status: `planned`
- category: `foundation_model_finetuning`
- paper family: `AIDO_full_finetune`
- role: Fine-tune selected AIDO.Cell-100M layers for K562 DEG classification with frozen/unfrozen layer policy recorded.
- requires: official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex implements only when selected. Must load real AIDO.Cell-100M; no random stand-in.

## Pipeline Grammar

```json
{
  "blueprint": "official_aido_full_finetune",
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
experiments/official_k562_scientific_policy_run_50/programs/official_k562_p3_official_aido_full_finetune_337e49b9/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Records frozen/trainable AIDO layers
- Forward returns [batch, 6640, 3]
- Does not alter official split

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
