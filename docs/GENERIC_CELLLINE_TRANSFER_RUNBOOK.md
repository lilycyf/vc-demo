# Generic Cell-Line Transfer Runbook

This runbook is the canonical procedure for running a VCHarness-style generic cell-line transfer test. A prompt should only specify run variables; all executable rules below are part of the repo contract.

## Purpose

Validate that the harness can move from one source-backed cell-line task to another without leaking K562-specific data, artifacts, or assumptions. K562 is a validation example, not a runtime template.

## Prompt Variables Contract

Prompts are variable handoffs only. They must not copy cookbook/runbook guardrails. The receiving Codex must read the repo docs and execute the current rules from the files.

Required prompt fields:

| Field | Meaning |
|---|---|
| `BASE_BRANCH` | Branch to start from |
| `RUN_BRANCH` | New branch for this run |
| `CELL_LINE_ID` | Cell line to run |
| `RUN_TYPE` | `loop_self_test` or `full_cellline_run` |
| `TEST_LEVEL` | One of the supported levels below |
| `RUN_DIR` | Fresh experiment directory |
| `TARGET_VAL_MACRO_F1` | Required for `full_cellline_run`; optional for loop tests |

The prompt should say: read `CODEX_AGENT_COOKBOOK.md`, this runbook, `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md`, and `ARTIFACT_ACQUISITION_RUNBOOK.md`. If `CELL_LINE_ID=K562`, also read `OFFICIAL_K562_IMPLEMENTATION_LOOP.md`.

Do not paste detailed runtime rules into the prompt. If a rule needs to change, update the cookbook/runbook first.


## Run Types Are Mandatory

Every handoff must distinguish run type from cell line. Do not infer run type from `TEST_LEVEL`.

| Run type | Purpose | Allowed levels | Default epochs | Quality interpretation |
|---|---|---|---:|---|
| `loop_self_test` | Validate runner wiring, proposal-pool pruning, strict artifact gates, implementation loop, and report counters | `preflight`, `transfer_64x16`, `transfer_150x40` | 1 | May not be used to claim model superiority |
| `full_cellline_run` | Run a real cell-line experiment whose primary objective is to beat the best root | `full_cellline_run` | 8 | Must report whether best generated child beats best root |

Hard rules:

- `full_cellline_run` must use `--level full_cellline_run`.
- `full_cellline_run` must use `--max-epochs >= 8`.
- `full_cellline_run` must explicitly set `--target-val-macro-f1 <score>`; the target cannot be implied.
- `transfer_64x16` and `transfer_150x40` are loop/self-test levels even if they generate many proposals.
- If the user asks to "完整跑" or "真实跑" a cell line, use `RUN_TYPE=full_cellline_run`, not `transfer_64x16`.
- Full runs require an artifact-constrained blueprint filter before training: exclude unresolved/blocked artifact-dependent blueprints from the main run and report exclusions separately.
- Known-unavailable artifacts must not stop the main full run. After source-backed acquisition proves unavailability, record the blocker, suppress/filter dependent blueprint families, and continue searching other feasible paths.

## Test Levels

Use `scripts/run_generic_cellline_transfer_test.py` to expand a short request into the standard invocation.

| Level | Proposals | Trained rollouts | Use |
|---|---:|---:|---|
| `preflight` | 8 | 2 | wiring and artifact readiness smoke |
| `transfer_64x16` | 64 | 16 | default transfer test |
| `transfer_150x40` | 150 | 40 | loop/self-test pressure test after 64x16 passes |
| `full_cellline_run` | 300 | 100 | root-beating full cell-line run; default 8 epochs |

## Standard Invocation

```bash
PYTHONPATH=src python scripts/run_generic_cellline_transfer_test.py   --cell-line ${CELL_LINE_ID}   --run-type ${RUN_TYPE}   --level ${TEST_LEVEL}   --execute
```

For resume:

```bash
PYTHONPATH=src python scripts/run_generic_cellline_transfer_test.py   --cell-line ${CELL_LINE_ID}   --run-type ${RUN_TYPE}   --level ${TEST_LEVEL}   --resume   --execute
```

The script writes `transfer_invocation.json` and `transfer_invocation.md` into the run directory before execution.

### Root-Beating Objective For Full Runs

A `full_cellline_run` is not complete merely because it generates proposals or trains roots. Its primary objective is to find a generated child that both beats the best root and reaches the user-specified target validation Macro-F1. The final report must include:

