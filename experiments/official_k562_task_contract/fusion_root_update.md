# Official K562 Fusion Root Update

## What Changed

- Added multi-embedding support to `official_k562_tsv`.
- Added `configs/official_k562_root_aido_gnn_embedding_mlp.json`.
- Added source-backed resolver/registry metadata for `GNN_Simple_Official_(D=256).h5ad`.
- Downloaded the GNN embedding on RunPod for validation, but did not commit the h5ad artifact.

## Smoke Validation

- Official K562 task rows: train `1388`, val `154`, test `421`.
- Target genes: `6640`.
- AIDO embedding dim: `640`.
- GNN embedding dim: `256`.
- Combined feature dim: `896`.

1-epoch smoke results:

| Root | Val Macro-F1 | Test Macro-F1 | Note |
|---|---:|---:|---|
| AIDO embedding MLP | 0.4066 | 0.4302 | single-artifact connectivity smoke |
| AIDO + GNN embedding MLP | 0.3816 | 0.4124 | verifies 640+256 fusion path |

These are not paper-result claims. They are smoke tests proving the official K562 data and artifact-fusion roots execute end to end.

## Remaining Official Best-Node Gap

The public VCHarness best node still expects `/home/Models/AIDO.Cell-100M` and `/home/Models/STRING_GNN`. Hugging Face exposes public `genbio-ai/AIDO.Cell-100M` and `genbio-ai/STRING_GNN` model repositories, but RunPod currently lacks `git-lfs`, so direct model-directory acquisition should be implemented with explicit file-level downloads or a checked `huggingface_hub` snapshot workflow rather than an unverified clone.
