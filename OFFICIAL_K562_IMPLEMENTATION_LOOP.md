# Official K562 Automatic Implementation Loop

This repo now supports a stricter paper-aligned loop for selected planned nodes:

1. MCTS selects a parent.
2. The harness generates a proposal pool.
3. In full-cellline runs, feasible proposals enter a global queue; the next rollout is the highest-priority queued proposal across all generated parents.
4. Duplicate or dominated proposals may be pruned, but local pool losers are not automatically discarded in global-queue mode.
5. The selected planned proposal is materialized by the implementation loop.
6. The loop runs compile and native forward/backward smoke.
7. Only a smoke-passing node is trained with `train_pending`.
8. Only a trained node backpropagates reward into MCTS.

This is the preferred mode for official K562 paper-aligned runs. Do not manually train every proposal.

## Strict Rules

- No silent fallback.
- Missing required artifacts must block/acquire; they must not be replaced by random or tabular stand-ins.
- Failed implementation attempts do not backpropagate reward.
- `candidate_queued` proposals remain eligible for later global selection; `pruned_not_selected` proposals are never trained.
- Test metrics are reported only after training; they must not guide implementation or repair.
- Generated native children must not inherit `external_static_node` backend from public static parents.
- Generated native children must use stable official K562 cached embeddings when a public static parent lacks native feature config.

## Main Flags

Use these flags through `scripts/run_official_k562_harness_search.py`:

```bash
--enable-implementation-loop
--implementation-repair-attempts 3
--allow-planned-blueprints
--strict-artifacts
--candidate-pool-size 4
--proposal-selection-mode global_queue   # required for full_cellline_run
--budget-proposals <N>
--budget-trained-nodes <M>
```

`--enable-repair-loop` is kept as a compatibility alias for `--enable-implementation-loop` in the official wrapper.

## Generated Logs

The automatic loop writes:

- `implementation_agent_report.json`
- `repair_log.jsonl`
- `agent_decision_trace.jsonl`
- node-local `native_smoke_attempt_<n>.json`
- normal `tree.json`, `mcts_trace.jsonl`, `implementation_queue.json`, `acquisition_queue.json`

A successful selected planned node should move from `needs_implementation` to `trained`. If realtime implementation cannot safely produce a real model, the node must become `implementation_skipped`, leave `implementation_queue.json`, and the global queue continues.

## Acceptance For Smoke Runs

A valid automatic-loop smoke should show:

- `pending_implementations: 0`
- `failures: 0` unless the purpose is a repair-failure test
- `trained_rollouts_this_invocation > 0`
- `candidate_queued > 0` in global-queue full runs, or `pruned_not_selected > 0` in local-pool smoke runs
- `repair_log.jsonl` exists
- `agent_decision_trace.jsonl` contains `implementation_selected` and `trained_and_backpropagated`

## Example Smoke

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_auto_impl_smoke \
  --experiment official_k562_auto_impl_smoke \
  --root-configs configs/official_k562_root_aido_embedding_mlp.json \
  --budget-proposals 2 \
  --budget-trained-nodes 1 \
  --candidate-pool-size 2 \
  --max-epochs 1 \
  --max-children 4 \
  --stop-no-improve 4 \
  --selection-policy uct \
  --official-blueprint-space \
  --allow-planned-blueprints \
  --strict-artifacts \
  --enable-implementation-loop \
  --implementation-repair-attempts 3 \
  --force-blueprint official_target_low_rank_head \
  --reset
```

## Next Scale Test

After the smoke passes, the next recommended run is:

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_auto_impl_64x16 \
  --experiment official_k562_auto_impl_64x16 \
  --root-configs \
    configs/official_k562_root_aido_embedding_mlp.json \
    configs/official_k562_root_aido_gnn_embedding_mlp.json \
        configs/official_k562_public_best_node_benchmark.json \
  --budget-proposals 64 \
  --budget-trained-nodes 16 \
  --candidate-pool-size 4 \
  --max-epochs 1 \
  --max-children 8 \
  --stop-no-improve 12 \
  --selection-policy uct \
  --official-blueprint-space \
  --allow-planned-blueprints \
  --strict-artifacts \
  --enable-implementation-loop \
  --implementation-repair-attempts 3 \
  --reset
```

