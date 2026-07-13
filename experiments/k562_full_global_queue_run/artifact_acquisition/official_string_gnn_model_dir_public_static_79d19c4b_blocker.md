# Artifact Blocker: public static wrapper STRING_GNN

- Node: `official_k562_root_aido_gnn_embedding_mlp_p8_official_public_static_node_family_wrapper_79d19c4b`
- Artifact: `official_string_gnn_model_dir`
- Strict result: blocked, not trained

Public static VCHarness wrappers require the real /home/Models/STRING_GNN trained model directory. That directory is absent, and acquisition_sources marks official_string_gnn_model_dir as non-automatic/unavailable without verifiable model weights; graph source files are not equivalent checkpoints.

No fallback/proxy was trained.
