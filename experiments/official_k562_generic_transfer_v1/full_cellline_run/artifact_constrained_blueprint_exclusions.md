# Artifact-Constrained Blueprint Exclusions

- Cell line: `K562`
- Run level: `full_cellline_run`
- Policy: source-backed artifacts only; no fallback/proxy training.
- Excluded blueprints: `10`

## Blocked Artifacts

### `official_string_gnn_model_dir`

- Expected path: `/home/Models/STRING_GNN`
- Reason: Public genbio-ai/STRING_GNN repository exposes no source-backed model weights/config through the Hugging Face API; graph TSV/H5AD artifacts are not an equivalent model directory.
- Policy: exclude dependent blueprints from the main full run and report separately; no fallback/proxy training

## Excluded Blueprints

- `official_native_public_best_reimplementation` (public_vcharness_best_path_native_exact) requires official_string_gnn_model_dir
- `official_public_best_node` (public_vcharness_best_path) requires official_string_gnn_model_dir
- `official_string_gnn_attention` (STRING_GNN_attention) requires official_string_gnn_model_dir
- `official_aido_string_fusion` (AIDO_STRING_fusion) requires official_string_gnn_model_dir
- `official_string_gnn_frozen_cache` (STRING_GNN_frozen_cached) requires official_string_gnn_model_dir
- `official_string_gnn_full_finetune` (STRING_GNN_full_finetune) requires official_string_gnn_model_dir
- `official_aido_string_concat_fusion` (AIDO_STRING_concat) requires official_string_gnn_model_dir
- `official_aido_string_gated_fusion` (AIDO_STRING_gated) requires official_string_gnn_model_dir
- `official_aido_string_cross_attention` (AIDO_STRING_cross_attention) requires official_string_gnn_model_dir
- `official_aido_string_bilinear_fusion` (AIDO_STRING_bilinear) requires official_string_gnn_model_dir
