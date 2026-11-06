# T47D Lineage Resistance Harness

## Scope And Status

This is a new task plugin, not a continuation of the K562/HELF classification experiments. The first approved stage is one RTX 3090, 100 GB persistent network volume, at most 24 hours, and at most $20 including a conservative $7 storage reservation. A 20-hour search ceiling leaves setup and shutdown margin. Do not interpret the ceiling as permission to leave the GPU idle.

The executable first-stage study predicts day-26 relative clonal selection from baseline/day-1/day-4 observations. It is **not** an exact replication of TraCSED, a clinical recommendation, or evidence that individual resistant cells have been reprogrammed.

Base branch: `aivc-helf-executable-foundation-full-run` (`18fcaa7` at initialization).
Development branch: `t47d-lineage-resistance-demo`.

## Universal Versus Task-Specific Code

- Reuse `vc_demo.harness.mcts` for UCT and reward backpropagation. No internal Codex API calls.
- Keep clone mapping, labels, grouped evaluation, representations, regression models, and task metrics in `vc_demo.t47d_lineage`.
- Do not change existing K562/HELF contracts or retrofit this task into Macro-F1 fields.
- The active Codex session performs source research and implementation. A planned family is not counted as executable, trained, or covered just because it has a name.
- Artifact presence is a feasibility gate, not evidence of scientific merit. The queue priority contains no present-artifact bonus.

## Sources

- GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE260703
- Processed inputs: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE260nnn/GSE260703/suppl/
- SOFT metadata: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE260nnn/GSE260703/soft/GSE260703_family.soft.gz
- Author code: https://github.com/Genentech/TraCSED, pinned commit `dc5a750ef6fc6adf50e362ba5c2d38bee6083289` on initial acquisition.
- Paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC11723929/
- Hallmark gene sets: https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/h.all.v2025.1.Hs.symbols.gmt

Retain the original source licenses. The author repository has an MIT license; this does not relicense GEO data, MSigDB gene sets, or the paper. Use the providers' own terms. Do not redistribute the paper's figures as edited figures.

## Data Contract

- Expression matrix: 200,429 cells x 58,302 genes before QC.
- GFP matrix: 199,998 possible barcode features x 200,429 cells.
- Match expression and GFP by unique cell identifier, not by an assumed common row order.
- Follow the author scripts: at least 500 detected genes, mitochondrial fraction at most 25%, and exactly one positive GFP barcode. Zero- and multi-barcode cells are not assigned an invented clone.
- The first acquisition yielded 47,718 QC-passing single-barcode cells and 46 eligible clones with at least ten baseline cells.
- Eligibility is baseline-only. The original paper's >=200 cells across time is a descriptive/reference cohort, not a prospective eligibility rule for this task.
- Repeated GSM entries share SAM sample identifiers. Preserve the original replicate labels and library prefixes, but do not claim independent biological replicates without supporting metadata.
- GEO labels baseline Day 0, whereas the paper Methods describe one day of DMSO. Record both. GEO lists 200 nM for the monotherapies; do not silently copy a conflicting dose from a figure or design document.
- Month 6 is a separate long-term condition. `180` is only a nominal ordering code, not an exact observed elapsed day.

Prediction unit: clone x treatment. The clone has one input sequence for days 0,1,4. Clone identity is used for grouping and labels, not as a learned categorical predictor.

Primary label:

```text
log2((day26_clone_fraction + 1e-5) / (baseline_clone_fraction + 1e-5))
```

Denominators include all QC-passing, uniquely barcoded cells in a condition, not only the eligible cohort. This is relative selection, not absolute viability. All clone labels share compositional denominators; bootstrap by clone, not by cell or treatment row.

Zero endpoint counts mean sampling non-detection, not established extinction. Keep a zero-count flag. Prespecified pseudocount sensitivities are 1e-6, 1e-5, 1e-4, never tuned to maximize test performance.

## Evaluation And Test Lock

1. Freeze a 20% clone-heldout test with split seed 20261106 (ten clones in the initial dataset).
2. Split the remaining clones into three grouped folds for each seed 3,7,11,17,23.
3. Fit gene selection, scalers, PCA, PLS, and supervised estimators on each training fold only.
4. Reward is the mean of five seed-level pooled out-of-fold Spearman correlations. MAE and treatment-stratified correlations are secondary.
5. Never inspect locked-test or Month-6 labels to select a model, modify the search policy, or stop the run.
6. Freeze the best root and generated pipeline before locked-test evaluation. Five refit seeds and their fixed mean ensemble are reported without test-based selection.
7. A run that has written `frozen_selection.json` cannot resume search against the same held-out test. Use a new registered experiment for further development and disclose prior test exposure.

