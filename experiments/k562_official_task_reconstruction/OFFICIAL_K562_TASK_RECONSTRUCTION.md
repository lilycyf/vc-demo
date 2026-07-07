# Official K562 Task Reconstruction Audit

## Executive conclusion

This audit finds that our current K562 demo is framework-aligned with VCHarness, but it is not yet a numeric reproduction of the official VCHarness K562 classification task. The official public K562 tree exposes enough code and memory to establish a different task geometry: 6,640 output genes, 1,388 training samples, three DEG classes, per-gene Macro-F1, and best-node architectures built around AIDO.Cell-100M plus STRING_GNN neighborhood attention. Our current K562 task uses a Norman/scPerturb-derived local split with 105 perturbation rows and 1,000 target genes.

Therefore the next implementation objective is not another search run. It is an official-task data reconstruction layer: prepare the official K562 train.tsv, val.tsv, test.tsv equivalent, align the 6,640 target-gene universe, and acquire/checkpoint the official model artifacts used by the best public node.

## Official VCHarness K562 facts observed

Source inspected: /workspace/_external/VCHarness/K562_cls, cloned from https://github.com/genbio-ai/VCHarness. The public repo says this case study covers Essential dataset classification tracks including K562.

- MCTS metadata:
  - total nodes: 153
  - draft nodes: 4
  - improvement nodes: 149
  - current step: 153
  - exploration constant: 1.4142135623730951
  - best score: 0.5128
  - global best node: node2-1-1-1-1-1
- Public artifact files:
  - memory markdown files: 153
  - node code files: 154
  - curve images: 153
- Code constants found repeatedly:
  - N_GENES: {'6640': 154}
  - N_CLASSES: {'3': 154}
  - CLASS_FREQ: {'[0.0429, 0.9251, 0.032]': 154}
  - AIDO_MODEL_DIR: {"'/home/Models/AIDO.Cell-100M'": 29, "'/home/Models/AIDO.Cell-10M'": 5}
  - STRING_MODEL_DIR: {"'/home/Models/STRING_GNN'": 19}
  - split file constants: train.tsv, val.tsv, test.tsv
- Regex evidence counts across official memory/code:
  - 6,640 target-gene evidence lines: 496
  - 1,388 training-sample evidence lines: 170
  - AIDO evidence lines: 2358
  - scFoundation evidence lines: 686
  - STRING/STRING_GNN evidence lines: 5352
  - metric evidence lines: 1587

## Official best-node architecture

Best node: node2-1-1-1-1-1.

Visible header from official code identifies it as AIDO.Cell-100M with LoRA plus STRING_GNN K=16 multi-head neighborhood attention and a 2-layer head. Important constants in that node include:

- N_GENES = 6640
- N_CLASSES = 3
- AIDO_MODEL_DIR = /home/Models/AIDO.Cell-100M
- STRING_MODEL_DIR = /home/Models/STRING_GNN
- AIDO_HIDDEN = 640
- STRING_HIDDEN = 256
- NEIGHBOR_K = 16
- N_ATTN_HEADS = 2
- CLASS_FREQ = [0.0429, 0.9251, 0.0320]
- TRAIN_TSV, VAL_TSV, TEST_TSV under data/

The official node memory reports test/validation F1 0.5128, best validation at epoch 77, and early stopping after 88 epochs. It also records that the improvement over its parent came from reducing STRING_GNN neighborhood size from K=24 to K=16, simplifying the head, restoring stronger dropout, and keeping 2-head neighborhood attention.

## Our current K562 facts

Current repo manifest inspected: data/cell_lines/k562_concat_esm2_gene_embedding/manifest.json.

- Source: NormanWeissman2019_filtered.h5ad from scPerturb Zenodo record 7041849
- Cell line/task: K562 / CRISPR_KO_DEG_classification
- Feature set: onehot_plus_delta_expression_plus_ESM2_D1280
- Perturbations: 105
- Features: 2385
- Target genes: 1000
- Split sizes: {'train': 73, 'val': 16, 'test': 16}
- Label rule: per perturbation, delta vs control mean expression; <=5th percentile down, >=95th percentile up, otherwise unchanged
- Target-gene selection: top 1000 genes by ncells then ncounts among expressed genes

