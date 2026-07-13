# Codex Implementation Task: `official_aido_full_finetune`

Implement the pending node-local `model.py` for this blueprint.
Do not modify data splits, labels, metrics, or artifact files.
Do not fabricate missing artifacts. If the model requires a missing artifact, stop and update acquisition queue instead.
Do not implement a compact/proxy/simplified stand-in. Formal K562 search requires exact public static execution or a real artifact-backed full blueprint implementation.
Do not import vc_demo.official_k562.native_models.OfficialK562NativeModel; that helper is smoke-only and forbidden for formal runs.

## Blueprint
{
  "id": "official_aido_full_finetune",
  "status": "planned",
  "official_k562": true,
  "category": "foundation_model_finetuning",
  "paper_family": "AIDO_full_finetune",
  "change_level": 5,
  "role": "Fine-tune selected AIDO.Cell-100M layers for K562 DEG classification with frozen/unfrozen layer policy recorded.",
  "requires": [
    "official_aido_cell_100m_model_dir",
    "official_essential_deg_with_split_h5ad"
  ],
  "fallback_allowed": false,
  "cost_class": "expensive",
  "implementation_mode": "planned_for_codex_on_selection",
  "implementation_notes": "Codex implements only when selected. Must load real AIDO.Cell-100M; no random stand-in.",
  "acceptance": [
    "Records frozen/trainable AIDO layers",
    "Forward returns [batch, 6640, 3]",
    "Does not alter official split"
  ]
}

## Original Request
# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f54f7d63

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042`
- parent val Macro-F1: `0.4375019371509552`
- parent strategy: `official_target_gene_head`

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
experiments/k562_full_global_queue_run/programs/official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f54f7d63/model.py
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
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.

