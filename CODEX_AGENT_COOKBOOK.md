# Codex Agent Cookbook

## Purpose And Ownership

Build a reusable, auditable research harness through tasks, not a model tuned to
one cell line. The active Codex is the researcher and implementer; this repository
must not call a Codex/OpenAI API internally. The harness supplies executable
contracts, state, evidence, proposals, acquisition and validation tools.

This file owns universal rules. `docs/RESEARCH_PROTOCOL.md` owns the shared
scientific protocol and APIs. Task runbooks own datasets, prediction units,
tensors, metrics, reference methods and model-specific training policies.
`ARTIFACT_ACQUISITION_RUNBOOK.md` owns public-resource acquisition.
The generic cell-line runbook describes the classification adapter only; it is
not a universal regression, trajectory or survival implementation.

Prompts should name the base/run branch, task or cell line, requested test type,
fresh run directory, and approved resource budget. Read repository rules rather
than copying historical instructions into every prompt. Reuse the current
development branch unless the user requests an isolated experiment branch.

## Hard Scientific Boundaries

- Freeze source data, eligibility, labels, group/split semantics, prediction
  horizon, target order, primary metric/direction and confirmation policy.
- No test/heldout/confirmation scores, labels, errors or feature importance may
  drive proposals, training, calibration, ranking, stopping or repair choices.
- Search and coverage produce development-only results. Native training defers
  test evaluation. Confirmation requires selected executable recipe fingerprints
  and closes that run to further search, including `train_pending`.
- Preserve the complete strongest reference recipe, not only its model name.
  Encoding, scaling, preprocessing, optimizer/regularization, effective budget,
  code, input content and artifact versions belong to its identity.
- No fabricated artifacts, proxy checkpoints, disguised substitute models,
  implicit synthetic task, nonfinite rewards, pruned training or untrained reward.
- A trained development rollout backpropagates exactly once. Replication is a
  separately identified experiment, not another application of the same reward.
- Smoke verifies interfaces/gradients. It is never formal scientific evidence.

## Codex Research Freedom

The blueprint is a hypothesis, not a complete architecture or a compulsory
mutation. Codex may design new architectures and public modules beyond the
manifest, use `agent_defined_candidate`, simplify a model, or choose replacement,
feature fusion, joint training, grouped cross-fitted residual, stacking or ablation.

The parent is an unchanged benchmark and source of evidence, NOT a mandatory
dense branch. There is no universal parent-preserving topology, fixed .25 mixing,
hidden-size cap, epoch minimum, or preference for a named foundation model.
Choose a faithful design within the task and approved resource contracts.
Existing agent-written `model.py` must be compiled and preserved, not overwritten
by an automatic template. Small models are legitimate when actually proposed as
small models; they cannot impersonate a required pretrained model.

Codex may change node-local model/config/helper code and declare a new effective
training policy. During a frozen experiment it may not change the scientific
task or silently rewrite baseline code. Framework bugs are repaired with a
versioned execution change and invalidation of affected results, not by mixing
old and new fold rewards under one identity.

## Research Loop

1. Read task sources, inspect independent group counts, sampling, missingness,
   potential label/input coupling and available budget. Register the protocol.
2. Register and replay exact strong/historical benchmark recipes. An unavailable
   historical artifact is an explicit comparison gap, never a weaker renamed root.
3. Declare separate coverage, optimization and confirmation budgets. Coverage is
   a method inventory exercise, not an optimization-score bonus.
4. Select a trained parent with MCTS; inspect development evidence and generate
   multiple falsifiable proposals. Replenish and re-rank the global queue after
   every completed rollout. Unselected/pruned proposals are not trained.
5. For the selected proposal, research/acquire any real missing artifact now.
   Implement and repair in the active Codex session. If infeasible after actual
   attempts, record the precise reason, skip that candidate and continue feasible
   queue entries. A queue file alone is not completion or a scientific blocker.
6. Record `research_hypothesis.json`: hypothesis, evidence references, expected
   change, falsification, composition and effective training policy. Compile,
   native-smoke, formally fit/evaluate and verify recipe provenance.
7. Train residual/stacking modules and combination weights using inner grouped
   OOF predictions. Never fit a residual from the parent's training predictions
   and call it cross-fitted. Do not use outer validation labels for a combiner.
8. Only then mark trained and backpropagate. Write development feedback with
   paired group-level gains, uncertainty, strata, convergence and resource cost.
   Let Codex use that evidence to propose the next experiment, including removal
   of an unhelpful complex component.
9. Stop only for the registered budget, stopping rule, reached optional target,
   exhausted feasible queue, true validity failure or approved resource boundary.
10. Freeze selected recipe fingerprints, open confirmation once, run registered
    confirmatory analyses and report. Do not resume search after seeing test.

## Evidence And Resource Policy

Independent samples are the declared groups, not cells, repeated folds or seeds.
Repeated CV is not independent confirmation. Pooled metrics must be accompanied
by task-appropriate within-condition diagnostics and mechanical/null controls.
Correlation with a ratio denominator, treatment identity or library is not proof
of the desired biological mechanism. Choose controls before interpreting gains.

Model families may use different training algorithms and budgets. Record the
actual solver, loss, epochs/iterations, stopping criterion and convergence, not
unused generic config fields. Comparable optimization opportunity does not mean
identical epoch counts. No global rule requires eight epochs or 100 rollouts.
Named run profiles are defaults; the task's registered plan determines adequacy.

Artifacts are feasibility gates, never a scientific-quality or ranking bonus.
Prefer primary sources; download/build when feasible, verify license/source,
content checksum, vocabulary/order, dimensions and actual model consumption.
Lack of a prewritten resolver is a Codex research task, not proof of unavailability.
If files are unpublished/incomplete, access-gated, unverifiable or beyond the
approved budget, record that exact limit and continue other valid hypotheses.

## Required Records

- `research_protocol.json`, full benchmark recipes and input/source fingerprints.
- Separate research budget plan/usage and effective per-model training policies.
- Tree, candidate hypotheses, selection/ranking reasons and trained-only trace.
- Development-only feedback, matched controls and group-aware uncertainty.
- Acquisition sources, checksums, alignment and license/feasibility decisions.
- Frozen selection/confirmation lock, confirmation report and exposure history.
- Independent execution, scientific, artifact-attribution and transfer verdicts.

Existing exposed test groups stay exposed, including after a new branch or seed.
A correctly executed null result is not an engineering failure. Conversely,
zero guardrail counters alone do not establish model superiority, fair baseline
comparison, artifact usefulness, or a broadly better framework.

## Validation And Delivery

Framework changes need static checks, negative/invariance tests and task-neutral
CPU integration tests before another scientific run. Check that poisoning test
values cannot change search context; code/data/scaling changes invalidate cached
results; composition preserves group boundaries; confirmation forbids reselection;
agent code survives materialization; unavailable artifacts are not ranked lower
merely for being unavailable; and resume cannot duplicate a completed reward.

Validate framework usefulness later on tasks not used to develop the framework,
against fixed strong baselines and equal-resource random search. Do not keep
retuning the current demonstration until it becomes positive.

Only commit source, task/config contracts, small metrics, tests, audit and reports.
Never commit data/, nodes/, weights, checkpoints, raw cell exports, model/cache
arrays, environments, private keys or tokens. Keep credentials container-local,
not on a permissive shared volume. Inspect actual staged paths and secrets before
commit/push. Preserve user changes and historical outputs. Do not extend the
approved cloud deadline or launch another resource without authorization.

