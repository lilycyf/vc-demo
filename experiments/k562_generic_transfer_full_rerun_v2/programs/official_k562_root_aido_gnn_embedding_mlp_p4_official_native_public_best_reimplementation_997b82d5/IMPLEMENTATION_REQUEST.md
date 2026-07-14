# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p4_official_native_public_best_reimplementation_997b82d5

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp_p9_official_target_bilinear_head_dc403b85`
- parent val Macro-F1: `0.44741949439048767`
- parent strategy: `official_target_bilinear_head`

## Blueprint

- id: `official_native_public_best_reimplementation`
- status: `planned`
- category: `native_reimplementation`
- paper family: `public_vcharness_best_path_native_exact`
- role: Full native reimplementation of the public K562 best-node family using the real public static recipe, AIDO, STRING_GNN, and official data contract.
- requires: official_public_best_node_code, official_aido_cell_100m_model_dir, official_string_gnn_model_dir, official_essential_deg_with_split_h5ad
- missing required artifacts now: official_string_gnn_model_dir

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Compact/proxy native stand-ins are forbidden. Codex must port the real public static node recipe or block with a precise implementation/artifact gap.

## Pipeline Grammar

```json
{
  "blueprint": "official_native_public_best_reimplementation",
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
experiments/k562_generic_transfer_full_rerun_v2/programs/official_k562_root_aido_gnn_embedding_mlp_p4_official_native_public_best_reimplementation_997b82d5/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Ports public static-node architecture/training recipe
- Uses AIDO and STRING_GNN artifacts directly
- Forward returns [batch, 6640, 3]
- No import of OfficialK562NativeModel

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.
