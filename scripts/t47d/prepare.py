"""Build a lineage-aware T47D dataset without fitting on held-out labels."""
from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import json
import re
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import io, sparse
from threadpoolctl import threadpool_limits


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def read_samples(path):
    records = []
    current = None
    with gzip.open(path, "rt") as stream:
        for line in stream:
            line = line.strip()
            if line.startswith("^SAMPLE = "):
                current = {"gsm": line.split(" = ")[1]}
                records.append(current)
            elif current is not None and line.startswith("!Sample_title = "):
                title = line.split(" = ", 1)[1]
                current.update(title=title, sample_id=title.split(",")[0],
                               replicate_label=re.search(r"replicate (\d+)", title).group(1))
            elif current is not None and line.startswith("!Sample_characteristics_ch1 = "):
                key, value = line.split(" = ", 1)[1].split(": ", 1)
                current[key] = value
    result = pd.DataFrame(records)
    def treatment(text):
        if text == "Baseline":
            return "baseline"
        if "+" in text:
            return "combination"
        return "palbociclib" if "Palbociclib" in text else "giredestrant"
    result["treatment_id"] = result["treatment"].map(treatment)
    result["time_day"] = result["time point"].map(
        lambda x: 180 if x == "Month 6" else int(x.split()[-1]))
    result["long_term"] = result["time point"].eq("Month 6")
    if result.groupby("sample_id")[["treatment_id", "time_day"]].nunique().max().max() != 1:
        raise ValueError("Conflicting metadata for a shared SAM identifier")
    return result


