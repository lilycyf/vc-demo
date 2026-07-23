# VCHarness Paper Model Universe

This document is the repo-level contract for the VCHarness-style model search space. The rule is strict:

> The search space may be larger than the VCHarness paper universe, but it must not be smaller. If a paper module cannot currently run, it remains in the universe and is labeled as task-gated, acquirable, source-backed reimplementation needed, or blocked unavailable. It is not silently removed.

## Evidence Scope

- The VCHarness preprint defines search over complete ML programs: preprocessing, biological foundation-model encoders, fusion operations, task heads, losses, and schedules.
- GenBio overview describes the closed loop: foundation-model library, coding agent, MCTS, feedback memory, and distributed execution.
- The public `genbio-ai/VCHarness` repository exposes static case-study trees for HepG2, Jurkat, K562, and hTERT-RPE1 classification tracks.

## Status Categories

| Status | Meaning |
|---|---|
| `paper_original_acquired_public_source` | Module or source-backed public artifact is acquired locally and can be used after audit. |
| `paper_original_acquired_public_source_but_task_embedding_contract_pending` | Checkpoint exists, but the selected node must still verify row order, vocabulary, and extraction for the cell-line task. |
| `paper_original_blocked_unavailable_primary_artifact` | The original artifact expected by paper/public code is not verifiably downloadable from primary sources. |
| `paper_original_acquirable_or_needs_verification` | Belongs to the paper universe; Codex must acquire and verify before training. |
| `paper_original_source_backed_reimplementation_needed` | No exact artifact has been verified; a documented public-data reimplementation is allowed but must be labeled. |
| `paper_original_task_gated_or_extension` | In the broader universe, but only selectable for task contracts with the needed modality. |
| `paper_level_derived_public_source` | Source-backed derived artifact, not necessarily the original checkpoint. |
| `paper_original_public_scaffold_acquired` | Public scaffold/code is available, but exact execution may still require non-public model dirs. |
| `no_artifact_required` | Baseline/ablation requiring only task data. |

## Complete Module Universe

