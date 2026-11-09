# Shared Research Protocol v2

## Version And Actual Entrypoint

Fresh research uses `PYTHONPATH=src python scripts/run_research_harness.py --run-dir
<fresh_run> <action>`, equivalently `python -m vc_demo.harness.research_v2`.
This is the executable shared session, not a document-only policy layer.

The active Codex operates context/propose/select/seal/execute/repair/skip/confirm
tools. There is no internal LLM API or random catalog generator pretending to be
research. CLI actions return the next work boundary; Codex continues in the same
session until a registered stop, rather than treating one handled request as a run.

Historical `research_contract.py`, `research_feedback.py`, `mcts.py` and existing
task runners remain v1 execution records. They are not rewritten to retroactively
repair completed studies. v2 has separate protocol/state/confirmation files.

## TaskSpec

Register JSON with:

- `schema_version=research_v2`, task_id, dataset/split SHA256, label_semantics,
  input_policy, prior_test_exposure and the complete `metric` below.
- `development_contract`: immutable JSON path containing row_ids, groups, targets,
  evaluation seeds, folds and the [row,seed] fold_ids assignment. Each fold partitions
  development groups into disjoint train/validation sets; each row has one OOF fold
  per seed. Repeated measurements of the same biological group stay together.
- `inputs`: role -> {path, sha256, scope: development|public}. Providers must enforce
  the task's train-only preprocessing/access policy; public raw sources are not
  automatically safe training data just because they are public.
- `benchmarks`: required exact baseline IDs; `reference_benchmark`: the strongest
  declared reference. Missing known baselines are comparison gaps, not weaker aliases.
- `benchmark_recipes`: a complete expected semantic recipe for every required ID,
  including parameters/training, code/input/artifact hashes and environment. These
  identities are frozen before results and enforced when sealing the baseline.
  Same name with weaker preprocessing or budget is rejected, not silently compared.
- `budget`: coverage inventory slots, successful optimization measurements and maximum
  confirmation models; `minimum_effect` predeclares
  the practical effect for descriptive development promotion support.
- `policy`: queue_capacity, min_new_proposals, parent_policy, exploration,
  uncertainty_weight, cost_penalty_per_hour; optional parent_active_limit,
  bootstrap_draws and allow_documented_exhaustion. These are registered choices,
  not universal task-specific constants.
- `resources`: user authorization_id and timezone-aware deadline_utc. Session actions
  check the deadline; separately arm a real execution/Pod watchdog for a hard cloud
  limit. A synchronous provider cannot be safely preempted by a JSON timestamp alone.
- Optional `confirmation_contract`: {path,sha256}. Its data is opened only after
  freezing; it contains source-backed heldout rows/groups/targets/seeds and the
  provider's prediction-input description. Groups must not overlap development.

Datasets, fold construction, biological interpretation and real model implementation
are task/provider responsibilities, not implicit classification defaults.

## MetricSpec

Required fields: name, direction, aggregation (`mean_seed` or `ensemble`),
prediction_unit, group_key; fixed labels for classification.

Built-ins: Spearman, MAE, macro-F1. Task-specific metrics may supply a separately
named scorer_path, scorer_sha256, scorer_function and prediction_kind. Custom
scorers are task code frozen before selection; moving identical code does not
change metric identity, changing its content does. Add metric-provider tests first.

Prediction tables preserve row_ids/groups/targets/seeds/fold_ids and contain:

- Regression predictions: [row,seed].
- Classification probabilities: [row,seed,fixed_class]; never average class IDs.
- Structured/multi-output tasks: [row,seed,...] predictions and row-aligned structured
  targets, using prediction_kind=structured and a frozen tested custom scorer. The
  task provider owns censoring, output-grid, target-axis and score-specific validation.
- metric_id and evidence_phase (`development` or `confirmation`).

Full OOF tables and inner group audits stay in ignored nodes/ receipts; state/CLI
summaries do not embed row-level predictions/labels. Do not commit raw receipts,
patient/group exports or private source contracts simply because their extension
is JSON. Only reviewed, authorized aggregate reports/metadata belong on GitHub.

