# Paper-Level Framework Upgrade 2

This upgrade moves the repo from a model-only program-node harness toward a single-cell-line paper-style automated modeling framework.

## 1. Artifact Registry

The registry lives at:

```text
configs/artifacts/k562_registry.json
```

It records ESM2, AIDO, scFoundation, STRING, and pathway artifacts as explicit resources with:

- id
- family/provider
- expected path
- source
- usable sides such as perturbation gene, target gene, cell state, graph, pathway
- required blueprints
- do-not-fabricate policy

Audit it with:

```bash
python -m vc_demo.harness.artifact_registry --cell-line K562
```

Each formal search writes:

```text
<run_dir>/artifact_registry_audit.json
```

## 2. Pipeline-Level Program Nodes

A node is no longer only a `model.py`. A node may now carry:

```text
pipeline.json
```

The manifest format is:

```text
vc_demo_pipeline_node.v1
```

It can declare:

- model entrypoint
- training/loss choice
- artifact requirements
- artifact usage claims
- guarded config patches under `model`, `training`, or `data`
- split/metric/artifact guardrails

The executor materializes the pipeline before training, writes `pipeline.json`, writes `pipeline_audit.json`, and records pipeline summary into `metrics.json` and `tree.json`.

## 3. Report Upgrade

Search summaries now include:

- pipeline kind
- loss type
- artifact sides used
- required and missing artifacts
- artifact manifest path
- per-node duration seconds
- artifact and pipeline audit table

This makes it possible to distinguish:

- passive row-level embedding use
- true target-gene artifact use
- graph/pathway/cell-state claims
- missing-artifact blocked nodes
- training-strategy-only nodes

## Agent Rule

A Codex experiment agent must not claim a node uses ESM2/AIDO/scFoundation/STRING/pathway unless the node's pipeline audit or artifact registry supports that claim. Missing artifacts should be recorded as missing or blocked, not replaced silently.

## Strict Artifact Mode

Formal testing uses strict artifact mode by default. `program_run` blocks and stops when a selected blueprint requires a missing artifact according to the registry. `train_pending` also refuses to train a pending node with missing artifacts unless `--allow-missing-artifact-fallbacks` is explicitly passed for a separate ablation. This prevents fallback models from contaminating artifact-search conclusions.

## Artifact Acquisition Queue

Strict artifact mode now distinguishes missing-artifact acquisition from fallback. When a selected blueprint requires a missing artifact, `program_run` writes `acquisition_queue.json` and stops with `requires_artifact_acquisition`. The correct next step is to search/download/build the real artifact, update the registry, rerun audit, and resume strict search.


Artifact acquisition is now resolver-backed: `src/vc_demo/harness/artifact_acquisition.py` consumes `acquisition_queue.json`, verifies or executes known source-backed artifact builders from `configs/artifacts/acquisition_sources.json`, and generates strict Codex acquisition tasks for artifacts that require official-source research. This keeps strict searches active without allowing fallback artifacts.

## Pre-Test Hardening

- `program_run` now writes `run_manifest.json` with commit, search parameters, artifact audit, queue paths, MCTS state, and best-node summary.
- Blueprint choice is artifact-aware by default: executable blueprints whose required artifacts are present are ranked before blueprints that would immediately require acquisition. Use `--no-artifact-aware-blueprint-policy` only for ablation.
- `ppi_graph_message_passing` is an implemented STRING/PPI graph smoother when `string_k562_gene_graph` is present. It reads `data/artifacts/string/k562_target_graph_edges.tsv` through `spec.artifacts` and does not fabricate edges.

## Autonomous Agent Loop

See `AUTONOMOUS_AGENT_LOOP_UPGRADE.md`. The framework now includes `preflight`, `autonomous_run`, `implementation_agent`, duplicate/memory guards, `search_memory.json`, and bounded automatic implementation/training cycles for safe node-local model templates.

## Codex Agent Cookbook

Formal runs use the user-launched Codex window as the coding/research agent. The repo must not call Codex/OpenAI APIs internally. See `CODEX_AGENT_COOKBOOK.md` for what Codex may change, must not change, and when official-source search is required.
