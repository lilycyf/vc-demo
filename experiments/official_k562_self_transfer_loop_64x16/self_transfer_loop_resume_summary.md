# K562 Generic Self-Transfer Loop Resume Summary

## Verdict

The pending `official_target_gene_head` node was implemented as a node-local, target-gene-aware PyTorch model using present official K562 task artifacts. It compiled, passed native forward/backward smoke, trained for one epoch with `train_pending`, and the same run was resumed without `--reset`.

The resumed search generated another proposal pool, pruned unselected proposals, and stopped at the next formal `requires_external_codex` pending node. The public-wrapper `/home/Models/STRING_GNN` blocker did not affect this loop-only root run.

## Counts

- trained count: `3`
- pending implementation count: `1`
- acquisition queue count: `0`
- generated proposals count: `8`
- pruned proposals count: `6`
- selected rollout count: `1 trained via train_pending; trace selected_for_training events=0`
- fallback count: `0`
- backprop_nontrained count: `0`
- backend anomaly count: `0`
- public wrapper STRING_GNN blocker triggered: `False`

## Selected Node

- node: `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042`
- strategy: `official_target_gene_head`
- status: `trained`
- val Macro-F1: `0.32795366644859314`
- test Macro-F1: `0.34598609805107117`
- backend/model type: `custom_program`
- native smoke output shape: `[2, 6640, 3]`
- trainable parameters: `1527811`
- artifact usage: `{'pipeline_kind': 'pipeline_program_node', 'pipeline_strategy': 'official_target_gene_head', 'loss_type': 'weighted_cross_entropy', 'uses_real_artifact': True, 'artifact_sides': ['perturbation_gene_or_context'], 'artifact_manifest_path': '', 'required_artifacts': ['official_essential_deg_with_split_h5ad'], 'missing_required_artifacts': []}`

## Best Nodes

- best root: `official_k562_root_aido_gnn_embedding_mlp`, val `0.38831961154937744`, test `0.3995912969112396`
- best generated child: `official_k562_root_aido_gnn_embedding_mlp_p4_official_target_gene_head_d1c96042`, val `0.32795366644859314`, test `0.34598609805107117`, status `trained`

## Resume Result

- stop reason: `pending implementation limit reached (1)`
- new pending node: `official_k562_root_aido_embedding_mlp_p3_official_string_neighborhood_attention_898d7103`
- new pending strategy: `official_string_neighborhood_attention`

## Proposal/Backprop Semantics

- Unselected proposals remained `pruned_not_selected`; no pruned node was trained.
- The selected pending node was trained before being marked `trained`.
- `train_pending` updated the tree and called MCTS backpropagation for the trained node; the trace file in this branch does not emit a separate `backpropagation` row for manual `train_pending`.
- No failed, pending, blocked, or pruned node was backpropagated according to the trace audit.
- No fallback or compact/native proxy markers were introduced.

## Phase Decision

This satisfies the K562 generic loop self-test for one pending implementation/resume cycle. It is appropriate to proceed to the next-stage second cell-line generic transfer test, while continuing to treat newly pending formal blueprints as implementation tasks rather than automatic compact substitutes.
