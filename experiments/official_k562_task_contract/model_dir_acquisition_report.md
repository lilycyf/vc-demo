# Official Model Directory Acquisition Report

## AIDO.Cell-100M

Downloaded selected public files from `genbio-ai/AIDO.Cell-100M` to `/home/Models/AIDO.Cell-100M`.

- Repo SHA: `b14a88b962758102e618289f4340f989bd6eebe5`
- Gated: `False`
- Private: `False`
- Downloaded files: `config.json, generation_config.json, model.safetensors, README.md, LICENSE`
- Total bytes: `399497468`

Validation status: `usable_with_warnings`.

Warnings:

- no tokenizer files detected; public VCHarness code calls AutoTokenizer.from_pretrained, so runtime equivalence is not yet proven

The directory now contains a config and safetensors weight file, so the artifact registry marks `official_aido_cell_100m_model_dir` as present. However, the public VCHarness best-node code calls `AutoTokenizer.from_pretrained(AIDO_MODEL_DIR)`, and the HF file list did not expose tokenizer files. Therefore this is a source-backed model directory acquisition with a tokenizer/runtime-equivalence warning, not yet a full best-node runtime proof.

## STRING_GNN

Checked public model repo `genbio-ai/STRING_GNN`.

- Repo exists and is public/non-gated.
- HF API currently lists only `.gitattributes`.
- No checkpoint/config/embedding model files were exposed through the model repo API.

Validation status: `missing`.

Warnings:

- directory does not exist; Hugging Face repo currently lists no weight files

The repo still has source-backed alternatives for graph/fusion work:

- `data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt`
- `data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad`

These are not the same as `/home/Models/STRING_GNN`.

## Registry State After Acquisition

- Present artifacts: `esm2_gene_embedding_h5ad, esm2_k562_target_manifest, string_k562_gene_graph, pathway_membership_matrix, official_essential_deg_with_split_h5ad, official_k562_aido_cell_100m_embedding_h5ad, official_string_gnn_keep20_graph, official_aido_cell_100m_model_dir, official_gnn_simple_embedding_h5ad`
- Missing artifacts: `aido_gene_or_cell_embeddings, scfoundation_cell_embeddings, official_string_gnn_model_dir`

## Next Step

The next implementation step is to create a VCHarness best-node compatibility runner that checks imports (`transformers`, `peft`, tokenizer availability, custom architecture loading) before attempting training. If tokenizer/model-class loading fails, the blocker should be recorded explicitly rather than replaced with a fallback.
