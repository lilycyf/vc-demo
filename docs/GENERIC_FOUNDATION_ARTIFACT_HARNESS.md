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
