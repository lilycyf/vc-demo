"""Frozen, clone-grouped early-to-endpoint regression contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

TREATMENTS = ("giredestrant", "palbociclib", "combination")
EARLY_DAYS = (0, 1, 4)
CV_SEEDS = (3, 7, 11, 17, 23)


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def make_split(clones):
    ordered = np.array(sorted(clones))
    ordered = np.random.default_rng(20261106).permutation(ordered)
    n_test = max(4, int(np.ceil(len(ordered) * .2)))
    test, development = sorted(ordered[:n_test]), sorted(ordered[n_test:])
    folds = []
    for seed in CV_SEEDS:
        shuffled = np.random.default_rng(seed).permutation(development)
        parts = np.array_split(shuffled, 3)
        for k, valid in enumerate(parts):
            train = sorted(set(development) - set(valid))
            folds.append({"seed": seed, "fold": k, "train_clones": train,
                          "validation_clones": sorted(valid)})
    return {"split_seed": 20261106, "test_clones": test,
            "development_clones": development, "folds": folds}


def load_bundle(prepared, pathways, run_dir):
    prepared, pathways, run_dir = map(Path, (prepared, pathways, run_dir))
    audit = json.loads((prepared / "dataset_manifest.json").read_text())
    clones = audit["clones_with_baseline_ge_10"]
    split = make_split(clones)
    split_path = run_dir / "grouped_splits.json"
    if split_path.exists() and json.loads(split_path.read_text()) != split:
        raise ValueError("Frozen grouped split differs from current dataset")
    dump(split_path, split)
    counts = pd.read_csv(prepared / "clone_condition_counts.csv")
    totals = counts.groupby(["treatment", "time_day"]).cell_count.sum().to_dict()
    n = counts.set_index(["clone_id", "treatment", "time_day"]).cell_count.to_dict()
    rows = pd.read_csv(prepared / "clone_expression_rows.csv")
    expr = sparse.load_npz(prepared / "clone_mean_log_expression.npz")
    gene_symbols = pd.read_csv(prepared / "gene_order.csv").gene_symbol.fillna("").to_numpy()
    index = {(r.clone_id, r.treatment, int(r.time_day)): i for i, r in rows.iterrows()}
    pathway_names, memberships = [], []
    for line in pathways.read_text().splitlines():
        terms = line.split("\t")
        if len(terms) < 3:
            raise ValueError("Invalid GMT input")
        mask = np.flatnonzero(np.isin(gene_symbols, terms[2:]))
        if len(mask) >= 5:
            pathway_names.append(terms[0])
            memberships.append(mask)
    if len(memberships) < 20:
        raise ValueError("Insufficient verified Hallmark gene coverage")
    expression, pathway, aux, meta = [], [], [], []
    for clone in sorted(clones):
        for ti, treatment in enumerate(TREATMENTS):
            seq, pa, frequencies, observed = [], [], [], []
            for day in EARLY_DAYS:
                trt = "baseline" if day == 0 else treatment
                key = (clone, trt, day)
                row = expr[index[key]].toarray()[0] if key in index else np.zeros(expr.shape[1])
                seq.append(row)
                pa.append([float(row[m].mean()) for m in memberships])
                count = n.get(key, 0)
                frequencies.append(count / totals[(trt, day)])
                observed.append(float(count >= 3))
            n0 = n[(clone, "baseline", 0)]
            n26 = n.get((clone, treatment, 26), 0)
            f0, f26 = n0 / totals[("baseline", 0)], n26 / totals[(treatment, 26)]
            expression.append(seq)
            pathway.append(pa)
            aux.append([*np.log10(np.maximum(frequencies, 1e-6)), *observed, *np.eye(3)[ti]])
            meta.append({"clone_id": clone, "treatment": treatment, "n_baseline": n0,
                         "n_day26": n26, "fraction_baseline": f0, "fraction_day26": f26,
                         "endpoint_sampling_zero": n26 == 0,
                         "label": float(np.log2((f26 + 1e-5) / (f0 + 1e-5))),
                         "split": "test" if clone in split["test_clones"] else "development"})
    contract = {
        "task": "T47D early state to day26 log2 relative clone selection",
        "unit": "clone x treatment; days0,1,4 sequence input", "accession": "GSE260703",
        "eligibility": audit["primary_eligibility"], "clone_count": len(clones),
        "prediction_rows": len(meta), "early_days": list(EARLY_DAYS), "endpoint_day": 26,
        "label": "log2((fraction_day26 + 1e-5)/(fraction_baseline + 1e-5))",
        "population_denominator": "all QC-passing, uniquely barcoded cells, not just eligible clones",
        "reward": "mean of 5 seed-level pooled 3-fold clone-grouped OOF Spearman values; maximize",
        "secondary_metric": "MAE; within-treatment Spearman",
        "test_policy": "locked clones and Month6 never used for candidate selection; unseal only after freeze",
        "compositional_caveat": "Relative fractions share a population denominator; not absolute growth or cell killing",
        "sampling_zero_policy": "Endpoint zero is sampling-nondetection, not proven extinction; sensitivity required",
        "preprocessing": "cellwise library normalization is label-free; HVG/PCA/scalers/PLS fitted on training folds only",
        "pathways": {"path": str(pathways), "names": pathway_names,
                     "sha256": hashlib.file_digest(pathways.open("rb"), "sha256").hexdigest(),
                     "method": "mean log1p normalized gene expression; not exact scuttle score"},
        "sensitivity_epsilons": [1e-6, 1e-5, 1e-4], "cv_seeds": list(CV_SEEDS),
        "research_scope": "retrospective cell-line analysis, not clinical efficacy or causal state reversal",
    }
    contract_path = run_dir / "task_contract.json"
    if contract_path.exists() and json.loads(contract_path.read_text()) != contract:
        raise ValueError("Task contract changed; start a new experiment rather than resuming")
    dump(contract_path, contract)
    return {"expression": np.array(expression, dtype=np.float32),
            "pathway": np.array(pathway, dtype=np.float32), "aux": np.array(aux, dtype=np.float32),
            "meta": pd.DataFrame(meta), "splits": split, "contract": contract}
