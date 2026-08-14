# AIVC HELF Artifact Acquisition Summary

## Present Source-Backed Artifacts

| artifact file | present | bytes |
|---|---:|---:|
| data/artifacts/helf/reactome_pathway_membership.npz | true | 19862 |
| data/artifacts/helf/reactome_pathway_membership.npz.manifest.json | true | 3389 |
| data/artifacts/helf/string_gene_graph.tsv | true | 229360 |
| data/artifacts/helf/string_gene_graph.tsv.manifest.json | true | 810 |
| data/artifacts/helf/string_gene_graph_features.npz | true | 120952 |

Reactome pathway membership and STRING target-gene graph features were present on the RunPod volume before this run and were used only when aligned artifact files existed. The harness did not use graph files as model checkpoints and did not create proxy or fallback foundation artifacts.

## Blocked Acquisition Items

| node | strategy | missing artifact | resolution |
|---|---|---|---|
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p22_foundation_scgpt_cell_encoder | foundation_scgpt_cell_encoder | scgpt_whole_human_checkpoint | block until source, shape, vocabulary/order, and provenance can be verified |
| aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_p30_foundation_scgpt_cell_encoder | foundation_scgpt_cell_encoder | scgpt_whole_human_checkpoint | block until source, shape, vocabulary/order, and provenance can be verified |
| aivc_helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing_p26_foundation_scgpt_cell_encoder | foundation_scgpt_cell_encoder | scgpt_whole_human_checkpoint | block until source, shape, vocabulary/order, and provenance can be verified |
| aivc_helf_perturb_root_residual_mlp_p2_foundation_scgpt_cell_encoder | foundation_scgpt_cell_encoder | scgpt_whole_human_checkpoint | block until source, shape, vocabulary/order, and provenance can be verified |
| aivc_helf_perturb_root_gated_mlp_p9_foundation_pathway_pooling_encoder_p38_foundation_scgpt_cell_encoder | foundation_scgpt_cell_encoder | scgpt_whole_human_checkpoint | block until source, shape, vocabulary/order, and provenance can be verified |
| aivc_helf_perturb_root_gated_mlp_p9_foundation_pathway_pooling_encoder_p34_foundation_scgpt_cell_encoder | foundation_scgpt_cell_encoder | scgpt_whole_human_checkpoint | block until source, shape, vocabulary/order, and provenance can be verified |
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p58_foundation_scgpt_cell_encoder | foundation_scgpt_cell_encoder | scgpt_whole_human_checkpoint | block until source, shape, vocabulary/order, and provenance can be verified |
| aivc_helf_perturb_root_mlp_p5_foundation_graph_laplacian_head_p24_weighted_ce_p62_foundation_scgpt_cell_encoder | foundation_scgpt_cell_encoder | scgpt_whole_human_checkpoint | block until source, shape, vocabulary/order, and provenance can be verified |

## Blocker Counts

- scgpt_whole_human_checkpoint: 8

## Policy Result

Missing scGPT whole-human checkpoint proposals were strict-blocked because source, shape, vocabulary/order, and provenance validation were required. Search continued with other queued candidates. No fallback or proxy model was trained.
