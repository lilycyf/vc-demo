# Final Conclusion: K562 single_cellline_small 50-node Budget Run

## Result

- Run dir: `experiments/k562_single_cellline_small_50`
- Budget: 50 candidate nodes
- Actual trained nodes: 13
- Stop reason: no improvement for 10 nodes
- Failed nodes: 0
- Pending implementations: 0
- Acquisition queue: 0

## Best Model

- Best overall: `root_concat_esm2_gene_embedding_gated_mlp`
  - val Macro-F1: 0.6685
  - test Macro-F1: 0.6137
- Best root: `root_concat_esm2_gene_embedding_gated_mlp`
  - val Macro-F1: 0.6685
  - test Macro-F1: 0.6137
- Improvement over best root: 0.0000

## What Was Exercised

- UCT parent selection with exploration constant sqrt(2).
- Artifact-aware blueprint ranking.
- Implemented program-node families: root, STRING graph message passing, STRING graph propagation, target-gene ESM2 bilinear, perturbation-side ESM2 projection, Reactome pathway pooling.
- Strict artifact mode: no fallback artifacts were trained.
- Repair workflow: ran and produced no repair tasks because there were no failed nodes in the final run.
- Acquisition workflow: no acquisition task was needed after Reactome pathway membership was built.

## Artifact State

- Present: ESM2 gene embedding H5AD, K562 target-gene ESM2 manifest, K562 STRING graph, Reactome pathway membership matrix.
- Missing: AIDO, scFoundation.
- Reactome pathway artifact: 1139 pathways, target coverage 0.742, source sha256 `8c1dbc8578431da5d2d5118262718c60b553a9be3398e93658daa069e4a9afd4`.

## Scientific Takeaway

For this small K562 formulation, the strongest model remains the perturbation-side ESM2 gated MLP root. The searched biological-prior children were executable and source-backed, but none improved validation Macro-F1 over the best root within the 4-epoch, 50-node-budget early-stopped run. This is a useful negative result: the framework now runs the loop cleanly, but the current task/data/model scale is still not equivalent to the paper K562 benchmark.
