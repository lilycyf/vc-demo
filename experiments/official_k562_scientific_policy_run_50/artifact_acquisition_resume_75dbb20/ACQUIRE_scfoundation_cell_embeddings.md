# Acquire Artifact: `scfoundation_cell_embeddings`

You are the Codex artifact acquisition agent for a strict VCHarness-style run.
Do not train fallback models and do not fabricate data.

## Trigger
- Node: `official_k562_root_aido_embedding_mlp_p1_official_scfoundation_top_layer_finetune_39582a38`
- Strategy/blueprint: `official_scfoundation_top_layer_finetune`
- Missing artifact: `scfoundation_cell_embeddings`
- Expected path: `data/artifacts/scfoundation`
- Registry source hint: `precomputed scFoundation cell-state embedding or approved encoder output`
- Resolver: `codex_research_download_or_encode_from_official_scfoundation_source`

## Required Workflow
1. Search official or primary sources for the real artifact or a reproducible way to build it.
2. Prefer exact public artifacts from the paper authors, official model/project repositories, HuggingFace datasets, STRING/Reactome/GO/MSigDB official releases, or documented checkpoints.
3. Download/build only source-backed artifacts. Record URL, version/date, checksum or file size, filtering rules, and coverage.
4. Write the artifact to the expected path or update the registry path if a better audited layout is necessary.
5. Update `configs/artifacts/k562_registry.json` with source-backed metadata only.
6. Run `python -m vc_demo.harness.artifact_registry --cell-line K562` and save the audit JSON/summary.
7. Resume the strict search without `--allow-missing-artifact-fallbacks`.

## Research Questions
- Is there an official/public scFoundation artifact matching these K562 perturbation rows?
- If not precomputed, what official checkpoint/code can encode the exact train/val/test cells?
- What input normalization and gene vocabulary are required?
- What file layout should the repo read at data/artifacts/scfoundation?

## Required Outputs
- embedding files or encoder output
- summary json with source/checkpoint/vocabulary/coverage
- registry update

## Forbidden
- No random embeddings, random graphs, synthetic pathway memberships, or randomly initialized checkpoints marked as real artifacts.
- No fallback training in formal search.
- No registry `present` claim unless the expected file exists and provenance is recorded.

## Handoff Back To Search
After acquisition and audit, rerun the strict `program_run` command for the same run directory. If a new artifact is missing, repeat acquisition.