The five root baselines are baseline-frequency ridge, baseline-pathway ridge, baseline-expression Elastic Net, baseline-pathway PLSR, and early-state XGBoost. Their inputs differ intentionally. The baseline-only and no-temporal controls must be used before attributing an advantage to time modeling.

## First-Stage Search

The current executable manifest has 120 explicit candidates:

- estimators: ridge, Elastic Net, PLSR, XGBoost, GRU, temporal Transformer, gated nonlinear residual;
- representations: early expression, Hallmark pathways, both, fold-fitted PCA;
- regularization: 1,10,100;
- temporal residual losses: Huber or MSE;
- neural training: 80 full-batch epochs, AdamW, gradient clipping; same prescribed settings across candidates.

These are genuine models for this small clone-level prediction task, not replacements for a claimed foundation checkpoint. GRU/Transformer candidates retain a fitted dense ridge branch and learn a temporal residual. Hallmark scoring is explicitly mean log-normalized expression, not an unverified claim to reproduce scuttle exactly.

UCT selects a trained parent. Four new candidates are added to a global queue before every rollout selection. Priority uses the parent's validation performance, uncertainty penalty, and model-family novelty. A global capacity of 48 queued candidates is enforced by ranking, not by automatically discarding three of every four proposals. Only the selected candidate is compiled, interface-smoked, and formally cross-validated. Only successful formal evaluation backpropagates. Unselected candidates are pruned at the registered budget boundary.

The default is 24 selected rollouts, with a no-improvement criterion only after at least 20 successful rollouts. This is a first-stage executable-subset experiment, not complete declared-universe coverage or an exact reproduction of VCHarness's private orchestrator.

## Commands

Work inside `/workspace/vc-demo` on the Pod, with dependencies persisted in `/workspace/t47d_venv`.

```bash
python scripts/t47d/acquire.py
OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=8 /workspace/t47d_venv/bin/python scripts/t47d/prepare.py
PYTHONPATH=src /workspace/t47d_venv/bin/python -m pytest tests/t47d -q
PYTHONPATH=src OPENBLAS_NUM_THREADS=2 /workspace/t47d_venv/bin/python scripts/t47d/run.py \
  --run-dir experiments/t47d_lineage_resistance_demo \
  --selected-rollouts 24 --max-runtime-hours 20
```

Resume before test unlock by adding `--resume`. Source hashes, frozen splits, and the task contract must match. A code or contract revision requires a fresh registered run; do not silently mix rewards from changed implementations.

Do not start formal search if static checks fail. Repair actual implementation errors; do not replace a failed model with a proxy or rewrite its metrics.

## Remaining Whole-Study Work

These are explicit remaining tasks, **not** already completed results:

1. Exact TraCSED reference: author R code expects internal `gp.sa.core`/`gstore` objects, a curated pathway file, Slingshot outputs, and selection JSON. Reconstruct those inputs from public counts and metadata, verify against the public methods, then call the genuine notebook functions. The R dependencies and JSON build are integration work, not proof that the raw public dataset is unavailable. The reference uses hindsight/pseudotime interpolation and must remain separately labeled from early-to-day26 forecasting.
2. Train-fold-only scVI latent, CellRank time kernel, pertpy distribution distances, and a censoring-aware hazard model. These are planned executable extensions, not included in the 120 implemented candidates.
3. Full matched-capacity/no-artifact and shuffled-membership controls. Simply permuting pathway names is not a shuffled biological membership control.
4. Locked Month-6 escape analysis, including clones outside the baseline-eligible cohort and an explicit out-of-horizon caveat.
5. Pseudocount and non-detection sensitivity, combination-suppression tables, biological-program trend replication, root-dominance audit, and complete eight-ablation accounting.
6. Publish a completion matrix distinguishing acquired, implemented, tested, formally evaluated, and scientifically supported components. Never call the whole study complete because the first-stage search ran.

The design document's weighted Resistance Attractor Score is exploratory, not a validated measured endpoint. Do not use its arbitrary weights as the search reward or as independent evidence of reversal.

## Persistence, Costs, And Git

- Network volume `/workspace` stores source data, virtualenv, clone-level tensors, h5ad, and fitted models.
- Git stores code, configs, contracts, checksums, lightweight tables, and reports only.
- Never commit private keys, tokens, MTX, h5ad, NPZ, `nodes/`, joblib models, or checkpoints.
- Staged checks must inspect actual path components and binary extensions, not reject harmless blueprint names containing the word `checkpoint`.
- Verify both GitHub deploy-key authentication and a successful push; a generated key alone is not access.
- The initial container's `runpodctl` has no API key. An unattended automatic stop is **not configured** merely because a sleep process exists. Keep active supervision and stop the GPU in the console before ending the session, or first configure and verify an authorized stop mechanism.
- Stopping a Pod does not delete its Network Volume. The $7/month storage charge continues until the user explicitly authorizes volume deletion.
