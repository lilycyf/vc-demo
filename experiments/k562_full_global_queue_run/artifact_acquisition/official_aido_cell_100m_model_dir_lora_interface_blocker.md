# AIDO.Cell-100M LoRA Interface Blocker

- Node: `official_k562_root_aido_gnn_embedding_mlp_p3_official_aido_lora_adapter_e12bdb28`
- Blueprint: `official_aido_lora_adapter`
- Artifact: `official_aido_cell_100m_model_dir`
- Expected path: `/home/Models/AIDO.Cell-100M`
- Decision: `blocked_unavailable_or_incomplete_interface`

## Checks Performed

- Verified `/home/Models/AIDO.Cell-100M` exists with `config.json`, `generation_config.json`, `model.safetensors`, `README.md`, and `LICENSE`.
- Inspected public VCHarness K562 static code; AIDO LoRA nodes call `AutoTokenizer.from_pretrained(AIDO_MODEL_DIR, trust_remote_code=True)` and `AutoModel.from_pretrained(AIDO_MODEL_DIR, trust_remote_code=True)`.
- Attempted both loads on RunPod; both failed because Transformers does not recognize `model_type=cellfoundation`.

## Reason

/home/Models/AIDO.Cell-100M contains config.json and model.safetensors, but Transformers cannot load model_type=cellfoundation or tokenizer with trust_remote_code=True in this environment. The public VCHarness LoRA implementation requires AutoModel/AutoTokenizer for AIDO.Cell-100M, so the artifact is incomplete for faithful LoRA fine-tuning. No fallback/proxy model was trained.

## Guardrail

Strict mode forbids replacing the AIDO backbone with cached embeddings, random layers, compact approximations, or proxy helpers. This node is blocked and the global queue should continue with other feasible candidates.
