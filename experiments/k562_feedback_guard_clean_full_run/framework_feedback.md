# Framework Feedback

- Run dir: `experiments/k562_feedback_guard_clean_full_run`
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.49353158473968506
- Best child: `official_k562_root_aido_gnn_embedding_mlp_p10_official_target_graph_conditioned_head_cc233d73` val=0.4935244619846344

## Findings

- root_dominance: best generated child did not beat best root
- unstable_positive_family:target_aware: mean_delta=0.0019, std=0.0079, win_rate=0.625
- discouraged_family:imbalance_training: repeated negative delta
- target_gap: best child is 0.0065 below target validation Macro-F1

## Policy

### Ranking Boosts

- `official_aido_string_fusion`: 0.08
- `official_gene_dropout_augmentation`: 0.08
- `official_swa_or_checkpoint_ensemble`: 0.06
- `official_target_bilinear_head`: 0.08
- `official_target_gene_head`: 0.1
- `official_target_low_rank_head`: 0.08
- `official_temperature_calibrated_head`: 0.06

### Ranking Penalties

- `imbalance_training`: 0.08

### Implementation Guidance

- Root-dominance observed: preserve the best parent dense branch and add the selected module as a residual/gated delta, not as a replacement.
- Target gap remains: favor competitive compositions that retain root performance and test one clear additional mechanism per rollout.

### Validation Recommendations

- Run multi-seed validation before promoting `target_aware` motifs; positive average lift is not yet stable.
