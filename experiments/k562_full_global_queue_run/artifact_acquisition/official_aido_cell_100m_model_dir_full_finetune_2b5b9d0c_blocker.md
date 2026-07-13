# Artifact Blocker: AIDO full fine-tune

- Node: `official_k562_root_aido_gnn_embedding_mlp_p12_official_aido_full_finetune_2b5b9d0c`
- Artifact: `official_aido_cell_100m_model_dir`
- Strict result: blocked, not trained

AIDO full fine-tune requires a verifiable AIDO.Cell-100M AutoModel/AutoTokenizer implementation and layer stack. The available /home/Models/AIDO.Cell-100M checkpoint has model_type=cellfoundation but no loadable verified architecture/tokenizer code, so strict fine-tuning cannot proceed without fallback/proxy code.

No fallback/proxy/cached-embedding replacement was trained.
