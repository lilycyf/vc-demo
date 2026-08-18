# AIVC HELF Best-Child Multiseed Ablation v1

## Executive conclusion

This ablation validates that the previously discovered child is a stable improvement over the best root baseline across seeds, not a one-seed accident. The full child reached mean validation Macro-F1 0.441935 versus the root mean 0.428366, a +0.013569 validation gain, and it beat the root on every tested seed.

However, the component attribution is nuanced: the dense matched-capacity no-artifact control reached mean validation Macro-F1 0.445881, which is +0.003946 above the full graph/focal child. That means the harness discovery is stable, but the observed gain should not be claimed as uniquely caused by the STRING graph artifact. The strongest interpretation is that the search found a useful higher-capacity/loss-shaped child, while the current graph residual contributes a smaller positive increment over the no-graph focal ablation.

## Experimental setup

- Cell line/task: HELF heldout-drug DEG direction classification.
- Previous run: `experiments/aivc_helf_perturb_harness_search_v1`.
- Best child: `aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p59_focal_loss`.
- Seeds: 3, 7, 11, 17, 23.
- Epochs per run: 8.
- Reward metric: validation Macro-F1. Test Macro-F1 is report-only.
- Artifact used by full graph child: `data/artifacts/helf/string_gene_graph_features.npz`, key `target_gene_embeddings`.
- Target validation Macro-F1: 0.42.

## Variants

| Variant | Purpose |
| --- | --- |
| `best_root_residual_mlp` | Best root baseline from previous search |
| `full_best_child_graph_focal` | Full discovered child: parent dense path plus STRING graph residual and focal loss |
| `ablate_no_graph_keep_focal` | Ablation without graph_laplacian_head / STRING artifact, keeping focal loss |
| `ablate_graph_no_loss_tricks` | Ablation without weighted CE / focal loss, keeping STRING graph residual |
| `ablate_no_graph_no_loss_tricks` | Ablation without graph artifact and without weighted/focal loss |
| `dense_capacity_no_artifact_focal` | Dense matched-capacity child without biological artifacts, keeping focal loss |

The requested graph/foundation-only versus dense+graph residual comparison is recorded as unsupported by the current model library. No graph-only proxy was created, because that would violate the no-proxy/fallback rule.

## Aggregate results

| Variant | Val Macro-F1 mean | Val std | Test Macro-F1 mean | Test std | Val delta vs root |
| --- | ---: | ---: | ---: | ---: | ---: |
| Best root residual MLP | 0.428366 | 0.002073 | 0.427376 | 0.001750 | +0.000000 |
| Full discovered child | 0.441935 | 0.001242 | 0.436781 | 0.001457 | +0.013569 |
| No graph, focal kept | 0.437925 | 0.002080 | 0.430691 | 0.002310 | +0.009559 |
| Graph kept, no focal/weighted CE | 0.431416 | 0.003446 | 0.432018 | 0.005229 | +0.003050 |
| No graph, no loss tricks | 0.428366 | 0.002073 | 0.427376 | 0.001750 | +0.000000 |
| Dense matched-capacity, no artifact | 0.445881 | 0.004571 | 0.446825 | 0.005211 | +0.017516 |

## Per-seed root versus full child

| Seed | Root val | Child val | Delta val | Root test | Child test | Delta test |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 0.430677 | 0.442476 | +0.011800 | 0.425438 | 0.438091 | +0.012653 |
| 7 | 0.428086 | 0.442911 | +0.014826 | 0.429260 | 0.438551 | +0.009291 |
| 11 | 0.426292 | 0.439785 | +0.013493 | 0.428930 | 0.435950 | +0.007020 |
| 17 | 0.430319 | 0.442478 | +0.012159 | 0.427463 | 0.435196 | +0.007733 |
| 23 | 0.426456 | 0.442024 | +0.015568 | 0.425789 | 0.436116 | +0.010327 |

## Component attribution

| Question | Estimate | Interpretation |
| --- | ---: | --- |
| Full child minus best root, validation | +0.013569 | Stable generated-child gain over the previous best root. |
| Full child minus best root, test | +0.009405 | Held-out report-only gain direction matches validation. |
| Graph residual contribution estimate | +0.004010 | Full graph+focal versus no-graph focal. Positive, but modest. |
| Loss contribution estimate | +0.010519 | Full graph+focal versus graph without focal/weighted CE. This is the largest measured component gain. |
| Dense capacity control minus full child, validation | +0.003946 | Dense matched-capacity no-artifact control outperformed the graph child, so artifact-specific claims need caution. |
| Full child minus target 0.42 | +0.021935 | The discovered child remains above the target on average. |

## Guardrails

| Guardrail | Count/status |
| --- | ---: |
| fallback_count | 0 |
| proxy_count | 0 |
| backprop_nontrained_count | 0 |
| backend_anomaly_count | 0 |
| pruned_node_training_count | 0 |
| failed | 0 |
| pending | 0 |
| blocked | 0 |
| required STRING graph artifact present | True |
| graph-only proxy created | False |
| test-guided selection | False |

## Final judgment

The previous best generated child is stable across the five-seed validation: it beats the best root on every seed and exceeds the target validation Macro-F1 on average.

The biological artifact contribution is present but not decisive in this ablation. The dense matched-capacity no-artifact focal control is the strongest variant in this run, so the next harness policy should test whether the graph residual is underpowered, whether the artifact feature needs a better fusion module, or whether the improvement is mainly from capacity and focal loss rather than the STRING-derived signal.

No fallback, proxy artifact, pruned-node training, non-trained backpropagation, backend anomaly, or test-guided selection was used.
