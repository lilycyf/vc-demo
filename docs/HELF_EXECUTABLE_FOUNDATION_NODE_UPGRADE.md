# HELF Executable Foundation Node Upgrade

This document records the framework upgrade that turns additional HELF perturbation foundation blueprints from manifest-only entries into source-backed executable search nodes.

## Scope

- Task: HELF perturbation DEG classification demo.
- Goal: keep the VCHarness-style loop generic while making more foundation/artifact-aware blueprint families executable.
- Policy: no fallback artifacts, no proxy foundation claims, no test-guided search, and no committed data/checkpoints.

## New Source-Backed Runtime Artifacts

| Artifact | Source | Runtime path | Coverage / shape | Git policy |
|---|---|---|---|---|
| `chemical_encoder_checkpoint_or_drug_fingerprints` | PubChem PUG REST + RDKit Morgan fingerprints | `data/artifacts/helf/drug_embeddings.npz` | 1.0 coverage, shape `[10, 2054]` | artifact file is runtime-only; summary is committed |
| `esm2_gene_or_protein_embeddings` | UniProt human protein TSV + HuggingFace `facebook/esm2_t6_8M_UR50D` | `data/artifacts/helf/esm2_gene_embeddings.npz` | 492/512 targets, shape `[512, 320]` | artifact file is runtime-only; summary is committed |

The larger `facebook/esm2_t33_650M_UR50D` checkpoint was verified downloadable on this RunPod. The current Blackwell GPU image uses torch 2.4.1, which cannot run CUDA kernels for `sm_120`, so the executable artifact was built on CPU with the smaller same-family ESM2 checkpoint. Rebuilding with the 650M checkpoint only requires a compatible PyTorch/CUDA image or CPU time.

## Blueprints Now Executable

| Family | Blueprint | Required artifacts | Execution behavior |
|---|---|---|---|
| `gene_or_protein_foundation_prior` | `esm2_target_gene_head` | esm2_gene_or_protein_embeddings | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |
| `gene_or_protein_foundation_prior` | `protein_embedding_fusion` | esm2_gene_or_protein_embeddings | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |
| `chemical_perturbation_encoder` | `rdkit_drug_fingerprint_fusion` | chemical_encoder_checkpoint_or_drug_fingerprints | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |
| `chemical_perturbation_encoder` | `chemberta_drug_encoder` | chemical_encoder_checkpoint_or_drug_fingerprints | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |
| `chemical_perturbation_encoder` | `drug_target_cross_attention` | chemical_encoder_checkpoint_or_drug_fingerprints, esm2_gene_or_protein_embeddings | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |
| `network_and_pathway_prior` | `string_graph_message_passing` | string_gene_graph | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |
| `network_and_pathway_prior` | `graph_laplacian_head` | string_gene_graph | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |
| `network_and_pathway_prior` | `pathway_pooling_encoder` | reactome_pathway_membership | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |
| `multimodal_fusion` | `pathway_drug_target_fusion` | chemical_encoder_checkpoint_or_drug_fingerprints, reactome_pathway_membership, esm2_gene_or_protein_embeddings | materialized as parent-preserving `artifact_augmented_residual_mlp` with source-backed artifact tables |

## Still Non-Executable Without Further Acquisition

| Family | Blueprint | Missing artifacts | Why not executable yet |
|---|---|---|---|
| `single_cell_foundation_encoder` | `scgpt_cell_encoder` | scgpt_whole_human_checkpoint | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |
| `single_cell_foundation_encoder` | `scgpt_adapter_finetune` | scgpt_whole_human_checkpoint | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |
| `single_cell_foundation_encoder` | `geneformer_cell_encoder` | geneformer_checkpoint | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |
| `single_cell_foundation_encoder` | `geneformer_adapter_head` | geneformer_checkpoint | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |
| `single_cell_foundation_encoder` | `scfoundation_cell_encoder` | scfoundation_checkpoint_or_service_output | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |
| `single_cell_foundation_encoder` | `uce_cell_embedding` | uce_checkpoint | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |
| `network_and_pathway_prior` | `tf_regulatory_attention` | regulatory_network_prior | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |
| `multimodal_fusion` | `cell_foundation_plus_drug_fusion` | scgpt_whole_human_checkpoint | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |
| `multimodal_fusion` | `cell_gene_graph_tri_modal_fusion` | geneformer_checkpoint | checkpoint or vocabulary/order contract is not yet validated; strict mode must acquire or block, not fallback |

## Runner Changes

- `scripts/run_helf_drug_harness_demo.py` now injects ESM2 target-gene embeddings and drug fingerprint tables into selected artifact-present foundation blueprints.
- Dense matched-capacity controls are generated for attribution, but their queue score is lower than the paired artifact child so they do not preempt artifact rollouts.
- Drug-only foundation blueprints are recognized as executable when `drug_embedding_tables` are present.

## Model Changes

- `ArtifactAugmentedResidualMLP` now supports target-only, drug-only, and drug+target artifact combinations.
- Drug fingerprints are fused through the perturbation drug one-hot tail of the model input and added as a gated context augmentation.
- Target artifacts such as Reactome, STRING graph features, and ESM2 embeddings remain target-aligned residual heads.

## Smoke Result

- Run dir: `experiments/aivc_more_executable_nodes_smoke_v2`.
- Foundation blueprints executable now: `9 / 18`.
- Trained selected rollouts: `8`.
- Trained foundation-artifact children: `6`.
- Blocked/acquisition: `0`.
- Fallback/proxy/backprop-nontrained: `0`.
- Best foundation artifact child beat root and dense control in this smoke, proving the new nodes are actually trainable rather than manifest-only.
