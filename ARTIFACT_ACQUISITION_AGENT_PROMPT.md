# Codex Artifact Acquisition Agent Prompt

Use this prompt when a strict VCHarness-style search stops with `requires_artifact_acquisition`.

## Mission

You are the artifact acquisition agent. Your job is to unblock the search by obtaining real, source-backed artifacts, not by changing the model to avoid the artifact.

## Start Here

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

## Rules

- Search official or primary sources first.
- Use public author artifacts, official model repositories, HuggingFace datasets, STRING/Reactome/GO/MSigDB official releases, or documented checkpoints.
- Record provenance: URL, version/date, file size or checksum, filtering/alignment rules, and coverage.
- Update `configs/artifacts/k562_registry.json` only after a real artifact exists or a reproducible source-backed build has completed.
- Run `python -m vc_demo.harness.artifact_registry --cell-line K562` after every acquisition.
- Resume the strict search only after the required artifact is present.

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

## K562 Artifact Policy: Derived vs Blocked

The official K562 strict search distinguishes deterministic derived artifacts from artifacts that require external provenance.

### Automatically Derivable

- `class_distribution`: derive with `scripts/build_k562_class_distribution.py` from `data/cell_lines/official_k562_cls/train.tsv` only. The resolver must not read validation or test labels to compute class weights. The artifact must record raw counts, training-label remap, recommended class weights, `split_used=train`, and `forbidden_splits=[val,test]`.
- `pathway_memberships`: derive only through the configured Reactome/MSigDB source-backed resolver and exact official target-gene order.

### Must Block Unless Source Is Configured

- `regulatory_network_artifact`: block unless a real public/approved TF-target or regulatory network source, version, filtering rule, checksum, and K562 target-gene alignment are recorded. Do not substitute STRING/PPI or pathway memberships and call it regulatory.
- `single_cell_foundation_model_artifact`: block unless a real scGPT/scFoundation/single-cell foundation checkpoint or row-aligned embedding artifact is configured with preprocessing, vocabulary, source, and coverage. Do not train a small expression fallback in strict mode.

If an artifact is listed as blocked, the correct action is to generate/complete an acquisition task, not to implement or train a fallback node.

