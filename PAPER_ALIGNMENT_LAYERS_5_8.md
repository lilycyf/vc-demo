# Paper Alignment Layers 5-8

This document records the repo-side alignment work for layers 5-8 of the single-cell-line VCHarness-style reproduction target.

## 5. Benchmark Alignment Layer

Goal: separate framework reproduction from numeric paper reproduction.

Added:

- `src/vc_demo/harness/benchmark_audit.py`
- Output: `benchmark_audit.json`

The benchmark audit checks root configs, data split presence, input dimensions, target-gene consistency, label classes, perturbation identifiers, and remaining paper-alignment questions.

Command:

```bash
python -m vc_demo.harness.benchmark_audit   --root-configs configs/k562_roots/root_concat_gated_mlp.json configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json configs/k562_roots/root_concat_esm2_target_aware_bilinear.json   --output experiments/<run>/benchmark_audit.json
```

Interpretation:

- `ready_for_single_cell_line_formal_search` means the repo task is internally consistent.
- It does not by itself prove exact numeric reproduction of the paper unless the paper's exact split/labels/baselines are verified.

## 6. Search Scale / Budget Layer

Goal: make run scale explicit and avoid confusing smoke/demo runs with paper-scale searches.

Added:

- `src/vc_demo/harness/scale_plan.py`
- Output: `scale_plan.json`

Profiles:

- `smoke`: wiring only
- `demo`: small end-to-end demo
- `single_cellline_small`: 50 nodes
- `single_cellline_medium`: 100 nodes
- `paper_scale_single_cellline`: 200 nodes, still below the paper's broader 600+ model system scale

Command:

```bash
python -m vc_demo.harness.scale_plan   --profile single_cellline_small   --experiment k562_formal_search   --run-dir experiments/k562_formal_search   --root-configs configs/k562_roots/root_concat_gated_mlp.json configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json configs/k562_roots/root_concat_esm2_target_aware_bilinear.json   --output experiments/k562_formal_search/scale_plan.json
```

## 7. Failure Repair Layer

Goal: make failed-node repair explicit and reproducible for the active Codex agent.

Added:

- `src/vc_demo/harness/repair_workflow.py`
- Output directory: `repair_tasks/`

Command:

```bash
python -m vc_demo.harness.repair_workflow   --run-dir experiments/<run>   --output-dir experiments/<run>/repair_tasks
```

Rules:

- Repair only node-local `model.py` unless the traceback proves a harness bug.
- Do not change data splits, labels, metrics, or artifact provenance.
- Record repair outcome in `search_memory.json`, `failures.json`, and the final analysis.

## 8. Paper-Style Final Analysis Layer

Goal: convert run logs into a scientific interpretation, not only an engineering summary.

Enhanced:

- `src/vc_demo/harness/final_analysis.py`

It now reads:

- `tree.json`
- `search_memory.json`
- `run_manifest.json`
- `failures.json`
- `benchmark_audit.json`
- `scale_plan.json`
- `repair_tasks/repair_tasks.json`

Command:

```bash
python -m vc_demo.harness.final_analysis   --run-dir experiments/<run>   --output experiments/<run>/final_analysis.md
```

The final analysis reports:

- best root vs best overall
- improvement over root
- benchmark alignment status
- search scale profile
- strategy family results
- artifact interpretation
- memory-derived motifs
- repair readiness
- next search recommendations

## Recommended Formal Run Order

```text
artifact_readiness
benchmark_audit
scale_plan
preflight
autonomous_run
repair_workflow if failures exist
final_analysis
final_conclusion
```
