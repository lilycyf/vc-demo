# Artifact Usefulness Report

- Run dir: `experiments/aivc_more_executable_nodes_smoke_v3`
- Artifact incremental gain proven: `False`
- Best child vs root val delta: `0.012086033821105957`
- Foundation vs root val delta: `0.012086033821105957`
- Foundation vs dense no-artifact val delta: `None`
- Foundation vs dense matched-control val delta: `None`

## Best Nodes

| Role | Node | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| Best root | `aivc_helf_perturb_root_mlp` | 0.4123806655406952 | 0.400498628616333 |
| Best generated child | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion` | 0.42446669936180115 | 0.4096287786960602 |
| Best foundation artifact child | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion` | 0.42446669936180115 | 0.4096287786960602 |
| Best dense no-artifact child | `` | None | None |
| Best dense matched control | `` | None | None |

## Interpretation

A child can beat the root because of capacity, loss, optimization, or artifacts. This report only treats biological artifacts as useful when a source-backed artifact child beats the best available dense no-artifact or paired dense matched-capacity control under the same validation-only selection policy.
