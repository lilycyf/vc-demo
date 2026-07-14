# Strict Artifact Blocker: official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_full_finetune_f54f7d63

- strategy: `official_aido_full_finetune`
- artifact: `official_aido_cell_100m_model_dir`
- expected path: `/home/Models/AIDO.Cell-100M`
- resolver result: path exists / selected files present
- blocker: the artifact is not verified loadable for full fine-tuning because the HuggingFace config uses model type `cellfoundation`, which is not recognized by the installed Transformers runtime and no source-backed architecture/tokenizer interface was available in the repo runbook.
- strict decision: no node-local fallback model was written; no cached embedding substitute was trained for this full-finetune blueprint.
- next required action: acquire the exact public VCHarness/ModelGenerator AIDO.Cell-100M runtime code or a verified AutoModel-compatible package for `cellfoundation`.
