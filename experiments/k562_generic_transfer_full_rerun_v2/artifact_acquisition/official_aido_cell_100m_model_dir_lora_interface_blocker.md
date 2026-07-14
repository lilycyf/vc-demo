# AIDO.Cell-100M LoRA Interface Blocker

Node: `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28`

Artifact: `official_aido_cell_100m_model_dir`

Expected path: `/home/Models/AIDO.Cell-100M`

Reason: /home/Models/AIDO.Cell-100M exists but cannot be loaded as a real AutoModel/AutoTokenizer artifact: Transformers reports unknown model_type cellfoundation and the model directory contains no verified remote architecture/tokenizer code. Strict LoRA cannot be implemented without the real AIDO.Cell-100M interface; h5ad embeddings or compact MLPs would be proxy/fallback.

Sources/files checked:

- `/home/Models/AIDO.Cell-100M/config.json`
- `/home/Models/AIDO.Cell-100M/model.safetensors`
- `transformers.AutoConfig/AutoModel/AutoTokenizer(..., trust_remote_code=True)`

Outcome: blocked until the official loadable `cellfoundation` architecture/tokenizer code or a complete source-backed AIDO.Cell-100M model package is available. No fallback model was trained.
