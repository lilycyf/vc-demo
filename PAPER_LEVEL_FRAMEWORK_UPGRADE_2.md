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
