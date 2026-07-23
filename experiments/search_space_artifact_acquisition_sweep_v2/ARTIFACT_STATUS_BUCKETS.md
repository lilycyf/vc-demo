# Paper-Universe Artifact Status Buckets

This file summarizes the artifact acquisition status for the current VCHarness paper-universe sweep. K562 is only a demo projection; these artifacts belong to the global paper-level search universe and must be task-gated for each future cell line or task.

## Already Prepared And Reusable

These artifacts are downloaded, verified, already present, or do not require a model artifact. They can be reused from the RunPod network volume or rebuilt through the replay script.

| Module | Status | RunPod path / note |
|---|---|---|
| AIDO.Cell-3M | downloaded | `/home/Models/AIDO.Cell-3M` |
| AIDO.Cell-10M | downloaded | `/home/Models/AIDO.Cell-10M` |
| AIDO.Cell-100M | downloaded | `/home/Models/AIDO.Cell-100M` |
| AIDO.DNA-300M | downloaded | `/home/Models/AIDO.DNA-300M` |
| ESM2 35M | downloaded | `/home/Models/ESM2_t12_35M_UR50D` |
| ESM2 150M | downloaded | `/home/Models/ESM2_t30_150M_UR50D` |
| ESM2 650M | downloaded | `/home/Models/ESM2_t33_650M_UR50D` |
| ESM2 3B | already present and verified | `/home/Models/ESM2_t36_3B_UR50D` |
| scFoundation | downloaded | `/home/Models/scFoundation` |
| scFoundation-cell | downloaded | `/home/Models/scfoundation-cell` |
| scGPT | downloaded | `/home/Models/scGPT` |
| Geneformer V2 104M | downloaded | `/home/Models/Geneformer-V2-104M` |
| GenePT composable embeddings | downloaded | `/home/Models/GenePT_composable_embeddings` |
| GenePT original ada | previously downloaded | `/home/Models/GenePT_original_ada` |
| scPRINT medium | previously downloaded | `/home/Models/scPRINT_medium` |
| STRING PPI graph | source-backed derived artifact | `data/artifacts/string/k562_target_graph_edges.tsv` |
| GNN Simple Official D256 | cached official embedding | `data/artifacts/gene_embeddings/GNN_Simple_Official_D256.h5ad` |
| Reactome/pathway memberships | source-backed derived artifact | `data/artifacts/pathways/k562_target_pathway_membership.npz` |
| Public VCHarness static tree | public scaffold present | `/workspace/_external/VCHarness` |
| Scratch baseline | no artifact needed | baseline/control only |

## Public But Not Downloaded Because Of Current Storage Quota

These are not scientific blockers. Public metadata/source exists, but the current RunPod volume hit a write quota around the present model set. Use a larger network volume, or free space, then rerun the downloader without `--skip-large --large-threshold-gb 20`.

| Module | Public source | Approx. repo size | Why not downloaded now |
|---|---|---:|---|
| AIDO.DNA-7B / AIDO.DNA2 | `genbio-ai/AIDO.DNA-7B` | ~58 GB | current RunPod writable quota insufficient |
| AIDO.Protein-16B / AIDOprot | `genbio-ai/AIDO.Protein-16B` | ~64 GB | current RunPod writable quota insufficient |
| Full scPRINT | `jkobject/scPRINT` | ~29 GB | current RunPod writable quota insufficient; medium checkpoint is already available separately |

## Not Directly Downloadable Or Not Directly Usable Even With More Space

These require authorization, missing primary files, or source-backed builders/reimplementations. Do not mark them as `present` just because a related graph, cache, or repository exists.

| Module | Current conclusion | What would be required |
|---|---|---|
| STRING_GNN official model directory | blocked unavailable primary artifact | `genbio-ai/STRING_GNN` exposes only `.gitattributes`; need real model dir with config/weights/`graph_data.pt`/`node_names.json`, or a separately labeled source-backed reimplementation |
| AlphaGenome | gated | HF metadata visible, but access requires authenticated approval/token |
| ProteinRAG 16B + structure | no verified direct public artifact found | source research or provider-approved artifact; do not substitute generic protein embeddings |
| TranscriptFormer | not a direct HF model snapshot in this downloader | clone/source build instructions and a verified checkpoint/encoder contract |
| DepMap | public data source, not checkpoint | choose release, download tables, align genes/cell lines, build resolver |
| GenotypeVAE | no verified direct checkpoint/source acquired | source-backed checkpoint or genotype-data training flow; task-gated unless genotype inputs exist |
| Positional 3M/10M/100M | builder needed | genome coordinate source, genome build, embedding recipe, target-gene alignment |
| Regulatory network prior | source-backed network needed | choose public regulatory network source, verify provenance, align vocabulary, build artifact |
| STRING Spectral | builder needed | derive spectral features from source-backed STRING graph with documented method |
| STRING Seq | builder needed | derive sequence/neighborhood features from source-backed STRING graph with documented recipe |
| STRING WaveGC | source-backed reimplementation needed | implement/train graph wavelet convolution from public STRING graph; do not call simple Laplacian WaveGC |
| STRING Net | source-backed reimplementation needed | implement/train documented graph-net from public STRING graph |

## Replay

Default replay for this RunPod volume:

```bash
bash experiments/search_space_artifact_acquisition_sweep_v2/DOWNLOAD_REPLAY_V2.sh
```

To acquire the large public artifacts, use a larger network volume and remove these flags from the replay script:

```bash
--skip-large --large-threshold-gb 20
```

## Git Policy

Model files stay on the RunPod network volume under:

```text
/workspace/models/search_space_artifacts
```

They are intentionally not committed to GitHub. The repo only commits scripts, manifests, Markdown reports, and small JSON metadata.
