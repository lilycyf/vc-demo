# Artifact Usefulness Report

- Run dir: `experiments/aivc_more_executable_nodes_smoke_v2`
- Artifact incremental gain proven: `True`
- Best child vs root val delta: `0.020339787006378174`
- Foundation vs root val delta: `0.020339787006378174`
- Foundation vs dense no-artifact val delta: `0.018890738487243652`
- Foundation vs dense matched-control val delta: `0.018890738487243652`

## Best Nodes

| Role | Node | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| Best root | `aivc_helf_perturb_root_mlp` | 0.4011034667491913 | 0.3975583612918854 |
| Best generated child | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion` | 0.42144325375556946 | 0.4116392433643341 |
| Best foundation artifact child | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion` | 0.42144325375556946 | 0.4116392433643341 |
| Best dense no-artifact child | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p18_foundation_chemberta_drug_encoder_dense_control` | 0.4025525152683258 | 0.39271438121795654 |
| Best dense matched control | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p18_foundation_chemberta_drug_encoder_dense_control` | 0.4025525152683258 | 0.39271438121795654 |

## Paired Artifact Controls

| Artifact child | Control child | Artifact val | Control val | Incremental gain |
|---|---|---:|---:|---:|
| `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p17_foundation_rdkit_drug_fingerprint_fusion` | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p17_foundation_rdkit_drug_fingerprint_fusion_dense_control` | 0.3924606740474701 | 0.397737592458725 | -0.005276918411254883 |
| `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p18_foundation_chemberta_drug_encoder` | `aivc_helf_perturb_root_mlp_p2_foundation_protein_embedding_fusion_p18_foundation_chemberta_drug_encoder_dense_control` | 0.3951749801635742 | 0.4025525152683258 | -0.007377535104751587 |

## Interpretation

A child can beat the root because of capacity, loss, optimization, or artifacts. This report only treats biological artifacts as useful when a source-backed artifact child beats the best available dense no-artifact or paired dense matched-capacity control under the same validation-only selection policy.
