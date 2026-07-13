# Codex Implementation Task: `official_aido_topk_layer_tuning`

Implement the pending node-local `model.py` for this blueprint.
Do not modify data splits, labels, metrics, or artifact files.
Do not fabricate missing artifacts. If the model requires a missing artifact, stop and update acquisition queue instead.
Do not implement a compact/proxy/simplified stand-in. Formal K562 search requires exact public static execution or a real artifact-backed full blueprint implementation.
Do not import vc_demo.official_k562.native_models.OfficialK562NativeModel; that helper is smoke-only and forbidden for formal runs.

## Blueprint
{
  "id": "official_aido_topk_layer_tuning",
  "status": "planned",
  "official_k562": true,
  "category": "foundation_model_finetuning",
  "paper_family": "AIDO_selective_finetune",
  "change_level": 5,
  "role": "Fine-tune top-k AIDO layers or adapters while keeping lower layers frozen.",
  "requires": [
    "official_aido_cell_100m_model_dir",
    "official_essential_deg_with_split_h5ad"
  ],
  "fallback_allowed": false,
  "cost_class": "expensive",
  "implementation_mode": "planned_for_codex_on_selection",
  "implementation_notes": "Codex chooses k and adapter placement, records parameter groups.",
  "acceptance": [
    "Reports top-k policy",
    "Uses AIDO artifact",
    "Forward returns [batch, 6640, 3]"
  ]
}

## Original Request
# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p8_official_aido_topk_layer_tuning_4f258bf5

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85`
- parent val Macro-F1: `0.44560250639915466`
- parent strategy: `official_target_bilinear_head`

## Blueprint

- id: `official_aido_topk_layer_tuning`
- status: `planned`
- category: `foundation_model_finetuning`
- paper family: `AIDO_selective_finetune`
- role: Fine-tune top-k AIDO layers or adapters while keeping lower layers frozen.
- requires: official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex chooses k and adapter placement, records parameter groups.

## Pipeline Grammar

```json
{
  "blueprint": "official_aido_topk_layer_tuning",
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
experiments/k562_full_global_queue_run/programs/official_k562_root_aido_gnn_embedding_mlp_p8_official_aido_topk_layer_tuning_4f258bf5/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Reports top-k policy
- Uses AIDO artifact
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.