Do not advance to 150/600+ proposal runs until this 64/16 run has clean implementation and repair logs.

## Negative Smoke Before Scale Runs

Run these before a 64/16 or larger test when changing the implementation loop.

### Missing Artifact Must Block

This checks that strict artifact mode blocks missing scFoundation artifacts before implementation or training:

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_auto_impl_missing_artifact_smoke \
  --experiment official_k562_auto_impl_missing_artifact_smoke \
  --root-configs configs/official_k562_root_aido_embedding_mlp.json \
  --budget-proposals 2 \
  --budget-trained-nodes 1 \
  --candidate-pool-size 2 \
  --max-epochs 1 \
  --max-children 4 \
  --stop-no-improve 4 \
  --selection-policy uct \
  --official-blueprint-space \
  --allow-planned-blueprints \
  --strict-artifacts \
  --enable-implementation-loop \
  --implementation-repair-attempts 3 \
  --force-blueprint official_scfoundation_top_layer_finetune \
  --reset
```

Expected:

- `requires_artifact_acquisition` or equivalent blocker appears.
- No node-local fallback `model.py` is trained.
- `trained_rollouts_this_invocation` remains 0 for the selected blocked rollout.
- `acquisition_queue.json` names `scfoundation_cell_embeddings`.

### Unknown Template Must Be Handled Realtime Or Skipped

Use this when adding a new planned blueprint without a local template. The selected node must be handled during the current Codex run. If Codex cannot safely generate a real artifact-backed `model.py`, the node becomes `implementation_skipped`, not pending-for-later. It is not trained and does not backpropagate. In `global_queue` full runs this is not a terminal stop reason: the search continues to other queued candidates.

Expected:

- `CODEX_IMPLEMENTATION_TASK.md` may be written for audit under the node's program directory.
- `implementation_queue.json` returns to empty for skipped nodes; no future manual queue is left behind.
- No fallback model is generated.
- No reward backpropagation occurs for that node.
- Full runs continue through the global queue instead of stopping at one unimplemented node.


## Acquisition Before Block

Formal K562 runs must treat a missing required artifact as an acquisition task before treating it as a final blocker:

1. Run the artifact acquisition command emitted in stdout or `run_manifest.json`.
2. Follow generated `ACQUIRE_<artifact>.md` tasks, especially for `scfoundation_cell_embeddings`.
3. Search official/primary/public sources and build only source-backed artifacts.
4. Audit shape, row/order alignment, vocabulary coverage, split coverage, leakage risk, and provenance.
5. Resume the same strict run if the artifact becomes present.
6. Keep the node blocked only if the source or tensor contract cannot be verified.

The negative missing-artifact smoke is the only case where stopping immediately after queue creation is acceptable; formal scale runs must perform the acquisition pass.

## Experiment Codex Handoff Semantics

Experiment Codex should now behave as an auditor/operator of the loop, not as the default implementer.

Default behavior:

1. Run with `--enable-implementation-loop`.
2. Do not manually inspect every pending node.
3. If `implementation_queue.json` is empty, continue/resume according to the run budget.
4. If a node is `blocked_missing_artifact` or `requires_artifact_acquisition`, do not merely stop and report. Run the artifact acquisition resolver, follow any generated `ACQUIRE_<artifact>.md`, attempt source-backed acquisition/build/audit, update registry if successful, and then resume. Stop only after the acquisition attempt produces a documented blocker.
5. If realtime implementation cannot safely create a real node-local `model.py`, mark the node `implementation_skipped`, leave no pending queue for later, and continue global search.
6. Never train fallback models in strict official mode.
7. Never count `candidate_queued`, `pruned_not_selected`, skipped, blocked, or failed nodes as trained rollouts.

The experiment report must include:

- proposal count
- trained rollout count
- queued proposal count
- pruned proposal count
- auto-implemented node count
- native smoke passed count
- repair attempt count
- failed implementation count
- requires-external-Codex count
- artifact blocker count
- backpropagation count
