# Complete Paper-Universe Artifact Checklist

This checklist covers every module currently declared in `configs/vcharness_paper_model_universe.json`. K562 is only a demo projection; this artifact inventory is global and task-gated.

## Summary

| Sweep status | Count |
|---|---:|
| `already_present_large_repo_not_redownloaded` | 1 |
| `blocked_unavailable_primary_artifact` | 1 |
| `download_failed_or_blocked` | 1 |
| `downloaded_or_verified` | 16 |
| `no_artifact_required` | 1 |
| `not_acquired_no_verified_direct_public_artifact` | 2 |
| `not_downloaded_builder_needed` | 3 |
| `not_downloaded_non_hf_model_source` | 1 |
| `not_downloaded_source_backed_network_needed` | 1 |
| `not_downloaded_source_backed_table_builder_needed` | 1 |
| `present_public_scaffold` | 1 |
| `present_source_backed_cached_embedding` | 1 |
| `present_source_backed_derived` | 2 |
| `skipped_large_by_policy` | 4 |
| `source_backed_builder_needed` | 2 |
| `source_backed_reimplementation_needed` | 2 |

## Storage And Replay

- Model files live under `/workspace/models/search_space_artifacts` on the RunPod network volume.
- `/home/Models/*` entries are symlinks for code compatibility.
- Model/data/checkpoint artifacts are intentionally not committed to GitHub.
- Replay command:

```bash
bash experiments/search_space_artifact_acquisition_sweep_v2/DOWNLOAD_REPLAY_V2.sh
```

## Full Module Checklist