The previous 50-node run in this repo showed the framework can execute MCTS/UCT search, strict artifacts, on-demand model implementation, STRING graph nodes, Reactome pathway nodes, and final reporting. But the best model stayed a perturbation-side ESM2 gated MLP root, and the run stopped after 13 trained nodes because no child improved validation Macro-F1 within the small local task.

## Match and mismatch table

| Dimension | Official public K562 evidence | Current repo K562 | Status |
|---|---|---|---|
| Cell line | K562 classification track | K562 | Matched at name level |
| Task family | 3-class DEG prediction, per-gene F1 | 3-class DEG prediction, Macro-F1 | Broadly matched |
| Data source | Essential dataset track per VCHarness repo; code expects train.tsv/val.tsv/test.tsv | NormanWeissman2019/scPerturb h5ad-derived NPZ | Not matched |
| Training size | memory repeatedly cites 1,388 samples | 73 train rows | Not matched |
| Output genes | code constants use 6,640 genes | 1,000 target genes | Not matched |
| Perturbation universe | memory mentions 1,542 perturbations in early baseline context | 105 perturbations | Not matched |
| Labels | official TSV labels, class freq [0.0429, 0.9251, 0.0320] | percentile delta-vs-control labels, exact 5/90/5 class counts | Not matched |
| Best model family | AIDO.Cell-100M LoRA + STRING_GNN K=16 neighborhood attention | ESM2 perturbation gated MLP root | Not matched |
| Search scale | 153 public K562 nodes | 13 trained nodes in 50-budget run | Smaller |
| Artifacts | AIDO.Cell-100M and STRING_GNN checkpoints expected under /home/Models | ESM2, STRING API graph, Reactome pathway present; AIDO/scFoundation missing | Partially matched |

## What must be rebuilt before claiming reproduction

1. Build official-task data inputs.

   The next code layer should create a data builder that outputs official-style train.tsv, val.tsv, and test.tsv with one row per perturbation/sample and a 6,640-length label vector. It must not reuse the current 1,000-gene Norman-derived manifest if the claim is numeric reproduction.

2. Recover the official target-gene universe.

   The official public code hard-codes N_GENES=6640, but the public VCHarness snapshot inspected here does not include the target gene list. We need either the official data package, a target-gene list from the related GenBio data release, or a deterministic reconstruction rule that yields the exact 6,640 order.

3. Recover the official splits and label rule.

   The official code uses train.tsv, val.tsv, and test.tsv; the public tree does not include these files. The current split and label rule are local approximations, not official.

4. Acquire official model artifacts.

   The best official node expects:

   - /home/Models/AIDO.Cell-100M
   - /home/Models/STRING_GNN

   Our current STRING graph artifact is useful, but it is not the same thing as a pretrained STRING_GNN checkpoint. The repo should distinguish graph edges from pretrained graph embeddings/model weights.

5. Add an official compatibility model interface.

   The current GeneratedModel(spec) interface predicts [batch, 1000, 3] from fixed NPZ features. Official-style nodes tokenize perturbation genes through AIDO.Cell, fuse STRING_GNN embeddings, and emit [batch, 3, 6640] or equivalent logits. We need a parallel official TSV datamodule/model interface rather than forcing the official geometry into the current NPZ feature API.

## Recommended next branch

Create an implementation branch for official_k562_data_contract with these deliverables:

- docs/OFFICIAL_K562_DATA_CONTRACT.md
- src/vc_demo/official_k562/ package or equivalent
- A validator that fails unless all of these are true:
  - train/val/test TSV files exist
  - label vectors have length 6,640
  - class frequency is close to [0.0429, 0.9251, 0.0320]
  - split train count is 1,388 if using the official public-track target
  - AIDO.Cell-100M artifact path is present
  - STRING_GNN checkpoint/artifact path is present
- A root config that reproduces the official baseline family before running search.

## Decision

Do not launch another 50-node or 200-node search yet if the goal is reproduction plus implementation. The framework is ready for pressure testing, but the data/model contract is still not the official K562 contract. The correct next step is to make the harness support official TSV + 6,640-gene output + AIDO.Cell/STRING_GNN artifacts as a first-class task mode.

## Audit artifacts

- Structured JSON: experiments/k562_official_task_reconstruction/official_k562_audit.json
- Audit script: scripts/audit_official_vcharness_k562.py
