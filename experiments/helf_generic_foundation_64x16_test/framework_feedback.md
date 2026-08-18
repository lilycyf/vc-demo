# Framework Feedback

- Run dir: `experiments/helf_generic_foundation_64x16_test`
- Best root: `aivc_helf_perturb_root_residual_mlp` val=0.4117428958415985
- Best child: `aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passin_p1_dense_matched_capacity_no_artifact_control_control_ec39ace9` val=0.4213203191757202

## Findings

- artifact_incremental_gain_not_proven: best artifact child does not beat dense matched-capacity/no-artifact comparator
- best_child_lift: best generated child beats best root by 0.0096 validation Macro-F1
- discouraged_family:stability_regularization: repeated negative delta
- discouraged_family:calibration: repeated negative delta
- discouraged_family:low_rank_head: repeated negative delta

## Artifact Usefulness

- Artifact incremental gain proven: `False`
- `best_child_vs_root_val`: 0.009577423334121704
- `foundation_vs_best_dense_no_artifact_val`: -0.003212451934814453
- `foundation_vs_dense_matched_control_val`: -0.003212451934814453
- `foundation_vs_root_val`: 0.006364971399307251

## Policy

### Ranking Boosts

- `artifact_attention_bias`: 0.06
- `artifact_residual_gate`: 0.08
- `dense_matched_capacity_no_artifact_control`: 0.1

### Ranking Penalties

- `calibration`: 0.08
- `low_rank_head`: 0.08
- `stability_regularization`: 0.08

### Implementation Guidance

- Artifact gain is not proven beyond dense control: preserve the strong dense branch, add artifact only as a small gated residual/attention bias, and train a paired no-artifact control whenever possible.
- A child beat the root: reuse its structural motif as a parent-preserving motif before broadening the search.

### Validation Recommendations

- Require artifact-vs-dense-control attribution before claiming biological prior usefulness.