| Module | Family | Sweep status | Local path | Size GB | Source / repo | Notes |
|---|---|---|---|---:|---|---|
| `AIDO.DNA` | AIDO | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/AIDO.DNA-300M` | 1.201 | `genbio-ai/AIDO.DNA-300M` | Downloaded/verified from primary public source. |
| `AIDO.DNA2` | AIDO | `skipped_large_by_policy` | `/workspace/models/search_space_artifacts/AIDO.DNA-7B` | 0.000 | `genbio-ai/AIDO.DNA-7B` | Estimated repo size exceeds 20.0 GB for this RunPod volume; rerun on larger volume to acquire. |
| `AIDO.Cell 3M` | AIDO.Cell | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/AIDO.Cell-3M` | 0.015 | `genbio-ai/AIDO.Cell-3M` | Downloaded/verified from primary public source. |
| `AIDO.Cell 10M` | AIDO.Cell | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/AIDO.Cell-10M` | 0.044 | `genbio-ai/AIDO.Cell-10M` | Downloaded/verified from primary public source. |
| `AIDO.Cell-100M` | AIDO.Cell | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/AIDO.Cell-100M` | 0.400 | `genbio-ai/AIDO.Cell-100M` | Downloaded/verified from primary public source. |
| `AIDO.Protein` | AIDO.Protein | `skipped_large_by_policy` | `/workspace/models/search_space_artifacts/AIDO.Protein-16B` | 0.000 | `genbio-ai/AIDO.Protein-16B` | Estimated repo size exceeds 20.0 GB for this RunPod volume; rerun on larger volume to acquire. |
| `AIDO Protein 16B / AIDOprot seq+struct` | AIDO.Protein | `skipped_large_by_policy` | `/workspace/models/search_space_artifacts/AIDO.Protein-16B` | 0.000 | `genbio-ai/AIDO.Protein-16B` | Estimated repo size exceeds 20.0 GB for this RunPod volume; rerun on larger volume to acquire. |
| `ProteinRAG 16B + structure` | protein_foundation_model | `not_acquired_no_verified_direct_public_artifact` | `` | 0.000 | `VCHarness task-atlas motif list` | No verified primary model artifact was found during HF search; needs source research or explicit provider/source. |
| `ESM2 35M` | ESM2 | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/ESM2_t12_35M_UR50D` | 0.136 | `facebook/esm2_t12_35M_UR50D` | Downloaded/verified from primary public source. |
| `ESM2 150M` | ESM2 | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/ESM2_t30_150M_UR50D` | 0.595 | `facebook/esm2_t30_150M_UR50D` | Downloaded/verified from primary public source. |
| `ESM2 650M` | ESM2 | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/ESM2_t33_650M_UR50D` | 2.610 | `facebook/esm2_t33_650M_UR50D` | Downloaded/verified from primary public source. |
| `ESM2 3B` | ESM2 | `already_present_large_repo_not_redownloaded` | `/workspace/models/search_space_artifacts/ESM2_t36_3B_UR50D` | 11.367 | `facebook/esm2_t36_3B_UR50D` | Local artifact exists; full repo metadata exceeds 20.0 GB so no duplicate download was attempted. |
| `STRING_GNN official model directory` | STRING_GNN | `blocked_unavailable_primary_artifact` | `/workspace/models/search_space_artifacts/STRING_GNN` | 0.000 | `genbio-ai/STRING_GNN` | Public repo did not expose required model-dir files. |
| `STRING PPI graph / keep20 graph` | STRING | `present_source_backed_derived` | `data/artifacts/string/k562_target_graph_edges.tsv` | 0.000 | `STRING v12 API / official STRING public data.` | Built from public STRING source for K562 target/perturbation vocabulary; not a STRING_GNN model checkpoint. |
| `STRING Spectral` | STRING_variant | `source_backed_builder_needed` | `` | 0.000 | `VCHarness task-atlas motif list` | Can be derived from public STRING graph with a documented spectral embedding builder; no original VCHarness artifact verified. |
| `STRING Seq` | STRING_variant | `source_backed_builder_needed` | `` | 0.000 | `VCHarness task-atlas motif list` | Can be derived from public STRING graph/sequence-neighborhood recipe; no exact original artifact verified. |
| `STRING WaveGC` | STRING_variant | `source_backed_reimplementation_needed` | `` | 0.000 | `VCHarness task-atlas motif list` | Requires graph wavelet convolution implementation/training from public STRING graph; no exact original artifact verified. |
| `STRING Net` | STRING_variant | `source_backed_reimplementation_needed` | `` | 0.000 | `VCHarness task-atlas motif list` | Requires graph-net implementation/training from public STRING graph; no exact original artifact verified. |
| `GNN Simple Official D256` | GNN_embedding | `present_source_backed_cached_embedding` | `data/artifacts/gene_embeddings/GNN_Simple_Official_D256.h5ad` | 0.000 | `genbio-ai/foundation-models-perturbation public dataset.` | Cached official embedding artifact from repo/data prep; not the STRING_GNN model dir. |
| `scFoundation` | single_cell_foundation_model | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/scFoundation_genbio` | 1.433 | `genbio-ai/scFoundation` | Downloaded/verified from primary public source. |
| `scGPT` | single_cell_foundation_model | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/scGPT_tdc` | 0.411 | `tdc/scGPT` | Downloaded/verified from primary public source. |
| `Geneformer` | single_cell_foundation_model | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/Geneformer-V2-104M` | 0.898 | `nvidia/geneformer_V2_104M` | Downloaded/verified from primary public source. |
| `TranscriptFormer` | single_cell_foundation_model | `not_downloaded_non_hf_model_source` | `/workspace/models/search_space_artifacts/TranscriptFormer_repo` | 0.000 | `czi-ai/transcriptformer` | This source is a code repository, not a directly snapshot_download-able HF model artifact in this script. Clone/build instructions are recorded instead. |
| `scPRINT` | single_cell_foundation_model | `skipped_large_by_policy` | `/workspace/models/search_space_artifacts/scPRINT` | 0.000 | `jkobject/scPRINT` | Estimated repo size exceeds 20.0 GB for this RunPod volume; rerun on larger volume to acquire. |
| `GenePT All` | gene_text_embedding | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/GenePT_composable_embeddings` | 5.911 | `honicky/genept-composable-embeddings` | Downloaded/verified from primary public source. |
| `GenePT BP` | gene_text_embedding | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/GenePT_composable_embeddings` | 5.911 | `honicky/genept-composable-embeddings` | Downloaded/verified from primary public source. |
| `GenePT CC` | gene_text_embedding | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/GenePT_composable_embeddings` | 5.911 | `honicky/genept-composable-embeddings` | Downloaded/verified from primary public source. |
| `GenePT MF` | gene_text_embedding | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/GenePT_composable_embeddings` | 5.911 | `honicky/genept-composable-embeddings` | Downloaded/verified from primary public source. |
| `GenePT NCBI` | gene_text_embedding | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/GenePT_composable_embeddings` | 5.911 | `honicky/genept-composable-embeddings` | Downloaded/verified from primary public source. |
| `GenePT N+U` | gene_text_embedding | `downloaded_or_verified` | `/workspace/models/search_space_artifacts/GenePT_composable_embeddings` | 5.911 | `honicky/genept-composable-embeddings` | Downloaded/verified from primary public source. |
| `DepMap` | functional_genomics_prior | `not_downloaded_source_backed_table_builder_needed` | `` | 0.000 | `DepMap public releases / VCHarness task-atlas motif list.` | DepMap is a public data source, not a single model checkpoint; resolver must choose release and align genes/cell lines. |
| `GenotypeVAE` | genotype_prior | `not_acquired_no_verified_direct_public_artifact` | `` | 0.000 | `VCHarness task-atlas motif list.` | No verified direct checkpoint/source was acquired; task-gated unless genotype inputs exist. |
| `Positional 3M` | positional_embedding | `not_downloaded_builder_needed` | `` | 0.000 | `VCHarness task-atlas motif list.` | Requires genomic coordinate source and embedding builder; not a direct HF checkpoint. |
| `Positional 10M` | positional_embedding | `not_downloaded_builder_needed` | `` | 0.000 | `VCHarness task-atlas motif list.` | Requires genomic coordinate source and embedding builder; not a direct HF checkpoint. |
| `Positional 100M` | positional_embedding | `not_downloaded_builder_needed` | `` | 0.000 | `VCHarness task-atlas motif list.` | Requires genomic coordinate source and embedding builder; not a direct HF checkpoint. |
| `AlphaGenome` | sequence_regulatory_model | `download_failed_or_blocked` | `/workspace/models/search_space_artifacts/AlphaGenome_fold_0` | 0.000 | `google/alphagenome-fold-0` | 401 Client Error. (Request ID: Root=1-6a61ed5c-7936c8d61ff4bfc70136b961;b8ae1173-9aef-4ddd-9a8a-d82821d915c5)

Cannot access gated repo for url https://huggingface.co/google/alphagenome-fold-0/resolve/4ce9fd40aa9a3161644efcb69c47551454c6e5ad/.gitattributes.
Access to model google/alphagenome-fold-0 is restricted. You must have access to it and be authenticated to access it. Please log in. |
| `Reactome/pathway memberships` | pathway_prior | `present_source_backed_derived` | `data/artifacts/pathways/k562_target_pathway_membership.npz` | 0.000 | `Reactome public pathway database or equivalent source-backed pathway release.` | Reactome/pathway target membership artifact is built per cell-line target order. |
| `Regulatory network prior` | regulatory_prior | `not_downloaded_source_backed_network_needed` | `` | 0.000 | `Public regulatory network source to be selected by acquisition resolver.` | Requires chosen public regulatory network source and cell-line/gene alignment; no fabricated edges. |
| `No pretrained / scratch baseline` | baseline | `no_artifact_required` | `` | 0.000 | `Baseline control.` | Baseline control; no model download. |
| `Public VCHarness static tree nodes` | public_static_tree | `present_public_scaffold` | `/workspace/_external/VCHarness` | 0.000 | `https://github.com/genbio-ai/VCHarness.` | Public static scaffold available; exact execution can still block on hidden model dirs such as STRING_GNN. |

## Important Blockers

- `STRING_GNN official model directory`: public `genbio-ai/STRING_GNN` exposes only `.gitattributes`; required model-dir files are absent, so this remains blocked unavailable primary artifact.
- `AlphaGenome`: public metadata is visible but model repos are gated and require authenticated access/approval.
- `AIDO.DNA-7B`, `AIDO.Protein-16B`, and full `jkobject/scPRINT`: public metadata exists, but the current RunPod volume hit write quota. They are not scientifically unavailable; acquire on a larger volume or after freeing space.
- `TranscriptFormer`, `DepMap`, positional priors, regulatory priors, and STRING variants beyond the graph: these require source-backed builders/resolvers rather than direct model snapshot downloads.
