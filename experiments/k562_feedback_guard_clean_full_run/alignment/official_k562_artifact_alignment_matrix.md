# Official K562 Artifact Alignment Matrix

- Registry: `configs/artifacts/k562_registry.json`
- Present artifacts: 8
- Missing artifacts: 8
- Reconstructed compatibility artifacts: none

| Artifact | Provider | Status | Present | Size | Equivalence claim |
|---|---|---|---:|---:|---|
| `esm2_gene_embedding_h5ad` | ESM2 | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `esm2_k562_target_manifest` | ESM2 | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `aido_gene_or_cell_embeddings` | AIDO | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `scfoundation_cell_embeddings` | scFoundation | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `string_k562_gene_graph` | STRING | original_public | true | 8653768 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `pathway_membership_matrix` | Reactome | original_public | true | 75429 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_essential_deg_with_split_h5ad` | GenBio AI HuggingFace | original_public | true | 54536850 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_k562_aido_cell_100m_embedding_h5ad` | AIDO.Cell-100M | original_public | true | 102556306 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_string_gnn_keep20_graph` | STRING_GNN | original_public | true | 27033534 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_aido_cell_100m_model_dir` | AIDO.Cell-100M | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `official_string_gnn_model_dir` | STRING_GNN | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `official_gnn_simple_embedding_h5ad` | GNN Simple Official | original_public | true | 43536698 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_public_best_node_code` | VCHarness | original_public | true | 40969 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `class_distribution` | repo-derived-official-k562-train-split | derived | true | 694 | derived local artifact; usable only with explicit provenance |
| `regulatory_network_artifact` | TBD source-backed regulatory network | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `single_cell_foundation_model_artifact` | scGPT or equivalent source-backed single-cell foundation model | missing | false | 0 | unavailable; strict official mode must acquire or block |
