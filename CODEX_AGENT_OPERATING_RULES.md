# Codex Agent Operating Rules

These rules are for any Codex agent running experiments in this repository.

## Core Role

You are both:

- experiment runner: execute the harness commands and monitor artifacts
- implementation agent: when a planned blueprint is selected, implement the requested `model.py` inside the node-local program directory

## Read Order

Before touching code or running experiments, read these files in order:

1. `E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md`
2. `F_PROGRAM_NODE_HARNESS_UPGRADE.md`
3. `PAPER_LEVEL_SEARCH_SPACE_SPEC.md`
4. `PUBLIC_ARTIFACT_ALIGNMENT.md`
5. `CODEX_AGENT_OPERATING_RULES.md`
6. the concrete task file supplied by the user, for example `TASK_K562_PROGRAM_SEARCH.md`

## Reusable Framework Files

These are framework files. Reuse them instead of writing new ad hoc scripts unless the task explicitly asks for a framework change.

- `src/vc_demo/harness/model_blueprints.py`: model/module design-space manifest
- `src/vc_demo/harness/program_run.py`: root training, parent selection, program-node proposal, pending implementation queue
- `src/vc_demo/harness/program_agent.py`: chooses/materializes blueprint children
- `src/vc_demo/harness/train_pending.py`: trains a `needs_implementation` node after `model.py` is implemented
- `src/vc_demo/harness/mcts.py`: parent selection and backpropagation
- `src/vc_demo/harness/executor.py`: training wrapper
- `src/vc_demo/harness/report.py`: search summary writer
- `src/vc_demo/models.py`: model registry and dynamic custom-program import

## Protected Surfaces

Do not modify unless the task explicitly authorizes it:

- raw data under `data/raw/`
- processed data under `data/cell_lines/`
- train/validation/test split semantics
- metric semantics: validation Macro-F1 is the search reward unless task says otherwise
- previous committed experiment results
- `.gitignore`

Do not commit:

- `data/`
- `experiments/**/nodes/`
- checkpoints such as `*.pt`
- `__pycache__/`
- `*.egg-info/`
- secrets or tokens

## Paper-Level Search-Space Rules

`PAPER_LEVEL_SEARCH_SPACE_SPEC.md` is part of the operating contract for serious VCHarness-style runs. It expands the search target from demo-scale architecture tweaks to a paper-level design space without requiring every model to be pre-implemented.

For serious runs, prefer nodes that make meaningful design-space moves:

- Level 1: training-only refinement
- Level 2: compact architecture change
- Level 3: representation change
- Level 4: multimodal fusion change
- Level 5: biological prior or foundation-model module

Do not spend most of a serious-search budget on Level 1 changes. When planned blueprints are selected, implement only the requested node-local `model.py` and record any missing external artifact or fallback explicitly.

A serious one-cell-line run should aim for at least 30 trained nodes, multiple root families, at least two on-demand planned-blueprint implementations, and at least one Level 4 or Level 5 child unless the user provides a smaller budget.

## Blueprint Rules

A blueprint can be one of:

- `implemented`: `program_agent.py` can generate `model.py` immediately
- `planned`: the harness may generate an `IMPLEMENTATION_REQUEST.md`, but it must not pretend that code exists

If a node has `status = needs_implementation`:

1. open its `IMPLEMENTATION_REQUEST.md`
2. implement only that node's `model.py`
3. keep the model compact enough for the current GPU
4. run compile/smoke validation
5. train it with `python -m vc_demo.harness.train_pending`
6. update final summary/conclusion

## Implementation Contract

Every node-local `model.py` must define:

```python
class GeneratedModel(nn.Module):
    def __init__(self, spec):
        ...
    def forward(self, x):
        ...
```

`forward(x)` must return logits shaped:

```text
[batch, n_targets, n_classes]
```

The model should use only fields available on `ModelSpec` unless the implementation request explicitly provides more data.

## MCTS Audit Rules

For program-node searches, parent selection must use the harness MCTS layer rather than hand-picked parents. The proposal for each child must preserve the `mcts_selected_parent`, `mcts_selection_policy`, and `mcts_candidates` fields.

The paper-aligned serious-search policy is `uct` with `exploration_c = sqrt(2) = 1.4142135623730951`, because the public VCHarness K562 tree artifacts expose UCT-style fields (`visits`, `Q_v`, `Exploitation`, `Exploration`, `uct`, and `stage`). PUCT remains available only as a repo-specific optional extension or ablation. Final reports must mention whether the run used UCT or PUCT and must not describe optional extensions as paper-confirmed behavior.

## Paper-Alignment Rule

When public paper artifacts define a mechanism, follow it. When they do not define a mechanism but the runnable loop needs one, implement the missing piece as an explicit repo-specific completion and record that status in the proposal/final report. Do not invent hidden paper details.


## Experiment Loop

Use this loop for program-node experiments:

1. Run `program_run` with the task's root configs and budget.
2. If it stops with pending implementations, inspect `implementation_queue.json`.
3. Implement queued `model.py` files one at a time.
4. Train each implemented node with `train_pending.py`.
5. Continue search if the task budget allows.
6. Write final conclusion.
7. Commit only allowed files and push to the requested branch.

## Required Final Conclusion

The final conclusion must include:

- command(s) used
- dataset/split and metric
- root baselines
- best overall node
- improvement over best root
- tree path to best node
- pending/failed nodes
- whether improvements came from config search, implemented program nodes, or newly implemented planned blueprints
- limitations versus the VCHarness paper

## K562 Artifact Policy: Derived vs Blocked

The official K562 strict search distinguishes deterministic derived artifacts from artifacts that require external provenance.

### Automatically Derivable

- `class_distribution`: derive with `scripts/build_k562_class_distribution.py` from `data/cell_lines/official_k562_cls/train.tsv` only. The resolver must not read validation or test labels to compute class weights. The artifact must record raw counts, training-label remap, recommended class weights, `split_used=train`, and `forbidden_splits=[val,test]`.
- `pathway_memberships`: derive only through the configured Reactome/MSigDB source-backed resolver and exact official target-gene order.

### Must Block Unless Source Is Configured

- `regulatory_network_artifact`: block unless a real public/approved TF-target or regulatory network source, version, filtering rule, checksum, and K562 target-gene alignment are recorded. Do not substitute STRING/PPI or pathway memberships and call it regulatory.
- `single_cell_foundation_model_artifact`: block unless a real scGPT/scFoundation/single-cell foundation checkpoint or row-aligned embedding artifact is configured with preprocessing, vocabulary, source, and coverage. Do not train a small expression fallback in strict mode.

If an artifact is listed as blocked, the correct action is to generate/complete an acquisition task, not to implement or train a fallback node.

