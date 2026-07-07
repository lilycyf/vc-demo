# K562 Cross-Run Diagnosis

This report compares the earlier enhanced PUCT-style run with the paper-aligned UCT run. It is diagnostic, not a new training run.

## Headline

Both runs completed the automated loop, but neither found a child node that beat the best root baseline. The current bottleneck is therefore not basic orchestration reliability; it is the usefulness of the searched model space under the currently available K562 features and missing external biological artifacts.

| Run | Policy | Trained | Children | Planned impl. | L4/L5 children | Failed | Pending | Best root val/test | Best child val/test | Best overall |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| PUCT-ish enhanced run | puct: 27 | 34 | 27 | 5 | 27 | 0 | 0 | 0.6499/0.6127 | 0.6439/0.5841 | root_concat_gated_mlp (0.6499) |
| Paper-aligned UCT run | uct: 23 | 30 | 23 | 6 | 8 | 0 | 0 | 0.6595/0.6149 | 0.6559/0.5907 | root_concat_gated_mlp (0.6595) |

## What Changed Between Runs

- The first run used the repo-enhanced PUCT-style path and reached 34 trained nodes; the best child still trailed the best root.
- The second run used paper-aligned UCT with exploration sqrt(2), reached 30 trained nodes, implemented more planned blueprints on demand, and still did not beat the best root.
- This makes the no-improvement result robust to the parent-selection policy change at the current scale.

## Per-Run Detail

### PUCT-ish enhanced run

- Branch: `origin/k562-paper-level-search-run`
- Trained nodes: 34 roots=7 children=27
- Failed/pending: 0/0
- Best root: `root_concat_gated_mlp` val=0.6499 test=0.6127
- Best overall: `root_concat_gated_mlp` val=0.6499 test=0.6127
- Best child: `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97` val=0.6439 test=0.5841 gap_vs_root=-0.0059/-0.0286
- Best child path: `root_concat_residual_mlp -> root_concat_residual_mlp_p1_mixture_of_experts_bb507bf4 -> root_concat_residual_mlp_p1_mixture_of_experts_df7b769f -> root_concat_residual_mlp_p1_mixture_of_experts_f4f761d6 -> root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88 -> root_concat_residual_mlp_p1_mixture_of_experts_8464479d -> root_concat_residual_mlp_p1_mixture_of_experts_a03c1399 -> root_concat_residual_mlp_p1_mixture_of_experts_513b5884 -> root_concat_residual_mlp_p1_mixture_of_experts_49d84667 -> root_concat_residual_mlp_p1_mixture_of_experts_a86cd846 -> root_concat_residual_mlp_p1_mixture_of_experts_269135c2 -> root_concat_residual_mlp_p1_mixture_of_experts_7f846804 -> root_concat_residual_mlp_p1_mixture_of_experts_214c9d4c -> root_concat_residual_mlp_p1_mixture_of_experts_be9104eb -> root_concat_residual_mlp_p1_mixture_of_experts_5796a973 -> root_concat_residual_mlp_p1_mixture_of_experts_060f6a76 -> root_concat_residual_mlp_p1_mixture_of_experts_2f0b1109 -> root_concat_residual_mlp_p1_mixture_of_experts_03075c2a -> root_concat_residual_mlp_p1_mixture_of_experts_9d8fdcfd -> root_concat_residual_mlp_p1_mixture_of_experts_492850ca -> root_concat_residual_mlp_p1_mixture_of_experts_c60eb670 -> root_concat_residual_mlp_p1_mixture_of_experts_85dd45d1 -> root_concat_residual_mlp_p1_mixture_of_experts_223a10cb -> root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97`
- Child level distribution: 4: 24, 5: 3
- Depth distribution: 0: 7, 1: 5, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1
- Strategy distribution: mixture_of_experts: 22, esm2_gene_projection: 1, aido_embedding_fusion: 1, pathway_pooling_encoder: 1, cross_attention_gene_perturbation: 1, gated_multimodal_fusion: 1
- Missing/fallback terms in reports: fallback: 9, aido: 8, esm2: 8, pathway: 8, missing: 7

