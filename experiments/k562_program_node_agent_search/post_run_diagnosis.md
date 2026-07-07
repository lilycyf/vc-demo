# K562 Paper-Level Search Post-Run Diagnosis

## Executive Diagnosis

The run validated the paper-level program-node loop, but it did not validate superior model discovery. The best child was close to the strongest root, yet still below it, and the best overall node remained the root baseline.

- Best root: `root_concat_gated_mlp` val=0.6499 test=0.6127.
- Best child: `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97` val=0.6439 test=0.5841.
- Child gap vs best root: -0.0059 validation Macro-F1 and -0.0286 test Macro-F1.
- Trained nodes: 34 total = 7 roots + 27 children.
- Planned on-demand children: 5; Level 4/5 children: 27.

The primary failure mode was not implementation instability: failed and pending nodes were both zero. The failure mode was search/model-space quality: most expanded children either lacked the biological artifact that would make the blueprint meaningful, or repeated the same implemented `mixture_of_experts` transformation down a long chain.

## Top-Line Metric Evidence

| Rank | Node | Kind | Strategy | Level | Val | Test | Delta vs Best Root |
|---|---|---|---|---|---|---|---|
| 1 | `root_concat_gated_mlp` | root | root |  | 0.6499 | 0.6127 | 0.0000 |
| 2 | `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97` | child | gated_multimodal_fusion | 4 | 0.6439 | 0.5841 | -0.0059 |
| 3 | `root_concat_residual_mlp_p1_mixture_of_experts_513b5884` | child | mixture_of_experts | 4 | 0.6414 | 0.5693 | -0.0085 |
| 4 | `root_concat_mlp` | root | root |  | 0.6403 | 0.5818 | -0.0096 |
| 5 | `root_concat_residual_mlp_p1_mixture_of_experts_492850ca` | child | mixture_of_experts | 4 | 0.6400 | 0.5733 | -0.0099 |
| 6 | `root_concat_residual_mlp_p1_mixture_of_experts_03075c2a` | child | mixture_of_experts | 4 | 0.6388 | 0.5718 | -0.0111 |
| 7 | `root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88` | child | mixture_of_experts | 4 | 0.6376 | 0.5692 | -0.0122 |
| 8 | `root_concat_residual_mlp_p1_mixture_of_experts_df7b769f` | child | mixture_of_experts | 4 | 0.6359 | 0.5687 | -0.0140 |
| 9 | `root_concat_residual_mlp_p1_mixture_of_experts_060f6a76` | child | mixture_of_experts | 4 | 0.6346 | 0.5799 | -0.0153 |
| 10 | `root_concat_residual_mlp_p1_mixture_of_experts_269135c2` | child | mixture_of_experts | 4 | 0.6338 | 0.5751 | -0.0161 |
| 11 | `root_concat_residual_mlp_p1_mixture_of_experts_f4f761d6` | child | mixture_of_experts | 4 | 0.6330 | 0.5736 | -0.0168 |
| 12 | `root_concat_residual_mlp_p1_mixture_of_experts_223a10cb` | child | mixture_of_experts | 4 | 0.6327 | 0.5631 | -0.0172 |

The best child missed the best root by only about 0.006 validation Macro-F1, so the search did find a near-competitive architecture. However, the test gap was larger, about 0.029 Macro-F1, so there is not enough evidence that the child was merely undertrained.

## Best Child Path

The best child was found at the end of a deep repeated-MoE chain:

