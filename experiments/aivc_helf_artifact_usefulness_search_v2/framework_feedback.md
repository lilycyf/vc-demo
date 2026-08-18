# Framework Feedback

- Run dir: `experiments/aivc_helf_artifact_usefulness_search_v2`
- Best root: `aivc_helf_perturb_root_residual_mlp` val=0.4292716979980469
- Best child: `aivc_helf_perturb_root_mlp_p31_foundation_graph_laplacian_head_29e4f32f_p31_dense_matched_capacity_no_artifact_control_control_8950845e` val=0.44976553320884705

## Findings

- artifact_incremental_gain_not_proven: best artifact child does not beat dense matched-capacity/no-artifact comparator
- best_child_lift: best generated child beats best root by 0.0205 validation Macro-F1
- discouraged_family:low_rank_head: repeated negative delta
- discouraged_family:stability_regularization: repeated negative delta
- discouraged_family:calibration: repeated negative delta
- unstable_positive_family:imbalance_training: mean_delta=0.0000, std=0.0019, win_rate=0.5416666666666666

## Artifact Usefulness

- Artifact incremental gain proven: `False`
- `best_child_vs_root_val`: 0.02049383521080017
- `foundation_vs_best_dense_no_artifact_val`: -0.012242048978805542
- `foundation_vs_dense_matched_control_val`: -0.012242048978805542
- `foundation_vs_root_val`: 0.008251786231994629

## Policy

### Ranking Boosts

- `artifact_attention_bias`: 0.06
- `artifact_residual_gate`: 0.08
- `dense_matched_capacity_no_artifact_control`: 0.1
- `official_gene_dropout_augmentation`: 0.08
- `official_swa_or_checkpoint_ensemble`: 0.06
- `official_temperature_calibrated_head`: 0.06

### Ranking Penalties

- `calibration`: 0.08
- `low_rank_head`: 0.08
- `stability_regularization`: 0.08

### Implementation Guidance

- Artifact gain is not proven beyond dense control: preserve the strong dense branch, add artifact only as a small gated residual/attention bias, and train a paired no-artifact control whenever possible.
- A child beat the root: reuse its structural motif as a parent-preserving motif before broadening the search.

### Validation Recommendations

- Require artifact-vs-dense-control attribution before claiming biological prior usefulness.
- Run multi-seed validation before promoting `imbalance_training` motifs; positive average lift is not yet stable.
