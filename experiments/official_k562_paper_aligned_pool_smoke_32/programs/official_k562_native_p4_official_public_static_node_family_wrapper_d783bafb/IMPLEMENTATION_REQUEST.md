# Implementation Request: official_k562_native_p4_official_public_static_node_family_wrapper_d783bafb

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_native_p2_official_aido_string_concat_fusion_5570bf15`
- parent val Macro-F1: `0.4257877767086029`
- parent strategy: `official_aido_string_concat_fusion`

## Blueprint

- id: `official_public_static_node_family_wrapper`
- status: `planned`
- category: `official_static_node`
- paper family: `public_static_tree_family`
- role: Wrap additional public K562 static nodes beyond node2-1-1-1-1-1 as benchmark candidates.
- requires: official_public_best_node_code, official_essential_deg_with_split_h5ad
- missing required artifacts now: none

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex selects a specific public static node id from the 154-node scaffold and records it.

## Pipeline Grammar

```json
{
  "blueprint": "official_public_static_node_family_wrapper",
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
experiments/official_k562_paper_aligned_pool_smoke_32/programs/official_k562_native_p4_official_public_static_node_family_wrapper_d783bafb/model.py
```

It must define `class GeneratedModel(nn.Module)` with `__init__(self, spec)` and `forward(self, x)`. The forward pass must return `[batch, n_targets, n_classes]` logits, which is `[batch, 6640, 3]` for official K562.

## Acceptance Criteria

- Records public node id
- External metrics contract enforced
- No debug metrics in benchmark mode

## Guardrails

Allowed files: node-local `model.py`, node-local config/pipeline metadata, and small helper modules under `src/vc_demo/official_k562/` when genuinely reusable.
Forbidden changes: official split files, labels, target-gene order, metric semantics, and artifact provenance.
Strict artifact rule: if a required artifact is missing, acquire the real artifact or block; do not train a fallback.
Smoke gate: run the commands in `smoke_contract.json` before training.
Keep the model compact enough for the current RunPod GPU.
