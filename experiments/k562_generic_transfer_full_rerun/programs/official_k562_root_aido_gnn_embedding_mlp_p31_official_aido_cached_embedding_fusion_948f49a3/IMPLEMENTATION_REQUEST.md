# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p31_official_aido_cached_embedding_fusion_948f49a3

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp`
- parent val Macro-F1: `0.4669579565525055`
- parent strategy: `root`

## Blueprint

- id: `official_aido_cached_embedding_fusion`
- status: `planned`
- category: `foundation_model_embedding`
- paper family: `AIDO_cached_embedding`
- role: Use precomputed/cached AIDO representations as frozen features fused with the DEG predictor.
- requires: official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex may cache embeddings inside the run directory; provenance and cache shape must be recorded.

## Pipeline Grammar

```json
{
  "blueprint": "official_aido_cached_embedding_fusion",
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
experiments/k562_generic_transfer_full_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p31_official_aido_cached_embedding_fusion_948f49a3/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Cache is derived from AIDO, not fabricated
- Records cache path
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.