def assign_clones(gfp, names):
    gfp = gfp.tocsc()
    gfp.eliminate_zeros()
    n_nonzero = np.diff(gfp.indptr)
    assigned = np.full(gfp.shape[1], "unknown", dtype=object)
    single = np.flatnonzero(n_nonzero == 1)
    assigned[single] = np.asarray(names)[gfp.indices[gfp.indptr[single]]]
    return assigned, n_nonzero


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/t47d_lineage/raw")
    parser.add_argument("--output-dir", default="data/t47d_lineage/prepared")
    parser.add_argument("--run-dir", default="experiments/t47d_lineage_resistance_demo")
    parser.add_argument("--min-baseline-cells", type=int, default=10)
    args = parser.parse_args()
    raw, out, run = map(Path, (args.raw_dir, args.output_dir, args.run_dir))
    out.mkdir(parents=True, exist_ok=True)
    run.mkdir(parents=True, exist_ok=True)
    file = lambda stem: raw / ("GSE260703_" + stem + ".gz")
    samples = read_samples(file("family.soft"))
    samples.to_csv(run / "sample_manifest.csv", index=False)
    cells = pd.read_csv(file("count_barcodes.csv"), header=None, names=["cell_barcode", "sample_id"])
    gfp_cells = pd.read_csv(file("gfp_barcodes.csv"), header=None, names=["cell_barcode", "sample_id"])
    if cells.cell_barcode.duplicated().any() or gfp_cells.cell_barcode.duplicated().any():
        raise ValueError("Cell barcodes are not unique")
    gfp_names = pd.read_csv(file("gfp_features.csv"), header=None)[0].to_numpy()
    with threadpool_limits(limits=8):
        gfp = io.mmread(file("gfp_matrix.mtx"))
    if gfp.shape != (len(gfp_names), len(gfp_cells)):
        raise ValueError("GFP matrix and row/column annotation shape mismatch")
    clone, multiplicity = assign_clones(gfp, gfp_names)
    assignments = pd.DataFrame({"cell_barcode": gfp_cells.cell_barcode, "clone_id": clone,
                                "barcode_multiplicity": multiplicity})
    cells = cells.merge(assignments, on="cell_barcode", how="left", validate="one_to_one")
    if cells.clone_id.isna().any():
        raise ValueError("Expression cells lack corresponding GFP annotation")
    lookup = samples.drop_duplicates("sample_id").set_index("sample_id")
    cells["treatment"] = cells.sample_id.map(lookup.treatment_id)
    cells["time_day"] = cells.sample_id.map(lookup.time_day)
    if cells.treatment.isna().any():
        raise ValueError("Unmapped expression sample identifier")
    cells["library_id"] = cells.cell_barcode.str.split("_").str[0]
    cells["replicate_id"] = cells.library_id
    cells["replicate_evidence"] = "library prefix; biological independence not established"
    genes = pd.read_csv(file("count_features.csv"), header=None, names=["gene_id", "gene_symbol"])
    print("Reading expression matrix", flush=True)
    with threadpool_limits(limits=8):
        matrix = io.mmread(file("count_matrix.mtx"))
    if matrix.shape != (len(genes), len(cells)):
        raise ValueError("Expression matrix and annotation shape mismatch")
    if matrix.data.min() < 0 or matrix.data.max() > np.iinfo(np.int32).max:
        raise ValueError("Invalid count range")
    counts = matrix.astype(np.int32).T.tocsr()
    del matrix, gfp
    gc.collect()
    totals = np.asarray(counts.sum(axis=1)).ravel()
    detected = np.diff(counts.indptr)
    mitochondrial = genes.gene_symbol.fillna("").str.startswith("MT-").to_numpy()
    mito_counts = np.asarray(counts[:, mitochondrial].sum(axis=1)).ravel()
    cells["total_counts"] = totals
    cells["detected_genes"] = detected
    cells["mitochondrial_fraction"] = mito_counts / np.maximum(totals, 1)
    cells["qc_status"] = np.where((detected >= 500) & (cells.mitochondrial_fraction <= .25), "pass", "excluded")
    cells["exclusion_reason"] = np.where(detected < 500, "detected_genes_lt_500",
                                         np.where(cells.mitochondrial_fraction > .25, "mitochondria_gt_25_percent", ""))
    cells.to_csv(out / "cell_qc_and_assignments.csv.gz", index=False)
    good = cells.qc_status.eq("pass") & cells.clone_id.ne("unknown")
    usable = cells.loc[good].copy()
    clone_counts = usable.groupby(["clone_id", "treatment", "time_day"], observed=True).size().rename("cell_count").reset_index()
    clone_counts.to_csv(out / "clone_condition_counts.csv", index=False)
    clone_counts.to_csv(run / "clone_condition_counts.csv", index=False)
    baseline = clone_counts.query("treatment == 'baseline'").set_index("clone_id").cell_count
    eligible = sorted(baseline[baseline >= args.min_baseline_cells].index)
    if len(eligible) < 8:
        raise ValueError(f"Only {len(eligible)} clones meet baseline-only eligibility; revise study design before splitting")
    # Eligibility uses baseline observations only, never endpoint abundance.
    observed = usable.clone_id.isin(eligible)
    aggregate_cells = usable.loc[observed].copy()
    locations = cells.index[good][observed]
    keys = list(zip(aggregate_cells.clone_id, aggregate_cells.treatment, aggregate_cells.time_day))
    unique_keys = sorted(set(keys))
    key_index = {key: i for i, key in enumerate(unique_keys)}
    indices = np.array([key_index[key] for key in keys])
    group_sizes = np.bincount(indices, minlength=len(unique_keys))
    group = sparse.csr_matrix((np.ones(len(indices), dtype=np.float32),
                               (indices, np.arange(len(indices)))), shape=(len(unique_keys), len(indices)))
    subset = counts[locations].astype(np.float32)
    subset = sparse.diags(1e4 / np.maximum(totals[locations], 1)).dot(subset).tocsr()
    subset.data = np.log1p(subset.data)
    aggregate = sparse.diags(1 / group_sizes).dot(group @ subset).tocsr()
    sparse.save_npz(out / "clone_mean_log_expression.npz", aggregate)
    raw_sums = group @ counts[locations]
    sparse.save_npz(out / "clone_pseudobulk_counts.npz", raw_sums)
    pd.DataFrame(unique_keys, columns=["clone_id", "treatment", "time_day"]).assign(
        cell_count=group_sizes).to_csv(out / "clone_expression_rows.csv", index=False)
    genes.to_csv(out / "gene_order.csv", index=False)
    # Persist QC-passing cells with lineage annotations for real scVI/trajectory candidates.
    obs = cells.loc[good].set_index("cell_barcode").copy()
    var = genes.set_index("gene_id")
    adata = ad.AnnData(counts[good.to_numpy()], obs=obs, var=var)
    adata.write_h5ad(out / "qc_counts.h5ad", compression="gzip")
    audit = {
        "raw_expression_shape": list(counts.shape), "raw_gfp_shape": [len(gfp_names), len(gfp_cells)],
        "cells_qc_pass": int(cells.qc_status.eq("pass").sum()),
        "cells_single_barcode": int((multiplicity == 1).sum()), "cells_qc_and_single_barcode": int(good.sum()),
        "clones_with_baseline_ge_10": eligible, "eligible_clone_count": len(eligible),
        "primary_eligibility": f"at least {args.min_baseline_cells} QC-passing baseline cells; no endpoint filter",
        "clone_assignment": "exactly one positive GFP feature; multi-barcode/zero-barcode unknown, no invented barcode merging",
        "min_detected_genes": 500, "max_mito_fraction": .25,
        "qc_source": "Genentech/TraCSED model_scripts/TraCSED_final_plsr.R",
        "replicate_caveat": "Repeated GSMs share SAM identifiers; library prefixes are not assumed independent biological replicates",
        "long_term_time": "Month 6 kept separate; 180 is a nominal ordering code, not an exact measured day",
        "baseline_caveat": "GEO labels Day 0; paper Methods describe 1-day DMSO exposure",
        "doublet_caveat": "Multi-barcode excluded; no unverified transcriptome doublet calls are fabricated",
    }
    write_json(run / "clone_assignment_audit.json", audit)
    write_json(out / "dataset_manifest.json", audit)
    acquisition = json.loads((raw / "download_manifest.json").read_text())
    write_json(run / "artifact_registry.json", acquisition)
    print(json.dumps(audit), flush=True)


if __name__ == "__main__":
    main()
