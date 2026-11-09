# Generic Cell-Line Transfer Runbook

## Current Protocol

Read CODEX_AGENT_COOKBOOK.md, RESEARCH_PROTOCOL.md and GENERIC_RESEARCH_RUNBOOK.md.
Fresh research uses `scripts/run_research_harness.py` (research_v2). This document
only describes what a source-backed cell-line classification provider must supply.
It is not the universal template for regression, trajectories or survival.

## Classification Provider Responsibilities

Specify the actual cell line/task, source data and eligibility, independent
perturbation/sample grouping, split, target-gene order and label vocabulary.
Do not copy an example cell line, its artifacts, labels or architecture choices.

Register the full primary MetricSpec, including aggregation order and fixed
classes. DEG tensors may be flattened to explicit prediction rows if each retains
the correct independent group and immutable target mapping. Providers return OOF
probabilities, not averaged class IDs or validation-fallback test scores.

Implement evaluate_development and predict_confirmation using actual task/model
code. Preserve train-only preprocessing and target/vocabulary alignment. Classification
stacking needs OOF logits/probabilities; continuous-regression residual helpers are
not silently applicable to category IDs.

Run provider-specific group/split, target-order and heldout-poisoning tests. Register
strongest exact benchmark recipes and real artifact policies. Heavy pretrained
modules require their authentic checkpoints; a graph or cached embedding is not
the checkpoint unless the candidate explicitly proposes that different module.

Operate the shared loop from GENERIC_RESEARCH_RUNBOOK.md. The active Codex researches,
implements, repairs/acquires and continues the queue. Scientific targets are optional
unless required by the user and registered before confirmation. No requirement that
every complex model beats every simple baseline or reaches a historical demo score.

## Historical Classification Profiles

`run_generic_cellline_transfer_test.py` and its preflight/64x16/150x40/full profiles
are v1 entrypoints. Their node counts, one/eight-epoch defaults and classification
backend are not v2 scientific policy. Dry-run legacy inspection remains possible.

An executed legacy resume must explicitly request --legacy-protocol --resume and
reference existing open state. Fresh v2 sessions use the new shared CLI/provider;
do not silently launch a legacy full run and label it v2. Regression/lineage tasks
must never be routed through the old classification executor.

## Acceptance

Use GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md and report independent layers, actual
compositions exercised, unused artifact controls as N/A, root/finalist predictions,
paired evidence, resource costs, exposure and semantic versus measurement counts.
