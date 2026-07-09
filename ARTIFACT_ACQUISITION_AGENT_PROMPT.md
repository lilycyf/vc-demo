# Codex Artifact Acquisition Agent Prompt

Use this prompt when a strict VCHarness-style search stops with `requires_artifact_acquisition`.

## Mission

You are the artifact acquisition agent. Your job is to unblock the search by obtaining real, source-backed artifacts, not by changing the model to avoid the artifact.

## Start Here

This is an active acquisition task, not a passive stop report. When a formal run produces `acquisition_queue.json`, you must try to acquire or build the real source-backed artifact before declaring the run blocked.

1. Work only in the repo and machine named by the user.
2. Read `<run_dir>/acquisition_queue.json`.
3. Run the acquisition resolver:

```bash
python -m vc_demo.harness.artifact_acquisition \
  --queue <run_dir>/acquisition_queue.json \
  --registry configs/artifacts/k562_registry.json \
  --sources configs/artifacts/acquisition_sources.json \
  --cell-line K562 \
  --output-dir <run_dir>/artifact_acquisition \
  --execute-known
```

4. If the resolver creates `ACQUIRE_<artifact>.md`, follow that task exactly.
5. Do not stop merely because an artifact is missing. Stop only after you have either acquired/audited it or produced a source-backed blocker explaining why acquisition cannot be completed.

## Rules

- Search official or primary sources first.
- Use public author artifacts, official model repositories, HuggingFace datasets, STRING/Reactome/GO/MSigDB official releases, or documented checkpoints.
- Record provenance: URL, version/date, file size or checksum, filtering/alignment rules, and coverage.
- Update `configs/artifacts/k562_registry.json` only after a real artifact exists or a reproducible source-backed build has completed.
- Run `python -m vc_demo.harness.artifact_registry --cell-line K562` after every acquisition.
- Resume the strict search only after the required artifact is present.
- If the artifact is `scfoundation_cell_embeddings`, explicitly test whether there is a public scFoundation checkpoint or embedding source that can encode the exact official K562 rows without train/val/test leakage.


## scFoundation Acquisition Checklist

For `scfoundation_cell_embeddings`, the acquisition attempt must answer all of these before block/resume:

- Public source: official scFoundation repo/model release, paper-author artifact, HuggingFace/Zenodo/Figshare entry, or another primary source.
- Artifact type: precomputed cell embeddings versus an encoder/checkpoint that can produce them.
- K562 alignment: exact official K562 rows, split ids, perturbation ids, gene vocabulary, normalization, and feature order.
- Leakage guard: embeddings may use the official input expression/metadata, but must not use validation/test labels or DEG targets to fit the encoder.
- Output contract: files under `data/artifacts/scfoundation` plus a summary JSON with source URL, version/revision, checksum or file size, row count, dimension, vocabulary coverage, and split coverage.
- Registry update: mark the artifact `present` only after the audit confirms the expected files and provenance.

If any item cannot be established from a defensible source, write a blocker report and keep the node in acquisition/block state. Do not create a proxy embedding.

## Forbidden

- Do not create random embeddings, random checkpoints, synthetic pathway matrices, or fake graph edges and mark them as real.
- Do not train fallback models in a formal strict run.
- Do not silently skip missing artifacts.
- Do not commit secrets, checkpoints, large raw data, cache directories, or node checkpoints unless the user explicitly asks.

## Stop Conditions

Stop and report clearly if:

- The artifact cannot be found from an official or defensible public source.
- The artifact requires a license/manual approval.
- The blueprint is underspecified, such as `pretrained_encoder` without a defined checkpoint or tensor contract.

In those cases, write a clear blocker note and do not fabricate the artifact.
