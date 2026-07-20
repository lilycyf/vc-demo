# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp`
- parent val Macro-F1: `0.47921982407569885`
- parent strategy: `root`

## Search Memory

Promising motifs from previous trained children:

Discouraged motifs/families:

## Blueprint

- id: `official_aido_lora_adapter`
- status: `planned`
- category: `foundation_model_finetuning`
- paper family: `AIDO_adapter`
- role: Use AIDO.Cell-100M as the backbone with frozen parameters plus LoRA/adapters and a DEG classification head.
- requires: official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad
- missing required artifacts now: official_aido_cell_100m_model_dir

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex agent must implement a node-local full artifact-backed model that loads AIDO.Cell-100M and documents frozen/trainable parameter groups. Proxy wrappers are forbidden.

## Codex Autonomy / Architecture Policy

The selected blueprint is a research delta, not the entire child model specification.
Implement `child = parent pipeline + selected blueprint modification` unless this request explicitly says to replace the parent.
Preserve useful parent dense/context trunks, dense target-logit branches, residual routes, and validated artifact branches by default.
Add target/graph/pathway/fusion modules as residual, gated, additive, bilinear, or attention branches that can improve the parent signal.
Use search-memory motifs and parent metrics to choose a competitive artifact-backed design; do not write the most minimal isolated module if it discards known useful parent structure.
Record in `pipeline.json` whether the implementation is parent_preserving_delta, replacement, or ablation.

## Framework Feedback


## Pipeline Grammar

```json
{
  "blueprint": "official_aido_lora_adapter",
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
experiments/k562_framework_feedback_full_run/programs/official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Loads /home/Models/AIDO.Cell-100M
- No random replacement for AIDO
- Forward returns [batch, 6640, 3]

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Formal implementation rule: do not create compact/proxy/simplified stand-ins; use exact public static execution or a real artifact-backed full blueprint implementation.
Forbidden import: `vc_demo.official_k562.native_models.OfficialK562NativeModel` is smoke-only and must not appear in formal node-local `model.py`.
Smoke gate: run the commands in `smoke_contract.json` before training.
If the faithful implementation cannot fit the current RunPod GPU, block with a compute/artifact requirement instead of downgrading the model.
