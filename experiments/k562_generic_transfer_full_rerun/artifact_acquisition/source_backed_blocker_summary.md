# Source-Backed Artifact Acquisition Blocker Summary

Run: `experiments/k562_generic_transfer_full_rerun`

## official_string_gnn_model_dir

Expected path: `/home/Models/STRING_GNN`. The resolver generated `ACQUIRE_official_string_gnn_model_dir.md`. Source probing checked HuggingFace `genbio-ai/STRING_GNN`; the model repo exists, but the public API lists only `.gitattributes` as a sibling and no config/checkpoint/model files. The GenBio foundation-models dataset provides the STRING keep20 graph source, but the runbook explicitly says graph source files are not equivalent to a trained `/home/Models/STRING_GNN` model directory. Therefore this artifact remains blocked as unavailable weights / incomplete tensor contract.

## scfoundation_cell_embeddings

Expected path: `data/artifacts/scfoundation`. Source probing checked the official BioMap scFoundation GitHub repo and HuggingFace `genbio-ai/scFoundation`, which exposes a checkpoint (`models.ckpt`) and documentation, plus `perturblab/scfoundation-cell`. However the required artifact for this run is not merely a checkpoint; it is a K562 split-row-aligned cell embedding artifact or a verified reproducible encoder output matching the official task rows, gene vocabulary, normalization, row order, and leakage guardrails. No already-aligned K562 embedding artifact or repo-validated builder for this exact contract was found during this acquisition pass. Therefore this remains blocked as missing tensor contract / row-order alignment, not replaced by random/proxy embeddings.

## Present/Verified During Resolver

The resolver verified existing source-backed artifacts for pathway memberships, class distribution, and regulatory network where applicable.

## Policy

No fallback, compact proxy, fake checkpoint, graph-as-model, or random embedding artifact was used.
