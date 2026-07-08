# Official K562 Gap Closing Notes

This branch upgrades the single-cell-line K562 harness from a runnable demo into a paper-aligned automatic modeling scaffold. It does not claim numerical equivalence to the unpublished internal VCHarness orchestrator; it makes the public K562 task, public static tree, artifact provenance, MCTS search, external static wrapper, and native editable candidates live in one auditable loop.

## What Is Aligned

- Task: official K562 CRISPR DEG classification.
- Split contract: train 1,388 / val 154 / test 421.
- Target genes: 6,640.
- Metric: Macro-F1.
- MCTS policy: UCT in the local harness.
- Node meaning: a full candidate training pipeline, including model code, training config, artifact contract, metrics, and provenance.

## Public Static Tree Scaffold

`scripts/build_official_k562_static_tree.py` parses the public VCHarness K562 static code directory and writes benchmark-only scaffold files:

- `official_k562_static_tree.json`
- `official_k562_node_catalog.md`
- `official_k562_best_path.json`

The parser infers parent-child relations from node ids. For example, `node2-1-1` has parent `node2-1`. The scaffold is not treated as local search output; it is used to compare what the local search covers and what remains unmapped.

## External Static Node Wrapper

The `external_static_node` backend now has two modes:

- `smoke`: keeps debug or max-step arguments and may mark test metrics as `missing_or_val_fallback`.
- `benchmark`: rejects debug or fast-dev arguments and requires an explicit test metric unless `allow_test_metric_fallback` is true.

Configs:

- `configs/official_k562_public_best_node_smoke.json`
- `configs/official_k562_public_best_node_benchmark.json`
- `configs/official_k562_public_best_node.json` remains a smoke-compatible alias.

Benchmark mode must not silently write a placeholder or validation fallback as test performance.

## Native Official Blueprint Space

The first native official blueprint family is implemented through `src/vc_demo/official_k562/native_models.py`:

- `official_target_gene_head`
- `official_string_gnn_attention`
- `official_aido_lora_adapter`
- `official_aido_string_fusion`
- `official_native_public_best_reimplementation`

The native public-best reimplementation is a compact compatibility v1. It is editable by the Codex agent and supports forward/backward smoke, but it is not a numerical clone of `node2-1-1-1-1-1_code.py`.

## Native Smoke Gate

Before a node-local `custom_program` trains, the executor runs `vc_demo.harness.native_program_smoke`:

- imports node-local `model.py`
- builds a real `ModelSpec`
- checks output shape `[batch, 6640, 3]`
- runs a backward pass
- writes `native_program_smoke.json`

If this gate fails, the node should enter repair/failure rather than train silently.

## Artifact Alignment

`scripts/write_official_k562_artifact_alignment.py` writes JSON and Markdown matrices with:

- artifact id
- provider
- local path
- size/checksum when available
- status: `original_public`, `derived`, `reconstructed_compatibility`, or `missing`
- equivalence claim
- required blueprint families

Important caveat: `official_string_gnn_model_dir` is marked as `reconstructed_compatibility`, not as an original public checkpoint. Reports must preserve this caveat when attributing score gaps.

## Validated Smoke Commands

Forced official child smoke:

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_gap_closing_smoke \
  --experiment official_k562_gap_closing_smoke \
  --root-configs \
    configs/official_k562_root_aido_embedding_mlp.json \
    configs/official_k562_root_aido_gnn_embedding_mlp.json \
    configs/official_k562_public_best_node_smoke.json \
    configs/official_k562_native_public_best_reimplementation.json \
  --budget-nodes 1 \
  --max-epochs 1 \
  --max-children 2 \
  --stop-no-improve 1 \
  --selection-policy uct \
  --official-blueprint-space \
  --force-blueprint official_target_gene_head \
  --reset
```

Unforced official blueprint smoke:

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_gap_closing_unforced_smoke \
  --experiment official_k562_gap_closing_unforced_smoke \
  --root-configs \
    configs/official_k562_root_aido_embedding_mlp.json \
    configs/official_k562_root_aido_gnn_embedding_mlp.json \
    configs/official_k562_public_best_node_smoke.json \
    configs/official_k562_native_public_best_reimplementation.json \
  --budget-nodes 2 \
  --max-epochs 1 \
  --max-children 2 \
  --stop-no-improve 2 \
  --selection-policy uct \
  --official-blueprint-space \
  --reset
```

Generate a final report for any run:

```bash
PYTHONPATH=src python scripts/write_official_k562_final_report.py \
  --run-dir experiments/official_k562_gap_closing_unforced_smoke \
  --output experiments/official_k562_gap_closing_unforced_smoke/final_report.md
```

## Next Scale Runs