`mean_seed` computes the complete OOF metric separately for every seed, then averages.
`ensemble` averages predictions first. Their identities differ. Reward and
paired_evidence use exactly the same MetricSpec; differing estimands are secondary
reports, not interchangeable scheduling feedback.

Group bootstrap preserves whole groups and the prediction-seed axis. It is explicitly
conditional on fitted OOF predictions, with no adaptive-selection correction. Per-task
strata, nested validation and independent confirmation need appropriate provider/analysis
contracts; v2 does not claim a universal inferential guarantee.

## Hypotheses, Identity And Implementation

`context` returns an immutable evidence_id and trained OOF receipt locations, actual
diagnostics, remaining budgets, declared inputs, parent recommendations and next_action.
Confirmation results are stored separately and never included. Snapshot references
are content-addressed, not a shared mutable latest-feedback file.

`propose --file <list.json>` accepts candidates with id, phase, parent_id,
proposed_recipe {parameters,training}, required_artifacts, hypothesis and estimate.
Hypothesis requires statement, expected_change, falsification, evidence_ids,
composition and, for parent scheduling, parent_conditioning. An intentional override
of the highest UCT recommendation additionally records parent_override_reason.

Allowed compositions: replace, feature_fusion, joint, crossfit_residual, crossfit_stack,
ablation. No family whitelist, modulo gate or compulsory root-preserving architecture.
Agent-defined model structures live in the actual parameters/provider code.

After `select`, Codex implements the selected candidate and calls `seal --node <id>
--file <implementation.json>`. That file supplies execution.code_files (including
provider), optional artifact_files, and the actual recipe:

```json
{
  "parameters": {"architecture": "the actual implemented design"},
  "training": {"solver": "the actual effective training policy"},
  "code_sha256": {"provider": "<content hash>"},
  "input_sha256": {"development_role": "<registered content hash>"},
  "artifact_sha256": {},
  "environment": {}
}
```

Execution locations are separate from scientific parameters. Semantic identity
binds actual config, training, component content, source/artifact roles, metric
and installed environment. Different node directories with identical semantics reuse
the completed measurement, without another fit or reward. An explicit replicate
has id, purpose and training_seed; it counts as a measurement, not a new architecture
or new independent dataset. Providers must actually apply declared replicate seeds.

Codex may improve a selected design rather than mechanically implementing its most
primitive interpretation; declare design_revision_reason when changing proposed
parameters/training. Existing scientific results cannot be repaired by overwriting
their identity. A revised completed/partial candidate gets a new ID and sealed recipe.

Artifact files must exist, match content hashes and include source, status
(original_public/derived/reconstructed_compatibility), and task-appropriate alignment.
Use existing acquisition tools and current Codex research; absence of a resolver is
not unavailability. Missing resources are investigated after scientific selection,
not used as a hidden model-quality score.

## Trusted Task Provider Contract

A provider module implements `evaluate_development(request)` and
`predict_confirmation(request)`. The shared engine imports the sealed actual code;
it never replaces the implementation with a compact proxy.

Development returns prediction_table, exact fit_audit for registered OOF folds,
checkpoint_files, consumed_artifact_roles, and diagnostics containing solver,
converged (true/false/unknown), train_loss, inner_validation_policy and outer_fit_count.
The provider owns actual fit/forward/backward, train-only transformations, native
smoke, convergence diagnostics and model-specific validation. Extend diagnostics
with curves, gradient/feature checks, total solver-fit counts, extra checkpoint-fit
counts and actual budgets. Outer-fold fits are not all nested solver fits.
Install/freeze core metric dependencies before registering a run. Model-specific
dependencies may use a faithful isolated runtime with audited environment-lock
artifacts; do not silently upgrade the active metric stack during selection.

OOF residual/stacking additionally returns composition_audit per outer seed/fold:
weight_training=grouped_oof, training-only weight_fit_groups and actual inner_folds.
The shared validator checks disjointness, outer-validation exclusion and complete
training-group coverage. Source review/tests must verify how designs/weights were
really produced; an invented audit is forbidden.

