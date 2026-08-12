from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import numpy as np


CONTROL_DRUGS = {"DMSO", "dmso", "medium", "Medium", "CTRL", "Ctrl", "control", "Control"}


def sparse_to_log_cpm(X):
    X = X.astype("float32").copy()
    totals = np.asarray(X.sum(axis=1)).reshape(-1).astype("float32")
    totals[totals <= 0] = 1.0
    scale = (10000.0 / totals).astype("float32")
    X = X.multiply(scale[:, None]).tocsr()
    X.data = np.log1p(X.data)
    return X


def split_drugs(drugs: list[str], seed: int) -> dict[str, list[str]]:
    rng = np.random.default_rng(seed)
    shuffled = np.array(sorted(drugs), dtype=object)
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = max(1, int(round(n * 0.70)))
    n_val = max(1, int(round(n * 0.15)))
    if n_train + n_val >= n:
        n_train = max(1, n - 2)
        n_val = 1
    return {
        "train": shuffled[:n_train].astype(str).tolist(),
        "val": shuffled[n_train:n_train + n_val].astype(str).tolist(),
        "test": shuffled[n_train + n_val:].astype(str).tolist(),
    }


def make_split(
    X,
    obs,
    split_drugs: list[str],
    control_idx: np.ndarray,
    feature_idx: np.ndarray,
    target_idx: np.ndarray,
    class_drugs: list[str],
    bootstraps_per_drug: int,
    cells_per_bootstrap: int,
    deg_threshold: float,
    seed: int,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    drug_to_col = {d: i for i, d in enumerate(class_drugs)}
    rows = []
    labels = []
    row_drugs = []
    row_ids = []
    ctrl = np.asarray(control_idx)
    for drug in split_drugs:
        treated = np.flatnonzero(obs["Drug"].astype(str).to_numpy() == drug)
        if len(treated) == 0:
            continue
        for rep in range(bootstraps_per_drug):
            t_idx = rng.choice(treated, size=min(cells_per_bootstrap, len(treated)), replace=len(treated) < cells_per_bootstrap)
            c_idx = rng.choice(ctrl, size=min(cells_per_bootstrap, len(ctrl)), replace=len(ctrl) < cells_per_bootstrap)
            t_feat = np.asarray(X[t_idx[:, None], feature_idx].mean(axis=0)).reshape(-1)
            c_feat = np.asarray(X[c_idx[:, None], feature_idx].mean(axis=0)).reshape(-1)
            t_target = np.asarray(X[t_idx[:, None], target_idx].mean(axis=0)).reshape(-1)
            c_target = np.asarray(X[c_idx[:, None], target_idx].mean(axis=0)).reshape(-1)
            delta_feat = (t_feat - c_feat).astype("float32")
            delta_target = (t_target - c_target).astype("float32")
            y = np.full(delta_target.shape[0], 1, dtype="int64")
            y[delta_target <= -deg_threshold] = 0
            y[delta_target >= deg_threshold] = 2
            onehot = np.zeros(len(class_drugs), dtype="float32")
            onehot[drug_to_col[drug]] = 1.0
            rows.append(np.concatenate([delta_feat, onehot]).astype("float32"))
            labels.append(y)
            row_drugs.append(drug)
            row_ids.append(f"{drug}__bootstrap_{rep:04d}")
    if not rows:
        raise ValueError("no rows generated for split")
    return {
        "features": np.stack(rows).astype("float32"),
        "labels": np.stack(labels).astype("int64"),
        "drug": np.asarray(row_drugs, dtype=object).astype(str),
        "row_id": np.asarray(row_ids, dtype=object).astype(str),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare HELF perturbation DEG-direction NPZ files from merged_data.h5ad.")
    parser.add_argument("--input", type=Path, default=Path("data/raw/merged_data.h5ad"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/cell_lines/helf_perturb_deg_cls"))
    parser.add_argument("--feature-genes", type=int, default=1024)
    parser.add_argument("--target-genes", type=int, default=512)
    parser.add_argument("--bootstraps-per-drug", type=int, default=64)
    parser.add_argument("--cells-per-bootstrap", type=int, default=96)
    parser.add_argument("--min-treated-cells", type=int, default=50)
    parser.add_argument("--deg-threshold", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=19)
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"missing input h5ad: {args.input}")
    adata = ad.read_h5ad(args.input)
    required_obs = ["Drug", "Treat"]
    missing = [c for c in required_obs if c not in adata.obs]
    if missing:
        raise SystemExit(f"h5ad is missing required obs columns: {missing}")
    X = adata.layers["raw_counts"] if "raw_counts" in adata.layers else adata.X
    X = sparse_to_log_cpm(X)

    drugs = adata.obs["Drug"].astype(str).to_numpy()
    treat = adata.obs["Treat"].astype(str).to_numpy()
    control_idx = np.flatnonzero((treat == "Ctrl") | np.isin(drugs, list(CONTROL_DRUGS)))
    if len(control_idx) < args.cells_per_bootstrap:
        raise SystemExit(f"not enough control cells: {len(control_idx)}")

    drug_counts = {d: int((drugs == d).sum()) for d in sorted(set(drugs)) if d not in CONTROL_DRUGS}
    perturbation_drugs = [d for d, n in drug_counts.items() if n >= args.min_treated_cells]
    if len(perturbation_drugs) < 5:
        raise SystemExit(f"need at least 5 perturbation drugs after filtering; got {len(perturbation_drugs)}")

    mean = np.asarray(X.mean(axis=0)).reshape(-1)
    mean_sq = np.asarray(X.power(2).mean(axis=0)).reshape(-1)
    var = mean_sq - mean ** 2
    detected = np.asarray((X > 0).sum(axis=0)).reshape(-1)
    eligible = detected >= max(10, int(0.002 * X.shape[0]))
    order = np.argsort(np.where(eligible, var, -np.inf))[::-1]
    target_idx = order[: args.target_genes]
    used_targets = set(target_idx.tolist())
    feature_pool = [int(i) for i in order if int(i) not in used_targets]
    feature_idx = np.asarray(feature_pool[: args.feature_genes], dtype=int)
    target_genes = np.asarray(adata.var_names, dtype=object)[target_idx].astype(str)
    feature_genes = np.asarray(adata.var_names, dtype=object)[feature_idx].astype(str)

    drug_splits = split_drugs(perturbation_drugs, args.seed)
    payloads = {}
    for offset, split_name in enumerate(["train", "val", "test"]):
        payloads[split_name] = make_split(
            X,
            adata.obs,
            drug_splits[split_name],
            control_idx,
            feature_idx,
            target_idx,
            perturbation_drugs,
            args.bootstraps_per_drug,
            args.cells_per_bootstrap,
            args.deg_threshold,
            args.seed + 100 * offset,
        )

    train_x = payloads["train"]["features"]
    mu = train_x.mean(axis=0, keepdims=True)
    sigma = train_x.std(axis=0, keepdims=True)
    sigma[sigma < 1e-6] = 1.0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    label_counts = {}
    for split_name, payload in payloads.items():
        x = ((payload["features"] - mu) / sigma).astype("float32")
        y = payload["labels"].astype("int64")
        files[split_name] = f"{split_name}.npz"
        label_counts[split_name] = {"down": int((y == 0).sum()), "unchanged": int((y == 1).sum()), "up": int((y == 2).sum())}
        np.savez_compressed(
            args.output_dir / files[split_name],
            features=x,
            labels=y,
            row_id=payload["row_id"],
            drug=payload["drug"],
            selected_genes=feature_genes,
            target_genes=target_genes,
            class_names=np.array(["down", "unchanged", "up"], dtype=object),
            perturbation_drugs=np.asarray(perturbation_drugs, dtype=object).astype(str),
        )

    summary = {
        "format": "npz",
        "task_id": "HELF_PERTURB_DEG",
        "task_type": "drug_perturbation_target_gene_deg_direction_prediction",
        "source_h5ad": str(args.input),
        "n_cells": int(adata.n_obs),
        "n_genes_original": int(adata.n_vars),
        "n_feature_genes": int(len(feature_idx)),
        "n_drug_onehot_features": int(len(perturbation_drugs)),
        "n_features": int(payloads["train"]["features"].shape[1]),
        "n_targets": int(len(target_idx)),
        "n_classes": 3,
        "class_names": ["down", "unchanged", "up"],
        "perturbation_drugs": perturbation_drugs,
        "drug_splits": drug_splits,
        "split_policy": "drug-level split before bootstrap; validation/test drugs are held-out perturbations",
        "control_policy": "Treat == Ctrl or Drug in DMSO/medium/control aliases",
        "feature_policy": "raw_counts -> CPM(1e4) -> log1p -> treated-control pseudobulk delta over high-variance feature genes + perturbation drug one-hot; z-score using train rows only",
        "label_policy": f"target-gene treated-control logCPM delta: <= -{args.deg_threshold} down, >= {args.deg_threshold} up, otherwise unchanged",
        "reward": "validation Macro-F1 over flattened target-gene DEG direction labels",
        "test_policy": "test Macro-F1 is report-only and must not drive search",
        "files": files,
        "counts_by_split": {k: int(v["features"].shape[0]) for k, v in payloads.items()},
        "label_counts_by_split": label_counts,
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output_dir / "task_contract.md").write_text("\n".join([
        "# HELF_PERTURB_DEG Task Contract",
        "",
        "Predict drug perturbation response as target-gene DEG direction in HELF cells.",
        "",
        "- Unit: bootstrap pseudobulk pair `(drug-treated cells, control cells)`.",
        "- Input: treated-control expression delta over feature genes plus perturbation drug one-hot.",
        "- Output: `[batch, n_target_genes, 3]` logits for down / unchanged / up.",
        "- Reward: validation Macro-F1 only.",
        "- Test Macro-F1: final report only.",
        "- Split: drug-level split before bootstrap, so val/test drugs are held-out perturbations.",
        "- Forbidden leakage: do not use test labels, test metrics, or split identity during search.",
        "- Artifact policy: no foundation artifacts are required for this small open-source demo.",
        "",
    ]))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
