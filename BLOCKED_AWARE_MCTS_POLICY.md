# Blocked-Aware MCTS Blueprint Policy

This repo keeps the paper-aligned MCTS parent selection formula intact: parent nodes are selected by UCT or optional PUCT in `src/vc_demo/harness/mcts.py`. The blocked-aware policy only affects the child blueprint generator after a parent is selected.

## Why This Exists

Strict official K562 mode must not train fallback models when a required artifact is missing. Earlier resume runs showed that MCTS could repeatedly spend expansion budget on the same unavailable artifact families, especially `single_cell_foundation_model_artifact`, `scfoundation_cell_embeddings`, and `regulatory_network_artifact`. That behavior is wasteful but should not be solved by pretending artifacts are present.

## Policy

The policy reads `search_memory.json` rebuilt from the current tree. A blueprint is suppressed only when the current run already contains repeated artifact-acquisition blockers for that blueprint, its paper family, or its required artifact IDs.

This is not an artifact-present ranking signal. A blueprint is not preferred merely because its artifacts are present. The policy only reallocates budget away from repeatedly blocked families so the search can keep exploring other paper-level families while acquisition tasks remain recorded.

Current thresholds are defined in `src/vc_demo/harness/program_agent.py`:

- `BLOCKED_ARTIFACT_SUPPRESSION_THRESHOLD = 2`
- `BLOCKED_STRATEGY_SUPPRESSION_THRESHOLD = 2`
- `BLOCKED_FAMILY_SUPPRESSION_THRESHOLD = 3`

When all choices are suppressed, the generator falls back to the full ranked pool instead of crashing.

## Strict Artifact Behavior

Suppression does not delete blockers. Existing blocked nodes remain in `tree.json`, `acquisition_queue.json`, reports, and final gap attribution. If a missing artifact later becomes available and the registry is updated, the blocker disappears from future memory rebuilds and the family becomes eligible again.

Fallback training remains forbidden in strict official mode.

## Operational Notes

- Default official wrapper behavior enables `--artifact-aware-blueprint-policy`.
- Use `--no-artifact-aware-blueprint-policy` only for ablation or debugging.
- The policy is visible in proposal metadata under `scientific_selection.policy = scientific_priority_with_blocked_artifact_budget_reallocation`.
- Suppressed choices expose `suppressed_by_blocked_artifact`, `repeated_blocked_artifacts`, `strategy_block_count`, and `family_block_count`.
