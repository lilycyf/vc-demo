# T47D Complete Public-Data Study

The canonical complete-scope run is
`experiments/t47d_lineage_resistance_full_v2` on branch
`t47d-lineage-resistance-demo`. The previous
`t47d_lineage_resistance_demo` run is an immutable pilot, not evidence that the
whole original task document was completed.

## Scope and Invariants

Follow the original `H1-P2_公开数据完整Demo_T47D组合逆转耐药状态.md`.
Do not replace the full study with an executable-subset smoke, omit a difficult
module, or count an untrained declaration as formal evidence.

- Fixed data: public GSE260703 processed counts and TraCe-seq barcodes.
- Fixed unit: clone x treatment, with early day0/day1/day4 sequence input.
- Fixed primary target: day26 log2 relative selection with eps=1e-5.
- Fixed baseline-only eligibility: >=10 QC single-barcode baseline cells.
- Fixed group split: 36 development and 10 heldout clones, seed20261106.
- Primary reward: mean of five seed-level pooled 3-fold clone OOF Spearman.
- All supervision, feature fitting and calibration are train-group confined.
- No fallback, proxy checkpoint, pruned training, or non-trained backpropagation.
- Prior pilot exposed the same test groups and Month6 observation. Report that
  limitation; never relabel them as a brand-new blind external validation.

## Environments and Persistence

Persist under the 100GB Network Volume mounted at `/workspace`:

| Path | Purpose |
|---|---|
| `/workspace/vc-demo` | Source, run contracts and lightweight results |
| `/workspace/t47d_full_venv` | PyTorch, scVI, scanpy, CellRank, pertpy, POT, lifelines |
| `/workspace/t47d_tf_venv` | Isolated genuine TensorFlow author models |
| `/workspace/t47d_r` | R, pls, scran, Slingshot, DelayedMatrixStats |
| `/workspace/_external/TraCSED` | Public author code pinned to dc5a750ef6fc6adf50e362ba5c2d38bee6083289 |
| `data/t47d_lineage/full_fold_artifacts` | Fold-only latents, gene orders, transition kernels, weights |
| `experiments/.../nodes` | Frozen fitted primary model artifacts; not committed |
| `experiments/.../reference/weights` | Author reference Keras models; not committed |

TensorFlow must receive the NVIDIA shared-library paths before import. The
worker configures the isolated runtime and uses GPU memory growth. Do not
silently drop to a different architecture if a dependency is missing.

Use the generated Python lock files and R explicit environment export to
recreate environments on a clean compatible Linux container. Deploy private
keys remain container-local, never plaintext on a permissive shared volume.

## Complete Command

```bash
cd /workspace/vc-demo
export PYTHONPATH=src
export OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=4
export JAX_PLATFORMS=cpu
/workspace/t47d_full_venv/bin/python scripts/t47d/full_demo.py --phase all
```

The full command runs data reconstruction, all formal search candidates,
public-author reference reconstruction, frozen evaluation, all ablations,
biological/sensitivity analysis and the final evidence-gated report. Separate
`--phase prepare|search|reference|evaluate|biology|report` options support repair
and resume; completing one phase is not completing the whole study.

## Search Contract

The manifest contains 107 effective templates, inside the original 80–150
range. Five roots and forty selected rollouts are formally evaluated. Each
candidate receives 15 complete fits, not a one-step smoke score.

The first coverage pass ensures the required representation/dynamics/fusion/
head/loss families receive evidence. Parent selection uses the existing UCT
core with exploration sqrt(2). The global queue ranks validation quality,
uncertainty and scientific family coverage; artifact presence is not a
scientific-priority bonus. Only the selected node is materialized and trained.
After a completed rollout, new proposals replenish the global queue. Its
capacity is48 and parent depth/proposal limits are recorded in run_manifest.

An inherited pipeline retains its parent's prediction and fits a .25 residual
addition on training labels. Ablations remove both inherited and internal dense
routes when requested. Node-local `build_model(config)` is authoritative for
formal CV, not merely compiled and then bypassed.

Do not change the task, rewards, group split or time cutoffs to improve scores.
Code/API/dependency errors must be repaired in real time, with logs retained and
completed fold results restored. No artificial missing-artifact blocker may
replace an installable public dependency. A numerical convergence problem must
not be converted to a successful constant value.

## Actual Modules

