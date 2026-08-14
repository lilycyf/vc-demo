# AIVC HELF Root Dominance Audit

This audit checks whether selected search children improved over trained root baselines. The task is HELF 10 umol / 48 h heldout-drug DEG direction prediction only. Validation Macro-F1 is the reward; test Macro-F1 is report-only.

## Summary

- Best root: `aivc_helf_perturb_root_residual_mlp` with val Macro-F1 `0.429629` and test Macro-F1 `0.427547`.
- Best generated child: `aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p59_focal_loss` with val Macro-F1 `0.445516` and test Macro-F1 `0.437810`.
- Child minus root validation delta: `0.015887`.
- Child beats root: `true`. Target val Macro-F1 0.42 reached: `true`.

## Trained Roots

| node | strategy | status | val Macro-F1 | test Macro-F1 | type |
|---|---|---|---:|---:|---|
| aivc_helf_perturb_root_residual_mlp | root | trained | 0.429629 | 0.427547 | root |
| aivc_helf_perturb_root_mlp | root | trained | 0.421142 | 0.421560 | root |
| aivc_helf_perturb_root_gated_mlp | root | trained | 0.413969 | 0.414213 | root |
| aivc_helf_perturb_root_low_rank_mlp | root | trained | 0.411544 | 0.409309 | root |

## Top Generated Children

| node | strategy | status | val Macro-F1 | test Macro-F1 | type |
|---|---|---|---:|---:|---|
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p59_focal_loss | focal_loss | trained | 0.445516 | 0.437810 | lightweight_executable_transform |
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce | weighted_ce | trained | 0.439215 | 0.433807 | lightweight_executable_transform |
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p63_focal_loss | focal_loss | trained | 0.436341 | 0.433919 | lightweight_executable_transform |
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p60_dropout_low | dropout_low | trained | 0.433935 | 0.431093 | lightweight_executable_transform |
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p64_dropout_low | dropout_low | trained | 0.432765 | 0.431583 | lightweight_executable_transform |
| aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_p27_weighted_ce | weighted_ce | trained | 0.432180 | 0.443474 | lightweight_executable_transform |
| aivc_helf_perturb_root_gated_mlp_p9_foundation_pathway_pooling_encoder_p39_weighted_ce | weighted_ce | trained | 0.431744 | 0.430993 | lightweight_executable_transform |
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head | foundation_graph_laplacian_head | trained | 0.430958 | 0.435753 | foundation_artifact_blueprint |
| aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_p31_weighted_ce | weighted_ce | trained | 0.430849 | 0.438783 | lightweight_executable_transform |
| aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing | foundation_string_graph_message_passing | trained | 0.430623 | 0.430722 | foundation_artifact_blueprint |
| aivc_helf_perturb_root_gated_mlp_p9_foundation_pathway_pooling_encoder | foundation_pathway_pooling_encoder | trained | 0.428355 | 0.434417 | foundation_artifact_blueprint |
| aivc_helf_perturb_root_gated_mlp_p9_foundation_pathway_pooling_encoder_p35_weighted_ce | weighted_ce | trained | 0.427853 | 0.434516 | lightweight_executable_transform |

## Interpretation

The best generated child improved over the best root by following a parent lineage that had already incorporated graph artifact augmentation and weighted cross entropy, then adding focal loss. This validates the intended harness behavior: roots act as baselines, proposal pools are screened, pruned proposals are not trained, and only selected executable rollouts receive training and reward backpropagation.
