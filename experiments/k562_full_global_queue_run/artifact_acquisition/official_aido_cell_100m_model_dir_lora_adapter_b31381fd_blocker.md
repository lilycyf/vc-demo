# Artifact Blocker: official_aido_cell_100m_model_dir for AIDO LoRA adapter

- Node: `official_k562_root_aido_gnn_embedding_mlp_p6_official_aido_lora_adapter_b31381fd`
- Strategy: `official_aido_lora_adapter`
- Artifact id: `official_aido_cell_100m_model_dir`
- Strict result: blocked, not trained

## Reason

AIDO LoRA adapter requires the real AIDO.Cell-100M AutoModel/AutoTokenizer architecture and layer/module names. /home/Models/AIDO.Cell-100M exists but cannot load model_type=cellfoundation with the available verified code, so LoRA placement cannot be implemented without fallback/proxy code.

No fallback, proxy, cached embedding replacement, or random LoRA target was trained.
