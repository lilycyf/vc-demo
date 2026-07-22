# Acquire Artifact: `official_string_gnn_model_dir`

You are the Codex artifact acquisition agent for a strict VCHarness-style run.
Do not train fallback models and do not fabricate data.

## Trigger
- Node: `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_0ea9e05d`
- Strategy/blueprint: `official_string_gnn_attention`
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

## STRING_GNN Model-Directory Acquisition Protocol

This artifact is a model directory expected by public VCHarness node code. It is not equivalent to the STRING edge graph, keep20 graph text file, or a generated embedding table.

Before blocking or resuming, complete this protocol:

1. Search primary/public sources: GenBio AI HuggingFace org, VCHarness repository/issues/releases, foundation-models-perturbation dataset/model cards, linked paper/code pages, Zenodo/Figshare/S3 links, and model repos named `STRING_GNN` or equivalent.
2. Inspect the public K562 static node code that imports `/home/Models/STRING_GNN`; record the expected loader class, config files, state-dict names, vocabulary, embedding dimension, and graph inputs.
3. If a source-backed downloadable model directory exists, download it to `/home/Models/STRING_GNN`, record source URL/revision/file sizes/checksums, and run model-dir validation.
4. If only source graph data is available, determine whether an official build/train script and checkpoint recipe exists. Do not train an ad hoc substitute and call it official.
5. If no source-backed checkpoint/model-dir is available, write a blocker report listing every source checked and classify the reason as unavailable weights, inaccessible license/manual approval, incomplete tensor contract, incompatible vocabulary, or non-equivalent reconstruction.
6. Update the artifact registry only after the real expected path exists and provenance is recorded. Otherwise keep the artifact missing/blocked and resume is not allowed for nodes requiring this artifact.

Do not use `official_string_gnn_keep20_graph`, `string_k562_gene_graph`, random GNN weights, or a compact graph head as `/home/Models/STRING_GNN`.

## Forbidden
- No random embeddings, random graphs, synthetic pathway memberships, or randomly initialized checkpoints marked as real artifacts.
- No fallback training in formal search.
- No registry `present` claim unless the expected file exists and provenance is recorded.

## Handoff Back To Search
After acquisition and audit, rerun the strict `program_run` command for the same run directory. If a new artifact is missing, repeat acquisition.