| Module | Family | CRISPR DEG candidate? | Current status | Strict rule |
|---|---|---:|---|---|
| `AIDO.DNA` | AIDO | task-gated | `paper_original_not_downloaded_large` | Task-gated; do not select for K562 DEG unless sequence/regulatory inputs are explicitly added. |
| `AIDO.DNA2` | AIDO | task-gated | `paper_original_not_downloaded_large` | Task-gated; cannot be silently substituted with nucleotide k-mers. |
| `AIDO.Cell 3M` | AIDO.Cell | yes | `paper_original_acquirable_or_needs_verification` | May be selected for K562 only after real checkpoint or cached embeddings are verified. |
| `AIDO.Cell 10M` | AIDO.Cell | yes | `paper_original_acquirable_or_needs_verification` | Must load real AIDO.Cell-10M or block. |
| `AIDO.Cell-100M` | AIDO.Cell | yes | `paper_original_acquired_public_source` | Usable as paper-original when checksum/provenance audit passes. |
| `AIDO.Protein` | AIDO.Protein | task-gated | `paper_original_acquirable_or_needs_verification` | Protein branch only; no random protein embedding substitute. |
| `AIDO Protein 16B / AIDOprot seq+struct` | AIDO.Protein | task-gated | `paper_original_not_downloaded_large` | Large protein branch; require explicit artifact and GPU budget. |
| `ProteinRAG 16B + structure` | protein_foundation_model | task-gated | `paper_original_not_downloaded_large` | Must be source-backed; graph/protein cache is not equivalent. |
| `ESM2 35M` | ESM2 | task-gated | `paper_original_acquirable_public_source` | Must map perturbed/target genes to protein sequences and record coverage. |
| `ESM2 150M` | ESM2 | task-gated | `paper_original_acquirable_public_source` | Must record sequence source and coverage. |
| `ESM2 650M` | ESM2 | task-gated | `paper_original_acquired_public_source` | Use real checkpoint/derived embeddings only. |
| `ESM2 3B` | ESM2 | task-gated | `paper_original_not_downloaded_large` | Large model; must be explicit in cost report. |
| `STRING_GNN official model directory` | STRING_GNN | yes | `paper_original_blocked_unavailable_primary_artifact` | Required for original static wrappers; STRING graph or cached embeddings are not substitutes. |
| `STRING PPI graph / keep20 graph` | STRING | yes | `paper_level_derived_public_source` | Usable for graph priors but not equivalent to STRING_GNN checkpoint. |
| `STRING Spectral` | STRING_variant | yes | `paper_original_source_backed_reimplementation_needed` | Derived graph feature, not official model unless exact artifact is published. |
| `STRING Seq` | STRING_variant | yes | `paper_original_source_backed_reimplementation_needed` | Must be auditable source-backed derived artifact. |
| `STRING WaveGC` | STRING_variant | yes | `paper_original_source_backed_reimplementation_needed` | Do not collapse to simple Laplacian and call it WaveGC. |
| `STRING Net` | STRING_variant | yes | `paper_original_source_backed_reimplementation_needed` | Must document architecture; simple graph degree is not enough. |
| `GNN Simple Official D256` | GNN_embedding | yes | `paper_original_acquired_public_source` | Usable as cached embedding/root, not as STRING_GNN model dir. |
| `scFoundation` | single_cell_foundation_model | yes | `paper_original_acquired_public_source_but_task_embedding_contract_pending` | Checkpoint present is not enough; selected node must verify row/vocab/order contract. |
| `scGPT` | single_cell_foundation_model | yes | `paper_original_acquired_public_source_but_task_embedding_contract_pending` | Must not use random expression encoder as scGPT. |
| `Geneformer` | single_cell_foundation_model | yes | `paper_original_acquired_public_source_but_task_embedding_contract_pending` | Must verify gene token vocabulary and cell input contract. |
| `TranscriptFormer` | single_cell_foundation_model | yes | `paper_original_acquirable_or_needs_verification` | Must be official/source-backed before selection can train. |
| `scPRINT` | single_cell_foundation_model | yes | `paper_original_acquired_public_source_but_task_embedding_contract_pending` | Must verify gene vocabulary and row alignment. |
| `GenePT All` | gene_text_embedding | yes | `paper_original_acquired_public_source` | Must record mapping coverage and missing genes. |
| `GenePT BP` | gene_text_embedding | yes | `paper_original_source_backed_reimplementation_needed` | Must distinguish derived BP subset from paper original artifact. |
| `GenePT CC` | gene_text_embedding | yes | `paper_original_source_backed_reimplementation_needed` | Must document exact text corpus. |
| `GenePT MF` | gene_text_embedding | yes | `paper_original_source_backed_reimplementation_needed` | Must document exact text corpus. |
| `GenePT NCBI` | gene_text_embedding | yes | `paper_original_source_backed_reimplementation_needed` | Must document source snapshot. |
| `GenePT N+U` | gene_text_embedding | yes | `paper_original_source_backed_reimplementation_needed` | Must not mix undocumented text snapshots. |
| `DepMap` | functional_genomics_prior | yes | `paper_original_source_backed_reimplementation_needed` | Must record release, gene IDs, and whether K562-specific signal is used. |
| `GenotypeVAE` | genotype_prior | task-gated | `paper_original_acquirable_or_needs_verification` | Task-gated; not selected for K562 unless genotype inputs exist. |
| `Positional 3M` | positional_embedding | task-gated | `paper_original_source_backed_reimplementation_needed` | Task-gated; coordinates and genome build must be recorded. |
| `Positional 10M` | positional_embedding | task-gated | `paper_original_source_backed_reimplementation_needed` | Task-gated; cannot use arbitrary target index as positional prior. |
| `Positional 100M` | positional_embedding | task-gated | `paper_original_source_backed_reimplementation_needed` | Task-gated; genome build required. |
| `AlphaGenome` | sequence_regulatory_model | task-gated | `paper_original_task_gated_or_extension` | Not a generic CRISPR DEG default; include so the universe is not smaller for sequence/regulatory tasks. |
| `Reactome/pathway memberships` | pathway_prior | yes | `paper_level_derived_public_source` | Must verify target order, pathway source, and coverage. |
| `Regulatory network prior` | regulatory_prior | yes | `paper_original_acquirable_or_needs_verification` | No fabricated regulatory edges. |
| `No pretrained / scratch baseline` | baseline | yes | `no_artifact_required` | Must be labeled baseline, not foundation model. |
| `Public VCHarness static tree nodes` | public_static_tree | task-gated | `paper_original_public_scaffold_acquired` | Scaffold/reference unless exact required artifacts are present. |

## Cell-Line Overfit Guard

K562 is a demo projection used to test the harness. It is not the template cell line and it must not define universal model priorities. The reusable object is the global universe plus task-gated projection mechanism. A new cell line must rebuild or verify its own task contract, artifact registry, roots, gates, and report; it should not inherit K562-specific paths, target order, or winning motifs as defaults.

## Practical Consequence

A CRISPR DEG run, including K562, is allowed to gate out AIDO.DNA, AIDO.DNA2, AlphaGenome, and other sequence-only modules unless the task contract includes sequence/regulatory inputs. That is not considered a smaller search space because the modules remain declared in `configs/vcharness_paper_model_universe.json` and the gate is explicit.

For modules such as STRING_GNN where public code requires `/home/Models/STRING_GNN` but the public primary repository does not expose checkpoint/config files, the correct behavior is `blocked_unavailable_primary_artifact` or a separately labeled `source_backed_reimplementation`, not fallback/proxy training.

## Audit

Run:

```bash
python scripts/audit_paper_model_universe.py
```

The audit fails if a required paper module is missing from the universe manifest or if a paper-aligned task projection, such as the K562 demo projection, does not reference the universe manifest.
