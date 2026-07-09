# Implementation Request: official_k562_native_p2_official_aido_topk_layer_tuning_1543d9b3

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_native_p2_official_string_gnn_attention_c7b091ac`
- parent val Macro-F1: `0.3701779544353485`
- parent strategy: `official_string_gnn_attention`

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
experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p2_official_aido_topk_layer_tuning_1543d9b3/model.py
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
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
