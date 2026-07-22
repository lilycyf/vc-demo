# Implementation Request: official_k562_root_aido_gnn_embedding_mlp_p7_official_aido_topk_layer_tuning_44e45044

## Research Task

K562 CRISPR perturbation DEG three-class classification on the official task contract. The node must predict logits for all 6,640 target genes and 3 DEG classes.

## Parent

`official_k562_root_aido_gnn_embedding_mlp_p9_official_class_imbalance_training_9c56100e`
- parent val Macro-F1: `0.47825559973716736`
- parent strategy: `official_class_imbalance_training`

## Search Memory

Promising motifs from previous trained children:
- official_target_gene_head: unspecified + unspecified val=0.4821
- official_pathway_pooling_reactome: unspecified + unspecified val=0.4929
- official_class_imbalance_training: unspecified + unspecified val=0.4055
- official_string_neighborhood_attention: unspecified + unspecified val=0.4428
- official_target_graph_conditioned_head: unspecified + unspecified val=0.4469
- official_target_low_rank_head: unspecified + unspecified val=0.4432
- official_target_bilinear_head: unspecified + unspecified val=0.4095
- official_focal_loss_training: unspecified + unspecified val=0.4075

Discouraged motifs/families:

## Blueprint

- id: `official_aido_topk_layer_tuning`
- status: `planned`
- category: `foundation_model_finetuning`
- paper family: `AIDO_selective_finetune`
- role: Fine-tune top-k AIDO layers or adapters while keeping lower layers frozen.
- requires: official_aido_cell_100m_model_dir, official_essential_deg_with_split_h5ad
- missing required artifacts now: official_aido_cell_100m_model_dir

## Contract Files

- `artifact_contract.json`: required/present/missing artifacts and strict-mode policy
- `smoke_contract.json`: compile, forward/backward, and training-smoke commands
- `parent_summary.json`: parent score/config/artifact context
- `pipeline.json`: executable pipeline grammar and artifact claims

## Implementation Notes

Codex chooses k and adapter placement, records parameter groups.

## Codex Autonomy / Architecture Policy

The selected blueprint is a research delta, not the entire child model specification.
Implement `child = parent pipeline + selected blueprint modification` unless this request explicitly says to replace the parent.
Preserve useful parent dense/context trunks, dense target-logit branches, residual routes, and validated artifact branches by default.
Add target/graph/pathway/fusion modules as residual, gated, additive, bilinear, or attention branches that can improve the parent signal.
Use search-memory motifs and parent metrics to choose a competitive artifact-backed design; do not write the most minimal isolated module if it discards known useful parent structure.
Record in `pipeline.json` whether the implementation is parent_preserving_delta, replacement, or ablation.

## Framework Feedback

- Root-dominance observed: preserve the best parent dense branch and add the selected module as a residual/gated delta, not as a replacement.
- Validation: Run multi-seed validation before promoting `target_aware` motifs; positive average lift is not yet stable.

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
experiments/k562_feedback_guard_clean_full_run/programs/official_k562_root_aido_gnn_embedding_mlp_p7_official_aido_topk_layer_tuning_44e45044/model.py
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
