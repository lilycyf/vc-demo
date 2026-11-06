# T47D Whole-Study Execution Contract

This contract follows the user's original H1-P2 design. It does not replace the
whole study with a first-stage executable subset. The old pilot remains frozen.

## Immutable Facts

- Source: GSE260703, the pinned Genentech/TraCSED repository, and source-backed
  human gene sets. No invented checkpoint or private-data substitute.
- Clone-level grouping, baseline-only cohort eligibility, early day 0/1/4 inputs,
  day-26 log2 relative-selection primary label, and validation Spearman remain.
- Existing clone split is retained. Its prior test exposure is explicitly
  disclosed; no changed split is advertised as a newly blinded test.
- The approved initial limit remains 24 hours/$20. The spending watchdog remains
  active. Scope is not reduced to fit a limit; unfinished work is saved accurately
  if that limit is actually reached.
- Smoke checks do not count as formal model evaluation. Pruned proposals are not
  trained. Reward is propagated only after successful formal validation.
- Ordinary missing dependencies, public downloads, and buildable representations
  are handled immediately, not declared unavailable without investigation.

## Required Implementation And Formal-Evidence Matrix

Every item below needs executable code, an input/output and leakage contract,
and a real-data result or a concrete demonstrated limitation. A label in a
manifest is not completion.

### Representations

- [ ] Clone pseudobulk counts, distinct from mean per-cell log expression
- [ ] Train-fold PCA
- [ ] Train-fold scVI with frozen out-of-sample encoder
- [ ] Source-backed Hallmark/ER/E2F/EMT programs
- [ ] pertpy distribution distances: energy/MMD/Wasserstein
- [ ] Train-only pseudotime/trajectory representation

### Dynamic Models And Author References

- [ ] Early day-1/4 Elastic Net
- [ ] GRU trajectory
- [ ] Temporal Transformer
- [ ] Actual author TraCSED functions, source-hashed, not a generic replacement
- [ ] Rebuilt author R PLSR/Slingshot/selection-JSON inputs
- [ ] CellRank time-directed kernel using real transport couplings
- [ ] Censoring-aware survival/hazard model, explicitly about persistent sampling
      non-detection rather than proven biological extinction

### Combination Interactions

- [ ] Additive monotherapy null, with exact response scale declared
- [ ] Bilinear drug interaction
- [ ] Parent-preserving gated pathway residual
- [ ] Cross-treatment attention
- [ ] Mixture of resistance experts

### Prediction Heads And Losses

- [ ] Continuous selection regression
- [ ] Positive-selection classification
- [ ] Monotherapy-resistant/combination-sensitive classification
- [ ] Early-warning ranking
- [ ] Huber
- [ ] Weighted BCE
- [ ] Focal loss
- [ ] Pairwise ranking loss
- [ ] Selection plus pathway multitask loss

### Formal Execution And Evaluation

- [ ] Five real roots
- [ ] Full manifest covering all named modules, not only implemented early models
- [ ] 20-40 selected formal rollouts with module/family coverage
- [ ] Node-local code is actually called for training, not merely compiled
- [ ] Parent-preserving composition formally evaluated
- [ ] Five-seed repeated clone-grouped CV
- [ ] Leave-one-clone-out
- [ ] Late-interval holdout
- [ ] Monotherapies-to-combination extrapolation
- [ ] Frozen Month-6 transport, with coverage and unavailable metrics explicit
- [ ] Spearman, MAE, clone-bootstrap 95% CI
- [ ] AUPRC, AUROC, NDCG, early warning, suppression accuracy, calibration
- [ ] Exploratory Resistance Attractor Score, never substituted for an observed
      endpoint or optimized on test labels

### All Eight Ablations

- [ ] No barcode-informed predictive inputs (ground-truth labels and group
      integrity necessarily still use the observed clone mapping)
- [ ] Baseline only
- [ ] No temporal ordering
- [ ] No pathway prior
- [ ] Shuffled biological memberships, not renamed pathway columns
- [ ] Matched-capacity no-artifact control
- [ ] No treatment interaction
- [ ] No dense parent route

### Final Deliverables

- [ ] Source/provenance and download/build instructions
- [ ] QC, clone assignment, sample/replicate confounding audit
- [ ] Reference-method alignment with every reconstruction difference disclosed
- [ ] Full search tree, selection/proposal/backprop trace, selected-rollout table
- [ ] Biological program and combination-suppression interpretation
- [ ] Generalization/uncertainty/root-dominance attribution
- [ ] Actual cost/time/GPU/package versions
- [ ] Whole-study completion matrix; no unexecuted requirement marked complete
- [ ] Allowed-files-only commit and verified push on the current branch

## Reference Versus Prediction Tracks

The original TraCSED analysis interpolates retrospectively along pseudotime and
is not an independent early-to-endpoint forecast. Run the genuine reference
workflow separately and label that distinction. Its hindsight-derived trajectory
and selection labels must not become features or rewards of the prospective
clone-heldout search.

Public raw data permit reconstruction work even though the author R scripts refer
to internal gp.sa.core/gstore objects. Preserve the exact author model functions;
record deviations in upstream gene-set versions, reconstructed clustering labels,
or unavailable custom signature definitions instead of pretending numerical
identity or stopping at the first private path string.
