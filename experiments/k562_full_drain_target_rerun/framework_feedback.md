# Framework Feedback

- Run dir: `experiments/k562_full_drain_target_rerun`
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.4880986213684082
- Best child: `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_neighborhood_attention_62af14f5` val=0.49478253722190857

## Findings

- best_child_lift: best generated child beats best root by 0.0067 validation Macro-F1
- validation_test_divergence: best child improves validation but loses held-out test Macro-F1
- discouraged_family:target_aware: repeated negative delta
- discouraged_family:imbalance_training: repeated negative delta
- discouraged_family:stability_regularization: repeated negative delta
- target_gap: best child is 0.0052 below target validation Macro-F1

## Policy

### Ranking Boosts

- `official_gene_dropout_augmentation`: 0.1
- `official_swa_or_checkpoint_ensemble`: 0.08
- `official_temperature_calibrated_head`: 0.08
- `official_weighted_ce_training`: 0.04

### Ranking Penalties

- `imbalance_training`: 0.08
- `stability_regularization`: 0.08
- `target_aware`: 0.08

### Implementation Guidance

- A child beat the root: reuse its structural motif as a parent-preserving motif before broadening the search.
- Validation/test divergence observed: prioritize regularized residual gates, calibration, and seed checks; avoid unconstrained replacement heads.
- Target gap remains: favor competitive compositions that retain root performance and test one clear additional mechanism per rollout.

### Validation Recommendations

- none
