# Final Search Analysis

## Result

- Run dir: `experiments/k562_single_cellline_small_50`
- Stop reason: no improvement for 10 nodes
- Trained nodes: 13
- Failed nodes: 0
- Best overall: `root_concat_esm2_gene_embedding_gated_mlp` val=0.6685 test=0.6137
- Best root: `root_concat_esm2_gene_embedding_gated_mlp` val=0.6685 test=0.6137
- Improvement over best root: 0.0000 validation Macro-F1

## Benchmark Alignment

- Benchmark status: ready_for_single_cell_line_formal_search
- Benchmark issues: 0
- Remaining question: Confirm the public paper's exact K562 split policy if claiming numeric reproduction rather than framework reproduction.
- Remaining question: Confirm DEG label construction and target gene universe against the paper artifact if available.
- Remaining question: Confirm expert baseline identity and hyperparameters before comparing absolute numbers to the paper.

## Search Scale

- Scale profile: single_cellline_small (small paper-style single-cell-line search)
- Planned budget nodes: 50
- Planned max epochs: 4

## Strategy Families

| Strategy | N | Best val | Best test | Grammar alignment |
|---|---:|---:|---:|---|
| `esm2_gene_projection` | 2 | 0.6582 | 0.5915 | perturbation-side ESM2 feature projection |
| `pathway_pooling_encoder` | 2 | 0.5491 | 0.5140 | pathway prior over target genes |
| `ppi_graph_message_passing` | 2 | 0.4037 | 0.3838 | STRING/PPI target-gene graph prior |
| `root` | 3 | 0.6685 | 0.6137 | blueprint not yet mapped into the grammar |
| `string_gnn_perturbation_propagator` | 2 | 0.3786 | 0.3639 | perturbation signal propagation through STRING graph |
| `target_gene_embedding_bilinear` | 2 | 0.4142 | 0.4111 | explicit perturbed/context and target-gene artifact geometry |

## Artifact Interpretation

- Present artifacts: esm2_gene_embedding_h5ad, esm2_k562_target_manifest, string_k562_gene_graph, pathway_membership_matrix
- Missing artifacts: aido_gene_or_cell_embeddings, scfoundation_cell_embeddings

## Memory-Derived Motifs

- Promising: ppi_graph_message_passing: logit_message_passing + graph_smoothed_target_head val=0.4037, ppi_graph_message_passing: logit_message_passing + graph_smoothed_target_head val=0.3846, string_gnn_perturbation_propagator: graph_propagation + propagated_target_head val=0.3593, string_gnn_perturbation_propagator: graph_propagation + propagated_target_head val=0.3786, target_gene_embedding_bilinear: bilinear_context_target + factorized_target_head val=0.4142, target_gene_embedding_bilinear: bilinear_context_target + factorized_target_head val=0.4142, esm2_gene_projection: two_branch_projection + dense_target_head val=0.6442, esm2_gene_projection: two_branch_projection + dense_target_head val=0.6582, pathway_pooling_encoder: pathway_pooling + pathway_target_head val=0.5395, pathway_pooling_encoder: pathway_pooling + pathway_target_head val=0.5491
- Discouraged: none recorded

## Repair Readiness

- No failed nodes recorded.

## Next Search Recommendations

- Acquire or explicitly reject missing high-value artifacts before claiming paper-level model-space coverage.
- Expand strategies that beat the best root; prune repeated strategies that fail to improve after the repeat limit.
- Treat training-only changes separately from architecture or biological-prior changes.
