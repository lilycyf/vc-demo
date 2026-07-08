# Acquire Artifact: `single_cell_foundation_model_artifact`

You are the Codex artifact acquisition agent for a strict VCHarness-style run.
Do not train fallback models and do not fabricate data.

## Trigger
- Node: `official_k562_root_aido_embedding_mlp_p3_official_scgpt_cell_encoder_d5b2bbc0`
- Strategy/blueprint: `official_scgpt_cell_encoder`
- Missing artifact: `single_cell_foundation_model_artifact`
- Expected path: `data/artifacts/single_cell_foundation_model`
- Registry source hint: `definition/source required before acquisition; no verified official scGPT/scFoundation K562 artifact configured`
- Resolver: `unconfigured`

## Required Workflow
1. Search official or primary sources for the real artifact or a reproducible way to build it.
2. Prefer exact public artifacts from the paper authors, official model/project repositories, HuggingFace datasets, STRING/Reactome/GO/MSigDB official releases, or documented checkpoints.
3. Download/build only source-backed artifacts. Record URL, version/date, checksum or file size, filtering rules, and coverage.
4. Write the artifact to the expected path or update the registry path if a better audited layout is necessary.
5. Update `configs/artifacts/k562_registry.json` with source-backed metadata only.
6. Run `python -m vc_demo.harness.artifact_registry --cell-line K562` and save the audit JSON/summary.
7. Resume the strict search without `--allow-missing-artifact-fallbacks`.

## Research Questions
- Identify and document the official source and exact alignment procedure.

## Required Outputs
- Artifact files
- Source/coverage summary
- Registry update

## Forbidden
- No random embeddings, random graphs, synthetic pathway memberships, or randomly initialized checkpoints marked as real artifacts.
- No fallback training in formal search.
- No registry `present` claim unless the expected file exists and provenance is recorded.

## Handoff Back To Search
After acquisition and audit, rerun the strict `program_run` command for the same run directory. If a new artifact is missing, repeat acquisition.
