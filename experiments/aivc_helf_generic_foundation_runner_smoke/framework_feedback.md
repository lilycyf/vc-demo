# Framework Feedback

- Run dir: `experiments/aivc_helf_generic_foundation_runner_smoke`
- Best root: `aivc_helf_perturb_root_gated_mlp` val=0.4011065661907196
- Best child: `aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_457c4213` val=0.41547608375549316

## Findings

- artifact_incremental_gain_not_proven: best artifact child does not beat dense matched-capacity/no-artifact comparator
- best_child_lift: best generated child beats best root by 0.0144 validation Macro-F1
- target_gap: best child is 0.0045 below target validation Macro-F1

## Artifact Usefulness

- Artifact incremental gain proven: `False`
- `best_child_vs_root_val`: 0.01436951756477356
- `foundation_vs_best_dense_no_artifact_val`: None
- `foundation_vs_dense_matched_control_val`: None
- `foundation_vs_root_val`: 0.01436951756477356

## Policy

### Ranking Boosts

- `artifact_attention_bias`: 0.06
- `artifact_residual_gate`: 0.08
- `dense_matched_capacity_no_artifact_control`: 0.1

### Ranking Penalties


### Implementation Guidance

- Artifact gain is not proven beyond dense control: preserve the strong dense branch, add artifact only as a small gated residual/attention bias, and train a paired no-artifact control whenever possible.
- A child beat the root: reuse its structural motif as a parent-preserving motif before broadening the search.
- Target gap remains: favor competitive compositions that retain root performance and test one clear additional mechanism per rollout.

### Validation Recommendations

- Require artifact-vs-dense-control attribution before claiming biological prior usefulness.
