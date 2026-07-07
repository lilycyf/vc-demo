# Task: K562 ESM2 Artifact Search

This task extends the K562 one-cell-line VCHarness-style reproduction by adding a real external biological artifact before running another search.

## Research Question

For K562 CRISPR perturbation DEG classification, does adding a real frozen ESM2 gene-level embedding artifact to the existing K562 concat features allow Codex + MCTS program-node search to find a model/pipeline that improves validation Macro-F1 over the best root baseline?

## Required Read Order

1. `E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md`
2. `PAPER_LEVEL_SEARCH_SPACE_SPEC.md`
3. `PUBLIC_ARTIFACT_ALIGNMENT.md`
4. `CODEX_AGENT_OPERATING_RULES.md`
5. `TASK_K562_ESM2_ARTIFACT_SEARCH.md`

## Data And Artifact

Use the existing K562 split semantics. Do not alter labels, target genes, or train/validation/test splits.

Source dataset:

```text
data/cell_lines/k562_concat
```

Real external artifact:

```text
data/artifacts/gene_embeddings/ESM2_D1280.h5ad
```

This artifact is downloaded from the public GenBio HuggingFace dataset path:

```text
gene_embeddings/ESM2_(D=1280).h5ad
```

If the file is missing on a fresh RunPod, download it with:

```bash
python scripts/download_foundation_artifact.py   --path 'gene_embeddings/ESM2_(D=1280).h5ad'   --output data/artifacts/gene_embeddings/ESM2_D1280.h5ad
```

Build the aligned dataset:

```bash
python scripts/build_gene_embedding_dataset.py   --source-dir data/cell_lines/k562_concat   --output-dir data/cell_lines/k562_concat_esm2_gene_embedding   --embedding-h5ad data/artifacts/gene_embeddings/ESM2_D1280.h5ad   --artifact-name ESM2_D1280   --gene-column symbol   --feature-mode source_plus_embedding   --summary experiments/k562_real_artifact_esm2_summary.json
```

Expected current audit:

- output feature dimension: 2385 = 1105 source concat features + 1280 ESM2 features
- perturbation coverage: about 96.19 percent
- missing perturbations: `ELMSAN1`, `KIAA1804`, `C19orf26`, `C3orf72`

Validate:

```bash
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562_concat_esm2_gene_embedding
python scripts/audit_real_dataset.py   --data-dir data/cell_lines/k562_concat_esm2_gene_embedding   --output experiments/k562_real_artifact_esm2_audit.json
```

## Root Config

Use this root config as the new biological-artifact baseline:

```text
configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json
```

It should be compared against the existing best non-artifact root:

```text
configs/k562_roots/root_concat_gated_mlp.json
```

## Search Rules

Use paper-aligned UCT unless explicitly running an ablation:

```text
--selection-policy uct
--exploration 1.4142135623730951
```

The search should prefer children that actually consume the ESM2-augmented input or implement better fusion/projection over it. Do not count a Level 5 node as a biological artifact node unless it uses the ESM2 feature dimensions or a documented artifact-derived representation.

## Suggested Smoke

Before a formal search, run one epoch to confirm the artifact root trains:

```bash
python -m vc_demo.train   --config configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json   --output-dir experiments/nodes/root_concat_esm2_gene_embedding_gated_mlp_smoke   --max-epochs 1
```

Current smoke result on RunPod:

```text
val Macro-F1: 0.3560
test Macro-F1: 0.3511
```

This is a plumbing smoke, not a scientific result, because it uses only one epoch.

## Formal Run Shape

Create a new branch and run a small confirmation search first:

```bash
git checkout -b k562-esm2-artifact-search
python -m vc_demo.harness.program_run   --experiment k562_esm2_artifact_search   --root-configs configs/k562_roots/root_concat_gated_mlp.json configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json   --run-dir experiments/k562_esm2_artifact_search   --budget-nodes 20   --max-epochs 4   --max-children 3   --stop-no-improve 8   --exploration 1.4142135623730951   --selection-policy uct   --seed 17   --allow-planned-blueprints   --max-pending-implementations 2   --reset
```

If a planned node requires implementation, implement only the selected node-local `model.py`, then train it with `train_pending.py`.

## Final Deliverable

Write:

```text
experiments/k562_esm2_artifact_search/final_conclusion.md
```

It must answer:

- Did the ESM2 artifact root beat the non-artifact best root?
- Did any child using ESM2 features beat both roots?
- Which nodes truly consumed the real ESM2 artifact?
- What was the artifact coverage and which perturbations were missing?
- Were failures due to search/model quality, artifact coverage, or implementation issues?

Do not commit `data/`, `experiments/**/nodes/`, checkpoints, pycache, egg-info, or the downloaded `.h5ad` artifact.
