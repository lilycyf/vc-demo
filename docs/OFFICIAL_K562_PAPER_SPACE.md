# Official K562 Paper-Space Harness

This branch connects the local `vc_demo` MCTS/program-node harness to a more paper-aligned single-cell-line K562 workflow.

## What Is New

- `external_static_node` execution backend for public VCHarness static nodes.
- `official_k562_public_best_node2_1_1_1_1_1` root config, wrapping `_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py`.
- Official K562 blueprint family for paper-level search:
  - `official_public_best_node`
  - `official_aido_lora_adapter`
  - `official_string_gnn_attention`
  - `official_aido_string_fusion`
  - `official_target_gene_head`
  - `official_class_imbalance_training`
- `--official-blueprint-space` routing so official K562 runs do not sample generic demo blueprints by default.
- Strict artifact audit additions for public best-node code, AIDO.Cell-100M, and STRING_GNN.

## External Static Node Contract

The external backend runs the public static code through the same harness interface as native nodes. It prepares official K562 TSV links, executes the static script, captures stdout, reads public metrics/log outputs, and writes standardized `metrics.json` with:

- `best_val_macro_f1`
- `test_macro_f1`
- `duration_seconds`
- `execution_backend=external_static_node`
- `external_script`
- `artifact_usage`

Fast smoke runs use debug arguments, so `test_macro_f1` may be derived from validation F1 when the public script does not emit held-out test F1. Full benchmark runs should remove debug/max-step limits.

## Artifact Provenance

The official public wrapper requires:

- official K562 TSV task files under `data/cell_lines/official_k562_cls`
- public best-node code under `_external/VCHarness/K562_cls/static`
- `/home/Models/AIDO.Cell-100M`
- `/home/Models/STRING_GNN`

`/home/Models/STRING_GNN` is currently a compatibility reconstruction from public official GNN embedding and graph artifacts unless an original upstream checkpoint is available. Reports must keep that caveat visible and must not claim numerical equivalence to an unpublished checkpoint.

## Smoke Command

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py   --run-dir experiments/official_k562_paper_space_smoke   --experiment official_k562_paper_space_smoke   --root-configs     configs/official_k562_root_aido_embedding_mlp.json     configs/official_k562_root_aido_gnn_embedding_mlp.json     configs/official_k562_public_best_node.json   --budget-nodes 1   --max-epochs 1   --max-children 2   --stop-no-improve 1   --selection-policy uct   --official-blueprint-space   --force-blueprint official_class_imbalance_training   --reset
```

The smoke should produce three roots plus one official child, with `official_k562_public_best_node2_1_1_1_1_1` appearing in `tree.json` and `search_summary.md` as an `external_static_node`.

## Next Scale-Up

After this smoke, the next meaningful run is a 50-node official K562 search with strict artifacts and official blueprint space enabled. Planned blueprints should either be implemented by the Codex agent using real audited artifacts or block/acquire missing artifacts; no fallback nodes should be trained in official mode.

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
