# AIVC HELF Perturbation Harness Search v1 Final Report

## Scope

This run evaluates heldout-drug perturbation response prediction for HELF cells treated at 10 umol for 48 h. The label is target-gene differential-expression direction: down, unchanged, or up. Validation Macro-F1 is the search reward; test Macro-F1 is report-only. This does not claim dose optimization, time optimization, or cross-cell-line generalization.

## Run Outcome

- stop_reason: `trained-node budget exhausted (16/16)`
- generated_proposals: `64`
- trained_selected_rollouts: `16`
- pruned_not_selected: `40`
- skipped: `0`
- blocked: `8`
- failed: `0`
- trained roots: `4`
- pending implementations: `0`
- trained foundation-artifact children: `3`

## Best Models

- Best root: `aivc_helf_perturb_root_residual_mlp` val `0.429629`, test `0.427547`.
- Best generated child: `aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p59_focal_loss` strategy `None` val `0.445516`, test `0.437810`.
- Child-vs-root validation delta: `0.015887`.
- Target 0.42 reached: `true`. Best child beats best root: `true`.

## Search Semantics

The harness generated 64 proposals in 16 candidate pools. Each pool selected one rollout for training or strict artifact blocking; non-selected candidates were marked pruned_not_selected and were not trained. Rewards were backpropagated only after successful training.

## Artifact Policy

Reactome and STRING target-gene artifacts were present and enabled source-backed artifact-augmented children. scGPT checkpoint-dependent proposals were not trained because the required source-backed checkpoint validation was unavailable in this run; these were recorded in acquisition_queue.json and search continued. No fallback or proxy foundation model was used.

## Guardrails

- fallback_count: `0`
- proxy_count: `0`
- backprop_nontrained_count: `0`
- backend_anomaly_count: `0`
- failed: `0`

## Report Files

- search_summary.md
- root_dominance_audit.md
- artifact_acquisition_summary.md
- guardrail_audit.json
