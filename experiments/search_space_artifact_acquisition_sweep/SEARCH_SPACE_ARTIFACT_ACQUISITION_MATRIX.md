# Search Space Artifact Acquisition Sweep

This file records public-source acquisition status for the current VCHarness-style search space. Large model/data files are stored on the RunPod network volume under `/workspace/models/search_space_artifacts`; they must not be committed to GitHub.

## Storage Policy

- Large artifacts: `/workspace/models/search_space_artifacts` and `/home/Models` symlinks.
- GitHub: only this metadata, replay script, registry/audit notes, and blocker reports.
- Forbidden in git: `data/`, `nodes/`, checkpoints, weights, `.pt`, `.pth`, `.ckpt`, `.bin`, `.safetensors`, `.h5ad`, `.npz`, `/home/Models`, `/workspace/models`.

## Summary Table

| Artifact | Source | Status | Local path | Required files | Size | Rebuild/training estimate | Notes |
|---|---|---|---|---|---:|---|---|
| `official_aido_cell_100m_model_dir` | `genbio-ai/AIDO.Cell-100M` | `acquired_public_source` | `/workspace/models/search_space_artifacts/AIDO.Cell-100M` | config.json, model.safetensors | 0.37 GB | 不需要自训；可直接下载。若任务级 LoRA/adapter，0.5-3 天。 | AIDO cell foundation backbone / LoRA / adapter / cached embedding generation |
| `official_string_gnn_model_dir` | `genbio-ai/STRING_GNN` | `blocked_unavailable_primary_artifact` | `/workspace/models/search_space_artifacts/STRING_GNN_OFFICIAL_UNAVAILABLE` | config.json, model.safetensors, pytorch_model.bin, graph_data.pt, node_names.json | 0.00 GB | 官方 checkpoint 不可验证公开。source-backed 最小重建 1-2 天；较靠谱 GNN 3-7 天；接近论文级 1-3 周且不保证数值等价。 | Official public VCHarness STRING_GNN AutoModel.from_pretrained(/home/Models/STRING_GNN) branch Missing in public source: config.json, model.safetensors, pytorch_model.bin, graph_data.pt, node_names.json. |
| `scfoundation_model_checkpoint_genbio` | `genbio-ai/scFoundation` | `acquired_public_source` | `/workspace/models/search_space_artifacts/scFoundation_genbio` | models.ckpt | 1.33 GB | checkpoint 已下载；还需 K562 row-aligned embedding/encoder contract，1-3 天。任务级 fine-tune 2-5 天。 | single-cell foundation model artifact; needs downstream K562 row-aligned embedding build before strict use |
| `scfoundation_cell_model_perturblab` | `perturblab/scfoundation-cell` | `acquired_public_source` | `/workspace/models/search_space_artifacts/scfoundation-cell` | config.json, model.pt | 0.44 GB | 替代 checkpoint 已下载；适配 K562 contract 1-3 天。 | alternative public scFoundation-style cell encoder checkpoint |
| `single_cell_foundation_model_scgpt` | `tdc/scGPT` | `acquired_public_source` | `/workspace/models/search_space_artifacts/scGPT_tdc` | config.json, model.safetensors | 0.19 GB | checkpoint 已下载；K562 tokenization/row contract 1-3 天，稳定 fine-tune 2-5 天。 | single-cell foundation encoder alternative; needs K562 tokenization/row contract adapter |
| `geneformer_v2_104m` | `ctheodoris/Geneformer` | `acquired_public_source` | `/workspace/models/search_space_artifacts/Geneformer-V2-104M` | Geneformer-V2-104M/config.json, Geneformer-V2-104M/model.safetensors | 0.39 GB | checkpoint 已下载；K562 tokenization/embedding 1-3 天，fine-tune 2-5 天。 | single-cell/gene foundation encoder alternative |
| `esm2_650m_protein_embedding_model` | `facebook/esm2_t33_650M_UR50D` | `acquired_public_source` | `/workspace/models/search_space_artifacts/esm2_t33_650M_UR50D` | config.json, model.safetensors, vocab.txt | 2.43 GB | 可直接用；K562 target/perturbation protein embedding 0.5-1 天。 | protein/gene product embedding branch for perturbation/target genes |
| `scprint_medium_checkpoint` | `jkobject/scPRINT` | `acquired_public_source` | `/workspace/models/search_space_artifacts/scPRINT_medium` | medium-v1.5.ckpt | 0.45 GB | checkpoint 已下载；loader/ontology/GRN contract 2-5 天。 | single-cell foundation / GRN-capable alternative; needs strict loader integration before use |
| `genept_original_ada_embedding` | `honicky/genept-composable-embeddings` | `acquired_public_source` | `/workspace/models/search_space_artifacts/GenePT_original_ada` | embedding_original_ada_text.parquet | 0.54 GB | embedding 已下载；gene alignment 0.5-1 天，不需要训练。 | gene-language embedding prior; needs target/perturbation gene ID alignment |

## Download Replay

Run from `/workspace/vc-demo` on a RunPod with the network volume mounted:

```bash
bash experiments/search_space_artifact_acquisition_sweep/DOWNLOAD_REPLAY.sh
```

## Blockers

### official_string_gnn_model_dir

- Source checked: `genbio-ai/STRING_GNN`
- Status: `blocked_unavailable_primary_artifact`
- Missing required files: `config.json, model.safetensors, pytorch_model.bin, graph_data.pt, node_names.json`
- Strict rule: do not substitute graph files, cached embeddings, random weights, or compact/proxy modules for this official checkpoint.

## Symlinks

```json
{
  "links": [
    {
      "artifact_id": "official_aido_cell_100m_model_dir",
      "link": "/home/Models/AIDO.Cell-100M",
      "status": "linked",
      "target": "/workspace/models/search_space_artifacts/AIDO.Cell-100M"
    },
    {
      "artifact_id": "scfoundation_model_checkpoint_genbio",
      "link": "/home/Models/scFoundation",
      "status": "linked",
      "target": "/workspace/models/search_space_artifacts/scFoundation_genbio"
    },
    {
      "artifact_id": "scfoundation_cell_model_perturblab",
      "link": "/home/Models/scfoundation-cell",
      "status": "linked",
      "target": "/workspace/models/search_space_artifacts/scfoundation-cell"
    },
    {
      "artifact_id": "single_cell_foundation_model_scgpt",
      "link": "/home/Models/scGPT",
      "status": "linked",
      "target": "/workspace/models/search_space_artifacts/scGPT_tdc"
    },
    {
      "artifact_id": "geneformer_v2_104m",
      "link": "/home/Models/Geneformer-V2-104M",
      "status": "linked",
      "target": "/workspace/models/search_space_artifacts/Geneformer-V2-104M"
    },
    {
      "artifact_id": "esm2_650m_protein_embedding_model",
      "link": "/home/Models/ESM2_t33_650M_UR50D",
      "status": "linked",
      "target": "/workspace/models/search_space_artifacts/esm2_t33_650M_UR50D"
    },
    {
      "artifact_id": "scprint_medium_checkpoint",
      "link": "/home/Models/scPRINT_medium",
      "status": "linked",
      "target": "/workspace/models/search_space_artifacts/scPRINT_medium"
    },
    {
      "artifact_id": "genept_original_ada_embedding",
      "link": "/home/Models/GenePT_original_ada",
      "status": "linked",
      "target": "/workspace/models/search_space_artifacts/GenePT_original_ada"
    }
  ]
}
```
