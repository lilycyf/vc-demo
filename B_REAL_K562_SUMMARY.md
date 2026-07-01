# B Stage Real K562 Dataset Summary

## Source

- Dataset: NormanWeissman2019_filtered.h5ad from scPerturb Zenodo record 7041849
- URL: https://zenodo.org/records/7041849
- DOI: 10.5281/zenodo.7041849
- Local raw file: data/raw/scperturb/NormanWeissman2019_filtered.h5ad

## Converted Harness Dataset

- Output directory: data/cell_lines/k562
- Format: split NPZ files plus manifest.json
- Perturbations: 105
- Feature dimension: 105 (perturbation one-hot)
- Target genes: 1000
- Splits: {'train': 73, 'val': 16, 'test': 16}
- Label counts: {'0': 5250, '1': 94500, '2': 5250}
- Label rule: per perturbation, delta vs control mean expression; <=5th percentile down, >=95th percentile up, otherwise unchanged

The data directory is intentionally ignored by git.

## Validation

```bash
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562
```

Validation passed on RunPod with train/val/test split sizes {'train': 73, 'val': 16, 'test': 16}.

## Single Node Smoke

```bash
python -m vc_demo.train \
  --config configs/real_k562_template.json \
  --output-dir experiments/nodes/real_k562_template_mlp \
  --max-epochs 1
```

- Best val Macro-F1: 0.3207
- Test Macro-F1: 0.3188
- Device: cuda

## Short Real MCTS

```bash
python -m vc_demo.mcts \
  --tree experiments/real_k562_tree.json \
  --reset \
  --steps 3 \
  --max-epochs 1 \
  --summary experiments/real_k562_mcts_summary.md \
  --root-config configs/real_k562_template.json \
  --root-name real_k562_template_mlp \
  --max-children 2
```

Result summary: experiments/real_k562_mcts_summary.md
