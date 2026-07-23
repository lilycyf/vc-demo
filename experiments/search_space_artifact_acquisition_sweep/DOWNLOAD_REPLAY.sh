#!/usr/bin/env bash
set -euo pipefail
python -m pip install -q huggingface_hub hf_transfer requests tqdm
export HF_HUB_ENABLE_HF_TRANSFER=1
mkdir -p /workspace/models/search_space_artifacts /home/Models

# official_aido_cell_100m_model_dir - AIDO.Cell-100M
hf download genbio-ai/AIDO.Cell-100M --type model --local-dir /workspace/models/search_space_artifacts/AIDO.Cell-100M --include 'config.json' --include 'generation_config.json' --include 'model.safetensors' --include 'README.md' --include 'LICENSE' --include '*.png'
ln -sfn /workspace/models/search_space_artifacts/AIDO.Cell-100M /home/Models/AIDO.Cell-100M

# scfoundation_model_checkpoint_genbio - GenBio scFoundation checkpoint
hf download genbio-ai/scFoundation --type model --local-dir /workspace/models/search_space_artifacts/scFoundation_genbio --include 'README.md' --include 'models.ckpt'
ln -sfn /workspace/models/search_space_artifacts/scFoundation_genbio /home/Models/scFoundation

# scfoundation_cell_model_perturblab - PerturbLab scFoundation cell model
hf download perturblab/scfoundation-cell --type model --local-dir /workspace/models/search_space_artifacts/scfoundation-cell --include 'README.md' --include 'config.json' --include 'model.pt'
ln -sfn /workspace/models/search_space_artifacts/scfoundation-cell /home/Models/scfoundation-cell

# single_cell_foundation_model_scgpt - scGPT public checkpoint
hf download tdc/scGPT --type model --local-dir /workspace/models/search_space_artifacts/scGPT_tdc --include 'README.md' --include 'config.json' --include 'model.safetensors'
ln -sfn /workspace/models/search_space_artifacts/scGPT_tdc /home/Models/scGPT

# geneformer_v2_104m - Geneformer V2 104M
hf download ctheodoris/Geneformer --type model --local-dir /workspace/models/search_space_artifacts/Geneformer-V2-104M --include 'README.md' --include 'Geneformer-V2-104M/config.json' --include 'Geneformer-V2-104M/generation_config.json' --include 'Geneformer-V2-104M/model.safetensors' --include 'Geneformer-V2-104M/training_args.bin'
ln -sfn /workspace/models/search_space_artifacts/Geneformer-V2-104M /home/Models/Geneformer-V2-104M

# esm2_650m_protein_embedding_model - ESM2 650M
hf download facebook/esm2_t33_650M_UR50D --type model --local-dir /workspace/models/search_space_artifacts/esm2_t33_650M_UR50D --include 'README.md' --include 'config.json' --include 'model.safetensors' --include 'special_tokens_map.json' --include 'tokenizer_config.json' --include 'vocab.txt'
ln -sfn /workspace/models/search_space_artifacts/esm2_t33_650M_UR50D /home/Models/ESM2_t33_650M_UR50D

# scprint_medium_checkpoint - scPRINT medium checkpoint
hf download jkobject/scPRINT --type model --local-dir /workspace/models/search_space_artifacts/scPRINT_medium --include 'README.md' --include 'medium-v1.5.ckpt' --include 'TFs.txt' --include 'attention_bias.npz'
ln -sfn /workspace/models/search_space_artifacts/scPRINT_medium /home/Models/scPRINT_medium

# genept_original_ada_embedding - GenePT original Ada gene embeddings
hf download honicky/genept-composable-embeddings --type model --local-dir /workspace/models/search_space_artifacts/GenePT_original_ada --include 'README.md' --include 'embedding_original_ada_text.parquet'
ln -sfn /workspace/models/search_space_artifacts/GenePT_original_ada /home/Models/GenePT_original_ada