```text
root_concat_residual_mlp -> root_concat_residual_mlp_p1_mixture_of_experts_bb507bf4 -> root_concat_residual_mlp_p1_mixture_of_experts_df7b769f -> root_concat_residual_mlp_p1_mixture_of_experts_f4f761d6 -> root_concat_residual_mlp_p1_mixture_of_experts_e1df0a88 -> root_concat_residual_mlp_p1_mixture_of_experts_8464479d -> root_concat_residual_mlp_p1_mixture_of_experts_a03c1399 -> root_concat_residual_mlp_p1_mixture_of_experts_513b5884 -> root_concat_residual_mlp_p1_mixture_of_experts_49d84667 -> root_concat_residual_mlp_p1_mixture_of_experts_a86cd846 -> root_concat_residual_mlp_p1_mixture_of_experts_269135c2 -> root_concat_residual_mlp_p1_mixture_of_experts_7f846804 -> root_concat_residual_mlp_p1_mixture_of_experts_214c9d4c -> root_concat_residual_mlp_p1_mixture_of_experts_be9104eb -> root_concat_residual_mlp_p1_mixture_of_experts_5796a973 -> root_concat_residual_mlp_p1_mixture_of_experts_060f6a76 -> root_concat_residual_mlp_p1_mixture_of_experts_2f0b1109 -> root_concat_residual_mlp_p1_mixture_of_experts_03075c2a -> root_concat_residual_mlp_p1_mixture_of_experts_9d8fdcfd -> root_concat_residual_mlp_p1_mixture_of_experts_492850ca -> root_concat_residual_mlp_p1_mixture_of_experts_c60eb670 -> root_concat_residual_mlp_p1_mixture_of_experts_85dd45d1 -> root_concat_residual_mlp_p1_mixture_of_experts_223a10cb -> root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97
```

This path matters because it shows the search did not simply stop at the root. It aggressively deepened one family, but most steps were the same transformation repeated rather than diverse architecture discovery.

## Strategy-Level Summary

| Strategy | Count | Level | Best Val | Mean Val | Worst Val | Best Test |
|---|---|---|---|---|---|---|
| gated_multimodal_fusion | 1 | 4 | 0.6439 | 0.6439 | 0.6439 | 0.5841 |
| mixture_of_experts | 22 | 4 | 0.6414 | 0.6323 | 0.6222 | 0.5799 |
| aido_embedding_fusion | 1 | 5 | 0.6313 | 0.6313 | 0.6313 | 0.5749 |
| esm2_gene_projection | 1 | 5 | 0.5510 | 0.5510 | 0.5510 | 0.5189 |
| pathway_pooling_encoder | 1 | 5 | 0.3498 | 0.3498 | 0.3498 | 0.3477 |
| cross_attention_gene_perturbation | 1 | 4 | 0.3158 | 0.3158 | 0.3158 | 0.3158 |

Observations:

- `mixture_of_experts` dominated the run: 22 of 27 children. Its best validation score was 0.6414, mean 0.6323, and best test 0.5799. This is stable, but below the best root.
- The only child that got close to the best root was `gated_multimodal_fusion`, but its external-prior branch was inactive, so it was still a tabular fallback rather than a true multimodal/foundation model.
- `pathway_pooling_encoder` and `cross_attention_gene_perturbation` were very weak in this run, suggesting that learnable slots/tokens without real biology can hurt more than help.

## Planned Blueprint And Fallback Diagnosis

| Blueprint | Diagnosis |
|---|---|
| `esm2_gene_projection` | missing protein sequence / ESM2 embedding artifact; fallback used frozen zero foundation prior plus tabular encoder |
| `aido_embedding_fusion` | missing AIDO embeddings; fallback used inactive frozen AIDO branch with gated tabular fusion |
| `pathway_pooling_encoder` | missing pathway memberships; fallback used learnable pathway slots without external pathway membership |
| `cross_attention_gene_perturbation` | no external artifact required, but used learnable target tokens rather than real gene/protein tokens |
| `gated_multimodal_fusion` | external prior embeddings inactive; fallback used two-view tabular gated fusion |

The planned blueprints were implemented honestly: missing ESM2/AIDO/pathway artifacts were recorded rather than fabricated. That is scientifically correct, but it also means the paper-level modules were not actually tested as paper-level biological priors. They were mostly fallback architecture ablations over the existing tabular features.

## PUCT Behavior Diagnosis

- Proposal files inspected: 27.
- Selection policy recorded in proposals: `puct`.
- Cases where selected parent was not the top scored candidate: 0.

