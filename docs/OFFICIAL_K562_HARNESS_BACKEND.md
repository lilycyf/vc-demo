# Official K562 Harness Backend

This document records the repo-side bridge between the reconstructed official K562 task contract and the `vc_demo.harness.program_run` MCTS/program-node search loop.

## What This Adds

The backend makes the official K562 single-cell-line task executable by the local harness, not only by the external public VCHarness static node script.

It validates and wires together:

- official K562 TSV data contract: `data/cell_lines/official_k562_cls/{train,val,test}.tsv`
- official target gene count: 6,640 genes
- official split sizes: train 1,388, validation 154, test 421
- official AIDO.Cell-100M perturbation embedding h5ad
- official GNN Simple embedding h5ad
- official root configs:
  - `configs/official_k562_root_aido_embedding_mlp.json`
  - `configs/official_k562_root_aido_gnn_embedding_mlp.json`

The wrapper is:

```bash
PYTHONPATH=src python scripts/run_official_k562_harness_search.py \
  --run-dir experiments/official_k562_harness_backend_smoke \
  --experiment official_k562_harness_backend_smoke \
  --budget-nodes 1 \
  --max-epochs 1 \
  --force-blueprint dual_path_gated_low_rank \
  --reset
```

## What A Node Means Here

In this backend, each MCTS node is a complete train/evaluate candidate on the official K562 task. A node includes:

- official K562 data representation
- selected perturbation embeddings
- model program or built-in model type
- training loss and optimizer settings
- one complete training run
- validation Macro-F1 reward used by MCTS
- held-out test Macro-F1 for reporting only

The smoke run proves that official K562 roots and generated child nodes can go through the same tree/search/report path as the earlier demo tasks.

## Strict Artifact Rule

Official artifact claims must not silently fallback. The backend preflight checks required public artifacts before search. If a future blueprint requires unavailable official artifacts, the search should create an acquisition/blocker record rather than training a random substitute.

Current required artifacts for this backend are:

- `official_essential_deg_with_split_h5ad`
- `official_k562_aido_cell_100m_embedding_h5ad`
- `official_gnn_simple_embedding_h5ad`

The public VCHarness best-node compatibility path additionally depends on local model dirs under `/home/Models`, and remains tracked separately.

## Current Smoke Result

Run directory:

```text
experiments/official_k562_harness_backend_smoke
```

The validation smoke trained two official roots plus one MCTS-selected child:

| Node | Kind | Val Macro-F1 | Test Macro-F1 |
|---|---|---:|---:|
| `official_k562_root_aido_embedding_mlp` | root | 0.4068 | 0.4306 |
| `official_k562_root_aido_gnn_embedding_mlp` | root | 0.4108 | 0.4432 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_dual_path_gated_low_rank_4c85c6a0` | program child | 0.4064 | 0.4284 |

This is a one-epoch integration smoke, not a paper score reproduction.

## What This Still Is Not

This backend does not yet make the local MCTS harness equivalent to the paper/public best-node architecture. In particular, it does not yet train the public `node2-1-1-1-1-1` AIDO LoRA + STRING_GNN multi-head attention model as a generated MCTS child.

The public best-node smoke remains separate because it uses external VCHarness node code and model-dir compatibility shims. The next alignment step is to either:

1. wrap that public node as a harness-executable root/candidate, or
2. implement an equivalent local `custom_program` blueprint with explicit AIDO AutoModel, LoRA, STRING_GNN attention, and official training settings.
