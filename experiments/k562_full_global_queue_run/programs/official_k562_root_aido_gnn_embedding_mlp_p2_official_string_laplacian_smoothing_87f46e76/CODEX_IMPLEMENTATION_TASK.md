# Codex Implementation Task: `official_string_laplacian_smoothing`

Implement the pending node-local `model.py` for this blueprint.
Do not modify data splits, labels, metrics, or artifact files.
Do not fabricate missing artifacts. If the model requires a missing artifact, stop and update acquisition queue instead.
Do not implement a compact/proxy/simplified stand-in. Formal K562 search requires exact public static execution or a real artifact-backed full blueprint implementation.
Do not import vc_demo.official_k562.native_models.OfficialK562NativeModel; that helper is smoke-only and forbidden for formal runs.

## Blueprint
{
  "id": "official_string_laplacian_smoothing",
  "status": "planned",
  "official_k562": true,
  "category": "graph_prior",
  "paper_family": "STRING_laplacian_prior",
  "change_level": 5,
  "role": "Regularize target-gene logits or embeddings with STRING graph Laplacian smoothing.",
  "requires": [
    "official_string_gnn_keep20_graph",
    "official_essential_deg_with_split_h5ad"
  ],
  "fallback_allowed": false,
  "cost_class": "medium",
  "implementation_mode": "planned_for_codex_on_selection",
  "implementation_notes": "Codex records smoothing strength and graph coverage.",
  "acceptance": [
    "Uses real graph adjacency",
    "Documents smoothing coefficient",
    "Forward returns [batch, 6640, 3]"
  ]
}

## Original Request
# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p2_official_string_laplacian_smoothing_87f46e76

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp_p2_official_swa_or_checkpoint_ensemble_889dddf0`
- parent val Macro-F1: `0.46610915660858154`
- parent strategy: `official_swa_or_checkpoint_ensemble`

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
experiments/k562_full_global_queue_run/programs/official_k562_root_aido_gnn_embedding_mlp_p2_official_string_laplacian_smoothing_87f46e76/model.py
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
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.

