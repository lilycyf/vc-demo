# K562 Feedback Guard Clean Full Run Audit

Run dir: `experiments/k562_feedback_guard_clean_full_run`

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
