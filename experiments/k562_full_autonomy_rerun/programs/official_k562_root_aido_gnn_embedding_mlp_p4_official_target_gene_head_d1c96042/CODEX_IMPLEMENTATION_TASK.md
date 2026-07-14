# Codex Implementation Task: `official_target_gene_head`

Implement the pending node-local `model.py` for this blueprint as a parent-preserving child when possible.
Treat the blueprint as a research delta, not as permission to discard the parent pipeline by default.
Do not modify data splits, labels, metrics, or artifact files.
Do not fabricate missing artifacts. If the model requires a missing artifact, stop and update acquisition queue instead.
Do not implement a compact/proxy/simplified stand-in. Formal search requires a real artifact-backed implementation, but Codex may preserve parent dense/residual routes and compose the selected module competitively.
Use parent_summary.json and search_memory motifs from the original request to retain useful branches unless replacement is explicitly requested.
Do not import vc_demo.official_k562.native_models.OfficialK562NativeModel; that helper is smoke-only and forbidden for formal runs.

## Blueprint
{
  "id": "official_target_gene_head",
  "status": "planned",
  "official_k562": true,
  "category": "prediction_head",
  "paper_family": "target_gene_aware_head",
  "change_level": 4,
  "role": "Add a target-gene-aware low-rank, bilinear, or multilayer DEG head over the official 6,640 targets.",
  "requires": [
    "official_essential_deg_with_split_h5ad"
  ],
  "fallback_allowed": false,
  "cost_class": "cheap",
  "implementation_notes": "May modify node-local head/factorization only; must not alter official target order or labels. The head must be implemented directly in node-local code, not via smoke-only proxy helpers.",
  "acceptance": [
    "Target dimension remains 6640",
    "Reports head rank/depth",
    "Forward returns [batch, 6640, 3]"
  ]
}

## Original Request
# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp`
- parent val Macro-F1: `0.48330000042915344`
- parent strategy: `root`

## Search Memory

Promising motifs from previous trained children:

Discouraged motifs/families:

## Blueprint

- id: `official_target_gene_head`
- status: `planned`
- category: `prediction_head`
- paper family: `target_gene_aware_head`
- role: Add a target-gene-aware low-rank, bilinear, or multilayer DEG head over the official 6,640 targets.
- requires: official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

May modify node-local head/factorization only; must not alter official target order or labels. The head must be implemented directly in node-local code, not via smoke-only proxy helpers.

## Codex Autonomy / Architecture Policy

The selected blueprint is a research delta, not the entire child model specification.
Implement `child = parent pipeline + selected blueprint modification` unless this request explicitly says to replace the parent.
Preserve useful parent dense/context trunks, dense target-logit branches, residual routes, and validated artifact branches by default.
Add target/graph/pathway/fusion modules as residual, gated, additive, bilinear, or attention branches that can improve the parent signal.
Use search-memory motifs and parent metrics to choose a competitive artifact-backed design; do not write the most minimal isolated module if it discards known useful parent structure.
Record in `pipeline.json` whether the implementation is parent_preserving_delta, replacement, or ablation.

## Pipeline Grammar

```json
{
  "blueprint": "official_target_gene_head",
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
experiments/k562_full_autonomy_rerun/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Target dimension remains 6640
- Reports head rank/depth
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.

