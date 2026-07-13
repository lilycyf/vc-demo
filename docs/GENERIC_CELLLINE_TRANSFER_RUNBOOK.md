# Generic Cell-Line Transfer Runbook

This runbook is the canonical procedure for running a VCHarness-style generic cell-line transfer test. A prompt should only specify the target `CELL_LINE_ID` and test level; all rules below are part of the repo contract.

## Purpose

Validate that the harness can move from one source-backed cell-line task to another without leaking K562-specific data, artifacts, or assumptions. K562 is a validation example, not a runtime template.

## Short Prompt Contract

A valid experiment handoff can be as short as:

```text
Run generic cell-line transfer test on RunPod `/workspace/vc-demo`.
Branch: generic-cellline-runner-fix
CELL_LINE_ID: <cell line>
TEST_LEVEL: transfer_64x16
Follow docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md and docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md.
Push results to generic-cellline-transfer-test-<slug>.
```

## Test Levels

Use `scripts/run_generic_cellline_transfer_test.py` to expand a short request into the standard invocation.

| Level | Proposals | Trained rollouts | Use |
|---|---:|---:|---|
| `preflight` | 8 | 2 | wiring and artifact readiness smoke |
| `transfer_64x16` | 64 | 16 | default transfer test |
| `transfer_150x40` | 150 | 40 | medium pressure test after 64x16 passes |

## Standard Invocation

```bash
PYTHONPATH=src python scripts/run_generic_cellline_transfer_test.py   --cell-line ${CELL_LINE_ID}   --level ${TEST_LEVEL}   --execute
```

For resume:

```bash
PYTHONPATH=src python scripts/run_generic_cellline_transfer_test.py   --cell-line ${CELL_LINE_ID}   --level ${TEST_LEVEL}   --resume   --execute
```

The script writes `transfer_invocation.json` and `transfer_invocation.md` into the run directory before execution.

## Source-Backed Task Contract

Before running a non-K562 cell line, create or verify:

```text
data/cell_lines/official_<slug>_cls/manifest.json
data/cell_lines/official_<slug>_cls/train.tsv
data/cell_lines/official_<slug>_cls/val.tsv
data/cell_lines/official_<slug>_cls/test.tsv
data/cell_lines/official_<slug>_cls/target_genes.tsv
```

The task contract must define:

- cell-line id
- split sizes
- target gene count
- target gene order
- label semantics
- reward metric: validation Macro-F1
- test metric: final report only
- source URL, source file, checksum, and build script when available

If these cannot be verified, stop with a blocker. Do not reuse K562 task files.

## Artifact Registry

Each transfer needs:

```text
configs/artifacts/<slug>_registry.json
configs/official_<slug>_roots/*.json
```

Artifacts must be labeled as `present`, `missing`, `acquired`, `reusable`, `cell_line_specific`, or `blocked`, with source/provenance notes. Missing artifacts enter acquisition first. If source, shape, row order, vocabulary, or provenance cannot be verified, block. Do not fallback.

## Root Configs

Root configs must point to the selected cell line's task and artifacts. They may not point to K562 data unless `CELL_LINE_ID=K562`.

Expected root families, subject to source-backed availability:

- AIDO embedding MLP
- AIDO+GNN embedding MLP
- optional public static wrapper for the selected cell line

## Pending Implementation Loop

When `implementation_queue.json` contains a selected planned node:

1. Read node-local `IMPLEMENTATION_REQUEST.md`, `CODEX_IMPLEMENTATION_TASK.md` if present, `artifact_contract.json`, `smoke_contract.json`, `base_config.json`, and `pipeline.json`.
2. If required artifacts are missing, run acquisition or block. Do not write `model.py`.
3. If required artifacts are present, implement only node-local `model.py` and node-local pipeline metadata. Tiny helpers may live under `src/vc_demo/official_<slug>/` only when necessary.
4. Run compile, native smoke, and `train_pending`.
5. Resume the same run without `--reset`.

Allowed edits during pending implementation:

```text
<run>/programs/<node>/model.py
<run>/programs/<node>/pipeline.json
src/vc_demo/official_<slug>/  # tiny helpers only when necessary
```

Forbidden edits:

- split files
- labels
- target gene order
- reward metric
- test labels
- artifact provenance
- unrelated cell-line files
- public wrapper code unless the task is explicitly public-wrapper compatibility
- raw data/artifact files as part of a model workaround

## Hard Guardrails

- no fallback model
- no compact/proxy model in formal tests
- no K562 data or artifact leakage into another cell line
- no test-set tuning
- unselected proposals are pruned, not trained
- selected rollout must train before backprop
- generated child must not route to `external_static_node` unless it is explicitly a public static wrapper candidate

## Reports

Each transfer run must produce a final report under the run root, conventionally:

```text
experiments/official_<slug>_generic_transfer_v1/final_generic_transfer_report.md
```

It must summarize task contract, artifacts, acquisition attempts, root baselines, proposal pool, selected/pruned rollouts, trained/pending/failed/blocked counts, best root, best child, and acceptance metrics.
