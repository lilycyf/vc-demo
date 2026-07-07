# Official Model Directory Acquisition

The public VCHarness K562 best node expects two local model directories:

- `/home/Models/AIDO.Cell-100M`
- `/home/Models/STRING_GNN`

This repo now includes `scripts/download_hf_model_snapshot.py`, a small downloader that uses the Hugging Face HTTP API directly and does not require `git-lfs` or `huggingface_hub`.

## AIDO.Cell-100M

Hugging Face model repo: `genbio-ai/AIDO.Cell-100M`.

Observed public files:

- `config.json`
- `generation_config.json`
- `model.safetensors`
- `pytorch_model.bin`
- `README.md`
- `LICENSE`

The resolver downloads the safetensors path plus config/docs to `/home/Models/AIDO.Cell-100M`. The public VCHarness code calls `AutoTokenizer.from_pretrained(AIDO_MODEL_DIR)`, but the HF file list did not expose tokenizer assets, so runtime equivalence to the original RunPod image still requires a tokenizer check.

## STRING_GNN

Hugging Face model repo: `genbio-ai/STRING_GNN`.

The API currently lists only `.gitattributes`. That means the model repo exists, but no usable weights are exposed through this public snapshot. The repo also has source-backed graph and embedding alternatives:

- `gnn/9606.protein.links.ensembl_900_keep20_adaptive.txt`
- `gene_embeddings/GNN_Simple_Official_(D=256).h5ad`

These are useful for embedding/fusion baselines, but they are not the same as `/home/Models/STRING_GNN`.
