# K562 to New Cell-Line Reusable Checklist

Use this checklist before claiming that another cell line has reached K562 Harness v1 / Phase-3.

## Required Contract

- Source-backed DEG label matrix is identified.
- Cell-line rows are filtered by official cell-line name, not inferred from filenames alone.
- Train/validation/test split is fixed and written to a manifest.
- Target gene order is fixed, documented, and validated.
- Labels keep the official semantics and remap only at training time when required.
- Reward is validation Macro-F1; test Macro-F1 is report-only.

## Required Artifact Policy

- Registry records every artifact id, path, source, provider, status, and whether it is reusable or cell-line-specific.
- Reusable artifacts can be shared only when the tensor contract is cell-line independent.
- Cell-line-specific embeddings must be acquired or built for that cell line; never reuse K562-specific h5ad embeddings.
- Missing artifacts first go through acquisition. The run must write an acquisition queue, acquisition report, and artifact-specific task before calling something a blocker.
- If source, checkpoint, row order, vocabulary, or shape cannot be verified, stop with acquisition/block.
- No random, tabular, small-MLP, or previous-cell-line fallback is allowed.

## Required Search Semantics

- MCTS selects a parent.
- A proposal pool is generated.
- Unselected proposals are recorded as `pruned_not_selected` and are not trained.
- Selected planned nodes materialize node-local `model.py` only after artifact checks pass.
- Compile and native forward/backward smoke must pass before training.
- Only trained nodes backpropagate reward.
- `external_static_node` is allowed only for explicit public static wrapper/benchmark roots.
- Generated native children must use native/program-node training backends.

## Required Reports

- Task contract audit JSON/MD.
- Artifact registry audit JSON.
- Root baseline summary.
- Search summary with proposal/trained/pruned/blocker counts.
- Final report with best root, best trained rollout, val/test Macro-F1, improvement, stop reason.
- Audit counts: fallback = 0, backprop_nontrained = 0.
- Forbidden staged-file check before commit.

## K562 v1 Reference Numbers

- Split: train 1388, val 154, test 421.
- Target genes: 6640.
- 64/16 run best root: official_k562_native_public_best_reimplementation, val 0.4332, test 0.4702.
- 64/16 best trained rollout: official_k562_native_p2_official_string_gnn_attention_c7b091ac, val 0.4421, test 0.4805.
- 150/40 best root: official_k562_native_public_best_reimplementation, val 0.4221, test 0.4559.
- 150/40 best trained rollout: official_k562_native_p6_official_target_graph_conditioned_head_e7c293b6, val 0.4470, test 0.4829.
- 150/40 strict blocker: scfoundation_cell_embeddings.

## Acquisition Closure

A strict blocker is acceptable only after the acquisition loop has produced:

- an acquisition queue item naming artifact id, node, strategy, expected path, and source hint;
- an acquisition report showing whether an automatic resolver was available and executed;
- an `ACQUIRE_<artifact>.md` task when no automatic resolver exists;
- a clear statement that no fallback model or fabricated artifact was trained.

For K562 v1 this closure exists for:

- `official_string_gnn_model_dir`
- `scfoundation_cell_embeddings`
