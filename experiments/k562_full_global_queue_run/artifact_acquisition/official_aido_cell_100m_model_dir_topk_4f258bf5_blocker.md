# Artifact Blocker: AIDO top-k layer tuning

- Node: `official_k562_root_aido_gnn_embedding_mlp_p8_official_aido_topk_layer_tuning_4f258bf5`
- Artifact: `official_aido_cell_100m_model_dir`
- Strict result: blocked, not trained

AIDO top-k layer tuning requires verifiable AIDO.Cell-100M layer/module code. The available checkpoint directory cannot load model_type=cellfoundation via verified AutoModel/AutoTokenizer, so no source-backed layer selection is possible.

No fallback/proxy was trained.
