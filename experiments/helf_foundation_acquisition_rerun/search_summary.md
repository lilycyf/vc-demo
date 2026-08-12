# HELF Perturbation Foundation Harness Rerun

## Executive Summary

- Run dir: `experiments/helf_foundation_acquisition_rerun`
- Task: `HELF_PERTURB_DEG` h5ad-derived drug perturbation DEG label prediction
- Reward: validation Macro-F1; test Macro-F1 is report-only.
- Stop reason: `trained-node budget exhausted (24/24)`
- Objective target val Macro-F1 >= 0.36: `pass`
- Best lightweight root: `root_residual_mlp.json` val `0.422175` / test `0.420741`
- Best generated child: `temperature_calibration` val `0.414177` / test `0.414133`; delta vs best root `-0.007998`
- Best foundation-artifact child: `helf_perturb_root_mlp_p13_foundation_pathway_pooling_encoder` val `0.395850` / test `0.387946`; delta vs best root `-0.026325`

## Counts

| Metric | Count |
|---|---:|
| generated_proposals | 96 |
| trained_selected_rollouts | 24 |
| pruned_not_selected | 72 |
| skipped | 0 |
| requires_artifact_acquisition | 0 |
| failed | 0 |
| fallback_count | 0 |
| proxy_count | 0 |
| backprop_nontrained_count | 0 |

Tree status counts: `{"pruned_not_selected": 72, "trained": 28}`

## What Was Done

- Prepared/validated the existing HELF real NPZ task and fixed the trainer to honor either `data` or `dataset` config keys, so HELF configs no longer fall back to synthetic defaults.
- Generated proposal pools of size 4 under the foundation-aware search space, then trained only selected rollouts. Unselected proposals were recorded as `pruned_not_selected`.
- Acquired source-backed Reactome pathway membership from the official Reactome GMT download and aligned it to the fixed HELF target-gene order.
- Acquired source-backed STRING target graph from the official STRING network API and built graph-derived target embeddings aligned to the HELF target-gene order.
- Materialized Reactome/STRING selected blueprints into artifact-backed target-aware bilinear heads; no compact/proxy/fallback foundation substitutes were used.

## Foundation Artifact Children

| Node | Strategy | Required artifact | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---:|---:|
| `helf_perturb_root_mlp_p13_foundation_pathway_pooling_encoder` | `foundation_pathway_pooling_encoder` | `reactome_pathway_membership` | 0.395850 | 0.387946 |
| `helf_perturb_root_low_rank_mlp_p6_foundation_pathway_pooling_encoder` | `foundation_pathway_pooling_encoder` | `reactome_pathway_membership` | 0.394039 | 0.385269 |
| `helf_perturb_root_low_rank_mlp_p9_foundation_pathway_pooling_encoder` | `foundation_pathway_pooling_encoder` | `reactome_pathway_membership` | 0.390909 | 0.384648 |
| `helf_perturb_root_residual_mlp_p1_foundation_string_graph_message_passing` | `foundation_string_graph_message_passing` | `string_gene_graph` | 0.338102 | 0.321997 |
| `helf_perturb_root_low_rank_mlp_p5_foundation_graph_laplacian_head` | `foundation_graph_laplacian_head` | `string_gene_graph` | 0.323610 | 0.307139 |
| `helf_perturb_root_residual_mlp_p2_foundation_graph_laplacian_head` | `foundation_graph_laplacian_head` | `string_gene_graph` | 0.319005 | 0.311389 |

## Top Lightweight Children

| Node | Strategy | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| `helf_perturb_root_low_rank_mlp_p12_feature_dropout_p67_temperature_calibration` | `temperature_calibration` | 0.414177 | 0.414133 |
| `helf_perturb_root_low_rank_mlp_p8_feature_dropout_p63_temperature_calibration` | `temperature_calibration` | 0.413853 | 0.416318 |
| `helf_perturb_root_low_rank_mlp_p7_low_rank_head_p39_temperature_calibration` | `temperature_calibration` | 0.413199 | 0.411428 |
| `helf_perturb_root_low_rank_mlp_p12_feature_dropout` | `feature_dropout` | 0.412731 | 0.412413 |
| `helf_perturb_root_low_rank_mlp_p7_low_rank_head_p43_temperature_calibration` | `temperature_calibration` | 0.412558 | 0.414304 |
| `helf_perturb_root_low_rank_mlp_p7_low_rank_head` | `low_rank_head` | 0.411570 | 0.411050 |
| `helf_perturb_root_gated_mlp_p27_low_rank_head_p59_temperature_calibration` | `temperature_calibration` | 0.411192 | 0.415306 |
| `helf_perturb_root_gated_mlp_p27_low_rank_head` | `low_rank_head` | 0.411124 | 0.407072 |

## Artifact Audit

- Present artifacts in registry audit: `['helf_perturb_deg_npz', 'helf_source_h5ad', 'reactome_pathway_membership', 'string_gene_graph']`
- Missing but not selected/trained in final run: `['chemical_encoder_checkpoint_or_drug_fingerprints', 'esm2_gene_or_protein_embeddings', 'geneformer_checkpoint', 'regulatory_network_prior', 'scfoundation_checkpoint_or_service_output', 'scgpt_whole_human_checkpoint', 'uce_checkpoint']`
- Selected missing-artifact blockers in final run: none.
- Reactome provenance: official current Reactome GMT zip; target coverage 333/512.
- STRING provenance: official STRING network API, species 9606, required_score=400; target coverage 447/512, 2229 deduplicated edges.

## Search Semantics Audit

- `proposal_pool_generated`: `24`
- `selected_for_training`: `24`
- `proposal_pruned`: `72`
- `trained_and_backpropagated`: `24`
- Non-trained backprop nodes: `[]`
- Only trained nodes received reward backpropagation.
- No fallback/proxy/compact substitute was used for missing foundation artifacts.

## Conclusion

The HELF foundation-artifact harness rerun passes the requested demo target: it generated 96 proposals, trained 24 selected rollouts, trained real Reactome and STRING foundation-artifact children, exceeded the 0.36 validation Macro-F1 target, and preserved strict no-fallback semantics. The best generated child did not beat the best root in this run; the result is therefore a successful harness/acquisition validation, not a new best scientific model.
