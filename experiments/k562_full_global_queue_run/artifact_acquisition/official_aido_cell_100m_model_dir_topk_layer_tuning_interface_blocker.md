# Artifact Blocker: official_aido_cell_100m_model_dir for top-k layer tuning

- Node: `official_k562_root_aido_gnn_embedding_mlp_p2_official_aido_topk_layer_tuning_73e7b933`
- Strategy: `official_aido_topk_layer_tuning`
- Artifact id: `official_aido_cell_100m_model_dir`
- Expected path: `/home/Models/AIDO.Cell-100M`
- Strict result: blocked, not trained

## Reason

AIDO top-k layer tuning requires the real AIDO.Cell-100M layer stack and tokenizer/model architecture. /home/Models/AIDO.Cell-100M contains weights/config but AutoModel/AutoTokenizer cannot load model_type=cellfoundation, so top-k trainable layers cannot be identified or fine-tuned without unverifiable/fallback code.

## Policy

No fallback, proxy, cached-embedding replacement, or random layer surrogate was trained. The global queue should continue with other feasible candidates.
