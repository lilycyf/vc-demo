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

- [x] Clone pseudobulk counts, distinct from mean per-cell log expression
- [x] Train-fold PCA
- [x] Train-fold scVI with frozen out-of-sample encoder
- [x] Source-backed Hallmark/ER/E2F/EMT programs
- [x] pertpy distribution distances: energy/MMD/Wasserstein
- [x] Train-only pseudotime/trajectory representation

### Dynamic Models And Author References

- [x] Early day-1/4 Elastic Net
- [x] GRU trajectory
- [x] Temporal Transformer
- [x] Actual author TraCSED functions, source-hashed, not a generic replacement
- [x] Rebuilt author R PLSR/Slingshot/selection-JSON inputs
- [x] CellRank time-directed kernel using real transport couplings
- [x] Censoring-aware survival/hazard model, explicitly about persistent sampling
      non-detection rather than proven biological extinction

### Combination Interactions

- [x] Additive monotherapy null, with exact response scale declared
- [x] Bilinear drug interaction
- [x] Parent-preserving gated pathway residual
- [x] Cross-treatment attention
- [x] Mixture of resistance experts

### Prediction Heads And Losses

- [x] Continuous selection regression
- [x] Positive-selection classification
- [x] Monotherapy-resistant/combination-sensitive classification
- [x] Early-warning ranking
- [x] Huber
- [x] Weighted BCE
- [x] Focal loss
- [x] Pairwise ranking loss
- [x] Selection plus pathway multitask loss

### Formal Execution And Evaluation

- [x] Five real roots
- [x] Full manifest covering all named modules, not only implemented early models
- [x] 20-40 selected formal rollouts with module/family coverage
- [x] Node-local code is actually called for training, not merely compiled
- [x] Parent-preserving composition formally evaluated
- [x] Five-seed repeated clone-grouped CV
- [x] Leave-one-clone-out
- [x] Late-interval holdout
- [x] Monotherapies-to-combination extrapolation
- [x] Frozen Month-6 transport, with coverage and unavailable metrics explicit
- [x] Spearman, MAE, clone-bootstrap 95% CI
- [x] AUPRC, AUROC, NDCG, early warning, suppression accuracy, calibration
- [x] Exploratory Resistance Attractor Score, never substituted for an observed
      endpoint or optimized on test labels

### All Eight Ablations

- [x] No barcode-informed predictive inputs (ground-truth labels and group
      integrity necessarily still use the observed clone mapping)
- [x] Baseline only
- [x] No temporal ordering
- [x] No pathway prior
- [x] Shuffled biological memberships, not renamed pathway columns
- [x] Matched-capacity no-artifact control
- [x] No treatment interaction
- [x] No dense parent route

### Final Deliverables

- [x] Source/provenance and download/build instructions
- [x] QC, clone assignment, sample/replicate confounding audit
- [x] Reference-method alignment with every reconstruction difference disclosed
- [x] Full search tree, selection/proposal/backprop trace, selected-rollout table
- [x] Biological program and combination-suppression interpretation
- [x] Generalization/uncertainty/root-dominance attribution
- [x] Actual cost/time/GPU/package versions
- [x] Whole-study completion matrix; no unexecuted requirement marked complete
- [ ] Allowed-files-only commit and verified push on the current branch

Execution evidence: `experiments/t47d_lineage_resistance_full_v2/completion_matrix.json` and
`complete_study_acceptance_audit.json` both passed. Scientific superiority is
not implied: historical Ridge and snapshot/abundance controls remain stronger.

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
