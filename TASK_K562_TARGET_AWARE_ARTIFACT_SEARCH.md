# Task: K562 Target-Aware Artifact Search

## Research Question

For one-cell-line K562 CRISPR perturbation DEG classification, can Codex + UCT/MCTS program search find a model that improves validation Macro-F1 when the model explicitly uses both perturbed-gene/context features and target-gene embeddings, instead of only appending ESM2 to tabular features?

## Required Read Order

1. `E_CODEX_AGENT_EXPERIMENT_RUNBOOK.md`
2. `PAPER_LEVEL_SEARCH_SPACE_SPEC.md`
3. `PUBLIC_ARTIFACT_ALIGNMENT.md`
4. `CODEX_AGENT_OPERATING_RULES.md`
5. `TARGET_AWARE_ARTIFACT_MODEL_SPACE.md`
6. `PAPER_LEVEL_FRAMEWORK_UPGRADE_2.md`
7. `TASK_K562_TARGET_AWARE_ARTIFACT_SEARCH.md`

## Required Artifacts

Use:

```text
data/cell_lines/k562_concat_esm2_gene_embedding
data/artifacts/gene_embeddings/ESM2_D1280.h5ad
```

Build the target-side manifest before running search:

```bash
python scripts/build_target_gene_artifact.py \
  --data-dir data/cell_lines/k562_concat_esm2_gene_embedding \
  --embedding-h5ad data/artifacts/gene_embeddings/ESM2_D1280.h5ad \
  --artifact-name ESM2_D1280 \
  --gene-column symbol \
  --summary experiments/k562_target_aware_artifact_manifest_summary.json
```

This writes ignored data files beside the dataset:

```text
data/cell_lines/k562_concat_esm2_gene_embedding/artifact_manifest.json
data/cell_lines/k562_concat_esm2_gene_embedding/target_gene_embeddings.npz
```

Do not commit these files.

## Root Baselines

Compare at least:

```text
configs/k562_roots/root_concat_gated_mlp.json
configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json
configs/k562_roots/root_concat_esm2_target_aware_bilinear.json
```

The third root is the upgraded baseline. It uses `model_type: target_aware_bilinear` and `artifact_manifest_path: auto`.

## Search Rules

Use public-artifact-aligned UCT:

```text
--selection-policy uct
--exploration 1.4142135623730951
```

The search may select implemented program-node blueprints including `target_gene_embedding_bilinear`. If it selects AIDO, scFoundation, STRING, pathway, or cross-attention routes, implement them only when the required real artifact is present and aligned. Otherwise record missing-artifact/blocking notes. Do not substitute random embeddings or synthetic graph edges and call them biological artifacts.

## Minimal Formal Run

```bash
python -m vc_demo.harness.program_run \
  --experiment k562_target_aware_artifact_search \
  --root-configs \
    configs/k562_roots/root_concat_gated_mlp.json \
    configs/k562_roots/root_concat_esm2_gene_embedding_gated_mlp.json \
    configs/k562_roots/root_concat_esm2_target_aware_bilinear.json \
  --run-dir experiments/k562_target_aware_artifact_search \
  --budget-nodes 24 \
  --max-epochs 4 \
  --max-children 3 \
  --stop-no-improve 8 \
  --exploration 1.4142135623730951 \
  --selection-policy uct \
  --artifact-registry configs/artifacts/k562_registry.json \
  --seed 23 \
  --allow-planned-blueprints \
  --max-pending-implementations 2 \
  --reset
```

If pending nodes appear, first confirm that all required artifacts are present. If any required artifact is missing, stop and write the blocked conclusion. Only implement selected node-local `model.py` files when the required real artifacts are present, then continue with:

```bash
python -m vc_demo.harness.train_pending --run-dir experiments/k562_target_aware_artifact_search
```

## Final Deliverable

Write:

```text
experiments/k562_target_aware_artifact_search/final_conclusion.md
```

It must answer:

- Did the target-aware ESM2 root beat the non-artifact and perturbation-only ESM2 roots?
- Did any child explicitly using target-gene embeddings beat all roots?
- Which nodes truly consumed `artifact_manifest.json` and `target_gene_embeddings.npz`?
- What were perturbation-gene and target-gene artifact coverages?
- Were failures due to model quality, artifact coverage, missing artifacts, or implementation issues?

Do not commit `data/`, `experiments/**/nodes/`, checkpoints, `.h5ad`, `.npz`, pycache, egg-info, secrets, or tokens.

## Strict Artifact Testing Rule

This formal testing task runs in strict artifact mode. If MCTS selects AIDO, scFoundation, STRING, pathway, or any other artifact-dependent blueprint and the required real artifact is missing, stop the search and record the node as `blocked_missing_artifact`. Do not implement or train a fallback model in the formal test. Fallbacks are allowed only in a separate ablation run with `--allow-missing-artifact-fallbacks`, and must not be counted as paper-aligned artifact usage.
