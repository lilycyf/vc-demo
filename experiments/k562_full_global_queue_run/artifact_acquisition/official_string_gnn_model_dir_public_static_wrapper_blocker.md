# Artifact Blocker: official_string_gnn_model_dir for public static wrapper

- Node: `official_k562_root_aido_gnn_embedding_mlp_p10_official_public_static_node_family_wrapper_786354b6`
- Strategy: `official_public_static_node_family_wrapper`
- Artifact id: `official_string_gnn_model_dir`
- Expected path: `/home/Models/STRING_GNN`
- Strict result: blocked, not trained

## Reason

The selected public static node family wrapper must execute source-backed VCHarness public static code through external_static_node. Public static K562 wrappers require /home/Models/STRING_GNN for the official model artifact contract, but /home/Models/STRING_GNN is absent and configs/artifacts/acquisition_sources.json marks official_string_gnn_model_dir as non-automatic/unavailable without a verified source-backed checkpoint or build procedure. A graph file is not an equivalent trained STRING_GNN model.

## Acquisition Status

`configs/artifacts/acquisition_sources.json` records this artifact as requiring Codex research/source-backed acquisition. It explicitly states that the public Hugging Face model repo currently lacks the needed model weights. No automatic resolver is available.

## Policy

No fallback, no compact/native proxy, and no graph-file-as-checkpoint substitute was trained. The global queue should continue with other candidates.
