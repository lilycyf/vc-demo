# Implementation Request: official_k562_native_p2_official_aido_string_concat_fusion_5570bf15

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_native_p3_official_aido_cached_embedding_fusion_3eab0a30`
- parent val Macro-F1: `0.41162657737731934`
- parent strategy: `official_aido_cached_embedding_fusion`

## Blueprint

- id: `official_aido_string_concat_fusion`
- status: `planned`
- category: `multimodal_fusion`
- paper family: `AIDO_STRING_concat`
- role: Concatenate AIDO and STRING/GNN representations before DEG prediction.
- requires: official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex may use cached representations but must preserve artifact claims.

## Pipeline Grammar

```json
{
  "blueprint": "official_aido_string_concat_fusion",
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
experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p2_official_aido_string_concat_fusion_5570bf15/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Uses AIDO and STRING branches
- Records dimensions
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