Small 50-node pressure test:

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_gap_closing_small_50 \
  --experiment official_k562_gap_closing_small_50 \
  --root-configs \
    configs/official_k562_root_aido_embedding_mlp.json \
    configs/official_k562_root_aido_gnn_embedding_mlp.json \
    configs/official_k562_public_best_node_smoke.json \
    configs/official_k562_native_public_best_reimplementation.json \
  --budget-nodes 50 \
  --max-epochs 3 \
  --max-children 3 \
  --stop-no-improve 12 \
  --selection-policy uct \
  --official-blueprint-space \
  --strict-artifacts \
  --allow-planned-blueprints \
  --enable-repair-loop \
  --enable-acquisition-loop \
  --max-blueprint-repeats -1 \
  --allow-parent-duplicate-blueprints \
  --reset
```

Medium 150-node run should only start after the 50-node run has a clean report and no unresolved critical artifact blocker.

## Guardrails For Codex Agent

Allowed changes during node implementation:

- node-local `model.py`
- node-local config or pipeline metadata
- small approved helper modules under `src/vc_demo/official_k562/`

Forbidden changes:

- official train/val/test split
- labels
- Macro-F1 metric
- target gene order
- artifact provenance claims
- silent fallback for missing required artifacts in strict official mode

## Full Paper-Scale Upgrade Contract

The current branch now treats the K562 paper-scale experiment as three linked contracts:

- Search-space manifest: `configs/official_k562_paper_scale_search_space.json` defines combinatorial dimensions whose estimated capacity must exceed 600 candidates. Planned entries are intentionally selectable without being pre-implemented.
- On-demand implementation: every planned node receives `IMPLEMENTATION_REQUEST.md`, `artifact_contract.json`, `smoke_contract.json`, `parent_summary.json`, and `pipeline.json`. Codex implements only the selected node and must obey strict artifact policy.
- MCTS traceability: every selection, expansion, pending implementation, artifact block, failure, and backpropagation is appended to `mcts_trace.jsonl` for final report attribution.

Use `scripts/audit_official_k562_paper_scale_search_space.py` to verify blueprint counts, status counts, required fields, and 600+ estimated search-space capacity before running 50/150/600-node experiments.

## Paper-Scale Search Contract

The official K562 harness now treats paper-scale search as a first-class contract, not as a fully pre-implemented model library.

Scale requirements:

- `smoke`: 3-5 trained/evaluated nodes, only for wiring checks.
- `pilot`: 20-50 trained/evaluated nodes, only for pressure testing.
- `medium`: 150 trained/evaluated nodes, useful for debugging breadth and repair/acquisition behavior.
- `paper-scale single-cell-line`: 600+ budget nodes for K562, matching the paper-level search order of magnitude rather than a demo run.
- `public static scaffold`: all 154 public K562 static nodes are benchmark/alignment candidates, not merely the single public best node.

The full search space does not need to be pre-implemented. A blueprint can be:

- `implemented`: executable immediately.
- `planned`: selectable by MCTS when `--allow-planned-blueprints` is set; Codex must implement it on demand.
- `blocked_missing_artifact`: must acquire the real artifact or stop; no fallback training in strict official mode.

Codex implementation rule:

When MCTS selects a planned blueprint, the harness should create a node-local `IMPLEMENTATION_REQUEST.md`. Codex then implements only the selected node's `model.py` or config-only patch, runs smoke/compile checks, trains/evaluates, and records the result. This is intentional: the paper-scale search space is a manifest and procedure, not a requirement to hand-code every candidate before search starts.

The machine-readable contract lives in:

```text
configs/official_k562_paper_scale_search_space.json
```

The official K562 selectable blueprint registry now includes implemented and planned entries across AIDO, scFoundation/single-cell foundation encoders, STRING_GNN, AIDO+STRING fusion, target-gene heads, pathway/regulatory priors, training strategies, and public static tree wrappers.

Paper-scale command shape:

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_paper_scale_600 \
  --experiment official_k562_paper_scale_600 \
  --root-configs \
    configs/official_k562_root_aido_embedding_mlp.json \
    configs/official_k562_root_aido_gnn_embedding_mlp.json \
    configs/official_k562_public_best_node_benchmark.json \
    configs/official_k562_native_public_best_reimplementation.json \
  --budget-nodes 600 \
  --max-epochs 5 \
  --max-children 4 \
  --stop-no-improve 60 \
  --selection-policy uct \
  --official-blueprint-space \
  --strict-artifacts \
  --allow-planned-blueprints \
  --enable-repair-loop \
  --enable-acquisition-loop \
  --max-blueprint-repeats -1 \
  --allow-parent-duplicate-blueprints \
  --max-pending-implementations 8 \
  --reset
```
