# Official K562 Best-Node Compatibility Summary

Date: 2026-07-07

Branch: `official-k562-best-node-compatibility`

## What Is Aligned

- Public VCHarness best node inspected: `K562_cls/static/node2-1-1-1-1-1_code.py`
- Official task constants recovered:
  - `N_GENES = 6640`
  - `N_CLASSES = 3`
  - `AIDO_GENES = 19264`
  - `AIDO_HIDDEN = 640`
  - `STRING_HIDDEN = 256`
  - `NEIGHBOR_K = 16`
  - `N_ATTN_HEADS = 2`
  - `CLASS_FREQ = [0.0429, 0.9251, 0.0320]`
- Official TSV task is present:
  - train: 1388 perturbations
  - validation: 154 perturbations
  - test: 421 perturbations
  - target genes: 6640
- AIDO.Cell-100M model directory is present at `/home/Models/AIDO.Cell-100M`.
- ModelGenerator AIDO.Cell source is present at `/workspace/_external/ModelGenerator/huggingface/aido.cell`.

## What Was Verified

The direct official ModelGenerator AIDO path works after installing official K562 optional dependencies:

- `CellFoundationConfig.from_pretrained("/home/Models/AIDO.Cell-100M")`: pass
- `CellFoundationModel.from_pretrained("/home/Models/AIDO.Cell-100M")`: pass
- `CellFoundationForMaskedLM.from_pretrained("/home/Models/AIDO.Cell-100M")`: pass

The verified AIDO config is:

- `model_type = cellfoundation`
- `hidden_size = 640`
- `num_hidden_layers = 18`
- `num_attention_heads = 20`
- `max_position_embeddings = 19264`

Transformers must be pinned to a compatible 4.x line. The RunPod check used `transformers==4.46.3`; `transformers 5.13.0` failed because ModelGenerator AIDO.Cell imports `find_pruneable_heads_and_indices`, which is absent there.

## What Is Still Blocked

The public VCHarness best-node code cannot be run unchanged yet.

Remaining blockers:

- The public node calls `AutoTokenizer.from_pretrained(AIDO_MODEL_DIR, trust_remote_code=True)`, but `/home/Models/AIDO.Cell-100M` has no tokenizer files.
- The public node calls `AutoModel.from_pretrained(AIDO_MODEL_DIR, trust_remote_code=True)`, but the local AIDO config has no `auto_map`, so Transformers Auto classes do not recognize `cellfoundation`.
- `/home/Models/STRING_GNN` is still missing.
- The expected STRING_GNN assets are not present:
  - model weights/config
  - `graph_data.pt`
  - `node_names.json`

## Interpretation

AIDO.Cell-100M itself is usable through the official ModelGenerator classes. That is necessary progress, but it is not yet equivalent to running the public VCHarness best node unchanged.

The next implementation step is not another training run. It is one of:

1. Acquire or reconstruct the official `/home/Models/STRING_GNN` directory expected by the public node.
2. Add an auditable compatibility layer for the AIDO public-node entrypoint:
   - either make the local AIDO model directory AutoModel-compatible with official code mappings,
   - or adapt the public node to the official ModelGenerator `CellFoundationModel` path while recording the deviation.
3. Resolve the tokenizer mismatch explicitly. AIDO.Cell official docs use fixed 19,264-gene expression tensors via gene alignment and preprocessing, not a standard text tokenizer.

Do not train a fallback node and call it the public best-node replication.
