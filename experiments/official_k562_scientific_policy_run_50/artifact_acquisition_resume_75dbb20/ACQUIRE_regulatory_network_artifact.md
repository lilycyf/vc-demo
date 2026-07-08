# Acquire Artifact: `regulatory_network_artifact`

You are the Codex artifact acquisition agent for a strict VCHarness-style run.
Do not train fallback models and do not fabricate data.

## Trigger
- Node: `official_k562_root_aido_embedding_mlp_p1_official_regulatory_network_prior_4cb71788`
- Strategy/blueprint: `official_regulatory_network_prior`
- Missing artifact: `regulatory_network_artifact`
- Expected path: `data/artifacts/regulatory_network`
- Registry source hint: `No verified K562-aligned regulatory source configured; strict mode must block.`
- Resolver: `source_definition_required_before_acquisition`

## Required Workflow
1. Search official or primary sources for the real artifact or a reproducible way to build it.
2. Prefer exact public artifacts from the paper authors, official model/project repositories, HuggingFace datasets, STRING/Reactome/GO/MSigDB official releases, or documented checkpoints.
3. Download/build only source-backed artifacts. Record URL, version/date, checksum or file size, filtering rules, and coverage.
4. Write the artifact to the expected path or update the registry path if a better audited layout is necessary.
5. Update `configs/artifacts/k562_registry.json` with source-backed metadata only.
6. Run `python -m vc_demo.harness.artifact_registry --cell-line K562` and save the audit JSON/summary.
7. Resume the strict search without `--allow-missing-artifact-fallbacks`.

## Research Questions
- Which public TF-target/regulatory network source is acceptable for K562 target genes?
- What version, license, confidence threshold, and gene identifier mapping are used?
- How is coverage over the exact 6,640 target-gene order audited?

## Required Outputs
- source-backed regulatory edge/prior artifact
- coverage and checksum summary
- registry update, or explicit blocker if no valid source exists

## Forbidden
- No random embeddings, random graphs, synthetic pathway memberships, or randomly initialized checkpoints marked as real artifacts.
- No fallback training in formal search.
- No registry `present` claim unless the expected file exists and provenance is recorded.

## Handoff Back To Search
After acquisition and audit, rerun the strict `program_run` command for the same run directory. If a new artifact is missing, repeat acquisition.
