# Codex Agent Cookbook For VCHarness-Style Runs

This repo does not call the Codex API internally. The Codex agent is the external executor launched by the user in a Codex window. The repo's job is to provide search state, queues, prompts, guardrails, runnable commands, and audit artifacts. The Codex agent's job is to operate the repo end to end on RunPod.

## Mental Model

```text
repo harness = orchestrator, state machine, queue writer, evaluator, auditor
Codex window = coding agent, artifact researcher, implementation fixer, experiment runner
```

Do not add code that tries to call Codex/OpenAI APIs from inside this repo for the formal run. If a node needs implementation, the harness writes `IMPLEMENTATION_REQUEST.md` or `CODEX_IMPLEMENTATION_TASK.md`; the active Codex agent reads that task and edits the repo directly.

## What Codex May Change

- Node-local `model.py` under a selected `experiments/<run>/programs/<node>/` directory.
- Small node-local docs that explain the implementation choice.
- Harness code when the task is explicitly framework development rather than a formal frozen experiment.
- Artifact registry metadata after a real artifact has been acquired or built from a documented public source.
- Small experiment metadata: `tree.json`, `search_summary.md`, `final_conclusion.md`, `run_manifest.json`, `search_memory.json`, queues, proposals, audit JSON, and acquisition summaries.
- Scripts that build documented artifacts, if source, version, and filtering/coverage are recorded.

## What Codex Must Not Change During A Formal Experiment

- Train/validation/test split semantics.
- Label construction or metric semantics.
- Test labels for tuning or selection.
- Existing root baseline configs, unless the task explicitly says to create a new root config branch.
- Raw data files as a way to improve metrics.
- `data/` contents in git commits, unless the user explicitly asks to commit a small source-backed artifact summary.
- Checkpoints, `nodes/`, cache files, pycache, egg-info, secrets, SSH keys, tokens.
- Artifact registry entries from missing to present unless the expected file exists and provenance is documented.

## What Requires Search Or External Source Verification

Codex should search official or primary sources before proceeding when any of these appears in `acquisition_queue.json` or a task file:

- `scfoundation_cell_embeddings`
- `aido_gene_or_cell_embeddings`
- `pathway_membership_matrix`
- `pretrained_encoder`
- Any new foundation model checkpoint or embedding table
- Any graph/pathway prior not already present in the registry

Rules for searched artifacts:

- Prefer official model/project pages, paper author repositories, HuggingFace datasets from the authors, STRING/Reactome/GO/MSigDB official releases, or documented checkpoints.
- Record URL, version/date, file size or checksum when feasible, filtering rules, alignment procedure, and gene/cell coverage.
- If the source is license-gated, ambiguous, missing, or too large for the current budget, stop and write a blocker. Do not fabricate a substitute.

## What Does Not Require Search

- Running `preflight`.
- Running `program_run` or `autonomous_run`.
- Training an already executable node.
- Implementing a selected node using only existing tensors, config fields, and registered present artifacts.
- Using `string_k562_gene_graph` when the registry audit reports it present.
- Using the already built ESM2 target manifest when the registry audit reports it present.

## Formal Run Procedure

1. Start from the branch named by the user.
2. Create a new run branch.
3. Run `python -m vc_demo.harness.preflight`.
4. If preflight is not ready, fix only the reported setup issue or stop with a blocker.
5. Run `python -m vc_demo.harness.autonomous_run` with the task budget.
6. If `implementation_queue.json` is non-empty, implement only the selected node-local `model.py` or follow `CODEX_IMPLEMENTATION_TASK.md`.
7. If `acquisition_queue.json` is non-empty, run `artifact_acquisition`; if it emits `ACQUIRE_<artifact>.md`, search/download/build the real artifact or stop with a blocker.
8. Resume the same run directory without changing data/splits/metrics.
9. Write `final_conclusion.md` with best root, best overall, improvement, artifact use, failures/blockers, and whether the result supports the research question.
10. Commit only allowed files and push the run branch.

## Stop Conditions

Stop the formal run when one of these is true:

- Budget is exhausted.
- No-improvement criterion is reached.
- A missing artifact requires source research and cannot be acquired safely.
- A blueprint is underspecified and cannot be implemented without changing the scientific task.
- Repeated implementation repair attempts fail and the failure is recorded.

## Required Records

Every formal run should preserve:

- `preflight.json`
- `tree.json`
- `search_memory.json`
- `run_manifest.json`
- `search_summary.md`
- `implementation_queue.json`
- `acquisition_queue.json`
- `failures.json`
- `proposals/*.json`
- `final_conclusion.md`

## Paper Alignment Layers 1-4

See `PAPER_ALIGNMENT_LAYERS_1_4.md` for the current alignment of the Codex execution layer, MCTS/proposal policy, model-space grammar, and artifact readiness layer.
