# K562 Paper-Level Program-Node Search Final Conclusion

## Commands And Setup

- Branch: `k562-paper-level-search-run`.
- Dataset/split: existing K562 `real_npz` data under `data/cell_lines`; train/validation/test split was not modified.
- Metric: validation Macro-F1 for search reward; validation and test Macro-F1 reported.
- Initial command: `python -m vc_demo.harness.program_run --experiment k562_program_node_agent_search --root-configs configs/k562_roots/*.json --run-dir experiments/k562_program_node_agent_search --budget-nodes 30 --max-epochs 4 --max-children 3 --stop-no-improve 12 --exploration 0.7 --selection-policy puct --seed 11 --allow-planned-blueprints --max-pending-implementations 2 --reset`.
- Continuation: pending planned blueprints were implemented node-locally, trained with `python -m vc_demo.harness.train_pending`, then the search was resumed from `tree.json` using PUCT.
- Harness change: `program_run` now resumes from an existing tree when run without `--reset`, and program node names use a short parent digest to avoid path-length failures.

## Final Counts

- Trained nodes: 34.
- Failed nodes: 0.
- Pending nodes: 0.
- Root families trained: 7.
- Planned blueprint nodes implemented on demand: 5.
- Level 4/5 trained children: 27.
- Approximate measured GPU wall-time lower bound from node metrics: 13.1 minutes, about 0.217 GPU-hours.

## Best Result

- Best root: `root_concat_gated_mlp` val Macro-F1 0.6499, test Macro-F1 0.6127.
- Best overall: `root_concat_gated_mlp` val Macro-F1 0.6499, test Macro-F1 0.6127.
- Improvement over best root: 0.0000 validation Macro-F1.
- Best path: `root_concat_gated_mlp`.

The best overall node was still the strongest root baseline. The program-node search satisfied the paper-level execution targets, but did not discover a child that improved validation Macro-F1 over `root_concat_gated_mlp`.

## Blueprint Coverage

- `aido_embedding_fusion`: 1, status=planned, level=5, category=foundation_model_fusion
- `cross_attention_gene_perturbation`: 1, status=planned, level=4, category=fusion
- `esm2_gene_projection`: 1, status=planned, level=5, category=foundation_model_fusion
- `gated_multimodal_fusion`: 1, status=planned, level=4, category=fusion
- `mixture_of_experts`: 22, status=implemented, level=4, category=fusion
- `pathway_pooling_encoder`: 1, status=planned, level=5, category=biological_prior
- `root`: 7

Level counts among trained child nodes:
- Level 4: 24
- Level 5: 3

Planned blueprints implemented on demand:
- `esm2_gene_projection` as `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460`: val 0.5510, test 0.5189, level 5
- `aido_embedding_fusion` as `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53`: val 0.6313, test 0.5749, level 5
- `pathway_pooling_encoder` as `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09`: val 0.3498, test 0.3477, level 5
- `cross_attention_gene_perturbation` as `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d`: val 0.3158, test 0.3158, level 4
- `gated_multimodal_fusion` as `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97`: val 0.6439, test 0.5841, level 4

## Missing Artifacts And Fallbacks

- `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460`: `missing_artifact = "protein_sequences_or_esm2_embeddings"`
- `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460`: `fallback = "frozen_zero_foundation_prior_plus_tabular_encoder"`
- `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53`: `missing_artifact = "aido_embeddings"`
- `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53`: `fallback = "inactive_frozen_aido_branch_with_gated_tabular_fusion"`
- `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09`: `missing_artifact = "pathway_memberships"`
- `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09`: `fallback = "learnable_pathway_slots_without_external_membership"`
- `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d`: `missing_artifact = "none_learnable_gene_tokens_used"`
- `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d`: `fallback = "learnable_target_token_table"`
- `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97`: `inactive_modalities = "external_prior_embeddings"`
- `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97`: `fallback = "two_view_tabular_gated_fusion"`

Foundation-model and graph/pathway priors were not faked. ESM2, AIDO, and pathway nodes record missing artifacts and use explicit compact fallbacks over the existing tabular features. Cross-attention and gated multimodal fusion use learnable target/context components allowed by their requests.

## Search Behavior

- Parent selection used the harness MCTS layer with `--selection-policy puct`; proposals preserve `mcts_selected_parent`, `mcts_selection_policy`, and candidate score records.
- The search explored Level 5 foundation/prior requests first, then resumed with implemented program-node blueprints to reach the minimum trained-node target.
- The strongest child was `root_concat_residual_mlp_p1_gated_multimodal_fusion_a52a6f97` at val 0.6439 and test 0.5841, close to but below the best root.
- The repeated `mixture_of_experts` chain was stable but plateaued around 0.62-0.64 validation Macro-F1, below the gated concat root baseline.

## Root Baselines

- `root_concat_gated_mlp`: val 0.6499, test 0.6127
- `root_concat_mlp`: val 0.6403, test 0.5818
- `root_concat_residual_mlp`: val 0.6283, test 0.5798
- `root_onehot_mlp`: val 0.6150, test 0.5594
- `root_concat_regularized_mlp`: val 0.6107, test 0.5753
- `root_delta_mlp`: val 0.6074, test 0.5711
- `root_concat_low_rank_mlp`: val 0.5878, test 0.5460

## Limitations Versus The Paper

- This is one cell line, not a multi-cell-line benchmark.
- The run reached 34 trained nodes, which meets the small serious-run target but is below a full 100-200 node single-cell-line paper-scale search.
- Foundation and biological-prior artifacts were absent; the implemented nodes explicitly used fallbacks rather than real ESM2/AIDO/pathway resources.
- The best child did not exceed the best root, so this run validates the paper-level program-node loop more than it demonstrates model discovery superiority.

## Artifacts

- `experiments/k562_program_node_agent_search/search_summary.md`
- `experiments/k562_program_node_agent_search/final_conclusion.md`
- `experiments/k562_program_node_agent_search/tree.json`
- `experiments/k562_program_node_agent_search/failures.json`
- `experiments/k562_program_node_agent_search/implementation_queue.json`
- `experiments/k562_program_node_agent_search/programs/<node>/model.py` for on-demand implementations
