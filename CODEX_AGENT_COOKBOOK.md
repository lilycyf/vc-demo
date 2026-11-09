# Codex Agent Cookbook

## Purpose And Ownership

Improve a reusable research framework through tasks, not a demo score. The active
Codex is the researcher and implementer. Do not call a Codex/OpenAI API internally.

This file owns universal boundaries and researcher freedom. `docs/RESEARCH_PROTOCOL.md`
owns executable contracts; `docs/GENERIC_RESEARCH_RUNBOOK.md` owns the shared loop;
task runbooks own data, models and scientific meaning. The artifact runbook owns
source-backed acquisition. Prompts reference these docs instead of copying rules.

Fresh research uses `scripts/run_research_harness.py` and `harness/research_v2/`.
Legacy classification and task runners remain historical implementations, not
evidence that their behavior satisfies v2. A new task must implement a faithful
provider; no registration is permission to silently use another task or synthetic data.

## Immutable Scientific Boundaries

- Freeze source content, eligibility, labels, independent groups/splits, time access,
  target order, the complete primary MetricSpec and confirmation/exposure policy.
- Freeze exact strongest benchmark recipes, including encoding, scaling, solver,
  actual training settings, code and dependency/input/artifact content identities.
- Search, feedback, selection, calibration and repair use development evidence only.
  Test/confirmation labels, scores or errors cannot rank hypotheses or tune training.
- A recipe/source change is a new scientific identity. Do not mix old and new folds.
  Exposed groups remain exposed after a branch, seed or protocol version changes.
- No fabricated artifacts, disguised small-model substitutes, implicit synthetic task,
  nonfinite reward, pruned training, in-sample residual called OOF, or untrained reward.
- A validated optimization measurement backpropagates once. Coverage and benchmark
  observations never consume optimization credit or expansion slots.
- Confirmation only loads frozen fitted checkpoints/calibrators. It closes selection;
  its results never enter research context. Smoke verifies interfaces, not superiority.
- Respect user-approved resources and existing shutdown protection. Never start a
  scientific run, create cloud resources or extend spending without authorization.

## Researcher Freedom

Blueprints and manifests are hypotheses and inventories, not architecture ceilings.
Codex may implement agent-defined candidates, use public modules beyond the inventory,
change effective training policies, simplify a model, replace it, fuse features,
jointly train components, or use valid grouped OOF residual/stacking.

The parent supplies unchanged benchmark evidence, not a compulsory dense branch.
No universal fixed mixing weight, hidden-size cap, epoch minimum, family whitelist,
mandatory foundation model or requirement that complex models beat simple baselines.
An intentional change from a selected design is allowed with a recorded reason and
sealed actual recipe. Preserve agent code; never overwrite it with a proxy template.

Use node-local code and appropriate task-provider helpers. A training-policy change
belongs in the recipe/provider, not in edits to labels, splits or the evaluation
metric. Core changes during an executed run require versioning and explicit result
invalidation, not silent compatibility edits.

## Active Research Loop

1. Inspect source data, independent sample counts, sampling/confounding, label-input
   coupling, usable observation windows, artifacts and approved resources.
2. Implement/validate the task provider and register TaskSpec, MetricSpec, exact strong
   benchmarks, separate coverage/optimization/confirmation budgets and stopping policy.
3. Replay required baselines. Coverage inventories methods; it is not optimization
   success and does not change optimization visits/Q or exhaust parent expansion.
4. Read an immutable development snapshot and actual OOF errors/diagnostics. Explain
   the parent-conditioned hypothesis, predicted increment, falsification and cost.
   UCT is a parent recommendation; an intentional override needs a research reason.
   Do not call a flat scheduler full paper-equivalent tree-descent MCTS.
5. Submit multiple proposals, retain/re-rank the global pool, and train only the
   selected next rollout. Replenish after each completed optimization measurement.
   Existing queued estimates can be revised using a new snapshot and logged rationale.
6. Handle selected work now: search/acquire missing public resources, implement,
   compile, native-smoke, seal actual contents and formally execute. No internal
   `requires_external_codex` terminal condition: this active Codex does the work.
7. If real implementation/acquisition attempts fail, document evidence and skip that
   candidate, then continue the feasible queue. A missing resolver or uncalled agent
   is not proof that an artifact/model is scientifically unavailable.
8. Validate OOF rows, groups, seeds, metric identity, actual fits, checkpoint contents,
   consumed artifact roles and diagnostics. Only then commit the reward once.
9. Distinguish measured paired evidence from numeric assumptions. Different model,
   representation, composition and loss contexts cannot be pooled into fake independent
   replicates. Artifact availability is feasibility, never a scientific-quality bonus.
10. Stop at the registered allocation, approved boundary or documented permissible
    feasible-space exhaustion. Handling one node is not completion. Freeze finalists
    before confirmation; an unsupported gain can correctly retain the strong baseline.

## Evidence And Validation

Reward, paired delta, ranking and promotion must share an executable metric identity,
including seed/fold aggregation order. A separately named ensemble metric is allowed;
it cannot silently substitute for the primary estimand.

Independent samples are groups, not cells, repeated folds or training seeds. Fixed-OOF
bootstrap is conditional descriptive evidence, not independent confirmation or a
correction for adaptive winner selection. Record convergence and actual effective
training settings; equal epoch counts are not equal optimization opportunity.

Separate execution, protocol, capability reachability, artifact consumption,
applicable attribution, scientific promotion and transfer verdicts. Removing an
unused module is `not_applicable`, not proof that the module is useful. Availability
or large parameter count does not establish scientific value.

Changes need CPU contract/negative/integration tests through the actual shared CLI:
aggregation reversal, coverage isolation, cost monotonicity, semantic duplicates,
replenishment, skip/repair, exactly-once resume, exposure poisoning and frozen-only
confirmation. Test both positive incremental signal and legitimate null results.
Fixtures are engineering tests, never scientific task results.

Before claiming framework benefit, compare with equal-resource random/simple search
and evaluate on independently specified tasks not used for framework development.
Do not repeatedly tune the same exposed demo until it becomes positive.

## Delivery

Report actual capabilities exercised and unexercised, baseline and finalist recipes,
paired evidence, applicable controls, costs/attempts, exposure and negative findings.
Code/API presence is not evidence that the running adapter exercised it.

Only commit source/contracts/tests/small metrics/reports. Never commit data/, nodes/,
weights/checkpoints, raw arrays/exports, environments, private keys or tokens. Inspect
actual staged paths and secrets; preserve user work, historical outputs and old code
that is content-bound by frozen recipes. Keep credentials off shared volumes.
