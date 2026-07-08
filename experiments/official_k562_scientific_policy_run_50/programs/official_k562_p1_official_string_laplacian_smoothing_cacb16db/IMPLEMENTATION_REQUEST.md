# Implementation Request: official_k562_p1_official_string_laplacian_smoothing_cacb16db

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_p1_official_target_graph_conditioned_head_ab86336c`
- parent val Macro-F1: `0.39674413204193115`
- parent strategy: `official_target_graph_conditioned_head`

## Blueprint

- id: `official_string_laplacian_smoothing`
- status: `planned`
- category: `graph_prior`
- paper family: `STRING_laplacian_prior`
- role: Regularize target-gene logits or embeddings with STRING graph Laplacian smoothing.
- requires: official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex records smoothing strength and graph coverage.

## Pipeline Grammar

```json
{
  "blueprint": "official_string_laplacian_smoothing",
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
experiments/official_k562_scientific_policy_run_50/programs/official_k562_p1_official_string_laplacian_smoothing_cacb16db/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Uses real graph adjacency
- Documents smoothing coefficient
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
