# Official K562 Missing Files Preparation

This document records the local compatibility files prepared for the public VCHarness K562 best node `node2-1-1-1-1-1`.

## Why This Exists

The official public node expects:

- `/home/Models/AIDO.Cell-100M`
- `/home/Models/STRING_GNN`
- `AutoTokenizer.from_pretrained(AIDO_MODEL_DIR, trust_remote_code=True)`
- `AutoModel.from_pretrained(AIDO_MODEL_DIR, trust_remote_code=True)`
- `AutoModel.from_pretrained(STRING_MODEL_DIR, trust_remote_code=True)`
- `graph_data.pt` and `node_names.json` under `/home/Models/STRING_GNN`

The public Hugging Face state available during this reconstruction does not expose all of those files:

- `genbio-ai/AIDO.Cell-100M` exposes weights/config, but no tokenizer files and no `auto_map`.
- `genbio-ai/STRING_GNN` exposes only `.gitattributes`, not model weights or graph files.

## What The Preparation Script Does

Run:

```bash
PYTHONPATH=/workspace/_external/ModelGenerator/huggingface/aido.cell \
python scripts/prepare_official_k562_missing_files.py \
  --output experiments/official_k562_task_contract/missing_files_preparation.json
```

The script prepares `/home/Models/AIDO.Cell-100M` by adding:

- `configuration_cellfoundation.py`
- `modeling_cellfoundation.py`
- `tokenization_cellfoundation.py`
- `tokenizer_config.json`
- `gene_id_to_aido_index.json`
- `OS_scRNA_gene_index.19264.tsv`
- `auto_map` entries in `config.json`

The AIDO model code is copied from official ModelGenerator source. The tokenizer is a compatibility shim for public VCHarness nodes that pass dictionaries such as `{"gene_ids": ["ENSG..."], "expression": [1.0]}`. It returns fixed-length AIDO expression tensors of shape `[batch, 19266]`.

The script prepares `/home/Models/STRING_GNN` by reconstructing a compatibility directory from public artifacts:

- `GNN_Simple_Official_D256.h5ad`
- `9606.protein.links.ensembl_900_keep20_adaptive.txt`

It writes:

- `config.json`
- `configuration_string_gnn_compat.py`
- `modeling_string_gnn_compat.py`
- `node_embeddings.pt`
- `graph_data.pt`
- `node_names.json`
- `pytorch_model.bin`

This is not a recovered original STRING_GNN checkpoint. It is a public-artifact compatibility reconstruction that preserves the expected local file interface and returns 256-dimensional node embeddings through `AutoModel`.

## Verified Smoke Tests

After preparation:

- `AutoConfig.from_pretrained("/home/Models/AIDO.Cell-100M", trust_remote_code=True)`: pass
- `AutoTokenizer.from_pretrained("/home/Models/AIDO.Cell-100M", trust_remote_code=True)`: pass
- `AutoModel.from_pretrained("/home/Models/AIDO.Cell-100M", trust_remote_code=True)`: pass
- `AutoModel.from_pretrained("/home/Models/STRING_GNN", trust_remote_code=True)`: pass
- Public best node `AIDOCellStringMultiHeadK16FusionModel(max_epochs=1).setup(stage="fit")`: pass

The strict compatibility checker now reports `status = compatible` with no blockers in:

```text
experiments/official_k562_task_contract/best_node_compatibility_after_missing_files.json
```

## Remaining Scientific Caveat

The loading and setup path is now compatible. This does not mean the published score has been reproduced yet.

The remaining work is to run the official K562 best-node training/evaluation path and compare validation/test Macro-F1 against the public VCHarness result. The STRING_GNN directory is reconstructed from public embedding/graph artifacts, so any result should explicitly label this as a compatibility reconstruction unless the original `/home/Models/STRING_GNN` checkpoint becomes available.
