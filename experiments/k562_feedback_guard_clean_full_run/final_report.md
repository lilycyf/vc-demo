# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `k562_feedback_guard_clean_full_run`
- Trained nodes: 24
- Failed nodes: 0
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 339
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 33
- Structural replicate nodes: 2
- Strict artifact rule: missing official artifacts must acquire/block, not fallback

## Artifact Alignment

- Present artifacts: 8
- Missing artifacts: esm2_gene_embedding_h5ad, esm2_k562_target_manifest, aido_gene_or_cell_embeddings, scfoundation_cell_embeddings, official_aido_cell_100m_model_dir, official_string_gnn_model_dir, regulatory_network_artifact, single_cell_foundation_model_artifact
- Reconstructed compatibility artifacts: none
- STRING_GNN compatibility caveat: reconstructed artifacts must not be claimed as numerically equivalent to unpublished original checkpoints.

## Public Static Tree Alignment

- Family groups mapped: 4
- The public static scaffold is benchmark/reference only; it is not counted as local search output.

| Public family | Node count | Local equivalent blueprints |
|---|---:|---|
| aido_lora_adapter | 6 | official_aido_lora_adapter |
| aido_string_fusion | 68 | official_aido_string_fusion |
| official_training_or_head_variant | 1 | official_target_gene_head |
| string_gnn_attention | 79 | official_string_gnn_attention |

## Scientific Search Coverage

