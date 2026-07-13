# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p8_official_scfoundation_top_layer_finetune_6a7046c6

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042`
- parent val Macro-F1: `0.4686342179775238`
- parent strategy: `official_target_gene_head`

## Blueprint

- id: `official_scfoundation_top_layer_finetune`
- status: `planned`
- category: `single_cell_foundation_model`
- paper family: `scFoundation_selective_finetune`
- role: Use scFoundation with top-layer selective fine-tuning, mirroring public static-node families where available.
- requires: scfoundation_cell_embeddings, official_essential_deg_with_split_h5ad
- missing required artifacts now: scfoundation_cell_embeddings

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex must acquire/verify scFoundation artifact first; otherwise block.

## Pipeline Grammar

```json
{
  "blueprint": "official_scfoundation_top_layer_finetune",
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
experiments/official_k562_generic_transfer_v1/full_cellline_run/programs/official_k562_root_aido_gnn_embedding_mlp_p8_official_scfoundation_top_layer_finetune_6a7046c6/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Documents scFoundation source
- Records top-layer policy
- No fallback expression MLP in strict mode

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.
