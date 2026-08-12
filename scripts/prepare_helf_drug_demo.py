from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import numpy as np


def stratified_split(labels: np.ndarray, train_frac: float, val_frac: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    split = np.empty(labels.shape[0], dtype=object)
    for cls in np.unique(labels):
        idx = np.flatnonzero(labels == cls)
        rng.shuffle(idx)
        n = len(idx)
        n_train = max(1, int(round(n * train_frac)))
        n_val = max(1, int(round(n * val_frac)))
        if n_train + n_val >= n:
            n_train = max(1, n - 2)
            n_val = 1
        split[idx[:n_train]] = "train"
        split[idx[n_train:n_train + n_val]] = "val"
        split[idx[n_train + n_val:]] = "test"
    return split.astype(str)


def sparse_to_log_cpm(X):
    X = X.astype("float32").copy()
    totals = np.asarray(X.sum(axis=1)).reshape(-1).astype("float32")
    totals[totals <= 0] = 1.0
    scale = (10000.0 / totals).astype("float32")
    X = X.multiply(scale[:, None]).tocsr()
    X.data = np.log1p(X.data)
    return X


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare HELF drug identity classification NPZ files from merged_data.h5ad.")
    parser.add_argument("--input", type=Path, default=Path("data/raw/merged_data.h5ad"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/cell_lines/helf_drug_cls"))
    parser.add_argument("--top-genes", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"missing input h5ad: {args.input}")
    adata = ad.read_h5ad(args.input)
    required_obs = ["Drug", "Treat", "Batch", "Sample", "CellLines", "Dose", "FixedTimePoint"]
    missing = [c for c in required_obs if c not in adata.obs]
    if missing:
        raise SystemExit(f"h5ad is missing required obs columns: {missing}")
    X = adata.layers["raw_counts"] if "raw_counts" in adata.layers else adata.X
    X = sparse_to_log_cpm(X)
    mean = np.asarray(X.mean(axis=0)).reshape(-1)
    mean_sq = np.asarray(X.power(2).mean(axis=0)).reshape(-1)
    var = mean_sq - mean ** 2
    detected = np.asarray((X > 0).sum(axis=0)).reshape(-1)
    eligible = detected >= max(10, int(0.002 * X.shape[0]))
    order = np.argsort(np.where(eligible, var, -np.inf))[::-1]
    selected = order[: args.top_genes]
    selected = selected[np.isfinite(var[selected])]
    genes = np.asarray(adata.var_names, dtype=object)[selected].astype(str)
    features = X[:, selected].toarray().astype("float32")

    drugs = adata.obs["Drug"].astype(str).to_numpy()
    classes = np.array(sorted(set(drugs)), dtype=object)
    label_map = {name: i for i, name in enumerate(classes.tolist())}
    labels = np.array([label_map[x] for x in drugs], dtype="int64")[:, None]
    split = stratified_split(labels.reshape(-1), 0.70, 0.15, args.seed)
    train_mask = split == "train"
    mu = features[train_mask].mean(axis=0, keepdims=True)
    sigma = features[train_mask].std(axis=0, keepdims=True)
    sigma[sigma < 1e-6] = 1.0
    features = ((features - mu) / sigma).astype("float32")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in ["train", "val", "test"]:
        mask = split == name
        out = f"{name}.npz"
        files[name] = out
        np.savez_compressed(
            args.output_dir / out,
            features=features[mask],
            labels=labels[mask],
            cell_ids=np.asarray(adata.obs_names, dtype=object)[mask].astype(str),
            drug=np.asarray(drugs, dtype=object)[mask].astype(str),
            treat=adata.obs["Treat"].astype(str).to_numpy()[mask],
            batch=adata.obs["Batch"].astype(str).to_numpy()[mask],
            sample=adata.obs["Sample"].astype(str).to_numpy()[mask],
            selected_genes=genes,
            target_genes=np.array(["drug_identity"], dtype=object),
            class_names=classes.astype(str),
        )
    summary = {
        "format": "npz",
        "task_id": "HELF_DRUG",
        "task_type": "single_cell_drug_identity_classification",
        "source_h5ad": str(args.input),
        "n_cells": int(adata.n_obs),
        "n_genes_original": int(adata.n_vars),
        "n_features": int(features.shape[1]),
        "n_targets": 1,
        "n_classes": int(len(classes)),
        "label_column": "Drug",
        "class_names": classes.astype(str).tolist(),
        "split_policy": "stratified_random_by_Drug_70_15_15_seeded; test labels are report-only",
        "feature_policy": "raw_counts -> CPM(1e4) -> log1p -> top variance genes -> z-score using train split statistics only",
        "files": files,
        "feature_key": "features",
        "label_key": "labels",
        "counts_by_split": {name: int((split == name).sum()) for name in ["train", "val", "test"]},
        "counts_by_class": {str(cls): int((drugs == cls).sum()) for cls in classes},
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output_dir / "task_contract.md").write_text("\n".join([
        "# HELF_DRUG Task Contract",
        "",
        "Predict the 12-way `Drug` identity from single-cell HELF expression profiles.",
        "",
        "- Reward: validation Macro-F1",
        "- Test Macro-F1: final report only",
        "- Input: log-normalized high-variance expression features",
        "- Output: `[batch, 1, 12]` logits",
        "- Forbidden leakage: do not use `Drug`, `Sample`, `Well`, or split labels as input features.",
        "",
    ]))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
