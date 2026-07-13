# Acquire Artifact: `official_string_gnn_model_dir`

You are the Codex artifact acquisition agent for a strict VCHarness-style run.
Do not train fallback models and do not fabricate data.

## Trigger
- Node: `generic_wrapper_preflight`
- Strategy/blueprint: `official_k562_tsv_mcts_harness_required_artifacts`
- Missing artifact: `official_string_gnn_model_dir`
- Expected path: `/home/Models/STRING_GNN`
- Registry source hint: `Exact model directory expected by public VCHarness node code; not equivalent to STRING graph edge file.`
- Resolver: `codex_research_download_from_official_genbio_or_string_gnn_source`

## Required Workflow
1. Search official or primary sources for the real artifact or a reproducible way to build it.
2. Prefer exact public artifacts from the paper authors, official model/project repositories, HuggingFace datasets, STRING/Reactome/GO/MSigDB official releases, or documented checkpoints.
3. Download/build only source-backed artifacts. Record URL, version/date, checksum or file size, filtering rules, and coverage.
4. Write the artifact to the expected path or update the registry path if a better audited layout is necessary.
5. Update `configs/artifacts/k562_registry.json` with source-backed metadata only.
6. Run `python -m vc_demo.harness.artifact_registry --cell-line K562` and save the audit JSON/summary.
7. Resume the strict search without `--allow-missing-artifact-fallbacks`.

## Research Questions
- Is /home/Models/STRING_GNN publicly downloadable, or must it be trained from gnn/9606...keep20 graph?
- What node embedding dimensionality and vocabulary are expected by VCHarness K562 best node?
- How should the repo distinguish STRING graph source data from trained STRING_GNN checkpoint?

## Required Outputs
- model directory or explicit blocker report
- source/build procedure
- registry update

## Forbidden
- No random embeddings, random graphs, synthetic pathway memberships, or randomly initialized checkpoints marked as real artifacts.
- No fallback training in formal search.
- No registry `present` claim unless the expected file exists and provenance is recorded.

## Handoff Back To Search
After acquisition and audit, rerun the strict `program_run` command for the same run directory. If a new artifact is missing, repeat acquisition.
