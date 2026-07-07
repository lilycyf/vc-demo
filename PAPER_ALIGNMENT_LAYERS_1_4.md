# Paper Alignment Layers 1-4

This document records the repo-side alignment work for the first four gaps between the demo framework and a single-cell-line VCHarness-style paper reproduction.

## 1. Codex Agent Execution Layer

The repo does not call the Codex API internally. The active user-launched Codex window is the coding/research agent. The repo provides state, queues, task files, guardrails, and audit outputs.

Aligned pieces:

- `CODEX_AGENT_COOKBOOK.md` defines what Codex may change, must not change, and when source search is required.
- `IMPLEMENTATION_REQUEST.md` and `CODEX_IMPLEMENTATION_TASK.md` are the node-local coding task interface.
- `ACQUIRE_<artifact>.md` is the artifact research/acquisition task interface.
- `search_memory.json` records successes, failures, blocked artifacts, blueprint counts, parent expansions, and inferred motifs.
- `repair_prompt(run_dir, node_name)` in `search_memory.py` provides a structured repair prompt for failed nodes.

Still intentionally external:

- Arbitrary model implementation and artifact research are performed by Codex in the repo, not by an internal API caller.

## 2. MCTS And Proposal Policy Layer

The repo keeps UCT/PUCT parent selection, but proposal selection is now more paper-like because it is stateful and artifact-aware.

Aligned pieces:

- MCTS selects the trained parent node.
- Artifact-aware blueprint ranking prefers executable high-level programs with present artifacts.
- Duplicate guards avoid repeatedly expanding the same blueprint on one parent and cap global blueprint repeats.
- `search_memory.json` summarizes prior expansions and can be read by the next Codex turn.
- `pipeline_grammar.py` maps each blueprint into a structured pipeline program instead of treating it as a single flat label.

Remaining gap:

- The proposal policy is still deterministic/grammar-guided, not a learned proposal model. Codex can still implement selected planned nodes using the cookbook.

## 3. Model Space / Pipeline Grammar Layer

The search space now has explicit dimensions that match the kind of program search described in the paper.

Grammar dimensions:

- representation
- perturbation_side
- target_side
- fusion
- prior
- head
- training_strategy
- fine_tuning

Implemented support:

- `pipeline_grammar.py` defines `PipelineProgram` entries for tabular, target-aware ESM2, STRING/PPI, pathway, scFoundation, AIDO, adapter, calibration, class-balanced, and conditional-computation families.
- `program_agent.py` attaches `pipeline_program` to proposals and pipeline manifests.
- `preflight.py` emits `pipeline_grammar_dimensions` and `pipeline_grammar_readiness`.
- `final_analysis.py` groups trained nodes by strategy family and reports grammar alignment.

Remaining gap:

- Some grammar programs are still planned and require Codex implementation or artifact acquisition before execution.

## 4. Artifact Layer

The artifact layer now distinguishes present, automatically resolvable, research-required, and contract-undefined artifacts.

Aligned pieces:

- `artifact_readiness.py` writes an action matrix for every registered artifact.
- `artifact_acquisition.py` verifies present artifacts, executes known resolvers, or emits Codex acquisition tasks.
- `preflight.py` includes artifact readiness and grammar readiness in one report.
- `configs/artifacts/acquisition_sources.json` defines known resolvers and research questions.

Current K562 artifact state:

- Present/usable: ESM2 gene embedding, ESM2 K562 target manifest, STRING K562 graph.
- Requires Codex official-source search: AIDO, scFoundation, pathway membership.
- Requires contract definition if selected: pretrained encoder.

Formal rule:

- Missing artifacts must trigger acquisition/search/blocker records, not fallback training, unless the user explicitly requests an ablation.

## Commands

Artifact readiness:

```bash
python -m vc_demo.harness.artifact_readiness   --registry configs/artifacts/k562_registry.json   --sources configs/artifacts/acquisition_sources.json   --output experiments/<run>/artifact_readiness.json
```

Preflight with grammar and artifact readiness:

```bash
python -m vc_demo.harness.preflight   --root-configs configs/k562_roots/root_concat_gated_mlp.json configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json configs/k562_roots/root_concat_esm2_target_aware_bilinear.json   --artifact-registry configs/artifacts/k562_registry.json   --cell-line K562   --output experiments/<run>/preflight.json
```

Final analysis:

```bash
python -m vc_demo.harness.final_analysis   --run-dir experiments/<run>   --output experiments/<run>/final_analysis.md
```
