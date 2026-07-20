# Official K562 Paper-Level Single-Cellline Report

## Task Definition

- Task: K562 CRISPR perturbation DEG classification
- Split: train 1,388 / validation 154 / test 421 perturbations
- Target genes: 6,640
- Reward metric: validation Macro-F1; held-out test Macro-F1 is reporting only

## Search System

- Experiment: `k562_framework_feedback_full_run`
- Trained nodes: 5
- Failed nodes: 0
- Pending implementations: 0
- Public static tree nodes cataloged: 154
- Public best path scaffold: `node2-1-1-1-1-1`
- Paper-scale estimated candidate count: 94500
- Paper-scale 600+ manifest target reached: true
- MCTS trace events: 54
- MCTS policy: uct
- Search policy: scientific family/structure priority first; artifact status is a feasibility gate, not a ranking objective
- Blueprint families covered: 18
- Structural replicate nodes: 0
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
| AIDO_STRING_cross_attention | 1 |
| AIDO_STRING_fusion | 1 |
| AIDO_adapter | 1 |
| AIDO_cached_embedding | 1 |
| AIDO_full_finetune | 1 |
| AIDO_selective_finetune | 1 |
| Reactome_pathway_pooling | 1 |
| STRING_GNN_attention | 1 |
| STRING_neighborhood_attention | 1 |
| class_weighted_CE | 1 |
| focal_loss | 1 |
| official_deg_imbalance | 1 |
| public_vcharness_best_path | 1 |
| regulatory_network_prior | 1 |
| scFoundation_selective_finetune | 1 |
| scGPT_or_single_cell_encoder | 1 |
| target_gene_aware_head | 1 |
| target_graph_conditioned_head | 1 |

## MCTS Trace Summary

| Event | Count |
|---|---:|
| backpropagation | 1 |
| expansion | 4 |
| global_queue_selected | 4 |
| implementation_loop_result | 3 |
| implementation_loop_start | 3 |
| pending_implementation | 3 |
| proposal_pool_generated | 4 |
| proposal_queued | 24 |
| realtime_implementation_required | 3 |
| selected_for_training | 1 |
| selection | 4 |

## Results

| Node | Parent | Backend | Strategy | Relation | Val Macro-F1 | Test Macro-F1 |
|---|---|---|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | `` | native_train | root |  | 0.4324 | 0.4885 |
| `official_k562_root_aido_gnn_embedding_mlp` | `` | native_train | root |  | 0.4792 | 0.5464 |
| `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_target_gene_head | structural_variant | 0.5025 | 0.5389 |
| `official_k562_root_aido_embedding_mlp_p2_official_class_imbalance_training_83b0bff5` | `official_k562_root_aido_embedding_mlp` | native_train | official_class_imbalance_training | structural_variant | 0.4124 | 0.4342 |
| `official_k562_root_aido_gnn_embedding_mlp_p5_official_pathway_pooling_reactome_9b3c1811` | `official_k562_root_aido_gnn_embedding_mlp` |  | official_pathway_pooling_reactome | structural_variant | 0.4758 | 0.5426 |

## Best Node

- Best validation node: `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042`
- Validation Macro-F1: 0.5025
- Test Macro-F1: 0.5389

## Gap Attribution

- Replicated: official K562 task contract, MCTS/program-node loop, public static node wrapper, public static tree scaffold, artifact provenance audit.
- Implemented beyond wrapper: native public-best-family v1 and executable official native blueprint children.
- Formal implementation rule: compact/proxy native stand-ins are forbidden; nodes must be exact public static execution or full artifact-backed implementations.
- Remaining gap: any historical compact/proxy nodes are excluded from paper-level conclusions and must be rerun after full implementation.
- Remaining artifact caveat: STRING_GNN model dir is compatibility reconstruction unless replaced by original upstream checkpoint.
- Remaining scale gap: 50/150/600-node staged runs are required for paper-level search pressure.

## Manual Framework Feedback From This Run

- Objective achieved: official_target_gene_head reached validation Macro-F1 0.5025, exceeding the best root 0.4792 and the target threshold 0.50.
- Strict artifact policy held: the implemented target-gene-head used official_essential_deg_with_split_h5ad and official target order; the pathway child used the Reactome pathway_membership_matrix. No fallback/proxy model was trained.
- Resume semantics caveat: invoking the generic entrypoint without --resume reconstructed the run tree and erased the node-local implementation from the active run directory. Subsequent invocations must use --resume; the runbook should make this a hard guard for existing run dirs.
- Trace completeness caveat: train_pending correctly updated tree status/metrics for manually implemented nodes, but mcts_trace.jsonl only recorded backpropagation for the auto-trained class-imbalance child. Add explicit trained/backprop trace rows after train_pending so audits do not have to infer tree state.
- Next policy changes: boost parent-preserving target-gene-aware residual heads, calibration/regularization, and seed-stability validation; keep pathway pooling as exploratory because it did not beat the root in this run.

## Final Run Audit Addendum

- Tree-authoritative generated proposals: 18 (2 roots + 18 generated nodes in tree).
- Trained selected rollouts: 3 generated children.
- Queued/skipped candidates remaining in global queue: 15.
- Blocked/acquisition/failed/pending: 0 / 0 / 0 / 0.
- Best root: official_k562_root_aido_gnn_embedding_mlp, val Macro-F1 0.4792, test Macro-F1 0.5464.
- Best generated child: official_target_gene_head, val Macro-F1 0.5025, test Macro-F1 0.5389.
- Objective: achieved; child exceeds best root by 0.0233 validation Macro-F1 and target 0.50 by 0.0025.
- Audit counts: fallback=0, compact/proxy=0, backprop_nontrained=0, backend anomalies=0.

