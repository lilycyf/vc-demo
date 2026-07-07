# Artifact Acquisition Runbook

Formal searches run in strict artifact mode. If a selected blueprint needs a missing artifact, the search must stop and create:

```text
<run_dir>/acquisition_queue.json
```

This is not a final scientific failure. It is the handoff into artifact acquisition.

## Resolver Command

Before doing manual research, run the acquisition resolver. It verifies already-present artifacts, executes known deterministic builders when allowed, and creates a strict Codex research task for artifacts whose public source must be investigated.

```bash
python -m vc_demo.harness.artifact_acquisition \
  --queue <run_dir>/acquisition_queue.json \
  --registry configs/artifacts/k562_registry.json \
  --sources configs/artifacts/acquisition_sources.json \
  --cell-line K562 \
  --output-dir <run_dir>/artifact_acquisition \
  --execute-known
```

If this writes `ACQUIRE_<artifact>.md`, follow `ARTIFACT_ACQUISITION_AGENT_PROMPT.md` and the generated task. The correct behavior is active source-backed acquisition, not waiting passively and not training a fallback.

## Required Behavior

When `acquisition_queue.json` is non-empty, the Codex agent must:

1. Read the queue item: artifact id, expected path, source hint, and triggering blueprint.
2. Search for the real artifact from official or primary sources.
3. Prefer existing public GenBio/HuggingFace artifacts when available.
4. For graph/pathway artifacts, build an aligned artifact from a public source only if source, version, filtering, and gene coverage can be documented.
5. Write the artifact under the expected `data/artifacts/...` path.
6. Update `configs/artifacts/k562_registry.json` only with source-backed metadata.
7. Run `python -m vc_demo.harness.artifact_registry --cell-line K562` and save/update audit output.
8. Resume the search from the same run dir or restart a clean run, still without fallback.

## Forbidden In Formal Tests

- Do not train a fallback model for a missing artifact.
- Do not create random embeddings and call them AIDO, scFoundation, ESM2, STRING, pathway, or pretrained artifacts.
- Do not fabricate graph edges, pathway memberships, or pretrained checkpoints.
- Do not mark an artifact as present unless the expected file exists and the source is recorded.

## Current K562 Priorities

1. `pretrained_encoder`
   - Needed by `selective_adapter_finetune`.
   - Must be a real checkpoint or clearly defined pretraining output, not a random frozen base.
2. `string_k562_gene_graph`
   - Needed by `ppi_graph_message_passing` and `string_gnn_perturbation_propagator`.
   - Should be aligned to K562 perturbation genes and target genes.
3. `pathway_membership_matrix`
   - Needed by `pathway_pooling_encoder`.
   - Should be aligned to the exact target gene list.
4. `aido_gene_or_cell_embeddings` / `scfoundation_cell_embeddings`
   - Use only if a real downloadable artifact or approved encoder output exists.

## Resume Rule

After acquisition, rerun the same strict search command without `--allow-missing-artifact-fallbacks`. If the artifact is now present, MCTS can implement/train the selected node. If another artifact is missing, produce the next acquisition queue item.

## Pre-Test Hardening

- `program_run` now writes `run_manifest.json` with commit, search parameters, artifact audit, queue paths, MCTS state, and best-node summary.
- Blueprint choice is artifact-aware by default: executable blueprints whose required artifacts are present are ranked before blueprints that would immediately require acquisition. Use `--no-artifact-aware-blueprint-policy` only for ablation.
- `ppi_graph_message_passing` is an implemented STRING/PPI graph smoother when `string_k562_gene_graph` is present. It reads `data/artifacts/string/k562_target_graph_edges.tsv` through `spec.artifacts` and does not fabricate edges.
