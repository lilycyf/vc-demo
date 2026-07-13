# Generic Cell-Line Transfer Invocation

- Cell line: `K562`
- Slug: `k562`
- Level: `transfer_64x16`
- Run dir: `experiments/official_k562_generic_transfer_v1/transfer_64x16`
- Experiment: `official_k562_transfer_64x16`
- Resume: `True`
- Root configs: `configs/official_k562_loop_roots/root_aido_embedding_mlp.json`, `configs/official_k562_loop_roots/root_aido_gnn_embedding_mlp.json`

## Command

```bash
PYTHONPATH=src /usr/bin/python scripts/run_official_cellline_harness_search.py --cell-line K562 --run-dir experiments/official_k562_generic_transfer_v1/transfer_64x16 --experiment official_k562_transfer_64x16 --root-configs configs/official_k562_loop_roots/root_aido_embedding_mlp.json configs/official_k562_loop_roots/root_aido_gnn_embedding_mlp.json --budget-proposals 64 --budget-trained-nodes 16 --candidate-pool-size 4 --max-epochs 1 --max-children 8 --stop-no-improve 12 --selection-policy uct --official-blueprint-space --allow-planned-blueprints --strict-artifacts --enable-implementation-loop --implementation-repair-attempts 3
```

## Required Runbook

Follow `docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md` and validate against `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md`.
