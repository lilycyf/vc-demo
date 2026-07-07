# K562 ESM2 Artifact Search Final Conclusion

## Setup

- Research question: whether a real frozen ESM2 gene-level embedding artifact improves K562 DEG classification inside the VCHarness-style Codex + MCTS loop.
- Search policy: UCT with exploration `1.4142135623730951`; PUCT was not used.
- Source non-artifact root: `configs/k562_roots/root_concat_gated_mlp.json`.
- Artifact root: `configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json`.
- Artifact dataset: `data/cell_lines/k562_concat_esm2_gene_embedding` (not committed).
- Stop reason: no improvement for 8 nodes.
- Trained nodes: 15; failed nodes: 0; pending nodes: 0.

## Artifact Audit

- Artifact source: public GenBio HuggingFace dataset `gene_embeddings/ESM2_(D=1280).h5ad`.
- Embedding rows: 23,122; unique gene symbols: 19,429; embedding dim: 1280.
- Output feature dim: 2385 = 1105 existing K562 concat features + 1280 ESM2 features.
- Perturbation coverage: 0.9619.
- Missing perturbations: `C19orf26, C3orf72, ELMSAN1, KIAA1804`.

## Results

| Rank | Node | Strategy | Uses ESM2 artifact | Val Macro-F1 | Test Macro-F1 |
|---:|---|---|---|---:|---:|
| 1 | `root_concat_gated_mlp` | root | false | 0.6628 | 0.6275 |
| 2 | `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` | esm2_gene_projection | true | 0.6591 | 0.5801 |
| 3 | `root_concat_esm2_gene_embedding_gated_mlp` | root | true | 0.6520 | 0.6107 |
| 4 | `root_concat_esm2_gene_embedding_gated_mlp_p1_mixture_of_experts_568d46e0` | mixture_of_experts | true | 0.6454 | 0.5710 |
| 5 | `root_concat_esm2_gene_embedding_gated_mlp_p2_focal_loss_training_strategy_28b52bf3` | focal_loss_training_strategy | true | 0.6170 | 0.5913 |
| 6 | `root_concat_esm2_gene_embedding_gated_mlp_p1_selective_adapter_finetune_d110bf14` | selective_adapter_finetune | true | 0.6092 | 0.5563 |
| 7 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_59171b80` | dual_path_gated_low_rank | true | 0.5714 | 0.5319 |
| 8 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_60828c40` | dual_path_gated_low_rank | true | 0.5652 | 0.5270 |
| 9 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_398e085c` | dual_path_gated_low_rank | true | 0.5640 | 0.5153 |
| 10 | `root_concat_gated_mlp_p1_dual_path_gated_low_rank_d587fd09` | dual_path_gated_low_rank | true | 0.5636 | 0.5240 |

- Best root: `root_concat_gated_mlp` val=0.6628 test=0.6275.
- Best overall: `root_concat_gated_mlp` val=0.6628 test=0.6275.
- Best child: `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` val=0.6591 test=0.5801.
- Best ESM2-consuming node: `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460` val=0.6591 test=0.5801.

## Answer

- Did the ESM2 artifact root beat the non-artifact root? No. ESM2 root val=0.6520, non-artifact root val=0.6628.
- Did any ESM2 child beat both roots? No. The best ESM2 child reached val=0.6591, below the non-artifact root val=0.6628.
- Did the experiment now use a real external artifact? Yes. The ESM2 artifact was downloaded, aligned by gene symbol, added to the dataset, validated, and consumed by root/child nodes.
- Main interpretation: adding ESM2 is now technically real, but at this 4-epoch/small-node budget it did not improve over the strong concat gated MLP root. The likely next issue is not artifact availability, but whether the model/fusion strategy and training budget are sufficient to exploit the artifact.

## Limitations

- The current K562 data is still the repo demo K562/Norman-derived dataset, not confirmed as the exact Essential Fold_0 from the paper.
- The ESM2 artifact is gene-level and frozen; no large foundation model was fine-tuned.
- The focal-loss planned node was implemented as a model-head fallback because the current pending-node contract only supplies `model.py`, not a custom loss hook.
- AIDO was not available; the AIDO node is explicitly a missing-artifact fallback and should not be counted as a real AIDO result.

## Next Recommendation

Run a controlled follow-up rather than another broad blind search: train the non-artifact root, ESM2 root, and top ESM2 child for more epochs and 3 seeds. If ESM2 still trails, try a target-gene-aware architecture that uses ESM2 for both perturbed genes and target genes, not only as an appended perturbation feature.
