# HELF Artifact Acquisition Report

## reactome_pathway_membership

- Status: `present`
- Source URL: https://reactome.org/download/current/ReactomePathways.gmt.zip
- Source/version: `Reactome current download at acquisition time`
- Filtering: Keep pathways with 3-256 HELF target genes, sorted by target coverage, capped at 512 pathways.

## string_gene_graph

- Status: `present`
- Source URL: https://string-db.org/api/tsv/network
- Source/version: `STRING network API species=9606 required_score=400`
- Filtering: POST HELF target genes to official STRING network API; keep target-target edges returned for species 9606 at required_score=400; deduplicate undirected pairs by max score.

## Remaining Registry Missing Artifacts

These were not selected as trainable blockers in the final clean run after Reactome/STRING became available.
- `chemical_encoder_checkpoint_or_drug_fingerprints`
- `esm2_gene_or_protein_embeddings`
- `geneformer_checkpoint`
- `regulatory_network_prior`
- `scfoundation_checkpoint_or_service_output`
- `scgpt_whole_human_checkpoint`
- `uce_checkpoint`
