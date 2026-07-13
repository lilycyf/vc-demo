# Generic Cell-Line Transfer Invocation

- Cell line: `K562`
- Slug: `k562`
- Run type: `full_cellline_run`
- Level: `full_cellline_run`
- Artifact-constrained filter required: `True`
- Proposal selection mode: `global_queue`
- Max epochs: `8`
- Target validation Macro-F1: `0.5`
- Run dir: `experiments/k562_generic_transfer_full_rerun`
- Experiment: `k562_generic_transfer_full_rerun`
- Resume: `False`
- Root configs: `configs/official_k562_loop_roots/root_aido_embedding_mlp.json`, `configs/official_k562_loop_roots/root_aido_gnn_embedding_mlp.json`

## Command

```bash
PYTHONPATH=src /usr/bin/python scripts/run_official_cellline_harness_search.py --cell-line K562 --run-dir experiments/k562_generic_transfer_full_rerun --experiment k562_generic_transfer_full_rerun --root-configs configs/official_k562_loop_roots/root_aido_embedding_mlp.json configs/official_k562_loop_roots/root_aido_gnn_embedding_mlp.json --budget-proposals 300 --budget-trained-nodes 100 --candidate-pool-size 6 --proposal-selection-mode global_queue --max-epochs 8 --max-children 10 --stop-no-improve 60 --selection-policy uct --official-blueprint-space --allow-planned-blueprints --strict-artifacts --enable-implementation-loop --implementation-repair-attempts 3 --reset
```

## Required Runbook

Follow `docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md` and validate against `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md`.
