# Artifact Blocker: official_aido_cell_100m_model_dir for full fine-tune

- Node: `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f54f7d63`
- Strategy: `official_aido_full_finetune`
- Artifact id: `official_aido_cell_100m_model_dir`
- Expected path: `/home/Models/AIDO.Cell-100M`
- Observed files: `config.json`, `generation_config.json`, `model.safetensors`, `README.md`, `LICENSE`
- Strict result: blocked, not trained

## Reason

AIDO.Cell-100M directory exists but is not loadable as a real AutoModel/AutoTokenizer artifact: Transformers reports unknown model_type cellfoundation; architecture/tokenizer code is missing or unverifiable. Strict full fine-tune cannot be implemented without the real public model interface.

## Validation Attempt

`AutoTokenizer.from_pretrained(..., trust_remote_code=True)` / `AutoModel.from_pretrained(..., trust_remote_code=True)` failed because the local Transformers install does not recognize `model_type=cellfoundation` and the directory does not include verifiable remote-code model/tokenizer implementation files.

## Policy

No fallback, proxy, or cached-embedding substitute was trained for this full-finetune blueprint. The search should continue with other queued candidates.
