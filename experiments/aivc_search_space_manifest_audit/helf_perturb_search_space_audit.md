# HELF Perturbation Search Space Audit

- Search space: `configs/helf_perturb_search_space.json`
- Registry: `configs/artifacts/helf_perturb_registry.json`
- Search space id: `helf_perturb_foundation_artifact_search_space_v2`
- Foundation blueprint count: `18`
- Executable now: `3`
- Artifact-present blueprints: `3`
- Artifact-missing blueprints: `15`
- Estimated candidate lower bound: `2400`
- Combinatorial dimension product: `230400`

## Implementation Status

- `acquirable_or_buildable_then_planned`: 5
- `implemented_as_parent_preserving_artifact_augmented_residual`: 3
- `planned_requires_checkpoint_or_contract_validation`: 9
- `planned_requires_drug_smiles_artifact`: 1

## Family Summary

| Family | Blueprints | Executable now | Missing artifact blueprints |
|---|---:|---:|---:|
| `chemical_perturbation_encoder` | 3 | 0 | 3 |
| `gene_or_protein_foundation_prior` | 2 | 0 | 2 |
| `multimodal_fusion` | 3 | 0 | 3 |
| `network_and_pathway_prior` | 4 | 3 | 1 |
| `single_cell_foundation_encoder` | 6 | 0 | 6 |

## Blueprint Table

| Family | Blueprint | Status | Required artifacts | Missing artifacts | Executable now |
|---|---|---|---|---|---:|
| `single_cell_foundation_encoder` | `scgpt_cell_encoder` | `planned_requires_checkpoint_or_contract_validation` | scgpt_whole_human_checkpoint | scgpt_whole_human_checkpoint | False |
| `single_cell_foundation_encoder` | `scgpt_adapter_finetune` | `planned_requires_checkpoint_or_contract_validation` | scgpt_whole_human_checkpoint | scgpt_whole_human_checkpoint | False |
| `single_cell_foundation_encoder` | `geneformer_cell_encoder` | `planned_requires_checkpoint_or_contract_validation` | geneformer_checkpoint | geneformer_checkpoint | False |
| `single_cell_foundation_encoder` | `geneformer_adapter_head` | `planned_requires_checkpoint_or_contract_validation` | geneformer_checkpoint | geneformer_checkpoint | False |
| `single_cell_foundation_encoder` | `scfoundation_cell_encoder` | `planned_requires_checkpoint_or_contract_validation` | scfoundation_checkpoint_or_service_output | scfoundation_checkpoint_or_service_output | False |
| `single_cell_foundation_encoder` | `uce_cell_embedding` | `planned_requires_checkpoint_or_contract_validation` | uce_checkpoint | uce_checkpoint | False |
| `gene_or_protein_foundation_prior` | `esm2_target_gene_head` | `acquirable_or_buildable_then_planned` | esm2_gene_or_protein_embeddings | esm2_gene_or_protein_embeddings | False |
| `gene_or_protein_foundation_prior` | `protein_embedding_fusion` | `acquirable_or_buildable_then_planned` | esm2_gene_or_protein_embeddings | esm2_gene_or_protein_embeddings | False |
| `chemical_perturbation_encoder` | `rdkit_drug_fingerprint_fusion` | `planned_requires_drug_smiles_artifact` | chemical_encoder_checkpoint_or_drug_fingerprints | chemical_encoder_checkpoint_or_drug_fingerprints | False |
| `chemical_perturbation_encoder` | `chemberta_drug_encoder` | `acquirable_or_buildable_then_planned` | chemical_encoder_checkpoint_or_drug_fingerprints | chemical_encoder_checkpoint_or_drug_fingerprints | False |
| `chemical_perturbation_encoder` | `drug_target_cross_attention` | `acquirable_or_buildable_then_planned` | chemical_encoder_checkpoint_or_drug_fingerprints, esm2_gene_or_protein_embeddings | chemical_encoder_checkpoint_or_drug_fingerprints, esm2_gene_or_protein_embeddings | False |
| `network_and_pathway_prior` | `string_graph_message_passing` | `implemented_as_parent_preserving_artifact_augmented_residual` | string_gene_graph | none | True |
| `network_and_pathway_prior` | `graph_laplacian_head` | `implemented_as_parent_preserving_artifact_augmented_residual` | string_gene_graph | none | True |
| `network_and_pathway_prior` | `pathway_pooling_encoder` | `implemented_as_parent_preserving_artifact_augmented_residual` | reactome_pathway_membership | none | True |
| `network_and_pathway_prior` | `tf_regulatory_attention` | `planned_requires_checkpoint_or_contract_validation` | regulatory_network_prior | regulatory_network_prior | False |
| `multimodal_fusion` | `cell_foundation_plus_drug_fusion` | `planned_requires_checkpoint_or_contract_validation` | scgpt_whole_human_checkpoint, chemical_encoder_checkpoint_or_drug_fingerprints | scgpt_whole_human_checkpoint, chemical_encoder_checkpoint_or_drug_fingerprints | False |
| `multimodal_fusion` | `cell_gene_graph_tri_modal_fusion` | `planned_requires_checkpoint_or_contract_validation` | geneformer_checkpoint, esm2_gene_or_protein_embeddings, string_gene_graph | geneformer_checkpoint, esm2_gene_or_protein_embeddings | False |
| `multimodal_fusion` | `pathway_drug_target_fusion` | `acquirable_or_buildable_then_planned` | chemical_encoder_checkpoint_or_drug_fingerprints, reactome_pathway_membership, esm2_gene_or_protein_embeddings | chemical_encoder_checkpoint_or_drug_fingerprints, esm2_gene_or_protein_embeddings | False |

## Interpretation

This audit distinguishes the declared model universe from the currently executable subset. Fast runs usually train the executable subset only; paper-scale runs require acquiring/building the missing checkpoint or embedding artifacts and increasing rollout/epoch budgets.
