# Artifact Usefulness Report

- Run dir: `experiments/aivc_helf_generic_foundation_runner_smoke`
- Artifact incremental gain proven: `False`
- Best child vs root val delta: `0.01436951756477356`
- Foundation vs root val delta: `0.01436951756477356`
- Foundation vs dense no-artifact val delta: `None`
- Foundation vs dense matched-control val delta: `None`

## Best Nodes

| Role | Node | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| Best root | `aivc_helf_perturb_root_gated_mlp` | 0.4011065661907196 | 0.4000442326068878 |
| Best generated child | `aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_457c4213` | 0.41547608375549316 | 0.41339072585105896 |
| Best foundation artifact child | `aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_457c4213` | 0.41547608375549316 | 0.41339072585105896 |
| Best dense no-artifact child | `` | None | None |
| Best dense matched control | `` | None | None |

## Interpretation

A child can beat the root because of capacity, loss, optimization, or artifacts. This report only treats biological artifacts as useful when a source-backed artifact child beats the best available dense no-artifact or paired dense matched-capacity control under the same validation-only selection policy.
