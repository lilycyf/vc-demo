# Generic Research And Cell-Line Acceptance

Canonical constraints live in CODEX_AGENT_COOKBOOK.md and RESEARCH_PROTOCOL.md.
These checks apply to fresh runs under the current protocol. Historical runs
retain their original results and limitations; they are not retroactively passed.

## Execution

- Requested task, adapter, run type, directory and resource budget are explicit.
- Real data and tensor/label/order contracts are validated; no implicit synthetic
  data, other-cell-line backend, proxy checkpoint or fabricated artifact.
- Selected nodes are actually implemented and trained. Compile/native smoke is
  interface validation only. Existing agent code is not overwritten by templates.
- Acquisition and repair receive same-session attempts; proven unavailable or
  infeasible candidates are logged/skipped without halting other feasible work.
- Only trained development rollouts backpropagate, exactly once; pruned, skipped,
  failed, pending and confirmation nodes do not.
- Resume replenishes and re-ranks the queue. Handling one pending item is not a
  valid terminal condition while the registered search remains open and funded.

## Protocol And References

- Protocol identifies data/split content, label semantics, independent group,
  time access, primary metric/direction and confirmation rules.
- All required strong/historical benchmark recipes are included and replayable.
  Same model names with different preprocessing are different comparisons.
- Effective training config, source, data, artifact and environment fingerprints
  are recorded. Changed scaling, code, data or actual epoch budget invalidates
  affected cached results instead of silently mixing folds.
- Coverage/optimization/confirmation plans and consumption are separate. Named
  profile defaults are not universal epoch or rollout requirements.
- Residuals and meta-weights use inner grouped OOF. Replacement/simplification is
  permitted; a strong parent benchmark does not require a retained dense branch.

## Information Boundaries

- Search training does not iterate/evaluate test data; metrics show withheld,
  not invented zeros or validation fallbacks.
- Test poisoning leaves feedback, parent summaries and candidate ranking unchanged.
- Feedback artifacts declare development provenance; legacy test-derived policies
  are not imported into new search memory.
- Confirmation requires actual selected recipe fingerprints, unchanged code/data,
  a frozen-selection lock and the declared confirmation budget.
- Opening confirmation closes search and train_pending. Test cannot tune another
  seed, epoch, architecture, calibration, acquisition choice or stopping rule.
- Prior exposure and unidentifiable metrics remain explicitly disclosed.

## Scientific And Attribution Verdicts

Execution success and scientific superiority are separate. Report the registered
objective status, matched paired gains/uncertainty, per-condition diagnostics,
simple/mechanical controls, convergence and effective sample size. A threshold
is required only if the task/user registered one; framework success is not
defined as making every complex model beat every simple baseline.

Artifact availability/use does not establish usefulness. Distinguish capacity,
training and actual artifact contribution with prespecified matched controls.
No temporal benefit may be claimed merely because a real temporal module ran.
No-positive-heldout recall is undefined, not100%. Repeated CV and an adaptive
development winner are not fresh independent confirmation.

## Framework Transfer Verdict

Use new tasks not used for framework development and equal-resource baselines
and random search before claiming a generally improved framework. Task-specific
scientific details remain adapters, not hardcoded cookbook choices. Test changes
with both regression and classification fixtures and adversarial negative cases.

## Required Outputs And Git Guard

Preserve protocol, recipe locks, budget usage, hypotheses, tree/trace, development
feedback, acquisition/repair evidence, frozen selection and a layered report.
Required invariant counters are zero: fallback/proxy, pruned training,
nontrained/duplicate/confirmation reward, unintended backend and forbidden files.

Never commit data/, nodes/, weights/checkpoints, *.pt/*.pth/*.ckpt/*.bin,
*.npz/*.h5ad, raw cell exports, environments, caches, private keys or tokens.
Review actual staged paths and secret patterns; a directory named in a harmless
model strategy is not itself a checkpoint artifact. Preserve user changes.