| Family | Count |
|---|---:|
| AIDO_STRING_bilinear | 2 |
| AIDO_STRING_concat | 3 |
| AIDO_STRING_cross_attention | 5 |
| AIDO_STRING_fusion | 11 |
| AIDO_STRING_gated | 3 |
| AIDO_adapter | 9 |
| AIDO_cached_embedding | 3 |
| AIDO_full_finetune | 4 |
| AIDO_selective_finetune | 4 |
| Reactome_pathway_pooling | 5 |
| STRING_GNN_attention | 10 |
| STRING_GNN_frozen_cached | 3 |
| STRING_GNN_full_finetune | 3 |
| STRING_laplacian_prior | 3 |
| STRING_neighborhood_attention | 5 |
| checkpoint_ensemble_or_SWA | 2 |
| class_weighted_CE | 3 |
| focal_loss | 4 |
| gene_dropout_augmentation | 3 |
| layerwise_lr_decay | 1 |
| multimodal_MoE | 3 |
| official_deg_imbalance | 5 |
| public_static_tree_family | 3 |
| public_vcharness_best_path | 4 |
| public_vcharness_best_path_native_exact | 1 |
| regulatory_network_prior | 4 |
| scFoundation_selective_finetune | 3 |
| scGPT_or_single_cell_encoder | 3 |
| target_bilinear_head | 4 |
| target_gene_aware_head | 10 |
| target_graph_conditioned_head | 5 |
| target_low_rank_head | 4 |
| temperature_calibration | 3 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| backpropagation | 2 |
| expansion | 23 |
| global_queue_selected | 23 |
| implementation_loop_result | 21 |
| implementation_loop_start | 21 |
| implementation_skipped | 1 |
| manual_train_pending_backpropagation | 20 |
| pending_implementation | 21 |
| proposal_pool_generated | 23 |
| proposal_pruned | 73 |
| proposal_queued | 65 |
| realtime_implementation_required | 21 |
| selected_for_training | 2 |
| selection | 23 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4337 | 0.4891 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4935 | 0.5434 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_gene_head | structural_variant | 0.4821 | 0.5194 |
| `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | `official_k562_root_aido_embedding_mlp` | native_train | official_class_imbalance_training | structural_variant | 0.4055 | 0.4240 |
| `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_pathway_pooling_reactome | structural_variant | 0.4929 | 0.5407 |
| `official_k562_root_aido_embedding_mlp_p1_official_string_neighborhood_attention_a25d8fa1` | `official_k562_root_aido_embedding_mlp` |  | official_string_neighborhood_attention | structural_variant | 0.4428 | 0.4967 |
| `official_k562_root_aido_embedding_mlp_p3_official_target_graph_conditioned_head_7d8e76f1` | `official_k562_root_aido_embedding_mlp` |  | official_target_graph_conditioned_head | structural_variant | 0.4469 | 0.4880 |
| `official_k562_root_aido_embedding_mlp_p6_official_target_low_rank_head_f28a1bc1` | `official_k562_root_aido_embedding_mlp` |  | official_target_low_rank_head | structural_variant | 0.4432 | 0.4874 |
| `official_k562_root_aido_embedding_mlp_p1_official_target_bilinear_head_217a17b9` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_target_bilinear_head | structural_variant | 0.4095 | 0.4322 |
| `official_k562_root_aido_embedding_mlp_p2_official_focal_loss_training_37672209` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_focal_loss_training | structural_variant | 0.4075 | 0.4231 |
| `official_k562_root_aido_gnn_embedding_mlp_p5_official_weighted_ce_training_ea636995` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_weighted_ce_training | structural_variant | 0.4866 | 0.5312 |
| `official_k562_root_aido_embedding_mlp_p10_official_gene_dropout_augmentation_ed174d61` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_gene_dropout_augmentation | structural_variant | 0.4206 | 0.4376 |
| `official_k562_root_aido_embedding_mlp_p11_official_temperature_calibrated_head_ddceef70` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_temperature_calibrated_head | structural_variant | 0.3954 | 0.4148 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_string_laplacian_smoothing_dbe5f678` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_string_laplacian_smoothing | structural_variant | 0.4870 | 0.5261 |
| `official_k562_root_aido_embedding_mlp_p9_official_multimodal_mixture_of_experts_4c5d0049` | `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` |  | official_multimodal_mixture_of_experts | structural_variant | 0.4191 | 0.4361 |
| `official_k562_root_aido_gnn_embedding_mlp_p3_official_layerwise_lr_schedule_30ef5f9a` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_layerwise_lr_schedule | structural_variant | 0.4800 | 0.5150 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_swa_or_checkpoint_ensemble_afa3a39a` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_swa_or_checkpoint_ensemble | structural_variant | 0.4902 | 0.5334 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_68ad862b` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_target_gene_head | replicate | 0.4795 | 0.5362 |
| `official_k562_root_aido_gnn_embedding_mlp_p9_official_class_imbalance_training_9c56100e` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | native_train | official_class_imbalance_training | structural_variant | 0.4783 | 0.5144 |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_neighborhood_attention_62af14f5` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_string_neighborhood_attention | structural_variant | 0.4841 | 0.5353 |
| `official_k562_root_aido_gnn_embedding_mlp_p11_official_pathway_pooling_reactome_6cb04fc4` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_pathway_pooling_reactome | replicate | 0.4718 | 0.5544 |
| `official_k562_root_aido_gnn_embedding_mlp_p10_official_target_graph_conditioned_head_cc233d73` | `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` |  | official_target_graph_conditioned_head | structural_variant | 0.4935 | 0.5414 |
| `official_k562_root_aido_gnn_embedding_mlp_p8_official_target_bilinear_head_495e575b` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` |  | official_target_bilinear_head | structural_variant | 0.4879 | 0.5310 |
| `official_k562_root_aido_gnn_embedding_mlp_p6_official_target_low_rank_head_4ca91b75` | `official_k562_root_aido_gnn_embedding_mlp_p4_official_string_laplacian_smoothing_dbe5f678` |  | official_target_low_rank_head | structural_variant | 0.4829 | 0.5302 |

## Best Node

- Best validation node: `official_k562_root_aido_gnn_embedding_mlp`
- Validation Macro-F1: 0.4935
- Test Macro-F1: 0.5434

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Formal implementation rule: compact/proxy native stand-ins are forbidden; nodes must be exact public static execution or full artifact-backed implementations.
- Remaining gap: any historical compact/proxy nodes are excluded from paper-level conclusions and must be rerun after full implementation.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.

## Framework Feedback and Guard Audit

## Outcome
- Best root: `official_k562_root_aido_gnn_embedding_mlp` val=0.493532, test=0.543417
- Best generated child: `official_k562_root_aido_gnn_embedding_mlp_p10_official_target_graph_conditioned_head_cc233d73` val=0.493524, test=0.541396
- Delta child vs root: -0.00000712
- Delta child vs target 0.50: -0.006476
- Root-beating achieved: `False`
- Target achieved: `False`

## Counts
- generated_proposals: 138
- trained_selected_rollouts: 22
- pruned: 73
- skipped: 1
- blocked: 0
- failed: 0
- pending: 0
- queued_candidates: 42

## Top Generated Children
- `official_k562_root_aido_gnn_embedding_mlp_p10_official_target_graph_conditioned_head_cc233d73` (official_target_graph_conditioned_head): val=0.493524, test=0.541396
- `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` (official_pathway_pooling_reactome): val=0.492855, test=0.540664
- `official_k562_root_aido_gnn_embedding_mlp_p1_official_swa_or_checkpoint_ensemble_afa3a39a` (official_swa_or_checkpoint_ensemble): val=0.490240, test=0.533419
- `official_k562_root_aido_gnn_embedding_mlp_p8_official_target_bilinear_head_495e575b` (official_target_bilinear_head): val=0.487869, test=0.531025
- `official_k562_root_aido_gnn_embedding_mlp_p4_official_string_laplacian_smoothing_dbe5f678` (official_string_laplacian_smoothing): val=0.486986, test=0.526074
- `official_k562_root_aido_gnn_embedding_mlp_p5_official_weighted_ce_training_ea636995` (official_weighted_ce_training): val=0.486595, test=0.531215
- `official_k562_root_aido_gnn_embedding_mlp_p8_official_string_neighborhood_attention_62af14f5` (official_string_neighborhood_attention): val=0.484149, test=0.535274
- `official_k562_root_aido_gnn_embedding_mlp_p6_official_target_low_rank_head_4ca91b75` (official_target_low_rank_head): val=0.482881, test=0.530181
- `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` (official_target_gene_head): val=0.482102, test=0.519384
- `official_k562_root_aido_gnn_embedding_mlp_p3_official_layerwise_lr_schedule_30ef5f9a` (official_layerwise_lr_schedule): val=0.479958, test=0.515039

## Strict Policy Audit
- fallback_count: 0
- proxy_count: 0
- backprop_nontrained_count: 0
- backend_anomaly_count: 0
- acquisition_queue_count: 0

## Implementation/Artifact Blockers
- `official_k562_root_aido_embedding_mlp_p12_official_public_static_node_family_wrapper_2d1d6507`: incomplete_runtime_artifact_contract - implementation-infeasible strict public wrapper: VCHarness public node code is present, but exact execution depends on undeclared runtime model directories /home/Models/AIDO.Cell-100M and /home/Models/STRING_GNN, and /home/Models is absent on this pod. No source-backed, shape/vocabulary/provenance-verified acquisition was available during this run, so no fallback/proxy model was trained.

## Framework Feedback
- root_dominance: best generated child did not beat best root
- unstable_positive_family:target_aware: mean_delta=0.0019, std=0.0079, win_rate=0.625
- discouraged_family:imbalance_training: repeated negative delta
- target_gap: best child is 0.0065 below target validation Macro-F1

## Guard Exercise
- Existing-run guard: respected: initial invocation created a fresh run dir; all subsequent existing-run invocations used --resume. Destructive no-resume rerun was not attempted.
- train_pending trace/manifest guard: exercised: train_pending wrote metrics back into tree/search_summary and agent_decision_trace includes trained/backprop events for implementation-loop nodes.