| Top child | Level | Depth | Strategy | Val | Test | Gap vs root val |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97 | 4 | 23 | gated_multimodal_fusion | 0.6439 | 0.5841 | -0.0059 |
| root_concat_residual_mlp_p1_mixture_of_experts_513b5884 | 4 | 7 | mixture_of_experts | 0.6414 | 0.5693 | -0.0085 |
| root_concat_residual_mlp_p1_mixture_of_experts_492850ca | 4 | 19 | mixture_of_experts | 0.6400 | 0.5733 | -0.0099 |
| root_concat_residual_mlp_p1_mixture_of_experts_03075c2a | 4 | 17 | mixture_of_experts | 0.6388 | 0.5718 | -0.0111 |
| root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88 | 4 | 4 | mixture_of_experts | 0.6376 | 0.5692 | -0.0122 |
| root_concat_residual_mlp_p1_mixture_of_experts_df7b769f | 4 | 2 | mixture_of_experts | 0.6359 | 0.5687 | -0.0140 |

### Paper-aligned UCT run

- Branch: `origin/k562-paper-aligned-uct-run`
- Trained nodes: 30 roots=7 children=23
- Failed/pending: 0/0
- Best root: `root_concat_gated_mlp` val=0.6595 test=0.6149
- Best overall: `root_concat_gated_mlp` val=0.6595 test=0.6149
- Best child: `root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d` val=0.6559 test=0.5907 gap_vs_root=-0.0036/-0.0241
- Best child path: `root_concat_residual_mlp -> root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d`
- Child level distribution: unknown: 14, 5: 4, 4: 4, 2: 1
- Depth distribution: 1: 9, 0: 7, 2: 3, 3: 2, 4: 2, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1
- Strategy distribution: dual_path_gated_low_rank: 14, mixture_of_experts: 3, esm2_gene_projection: 1, aido_embedding_fusion: 1, pathway_pooling_encoder: 1, cross_attention_gene_perturbation: 1, uncertainty_calibrated_head: 1, selective_adapter_finetune: 1
- Missing/fallback terms in reports: fallback: 10, aido: 7, esm2: 7, pathway: 7, missing: 7

| Top child | Level | Depth | Strategy | Val | Test | Gap vs root val |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d | 2 | 1 | uncertainty_calibrated_head | 0.6559 | 0.5907 | -0.0036 |
| root_concat_regularized_mlp_p1_mixture_of_experts_47d46756 | 4 | 1 | mixture_of_experts | 0.6279 | 0.5721 | -0.0316 |
| root_concat_regularized_mlp_p1_mixture_of_experts_46004776 | 4 | 2 | mixture_of_experts | 0.6259 | 0.5713 | -0.0336 |
| root_concat_regularized_mlp_p1_mixture_of_experts_51750e6b | 4 | 3 | mixture_of_experts | 0.6244 | 0.5589 | -0.0351 |
| root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53 | 5 | 1 | aido_embedding_fusion | 0.6192 | 0.5914 | -0.0403 |
| root_delta_mlp_p1_dual_path_gated_low_rank_1ee05fa7 | unknown | 3 | dual_path_gated_low_rank | 0.5790 | 0.5327 | -0.0805 |

## Diagnosis

1. The strongest baseline is already hard to beat at the current epoch budget. In both runs, `root_concat_gated_mlp` is the best overall model, not merely the best root.
2. Search policy was not the main blocker. Switching from enhanced PUCT-style selection to paper-aligned UCT changed the tree behavior but did not make children surpass the root.
3. Planned blueprints mostly tested code-generation ability rather than new biological signal. The reports repeatedly mention missing/fallback conditions around external artifacts such as ESM2/AIDO/scFoundation/STRING/pathway resources.
4. Many children are architectural heads/fusion variants on the same underlying features. Without new embeddings, graph priors, or stronger representation changes, Level 4/5 labels do not necessarily mean Level 4/5 information content.
5. No failed or pending nodes is good news: the implementation loop is stable enough to support a larger or richer experiment.

## Recommended Next Step

The next useful upgrade is not another 30-node blind run. It should be one of these, in priority order:

1. Add at least one real external biological artifact and rerun: ESM2 gene embeddings, STRING/PPI graph features, pathway membership features, or scFoundation-style cell embeddings.
2. Re-run the best root and top 3 children with multiple seeds and a larger epoch budget to estimate whether the observed gaps are robust or training-noise dominated.
3. Add a proposal constraint that requires each planned Level 4/5 node to declare which new information source it actually consumes; otherwise label it as an architectural fallback, not a biological-prior node.
4. Scale only after the above: a 100+ node run is now technically feasible, but without richer artifacts it will likely spend more GPU on variants of the same signal.

## Concrete Handoff

For the next Codex run, the best task is: implement one real biological artifact integration first, then run a smaller confirmation search. The cleanest first artifact is static gene-level embeddings because it changes the input representation without requiring a full graph training stack.