- best root val/test Macro-F1
- best generated child val/test Macro-F1
- delta child vs root
- target validation Macro-F1
- delta child vs target
- whether both primary objectives were achieved
- if not achieved, root-dominance attribution covering artifact limits, training budget, model-space limits, implementation limits, and optimization stability

If no child beats root or no child reaches the target score, the run can be considered mechanically complete but scientifically not successful for the full-run objective.

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

### Codex Research Acquisition

`requires_codex_research_download_or_build` is not a final stop. It means a separate artifact-acquisition Codex step must run before the transfer test can be called blocked.

When `acquisition_queue.json` or `artifact_acquisition/ACQUIRE_<artifact>.md` appears:

1. Generate the short acquisition handoff:

```bash
PYTHONPATH=src python scripts/generate_artifact_acquisition_prompt.py   --run-dir <run-dir>   --cell-line ${CELL_LINE_ID}   --branch <run-branch>
```

2. The acquisition Codex must search official/primary public sources, inspect expected loader/tensor contracts, and either acquire/build the exact source-backed artifact or write a blocker report.
3. A final `blocked` decision is allowed only after this research step records checked sources and a concrete reason such as unavailable weights, inaccessible license/manual approval, incomplete tensor contract, incompatible vocabulary, non-equivalent reconstruction, or leakage risk.
4. If acquired, update the registry/provenance, rerun artifact audit, then resume the same transfer run with `scripts/run_generic_cellline_transfer_test.py --resume --execute`.
   On resume, previously blocked nodes whose required artifacts now audit as present must be reactivated into the global queue instead of remaining blockers.
5. If not acquired, keep the artifact missing/blocked. Do not train substitute nodes.

For `official_string_gnn_model_dir`, the Codex acquisition step must not treat `official_string_gnn_keep20_graph` or `string_k562_gene_graph` as the model directory. It must find the real `/home/Models/STRING_GNN` checkpoint/model layout or explicitly prove that no public equivalent is available.

## Root Configs

Root configs must point to the selected cell line's task and artifacts. They may not point to K562 data unless `CELL_LINE_ID=K562`.

Expected root families, subject to source-backed availability:

- AIDO embedding MLP
- AIDO+GNN embedding MLP
- optional public static wrapper for the selected cell line

## Realtime Implementation Loop

When `implementation_queue.json` contains a selected planned node, the experiment Codex must handle it immediately, not leave it for a later run:

1. Read node-local `IMPLEMENTATION_REQUEST.md`, `CODEX_IMPLEMENTATION_TASK.md` if present, `artifact_contract.json`, `smoke_contract.json`, `base_config.json`, and `pipeline.json`.
2. If required artifacts are missing, run acquisition or block. Do not write `model.py`.
3. If required artifacts are present, implement only node-local `model.py` and node-local pipeline metadata. Tiny helpers may live under `src/vc_demo/official_<slug>/` only when necessary.
4. Run compile, native smoke, and `train_pending`.
5. In `loop_self_test`, if no safe real implementation can be produced, mark the node `implementation_skipped`, clear it from `implementation_queue.json`, and continue global search. In `full_cellline_run`, do not auto-skip an artifact-present selected node; stop with `requires_realtime_implementation`, implement node-local `model.py` in the same Codex session, then resume. Only documented artifact/source/contract blockers may prevent implementation.
6. Resume or continue the same run without `--reset`.

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

## Full-Run Completion Gate

For `RUN_TYPE=full_cellline_run`, proposal exhaustion alone is not a valid completion condition. The run is invalid if:

- no generated child was trained;
- selected artifact-present planned nodes were converted directly to `implementation_skipped`;
- the trained-rollout budget was not reached and feasible queued candidates remain;
- best generated child cannot be compared to best root.

Such a run must be reported as `framework_failed_no_generated_child_trained` or `requires_realtime_implementation`, not as a completed full experiment.

## Full-Run Completion Gate

For `RUN_TYPE=full_cellline_run`, proposal exhaustion alone is not a valid completion condition. The run is invalid if:

- no generated child was trained;
- selected artifact-present planned nodes were converted directly to `implementation_skipped`;
- the trained-rollout budget was not reached and feasible queued candidates remain;
- best generated child cannot be compared to best root.

Such a run must be reported as `framework_failed_no_generated_child_trained` or `requires_realtime_implementation`, not as a completed full experiment.

## Reports

Each transfer run must produce a final report under the run root, conventionally:

```text
experiments/official_<slug>_generic_transfer_v1/final_generic_transfer_report.md
```

It must summarize task contract, artifacts, acquisition attempts, root baselines, proposal pool, selected/pruned rollouts, trained/pending/failed/blocked counts, best root, best child, and acceptance metrics.
