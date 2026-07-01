# vc-demo

A minimal, runnable scaffold for reproducing the *shape* of a VCHarness-style experiment on one cell line.

This repository currently implements an A-level demo:

- a synthetic CRISPR perturbation response dataset with train/validation/test splits
- a configurable perturbation-response model
- a training entrypoint that writes metrics, checkpoints, and node memory
- a small MCTS-style search driver that selects nodes, proposes child configs,
  trains them, reads metrics, and backpropagates validation Macro-F1 into the tree

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

## Synthetic MCTS demo

Run a clean cheap search with eight trained child candidates:

```bash
PYTHONPATH=src python -m vc_demo.mcts \
  --tree experiments/tree.json \
  --reset \
  --steps 8 \
  --max-epochs 2 \
  --summary experiments/synthetic_mcts_summary.md
```

The committed demo summary is `experiments/synthetic_mcts_summary.md`. It lists
each trained node's config, validation Macro-F1, test Macro-F1, and best-so-far
curve. Checkpoints and per-node metrics remain local under `experiments/nodes/`.

## Typical next step

Replace `SyntheticPerturbationDataset` in `src/vc_demo/data.py` with a real one-cell-line perturbation dataset loader, then let the agent generate child configs and model variants while keeping the train/evaluate interface stable.

## B-stage real cell-line scaffold

The repo now includes a real-data interface without committing large biological files.
Use `dataset_type: "real_npz"` to train on a local one-cell-line dataset laid out as
`manifest.json` plus NPZ split files.

Framework validation with a tiny generated fixture:

```bash
python scripts/make_fake_real_dataset.py --data-dir data/cell_lines/k562_demo
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562_demo
python -m vc_demo.train \
  --config configs/real_k562_demo_fixture.json \
  --output-dir experiments/nodes/real_k562_demo_fixture \
  --max-epochs 1
```

Real K562 template:

```bash
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562
python -m vc_demo.train \
  --config configs/real_k562_template.json \
  --output-dir experiments/nodes/real_k562_template_mlp \
  --max-epochs 1
```

See `data/README.md` and `B_REAL_CELLLINE_HANDOFF.md` for the data contract and
handoff instructions.
