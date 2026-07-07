# K562 Paper-Aligned UCT Program-Node Search Final Conclusion

## Setup

- Branch: `k562-paper-aligned-uct-run`.
- Research question: can VCHarness-style Codex agent + MCTS program-node search improve K562 CRISPR perturbation differential-expression label prediction over the best root baseline?
- Dataset/split: existing K562 `real_npz` data in `data/cell_lines`; `data/raw`, `data/cell_lines`, split semantics, and metric semantics were not modified.
- Reward/metric: validation Macro-F1 for search reward; validation and test Macro-F1 reported.
- Paper-aligned policy: UCT, exploration `sqrt(2)=1.4142135623730951`; PUCT was not used.
- Formal command: `python -m vc_demo.harness.program_run --experiment k562_program_node_agent_search --root-configs configs/k562_roots/*.json --run-dir experiments/k562_program_node_agent_search --budget-nodes 30 --max-epochs 4 --max-children 3 --stop-no-improve 12 --exploration 1.4142135623730951 --selection-policy uct --seed 11 --allow-planned-blueprints --max-pending-implementations 2 --reset`.
- Continuation: selected planned blueprints were implemented only as node-local `model.py`, trained with `train_pending.py`, then the search continued with UCT.

## Final Counts

- Trained nodes: 30.
- Root baselines: 7.
- Planned blueprints implemented on demand: 6.
- Level 4/5 trained children: 8.
- Failed nodes: 0.
- Pending nodes: 0.
- GPU wall-time lower-bound estimate from node metric mtimes: 7.1 minutes / 0.118 GPU-hours.

## Best Result

- Best root: `root_concat_gated_mlp` val Macro-F1 0.6595, test Macro-F1 0.6149.
- Best overall: `root_concat_gated_mlp` val Macro-F1 0.6595, test Macro-F1 0.6149.
- Improvement over best root: 0.0000 validation Macro-F1.
- Best path: `root_concat_gated_mlp`.

The search did not find a child node that exceeded the best root baseline. The closest child was below the best gated concat root.

## Blueprint Usage

- `aido_embedding_fusion`: 1, status=planned, level=5, category=foundation_model_fusion
- `cross_attention_gene_perturbation`: 1, status=planned, level=4, category=fusion
- `dual_path_gated_low_rank`: 14, status=implemented, level=2, category=architecture_program
- `esm2_gene_projection`: 1, status=planned, level=5, category=foundation_model_fusion
- `mixture_of_experts`: 3, status=implemented, level=4, category=fusion
- `pathway_pooling_encoder`: 1, status=planned, level=5, category=biological_prior
- `root`: 7
- `selective_adapter_finetune`: 1, status=planned, level=5, category=fine_tuning
- `uncertainty_calibrated_head`: 1, status=planned, level=2, category=prediction_head

Level counts among child nodes:
- Level 2: 15
- Level 4: 4
- Level 5: 4

Planned implementations:
- `esm2_gene_projection` / `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460`: val 0.5562, test 0.5218, level 5
- `aido_embedding_fusion` / `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53`: val 0.6192, test 0.5914, level 5
- `pathway_pooling_encoder` / `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09`: val 0.5210, test 0.4797, level 5
- `cross_attention_gene_perturbation` / `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d`: val 0.3158, test 0.3158, level 4
- `uncertainty_calibrated_head` / `root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d`: val 0.6559, test 0.5907, level 2
- `selective_adapter_finetune` / `root_concat_residual_mlp_p2_selective_adapter_finetune_9ad96574`: val 0.3582, test 0.3716, level 5

## Missing Artifacts And Fallbacks

- `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460`: `missing_artifact = "protein_sequences_or_esm2_embeddings"`
- `root_concat_gated_mlp_p1_esm2_gene_projection_3ed40460`: `fallback = "frozen_zero_esm2_prior_plus_tabular_encoder"`
- `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53`: `missing_artifact = "aido_embeddings"`
- `root_concat_gated_mlp_p2_aido_embedding_fusion_05efdf53`: `fallback = "inactive_frozen_aido_branch_with_gated_tabular_fusion"`
- `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09`: `missing_artifact = "pathway_memberships"`
- `root_concat_mlp_p1_pathway_pooling_encoder_d60ffd09`: `fallback = "learnable_pathway_slots_without_external_membership"`
- `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d`: `missing_artifact = "none_learnable_gene_tokens_used"`
- `root_concat_mlp_p2_cross_attention_gene_perturbation_0e07750d`: `fallback = "learnable_target_token_table"`
- `root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d`: `calibration_note = "learns temperature-like logit scale during training; no test-threshold tuning"`
- `root_concat_residual_mlp_p2_selective_adapter_finetune_9ad96574`: `missing_artifact = "pretrained_encoder"`
- `root_concat_residual_mlp_p2_selective_adapter_finetune_9ad96574`: `fallback = "frozen_random_base_projection_plus_trainable_adapter"`

ESM2, AIDO, pathway, and pretrained-adapter artifacts were not present and were not fabricated. Those nodes explicitly record frozen/inactive or learnable fallback branches.

## Search Behavior

- Parent selection used UCT with exploration `sqrt(2)`, matching the paper-aligned public artifact rule.
- PUCT was not used in this run.
- Proposals include MCTS fields such as `mcts_selected_parent`, `mcts_selection_policy`, and candidate UCT score components.
- The strongest planned child was `root_concat_residual_mlp_p1_uncertainty_calibrated_head_396fae7d`, with val Macro-F1 0.6559 and test Macro-F1 0.5907, close to but below the best root.

## Root Baselines

- `root_concat_gated_mlp`: val 0.6595, test 0.6149
- `root_concat_mlp`: val 0.6516, test 0.5932
- `root_concat_residual_mlp`: val 0.6244, test 0.5599
- `root_delta_mlp`: val 0.6138, test 0.5770
- `root_onehot_mlp`: val 0.6059, test 0.5532
- `root_concat_regularized_mlp`: val 0.5937, test 0.5418
- `root_concat_low_rank_mlp`: val 0.5406, test 0.5050

## Limitations

- This is one cell line and 30 trained nodes, not a full 100-200 node single-cell-line paper-scale search.
- Several Level 5 blueprints were implemented with explicit fallbacks because public/precomputed artifacts were unavailable.
- The run validates paper-aligned UCT program-node mechanics, but does not demonstrate improvement beyond the best root.
- Any fallback modules are repo-specific implementation completions, not paper-confirmed foundation-model behavior.

## Artifacts

- `experiments/k562_program_node_agent_search/search_summary.md`
- `experiments/k562_program_node_agent_search/final_conclusion.md`
- `experiments/k562_program_node_agent_search/tree.json`
- `experiments/k562_program_node_agent_search/failures.json`
- `experiments/k562_program_node_agent_search/implementation_queue.json`
- `experiments/k562_program_node_agent_search/proposals/*.json`
- `experiments/k562_program_node_agent_search/programs/<node>/model.py` for selected planned implementations
