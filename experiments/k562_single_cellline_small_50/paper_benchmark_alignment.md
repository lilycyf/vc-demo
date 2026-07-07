# Paper Benchmark Alignment Audit: K562 Single-Cell-Line Run

## Source Checks

- Paper/code target: `genbio-ai/VCHarness`, public case-study repo for the Essential dataset four classification tracks: HepG2, Jurkat, hTERT-RPE1, and K562. Source: https://github.com/genbio-ai/VCHarness
- Official K562 VCHarness artifact inspected locally at `/workspace/_external/VCHarness/K562_cls/mcts_data.json`.
- Related foundation-model perturbation benchmark repo says it analyzes 600+ models across chemical/genetic perturbation datasets and continuous/discrete perturbation prediction formulations. Source: https://github.com/genbio-ai/foundation-models-perturbation
- Current repo data source: `NormanWeissman2019_filtered.h5ad` from scPerturb Zenodo record 7041849, encoded into repo-local NPZ splits.
- Pathway source: Reactome official GMT download, `https://reactome.org/download/current/ReactomePathways.gmt.zip`; Reactome documents open data/downloads and Content Service at https://reactome.org/download-data.

## What Matches

- Same cell-line focus: K562 single-cell-line classification track.
- Same broad task family: perturbation-response DEG classification with Macro-F1-style model selection.
- Same harness pattern: MCTS/UCT parent selection, generated child programs, node-local model code, train/evaluate/backpropagate loop, memory/report artifacts.
- Same single-cell-line experimental discipline: test split is reported after validation selection; data/splits/labels are not modified by child nodes.
- Similar biological artifact families now executable in this repo: perturbation-side ESM2, target-gene ESM2 manifest, STRING graph, and Reactome pathway membership.

## What Does Not Match

- Official VCHarness K562 public tree reports `total_nodes=153`, `draft_nodes=4`, `improvement_nodes=149`, best score `0.5128`, global best `node2-1-1-1-1-1`.
- Official K562 memory text shows a much larger target/task scale: 1,388 training samples and 6,640-gene differential-expression outputs in at least the visible node memory.
- This repo run uses 105 perturbation rows split 73/16/16 and 1,000 target genes.
- This repo label construction is local: delta-vs-control mean expression with <=5th percentile down and >=95th percentile up labels.
- This repo does not yet confirm the exact public paper/VCHarness K562 split policy, exact target-gene universe, exact DEG label construction, or expert baseline hyperparameters.
- AIDO and scFoundation artifacts remain missing, so the full paper-level foundation-model artifact space is not complete.

## Current Run Contract

- Alignment status from audit: `ready_for_single_cell_line_formal_search`.
- Audit issues: `0`.
- Root configs: `3`.
- K562 split sizes: train 73, validation 16, test 16.
- Target genes: 1000.
- Label classes: 3 (`down`, `unchanged`, `up`).

## Interpretation

This run is a framework-aligned, source-backed K562 single-cell-line reproduction attempt. It is not a numeric reproduction of the paper K562 result. The gap is not just compute; the public VCHarness K562 tree indicates a larger task geometry and likely different prepared benchmark artifacts.
