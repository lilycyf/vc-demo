# Generic Cell-Line Transfer Invocation

- Cell line: `K562`
- Slug: `k562`
- Run type: `full_cellline_run`
- Level: `full_cellline_run`
- Artifact-constrained filter required: `True`
- Max epochs: `8`
- Target validation Macro-F1: `0.5`
- Run dir: `experiments/official_k562_generic_transfer_v1/full_cellline_run`
- Experiment: `official_k562_full_cellline_run`
- Resume: `True`
- Root configs: `configs/official_k562_loop_roots/root_aido_embedding_mlp.json`, `configs/official_k562_loop_roots/root_aido_gnn_embedding_mlp.json`

## Command

```bash
PYTHONPATH=src /usr/bin/python scripts/run_official_cellline_harness_search.py --cell-line K562 --run-dir experiments/official_k562_generic_transfer_v1/full_cellline_run --experiment official_k562_full_cellline_run --root-configs configs/official_k562_loop_roots/root_aido_embedding_mlp.json configs/official_k562_loop_roots/root_aido_gnn_embedding_mlp.json --budget-proposals 300 --budget-trained-nodes 100 --candidate-pool-size 6 --max-epochs 8 --max-children 10 --stop-no-improve 60 --selection-policy uct --official-blueprint-space --allow-planned-blueprints --strict-artifacts --enable-implementation-loop --implementation-repair-attempts 3
```

## Required Runbook

Follow `docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md` and validate against `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md`.
