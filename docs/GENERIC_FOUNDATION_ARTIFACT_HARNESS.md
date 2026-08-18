# Generic Foundation Artifact Harness Framework

This document separates the reusable harness layer from cell-line or task-specific configuration.

## Universal Framework Layer

The following behavior must be cell-line agnostic:

- load the task contract from the selected root configs and dataset manifest;
- load artifact registry from `--artifact-registry` or `configs/artifacts/<cell_line_slug>_registry.json`;
- audit artifact presence using both `path` and `expected_path`;
- treat empty model directories as missing;
- generate proposal pools and train only selected rollouts;
- when a selected rollout needs artifacts, run source-backed acquisition/build first;
- block only after source, shape, vocabulary, row order, provenance, license, or compute/storage feasibility cannot be verified;
- when a selected rollout needs implementation and required artifacts are present, the active Codex session must implement, compile, smoke, train, and backprop, or mark a documented implementation-infeasible skip and continue global queue;
- never use fallback/proxy/compact replacements while claiming foundation artifact usage;
- never backprop untrained, blocked, skipped, failed, or pruned candidates.

Generic code locations:

- `src/vc_demo/harness/artifact_registry.py`
- `src/vc_demo/harness/artifact_acquisition.py`
- `src/vc_demo/harness/autonomous_run.py`
- `src/vc_demo/harness/implementation_agent.py`
- `src/vc_demo/harness/program_run.py`
- `scripts/run_generic_cellline_transfer_test.py`

## Task-Specific Layer

Cell-line or dataset-specific files define facts, not control-flow policy:

- root configs;
- dataset preparation scripts;
- artifact registry entries and expected paths;
- task contract, label semantics, target order, split policy;
- optional model-space priorities for that task.

Examples:

- HELF perturbation task: `configs/artifacts/helf_perturb_registry.json`, `configs/helf_perturb_search_space.json`, `docs/HELF_PERTURBATION_*`.
- K562 official task: `configs/artifacts/k562_registry.json`, `OFFICIAL_K562_IMPLEMENTATION_LOOP.md`.

## What This Upgrade Fixed

- Artifact registry loading is now generic instead of defaulting all non-K562 cell lines to K562.
- Registry audits now recognize `expected_path` as well as `path`.
- Empty model directories no longer count as present foundation artifacts.
- Artifact acquisition tasks name the active cell line and registry path instead of hard-coding K562.
- The autonomous loop treats `trained` as a successful implementation-agent result.
- HELF acquisition queue items now expose one missing artifact per item, with artifact id and expected path, so a generic resolver can process them.

## Operational Rule

A short experiment prompt should only provide variables such as branch, cell line, run type, target score, and run directory. Codex must read the repo docs and apply this generic framework. Long copied prompts should not re-encode framework rules.

## Parent-Preserving Foundation Children

A reusable foundation-aware run must distinguish artifact acquisition from artifact use. Once an artifact is source-backed and aligned, the default implementation pattern is augmentation:

```text
strong dense parent branch -> base logits
source-backed artifact branch -> residual correction
final logits = base logits + gated residual correction
```

This policy is generic across cell lines. It avoids the common failure mode where a pathway/graph/foundation prior replaces the dense perturbation signal and underperforms a root. Search should still explore ablations, but ablations must be explicitly labeled and should not be the default child behavior.

Candidate-pool behavior:

- Generate both artifact-present and missing-artifact foundation proposals.
- Missing artifacts go through acquisition/block logic.
- Artifact-present foundation proposals receive enough rollout priority to be trained, so the framework can test whether real priors help.
- The priority is a feasibility/coverage control, not a biological claim.

Required audit fields for trained foundation children:

- `proposal_type = foundation_artifact_blueprint`
- `required_artifacts` and `missing_required_artifacts`
- `foundation_augmentation_policy`
- `fallback/proxy = 0`
- best validation Macro-F1 and report-only test Macro-F1


## Artifact Usefulness Controls

Foundation-aware search must test whether a source-backed artifact adds information beyond a stronger dense model. When an artifact-present proposal is generated, the harness should, when budget allows, add a paired control:

```text
same parent + comparable dense capacity/loss choices + no artifact tables
```

The paired control is not a fallback. It is an attribution experiment. Its role is to answer whether the artifact branch contributes beyond capacity or optimization.

Required report files:

- `artifact_usefulness_report.json`
- `artifact_usefulness_report.md`

Required fields:

- best root;
- best generated child;
- best foundation-artifact child;
- best dense no-artifact child;
- best dense matched no-artifact control;
- foundation-vs-root validation gain;
- foundation-vs-dense-control validation gain;
- paired artifact/control comparisons.

A biological artifact usefulness claim is valid only when source-backed artifact children beat the relevant dense no-artifact comparator under validation-only selection. Otherwise the result is a model-search win, not an artifact-evidence win.


## Search-Space Manifest Audit

A foundation-aware harness should distinguish the declared search-space universe from the currently executable subset. Run:

```bash
PYTHONPATH=src python scripts/audit_helf_search_space.py
```

The audit reports:

- total foundation blueprints;
- executable-now blueprint count;
- artifact-present blueprint count;
- artifact-missing blueprint count;
- implementation status counts;
- family coverage;
- combinatorial dimension product.

Fast runs are expected when only a small executable subset is available or when epoch/rollout budgets are low. A run should not be described as full search-space coverage unless the audit shows that the relevant artifact families are present or explicitly blocked after source-backed acquisition.

