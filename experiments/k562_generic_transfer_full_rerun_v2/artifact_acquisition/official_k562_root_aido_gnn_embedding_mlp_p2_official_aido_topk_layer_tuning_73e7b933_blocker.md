# Strict Artifact Blocker: official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_73e7b933

- strategy: `official_aido_topk_layer_tuning`
- artifact: `official_aido_cell_100m_model_dir`
- expected path: `/home/Models/AIDO.Cell-100M`
- blocker: selected top-k layer tuning requires real AIDO.Cell-100M layer modules and tokenizer/runtime code. The existing model directory is present but not verified loadable as `cellfoundation` in the installed runtime.
- strict decision: no fallback/proxy/cached-embedding substitute was trained.
- next action: acquire verified source-backed AIDO runtime code compatible with the public VCHarness implementation.
