# Implementation Request: official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_229ce930

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_embedding_mlp_p2_official_aido_cached_embedding_fusion_a1e56f8e`
- parent val Macro-F1: `0.4180505573749542`
- parent strategy: `official_aido_cached_embedding_fusion`

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
experiments/official_k562_scientific_policy_run_50/programs/official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_229ce930/model.py
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
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
