# Public VCHarness Artifact Alignment

This repository aims to build a runnable VCHarness-style loop with Codex as the code-writing agent. The implementation rule is:

- If the paper or public artifacts specify a behavior, align to that behavior.
- If a behavior is not specified but is required for a complete runnable loop, add an explicit implementation completion and label it as repo-specific.

## Publicly Confirmed Behaviors

From the public VCHarness task page and tree artifacts:

- The system combines biological foundation-model modules, an AI coding agent, and Monte Carlo Tree Search to search perturbation-response model designs.
- The Essential benchmark case study covers HepG2, Jurkat, hTERT-RPE1, and K562 classification tracks.
- Public artifacts index 618 nodes across the showcased tasks.
- The K562 public tree exposes UCT-style fields, including `exploration_c`, `visits`, `Q_v`, `Exploitation`, `Exploration`, `uct`, and `stage`.
- The public tree uses `exploration_c = 1.4142135623730951`, which is sqrt(2).

## Paper-Aligned Defaults In This Repo

For serious one-cell-line reproduction runs, use:

- `--selection-policy uct`
- `--exploration 1.4142135623730951`
- validation Macro-F1 as the rollout reward unless the task explicitly defines another reward
- one node as one complete trainable candidate program/pipeline
- Codex as the implementation agent for selected planned blueprints only
- explicit records for `mcts_selected_parent`, `mcts_selection_policy`, `mcts_candidates`, `visits`, `Q_v`, `Exploitation`, `Exploration`, `uct`, and `stage`

## Repo-Specific Implementation Completions

These are necessary for a runnable system but should not be described as confirmed paper internals unless later source material confirms them:

- exact Codex prompt templates
- exact child proposal grammar
- exact planned-blueprint implementation request format
- stopping rules such as no-improvement threshold, node budget, pending implementation limit, and cost/time budget
- fallback behavior when ESM2/AIDO/scFoundation/STRING/pathway artifacts are missing
- optional PUCT selection mode and empirical priors
- optional diversity, breadth, depth, or repeated-strategy penalties

## Reporting Rule

Final reports must distinguish:

- paper-aligned mechanisms: directly supported by public paper artifacts
- implementation completions: added here because the public sources do not define the missing operational detail
- optional extensions: useful for experimentation but not claimed as paper behavior