Fitted artifacts must be persisted under ignored `RUN_DIR/nodes/<id>` before
confirmation. Artifacts declared as consumed must be backed by real provider use;
source review/adapter tests verify that claim. Equality of self-reported roles is
not hardware tracing or proof that a malicious provider actually used a module.

Providers are reviewed/trusted code, not an OS security sandbox. The engine checks
rows, groups, seeds, declared fits, contents and checkpoints, but cannot prove that
arbitrary Python never reads a hidden label or calls fit internally. Each real adapter
needs poisoning/invariance tests and source-backed access/OOF validation. The shared
regression/classification fixtures do not certify every biological adapter.

Confirmation calls only predict_confirmation with frozen files. It checks source
and checkpoint identities, requires zero model/calibration refits, verifies group
disjointness and stores report-only scores. Provider tests must prove predict-only
behavior; a boolean alone is not a security guarantee.

## Policy, Credit And Lifecycle

Parent policy is explicitly `uct_parent_scheduler` or `global_queue`. The former
recommends trained parents; it is not advertised as full tree-descent paper MCTS.
Coverage/benchmark associations are comparison edges, not optimization ancestry.
Their own scores remain available, but their observations do not increment
optimization visits/Q or exhaust raw-child limits. Only in-flight optimization work
may count toward the optional active limit, not pruned/done/queued inventory items.

A documented unavailable coverage item is a handled inventory slot, not a trained
method or successful fit. It cannot trap the whole run before optimization; report
coverage_inventory_handled, actual coverage fits and coverage_gaps separately.

Expected gains and uncertainty are measured matching development evidence or labeled
research assumptions with rationale. There is no automatic whole-family averaging.
Measured estimates reference stored paired evidence with the same metric_id.

Costs separately include acquisition, cache_miss, fit and evaluation seconds.
Priority is gain + registered_uncertainty_weight * uncertainty - registered_cost_penalty
* cost_hours. Its cost effect is monotonic even for negative gains. It is an explicit
research heuristic, not a calibrated Bayesian posterior or guarantee of optimal search.

`rerank` accepts a current evidence_id and updates for queued estimates, logging old
and new assumptions. Global capacity pruning uses the current queue, not local top1.
Successful optimization commits one reward and advances the cycle; the next selection
requires newly researched proposals. Pruned nodes never execute. A recovered committed
receipt is validated/reused, not retrained/backpropagated again.

Execution errors yield repair_needed. Current Codex repairs/reseals or issues a
documented skip with actual action/evidence, then continues the queue. A missing
implementation is current work, not a terminal requires_external_codex verdict.

If new ideas are genuinely exhausted and this stop rule was registered, `exhaustion`
records real attempts; existing queued work still drains before closure. It does not
turn an unprocessed implementation/acquisition queue into a completed study.

## Layered Conclusions

`report` separates execution completion, unique semantic candidates, repeated
measurements, exercised/unexercised compositions, development promotion support,
retained baseline, artifact attribution and unestablished transfer claims.

`control_verdict` marks removal of an unused module not_applicable; a used-module
control needs actual dependency removal, not merely another config label. A score
drop is not required for a control to be applied, nor guaranteed by authentic use.

The actual session exposes `control --file` with control_id, target, removed_roles,
optional intervention and a matched-control rationale. It uses trained receipts,
semantic identities and provider-reported module roles; applicable comparisons reuse
the same paired metric. Register required_controls IDs in TaskSpec before selection;
their applicable/N/A outcomes must be recorded before opening confirmation. The engine
does not infer fairness or biological causality merely from a role declaration.

`freeze` closes selection and requires actual trained finalists/checkpoints within
budget. A finalist is not automatically a scientifically supported replacement.
No return to search after confirmation. New versions/tasks must preserve exposure
history; new blind evidence requires independent groups, not a fresh directory.
The exposure flag records audited researcher knowledge; it does not automatically
discover disclosures or evaluations performed outside the registered repository.
