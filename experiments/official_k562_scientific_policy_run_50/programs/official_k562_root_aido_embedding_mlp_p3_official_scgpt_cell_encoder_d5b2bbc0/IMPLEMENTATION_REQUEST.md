# Implementation Request: official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_d5b2bbc0

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_embedding_mlp_p1_official_pathway_pooling_reactome_1792359c`
- parent val Macro-F1: `0.40537509322166443`
- parent strategy: `official_pathway_pooling_reactome`

## Blueprint

- id: `official_scgpt_cell_encoder`
- status: `planned`
- category: `single_cell_foundation_model`
- paper family: `scGPT_or_single_cell_encoder`
- role: Use a single-cell foundation model style encoder for cell/expression state if a real artifact is present or acquired.
- requires: single_cell_foundation_model_artifact, official_essential_deg_with_split_h5ad
- missing required artifacts now: single_cell_foundation_model_artifact

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

If artifact is not public or cannot be acquired, node must block instead of fallback.

## Pipeline Grammar

```json
{
  "blueprint": "official_scgpt_cell_encoder",
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
experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_d5b2bbc0/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Records artifact source
- No random encoder substitution
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
