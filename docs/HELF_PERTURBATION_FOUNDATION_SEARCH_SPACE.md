# HELF Perturbation Foundation Search Space

This document defines the heavy-artifact search space for `HELF_PERTURB_DEG`. The lightweight PyTorch models are only baseline/smoke checks. The main VCHarness-style search should prefer source-backed biological foundation artifacts when they are available or buildable.

## Task

Predict drug perturbation response in HELF cells as target-gene DEG direction.

- Input unit: treated-control pseudobulk delta for one drug perturbation.
- Output: `[batch, n_target_genes, 3]` down / unchanged / up logits.
- Reward: validation Macro-F1.
- Test Macro-F1: final report only.

## Artifact Policy

Every selected foundation proposal must first pass artifact validation.

- If artifact is already present, validate shape, vocabulary, row order, coverage, and provenance.
- If artifact is missing but source-backed, Codex should download or build it immediately.
- If artifact source, shape, vocabulary, or provenance cannot be verified, block the selected node and continue search.
- Never replace a missing foundation model with a compact/proxy local model while claiming foundation usage.

Registry: `configs/artifacts/helf_perturb_registry.json`.

## Foundation Artifact Universe

| Group | Candidate artifact | Expected role | Status |
|---|---|---|---|
| Single-cell FM | scGPT whole-human checkpoint | encode treated/control cell states; adapter/fine-tune options | planned acquisition |
| Single-cell FM | Geneformer checkpoint | rank-token transcriptome encoder; adapter/head search | planned acquisition |
| Single-cell FM | scFoundation checkpoint or service embeddings | cell-state foundation embeddings | planned acquisition/block if unavailable |
| Single-cell FM | UCE checkpoint | universal cell embeddings for HELF treated/control cells | planned acquisition |
| Gene/protein FM | ESM2 gene/protein embeddings | target-gene-aware head geometry | planned build/acquisition |
| Drug FM | RDKit fingerprints / ChemBERTa-style encoder | encode perturbing drug beyond one-hot | planned build/acquisition |
| Network prior | STRING gene graph | graph message passing / Laplacian smoothing | planned build |
| Pathway prior | Reactome membership | pathway pooling / hierarchical head | planned build |
| Regulatory prior | DoRothEA/TRRUST/ENCODE-like network | TF-target regulatory attention | source selection required |

## Blueprint Families

### Single-cell Foundation Encoders

- `scgpt_cell_encoder`
- `scgpt_adapter_finetune`
- `geneformer_cell_encoder`
- `geneformer_adapter_head`
- `scfoundation_cell_encoder`
- `uce_cell_embedding`

These nodes should compare treated and control cell-state embeddings, then predict target-gene DEG direction.

### Gene Or Protein Foundation Priors

- `esm2_target_gene_head`
- `protein_embedding_fusion`

These nodes make the model understand target genes as biological entities, not just target indices.

### Chemical Perturbation Encoders

- `rdkit_drug_fingerprint_fusion`
- `chemberta_drug_encoder`
- `drug_target_cross_attention`

These nodes make the perturbation representation stronger than drug one-hot.

### Network And Pathway Priors

- `string_graph_message_passing`
- `graph_laplacian_head`
- `pathway_pooling_encoder`
- `tf_regulatory_attention`

These nodes add biological prior structure over target genes.

### Multimodal Fusion

- `cell_foundation_plus_drug_fusion`
- `cell_gene_graph_tri_modal_fusion`
- `pathway_drug_target_fusion`

These are the most VCHarness-like candidates because each node is a full executable modeling pipeline, not a small hyperparameter tweak.

## Baseline Tier

The existing MLP/residual/gated/low-rank PyTorch models remain useful for smoke and baseline comparisons, but they are not sufficient for the formal foundation-artifact demo.

## Formal Demo Success Criteria

A formal run should report:

- best lightweight baseline;
- best foundation-artifact child;
- artifact acquisition outcomes;
- blocked artifacts and exact blocker evidence;
- whether any selected foundation node used fallback/proxy, which must be zero;
- whether the best child beats the best root on validation Macro-F1.
