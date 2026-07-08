# Official K562 Artifact Alignment Matrix

- Registry: `configs/artifacts/k562_registry.json`
- Present artifacts: 11
- Missing artifacts: 2
- Reconstructed compatibility artifacts: official_string_gnn_model_dir

| Artifact | Provider | Status | Present | Size | Equivalence claim |
|---|---|---|---:|---:|---|
| `esm2_gene_embedding_h5ad` | ESM2 | original_public | true | 242230762 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `esm2_k562_target_manifest` | ESM2 | derived | true | 2564 | derived local artifact; usable only with explicit provenance |
| `aido_gene_or_cell_embeddings` | AIDO | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `scfoundation_cell_embeddings` | scFoundation | missing | false | 0 | unavailable; strict official mode must acquire or block |
| `string_k562_gene_graph` | STRING | original_public | true | 8690319 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `pathway_membership_matrix` | Reactome | original_public | true | 75429 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_essential_deg_with_split_h5ad` | GenBio AI HuggingFace | original_public | true | 54536850 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_k562_aido_cell_100m_embedding_h5ad` | AIDO.Cell-100M | original_public | true | 102556306 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_string_gnn_keep20_graph` | STRING_GNN | original_public | true | 27033534 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_aido_cell_100m_model_dir` | AIDO.Cell-100M | original_public | true | 0 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_string_gnn_model_dir` | STRING_GNN | reconstructed_compatibility | true | 0 | compatibility reconstruction; do not claim numerical equivalence to unpublished original checkpoint |
| `official_gnn_simple_embedding_h5ad` | GNN Simple Official | original_public | true | 43536698 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
| `official_public_best_node_code` | VCHarness | original_public | true | 40969 | public artifact available locally; equivalent to the cited public source subject to checksum/source metadata |
