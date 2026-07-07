# Official K562 Task Contract Implementation

## What Was Implemented

- Added official K562 Essential DEG contract builder and validator.
- Added `official_k562_tsv` dataset support in `vc_demo.data`.
- Added source-backed artifact registry entries for the official Essential h5ad, K562 AIDO.Cell-100M embedding h5ad, and official GNN graph file.
- Added a runnable official K562 root config: `configs/official_k562_root_aido_embedding_mlp.json`.
- Added docs in `docs/OFFICIAL_K562_DATA_CONTRACT.md`.

## Source-Backed Artifacts Downloaded On RunPod

These files were downloaded to RunPod for validation and smoke testing, but should not be committed as code:

- `data/artifacts/official_k562/essential_deg_with_split.h5ad`
- `data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad`
- `data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt`

## Generated Official Task Data

Generated under `data/cell_lines/official_k562_cls`:

- `train.tsv`
- `val.tsv`
- `test.tsv`
- `target_genes.tsv`
- `manifest.json`

Validation status: `passed`.

- train rows: `1388`
- val rows: `154`
- test rows: `421`
- target genes: `6640`
- label vector lengths observed: `[6640]`
- issues: `[]`

## Runnable Smoke Test

Command:

```bash
python -m vc_demo.train \
  --config configs/official_k562_root_aido_embedding_mlp.json \
  --output-dir experiments/official_k562_task_contract/root_aido_embedding_mlp_smoke \
  --max-epochs 1
```

Result:

- device: `cuda`
- dataset type: `official_k562_tsv`
- best val Macro-F1: `0.4066`
- test Macro-F1: `0.4302`
- test loss: `0.5915`

This is only a connectivity smoke test. It is not a paper result and should not be compared to the official VCHarness best node.

## Remaining Gap To Official Best Node

The official K562 task data contract is now executable. The public VCHarness best-node code still expects model directories that are not yet present:

- `/home/Models/AIDO.Cell-100M`
- `/home/Models/STRING_GNN`

The downloaded AIDO h5ad gives a source-backed 640-dimensional K562 gene embedding and makes an embedding baseline runnable. It is not the same as the AutoModel + tokenizer directory used by the public best node. The downloaded GNN file is a source-backed graph/edge artifact, not necessarily a trained STRING_GNN model directory.

## Registry State

- Present artifacts: `esm2_gene_embedding_h5ad, esm2_k562_target_manifest, string_k562_gene_graph, pathway_membership_matrix, official_essential_deg_with_split_h5ad, official_k562_aido_cell_100m_embedding_h5ad, official_string_gnn_keep20_graph`
- Missing artifacts: `aido_gene_or_cell_embeddings, scfoundation_cell_embeddings, official_aido_cell_100m_model_dir, official_string_gnn_model_dir`
