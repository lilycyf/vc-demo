# Data Layout

Large biological data should stay out of Git. Put local one-cell-line datasets under:

```text
data/cell_lines/<cell_line>/
```

The B-stage loader currently supports compressed NumPy NPZ files plus a manifest.

## Split-File Layout

Preferred layout:

```text
data/cell_lines/k562/
  manifest.json
  train.npz
  val.npz
  test.npz
```

Each NPZ contains:

- `features`: `float32` matrix shaped `[n_perturbations, n_features]`
- `labels`: `int64` matrix shaped `[n_perturbations, n_target_genes]`

Labels use the DEG classification convention:

- `0`: down
- `1`: unchanged
- `2`: up

Minimal `manifest.json`:

```json
{
  "format": "npz",
  "cell_line": "K562",
  "task": "CRISPR_KO_DEG_classification",
  "feature_key": "features",
  "label_key": "labels",
  "n_classes": 3,
  "class_names": ["down", "unchanged", "up"],
  "files": {
    "train": "train.npz",
    "val": "val.npz",
    "test": "test.npz"
  }
}
```

## Single-File Layout

Also supported:

```text
data/cell_lines/k562/
  manifest.json
  dataset.npz
```

The NPZ must include `features`, `labels`, and a string `split` array with values
`train`, `val`, or `test`.

```json
{
  "format": "npz",
  "cell_line": "K562",
  "feature_key": "features",
  "label_key": "labels",
  "split_key": "split",
  "n_classes": 3,
  "file": "dataset.npz"
}
```

## Validate

```bash
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562
```

## Fixture

To verify the real-data code path without downloading biological data:

```bash
python scripts/make_fake_real_dataset.py --data-dir data/cell_lines/k562_demo
python scripts/validate_real_dataset.py --data-dir data/cell_lines/k562_demo
python -m vc_demo.train \
  --config configs/real_k562_demo_fixture.json \
  --output-dir experiments/nodes/real_k562_demo_fixture \
  --max-epochs 1
```
