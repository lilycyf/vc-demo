# Official K562 Data Contract

This repo now treats the paper-aligned K562 task as a separate contract from the earlier Norman/scPerturb demo task.

## Source Artifacts

- DEG labels: `data/artifacts/official_k562/essential_deg_with_split.h5ad`
  - Source: `genbio-ai/foundation-models-perturbation`, `essential/essential_deg_with_split.h5ad`
  - Matrix shape observed on RunPod: `7847 x 6640`
- AIDO K562 embedding: `data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad`
  - Source: `gene_embeddings/AIDOcell_100M_essential_K-562_2025_11_26_(D=640).h5ad`
- GNN graph source: `data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt`
  - Source: `gnn/9606.protein.links.ensembl_900_keep20_adaptive.txt`

## Split Policy

The official benchmark code in `genbio-ai/foundation-models-perturbation` defines Essential DEG train/test by cell line and fold:

- Cell line: `K-562`
- Fold: `0`
- Test rows: rows where `obs.test_split == 0`
- Train pool rows: all other K-562 rows

The public VCHarness K562 memory reports `1,388` training samples. For K-562 fold 0, the train pool has `1,542` rows. A 10 percent validation carve-out with a fixed seed leaves `1,388` training rows, matching the public VCHarness memory.

Default contract:

- `fold = 0`
- `val_fraction = 0.10`
- `val_seed = 20260414`
- `train = 1388`
- `val = 154`
- `test = 421`
- `n_target_genes = 6640`
- raw labels are `-1, 0, 1`; training remaps them to `0, 1, 2`

## Generated Files

Run:

```bash
python scripts/build_official_k562_task.py build \
  --source-h5ad data/artifacts/official_k562/essential_deg_with_split.h5ad \
  --output-dir data/cell_lines/official_k562_cls
```

This writes untracked data files:

- `train.tsv`
- `val.tsv`
- `test.tsv`
- `target_genes.tsv`
- `manifest.json`

The TSV columns match the public VCHarness node code:

- `pert_id`
- `symbol`
- `label`

where `label` is a JSON list of 6,640 raw DEG classes.

## Validation

Run:

```bash
python scripts/build_official_k562_task.py validate \
  --data-dir data/cell_lines/official_k562_cls \
  --output experiments/official_k562_task_contract/validation.json
```

The validator fails if:

- any split TSV is missing
- any label vector is not length 6,640
- `target_genes.tsv` is not length 6,640
- train rows are not 1,388 for the default fold-0 contract
- manifest alignment flags disagree with the public VCHarness facts

## What This Does Not Yet Claim

This contract reproduces the official K562 task geometry and data split used for VCHarness-style experiments. It does not yet reproduce the public best node numerically, because the public best node uses an AIDO.Cell-100M AutoModel directory and STRING_GNN model directory under `/home/Models`. The downloaded AIDO h5ad and GNN graph are source-backed artifacts, but they are not necessarily the exact model directories expected by the public generated node code.
