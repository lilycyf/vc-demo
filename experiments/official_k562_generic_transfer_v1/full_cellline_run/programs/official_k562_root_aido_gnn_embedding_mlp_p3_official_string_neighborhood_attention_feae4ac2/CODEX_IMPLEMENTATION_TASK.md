# Codex Implementation Task: `official_string_neighborhood_attention`

Implement the pending node-local `model.py` for this blueprint.
Do not modify data splits, labels, metrics, or artifact files.
Do not fabricate missing artifacts. If the model requires a missing artifact, stop and update acquisition queue instead.
Do not implement a compact/proxy/simplified stand-in. Formal K562 search requires exact public static execution or a real artifact-backed full blueprint implementation.
Do not import vc_demo.official_k562.native_models.OfficialK562NativeModel; that helper is smoke-only and forbidden for formal runs.

## Blueprint
{
  "id": "official_string_neighborhood_attention",
  "status": "planned",
  "official_k562": true,
  "category": "graph_prior",
  "paper_family": "STRING_neighborhood_attention",
  "change_level": 5,
  "role": "Apply K-hop STRING neighborhood attention around perturbed and target genes.",
  "requires": [
    "official_string_gnn_keep20_graph",
    "official_essential_deg_with_split_h5ad"
  ],
  "fallback_allowed": false,
  "cost_class": "medium",
  "implementation_mode": "planned_for_codex_on_selection",
  "implementation_notes": "Codex implements attention over real graph neighborhoods with missing genes handled by self loops only.",
  "acceptance": [
    "Reports K and attention heads",
    "No fake graph edges",
    "Forward returns [batch, 6640, 3]"
  ]
}

## Original Request
# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_10c0794d`
- parent val Macro-F1: `0.4737436771392822`
- parent strategy: `official_target_gene_head`

## Blueprint

- id: `official_string_neighborhood_attention`
- status: `planned`
- category: `graph_prior`
- paper family: `STRING_neighborhood_attention`
- role: Apply K-hop STRING neighborhood attention around perturbed and target genes.
- requires: official_string_gnn_keep20_graph, official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex implements attention over real graph neighborhoods with missing genes handled by self loops only.

## Pipeline Grammar

```json
{
  "blueprint": "official_string_neighborhood_attention",
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
experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_string_neighborhood_attention_feae4ac2/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Reports K and attention heads
- No fake graph edges
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.

