# vc-demo

A minimal, runnable scaffold for reproducing the *shape* of a VCHarness-style experiment on one cell line.

This repository currently implements an A-level demo:

- a synthetic CRISPR perturbation response dataset with train/validation/test splits
- a configurable perturbation-response model
- a training entrypoint that writes metrics, checkpoints, and node memory
- a small MCTS-style search driver that proposes child experiment configs

It does **not** yet reproduce the paper's full 600+ model search or use the real GenBio foundation-model embeddings. Treat it as the controllable harness that a later Codex/agent window can extend.

## Smoke test

```bash
bash scripts/smoke.sh
```

Expected outputs:

- `experiments/nodes/root_mlp/metrics.json`
- `experiments/nodes/root_regularized_mlp/metrics.json`
- `experiments/tree.json`
- proposed child configs under `experiments/proposals/`

## Typical next step

Replace `SyntheticPerturbationDataset` in `src/vc_demo/data.py` with a real one-cell-line perturbation dataset loader, then let the agent generate child configs and model variants while keeping the train/evaluate interface stable.
