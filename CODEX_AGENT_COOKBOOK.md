# Codex Agent Cookbook For VCHarness-Style Runs

This repo does not call the Codex API internally. The Codex agent is the external executor launched by the user in a Codex window. The repo's job is to provide search state, queues, prompts, guardrails, runnable commands, and audit artifacts. The Codex agent's job is to operate the repo end to end on RunPod.

## Document Ownership

Rules live in the repo documents, not in copied chat prompts.

- `CODEX_AGENT_COOKBOOK.md` is the canonical source for universal agent rules, guardrails, git hygiene, artifact acquisition semantics, and realtime implementation semantics.
- `docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md` is the canonical source for how to execute a generic cell-line run.
- `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md` is the canonical source for pass/fail checks.
- `ARTIFACT_ACQUISITION_RUNBOOK.md` is the canonical source for source-backed artifact acquisition.
- K562-specific details belong in `OFFICIAL_K562_IMPLEMENTATION_LOOP.md`, not in generic prompts.

Experiment prompts must be variable-only handoffs. They should name the branch, cell line, run type, target score, run directory, and output branch, then instruct Codex to read the repo docs. Do not duplicate long cookbook/runbook rules in prompts; duplicated rules drift and become stale.

## Mental Model

```text
repo harness = orchestrator, state machine, queue writer, evaluator, auditor
Codex window = coding agent, artifact researcher, implementation fixer, experiment runner
```

Do not add code that tries to call Codex/OpenAI APIs from inside this repo for the formal run. If a selected node needs implementation, the harness writes `IMPLEMENTATION_REQUEST.md` or `CODEX_IMPLEMENTATION_TASK.md`; the active Codex agent must handle that task during the current run. For loop/self-tests, an unimplemented node may be marked `implementation_skipped` and the global queue may continue. For `full_cellline_run`, artifact-present selected nodes must not be passively auto-skipped or left for a later Codex. `requires_realtime_implementation` is an action point for the current Codex session: inspect the task, implement node-local `model.py`, smoke/train it, and resume. If a real implementation cannot be produced after documented attempts, mark the candidate as implementation-infeasible/skipped with a precise reason and continue the global queue; do not leave a pending queue for later.


## Codex Autonomy Policy

The guardrails protect scientific validity; they do not define the entire model. Codex is expected to act as an active model engineer inside those boundaries.

Hard constraints:

- Do not change split semantics, label construction, target-gene order, reward metric, test-label usage, or artifact provenance.
- Do not fabricate artifacts, train fallback models, or call compact/proxy/simplified stand-ins real implementations.
- Do not backpropagate reward for untrained, skipped, blocked, failed, or pruned proposals.

Autonomous choices Codex should make during selected-node implementation:

- Treat the selected blueprint as a research hypothesis or mutation, not as the full model specification.
- Implement child nodes as `parent pipeline + selected modification` by default.
- Preserve useful parent structure, especially dense/context trunks, dense target-logit branches, residual routes, and proven artifact branches, unless the request explicitly says to replace them.
- Add biological/target/graph modules as residual, gated, additive, bilinear, or attention branches that can compete with the parent baseline instead of deleting the parent signal.
- Use `search_memory.json`, `parent_summary.json`, previous successful motifs, and failure/blocker records to decide the concrete implementation.
- If a faithful implementation has multiple valid designs, choose the most competitive artifact-backed design that fits the current GPU and documents the choice.
- If an artifact/source/contract is impossible to verify, suppress or block that family and continue the global queue; do not let one unavailable family end the search when feasible families remain.

A full run should therefore produce competitive, auditable children, not a sequence of isolated minimal blueprint demos.

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
- Stop with a blocker only when the source cannot be verified, the public files are incomplete/non-equivalent, the tensor contract cannot be proven, the source is license-gated/manual-approval-only, or the artifact is infeasible for the current approved compute/storage budget. Otherwise acquire/build it immediately, audit it, and resume the same run. Do not fabricate a substitute.

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
6. If `implementation_queue.json` is non-empty, handle the selected node immediately. In `full_cellline_run`, artifact-present selected nodes must be implemented, compiled, native-smoked, trained, and backpropagated before the run can be considered valid. `implementation_skipped` is allowed only for loop/self-tests or after a documented artifact/contract blocker; it is not a substitute for writing `model.py` in a full run.
7. If `acquisition_queue.json` is non-empty, handle it in the same Codex session: run `artifact_acquisition`, execute any known resolver, and if it emits `ACQUIRE_<artifact>.md`, immediately search/download/build the real source-backed artifact, audit it, update registry, and resume. Do not hand it off or stop at queue creation. Stop with a blocker only after the acquisition attempt proves no verifiable source exists, public files are incomplete/non-equivalent, or source/provenance/shape/row-order/vocabulary cannot be verified.
8. Resume or continue the same run directory without changing data/splits/metrics.
9. Write `final_conclusion.md` with best root, best overall, improvement, artifact use, failures/blockers, and whether the result supports the research question.
10. Commit only allowed files and push the run branch.

## Stop Conditions

Stop the formal run when one of these is true:

- Budget is exhausted.
- No-improvement criterion is reached.
- A missing artifact requires source research and cannot be acquired safely.
- No queued executable candidate remains after skipped implementations and documented artifact blockers.
- Repeated implementation repair attempts fail and the failure is recorded. In `full_cellline_run`, this is a real failure unless an artifact/source/contract blocker is documented.

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

## Paper Alignment Layers 5-8

See `PAPER_ALIGNMENT_LAYERS_5_8.md` for benchmark audit, search scale planning, failure repair workflow, and paper-style final analysis.
