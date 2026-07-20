# Framework Feedback

- Run dir: `experiments/k562_framework_feedback_full_run`
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.47921982407569885
- Best child: `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` val=0.5025076270103455

## Findings

- best_child_lift: best generated child beats best root by 0.0233 validation Macro-F1
- validation_test_divergence: best child improves validation but loses held-out test Macro-F1

## Policy

### Ranking Boosts

- `official_gene_dropout_augmentation`: 0.1
- `official_swa_or_checkpoint_ensemble`: 0.08
- `official_temperature_calibrated_head`: 0.08
- `official_weighted_ce_training`: 0.04

### Ranking Penalties


### Implementation Guidance

- A child beat the root: reuse its structural motif as a parent-preserving motif before broadening the search.
- Validation/test divergence observed: prioritize regularized residual gates, calibration, and seed checks; avoid unconstrained replacement heads.

### Validation Recommendations

- none

## Manual Framework Feedback From This Run

- Objective achieved: official_target_gene_head reached validation Macro-F1 0.5025, exceeding the best root 0.4792 and the target threshold 0.50.
- Strict artifact policy held: the implemented target-gene-head used official_essential_deg_with_split_h5ad and official target order; the pathway child used the Reactome pathway_membership_matrix. No fallback/proxy model was trained.
- Resume semantics caveat: invoking the generic entrypoint without --resume reconstructed the run tree and erased the node-local implementation from the active run directory. Subsequent invocations must use --resume; the runbook should make this a hard guard for existing run dirs.
- Trace completeness caveat: train_pending correctly updated tree status/metrics for manually implemented nodes, but mcts_trace.jsonl only recorded backpropagation for the auto-trained class-imbalance child. Add explicit trained/backprop trace rows after train_pending so audits do not have to infer tree state.
- Next policy changes: boost parent-preserving target-gene-aware residual heads, calibration/regularization, and seed-stability validation; keep pathway pooling as exploratory because it did not beat the root in this run.