| Selected Parent | Times Selected |
|---|---|
| `root_concat_gated_mlp` | 2 |
| `root_concat_mlp` | 2 |
| `root_concat_residual_mlp_p1_mixture_of_experts_223a10cb` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_2f0b1109` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_5796a973` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_7f846804` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_85dd45d1` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_a86cd846` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_060f6a76` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_9d8fdcfd` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_513b5884` | 1 |
| `root_concat_residual_mlp_p1_mixture_of_experts_a03c1399` | 1 |

PUCT behaved deterministically with the recorded scores: the selected parent matched the top candidate in the proposal records. The issue is therefore less a scoring bug and more an interaction between parent selection and proposal generation.

Specifically, after the first planned-blueprint attempts, the run repeatedly selected the newest `mixture_of_experts` child as the next parent. Because each newest child had few children and acceptable validation performance, progressive widening made it eligible, and the proposal generator repeatedly chose `mixture_of_experts` for child index 1. This produced a long depth chain instead of a broad comparison across distinct blueprint families.

## Search Shape

| Level | Children | Best Val | Mean Val |
|---|---|---|---|
| 4 | 24 | 0.6439 | 0.6196 |
| 5 | 3 | 0.6313 | 0.5107 |

| Category | Children | Best Val | Mean Val |
|---|---|---|---|
| fusion | 24 | 0.6439 | 0.6196 |
| foundation_model_fusion | 2 | 0.6313 | 0.5912 |
| biological_prior | 1 | 0.3498 | 0.3498 |

Level 4/5 coverage looks strong by count, but the content is less strong: 22 of the Level 4 nodes are repeated implemented MoE descendants, and three Level 5 nodes are missing-artifact fallbacks.

## Why The Best Child Did Not Beat The Root

1. The root was already strong. `root_concat_gated_mlp` starts at 0.6499 validation Macro-F1, above all other root families and very close to the best child family's ceiling.

2. True biological priors were absent. ESM2, AIDO, and pathway nodes did not use real external artifacts. Without those artifacts, their implementations became controlled fallbacks, not paper-equivalent foundation/graph modules.

3. The proposal distribution collapsed. The search spent most of the post-fallback budget on a repeated `mixture_of_experts` lineage. That lineage plateaued around 0.63-0.64 and did not create qualitatively new information.

4. Breadth was too limited after the fallback phase. Several planned families were tried once, but the search did not force enough breadth across `gated_multimodal_fusion`, `film_conditioned_residual`, `target_factor_router`, `class_balanced_deg_classifier`, or other non-MoE blueprints.

5. Training budget per node was small. Four epochs is appropriate for a harness validation run, but it may under-rank deeper or attention-based children. However, the large drop in pathway/cross-attention nodes is too big to explain by epochs alone.

## What To Change Next

Recommended next run: do not simply increase the node count. First change the search controls so the next 30-60 nodes are more informative.

1. Add blueprint diversity constraints.
   Require a minimum number of distinct strategies before a strategy can be repeated more than 3-5 times. This directly addresses the MoE chain collapse.

2. Add parent-depth and same-strategy penalties to PUCT.
   Penalize selecting a parent if the path already contains repeated identical strategies. This keeps MCTS from walking a single lineage when the reward is merely stable rather than improving.

3. Force a breadth pass after planned fallbacks.
   Try `film_conditioned_residual`, `target_factor_router`, `class_balanced_deg_classifier`, and `gated_multimodal_fusion` from the top 2-3 roots before allowing another long MoE chain.

4. Add at least one real artifact before testing Level 5 claims.
   The highest-value artifact is likely an aligned gene/protein embedding table or STRING/pathway graph mapped to the target genes. Without that, Level 5 remains mostly a fallback test.

5. Re-run top 3 children with a larger epoch budget.
   Before scaling to 100+ nodes, retrain the best child, best MoE descendant, and best planned-fallback child with a higher epoch cap and multiple seeds to estimate variance.

## Bottom Line

This run is a successful systems validation and a negative model-discovery result. The harness can execute paper-style program-node search with PUCT, planned blueprints, on-demand implementation, and clean artifact recording. The next bottleneck is not basic automation; it is search diversity and real biological inputs.

The most important next engineering change is to prevent repeated-strategy lineage collapse. The most important scientific change is to provide at least one real biological prior artifact so Level 5 nodes are no longer fallbacks.