- Pseudobulk raw-count aggregation and normalized expression.
- Train-only PCA, real count-trained scVI and curated public Hallmark means.
- Actual pertpy E-distance, RBF MMD and OTT Wasserstein, plus separately named
  POT sliced Wasserstein. Reuse exact reference statistics for speed; do not
  subsample away the full cell population or accept nonfinite-cost sentinels.
- Train-only diffusion pseudotime with explicit out-of-sample query projection.
- Actual CellRank RealTimeKernel with measured-time POT couplings, saved sparse
  transition matrices, and training-kernel descriptor projection to query cells.
  Baseline-only controls use an explicitly labeled stationary ConnectivityKernel.
- Early ElasticNet, GRU, temporal Transformer, genuine source-extracted TraCSED
  architecture, and interval/right-censored lognormal AFT.
- Monotherapy additive null, bilinear interaction, gated pathway residual,
  cross-treatment attention and innate/adaptive/persistent MoE.
- Continuous, positive-selection, mono-positive/combo-negative and ranking heads.
- Huber, weighted BCE, focal, pairwise ranking and pathway multitask losses.

Classification auxiliary labels use training indices only. In monotherapy-only
training, the unobservable combination-sensitive class is masked rather than
reading combination ground truth. AFT events mean persistent sampled-count
non-detection below3 cells, not proven biological death.

## Author Reference Track

Run actual R PLSR/Slingshot on all source-valid measured time points, then the
source-extracted author TensorFlow seq8 architecture, no-attention,
no-feedforward, and author linear reference across the four prefix intervals.
Use 20 epochs, batch32, heads40, head size5, ff_dim5 and Dense256 as published
code specifies. Keep the author's effective computation graph and record its
quirks rather than silently substituting a modern Transformer.

Save code hashes, genuine fitted models, curve-grid choices, predictions,
exclusions and 30-permutation feature importance. Prefix windows with no valid
author seq8 train/validation pair are explicitly unidentifiable, not fake fits.

The public R code refers to private SCE/gstore objects and an inaccessible
custom gene-set revision. Rebuild IO from public counts and public Hallmark,
retain original count filtering and normalization logic, and record cluster-ID
and gene-set-version differences. Never claim exact numerical reproduction of
unavailable private preprocessing.

Retrospective pseudotime interpolation is separate from prospective early-state
prediction; it is never used as a heldout-clone forecasting reward.

## Formal Evaluation and Required Controls

1. Primary repeated clone-group CV and frozen root/child test comparison.
2. Forty-six-clone LOCO after architecture freeze, labeled secondary complete-
   data cross-fitting, not the original independent test protocol.
3. Day8-supervision to day26 holdout, no day26 training labels.
4. Monotherapy-supervision to combination challenge on unseen clone groups.
5. Month6 escape audit, with explicit zero-positive-test limitations.

Also compute clone bootstrap95% CI, MAE, AUROC/AUPRC, clone-wise NDCG,
early-warning by cutoff day, suppression direction/class accuracy, and Brier/ECE
from development-OOF-only calibration.

Run all eight 15-fit ablations: no barcode-informed inputs (retain real labels
and clone grouping), baseline only, no temporal order, no pathway, globally
shuffled gene memberships, representation-width-matched no artifact, no
treatment interaction, and no dense parent.

The exploratory RAS uses original prespecified .40/.25/.20/.15 weights,
training-only scaling and negative-clone prototypes, and predicted persistence.
No query future observations enter its predictors. A Month6 cohort with no
heldout positive cannot identify unseen-escape recall. Report undefined rather
than manufacturing a positive validation outcome.

## Completion and Budget

`completion_matrix.json` is evidence-gated. It must not say complete unless the
actual fold counts, models, reference runs, ablations and challenge outputs
exist. Scientific superiority remains separate: a root-dominant outcome is
valid only with the complete root-dominance audit, not an excuse to omit work.

The initial user authorization is at most24h and $20. The independent budget
watchdog stops the GPU before 2026-11-07 07:30 UTC. Do not extend spending or
create additional resources automatically. If that real limit is reached,
persist actual remaining work and identify it honestly without redefining the
original scope as complete.

## Submission Guard

Commit source, docs, configs, versions, splits, small metrics, traces, catalogues
and scientific figures only. Exclude raw/derived data matrices, reference cell
input JSON, nodes/, weights/, .rds, .keras, .pt/.pth, .h5ad/.npz, checkpoints,
pycache and private keys. Scan the actual staged file list before commit/push;
do not use a broad `git add experiments/`.
