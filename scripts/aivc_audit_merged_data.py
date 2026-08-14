from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd

CONTROL_RE = re.compile(r"control|ctrl|vehicle|dmso|untreat|untreated|mock|none", re.I)
KEY_COLUMNS = [
    "Treat",
    "Drug",
    "Dose",
    "FixedTimePoint",
    "CellLines",
    "BioRep",
    "Batch",
    "Well",
    "Sample",
]


def jsonable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.ndarray,)):
        return value.tolist()
    if pd.isna(value):
        return None
    return value


def value_counts(series: pd.Series, limit: int = 40) -> dict[str, Any]:
    counts = series.astype(str).fillna("<NA>").value_counts(dropna=False)
    return {
        "n_unique": int(counts.shape[0]),
        "top": {str(k): int(v) for k, v in counts.head(limit).items()},
        "truncated": bool(counts.shape[0] > limit),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h5ad", default="data/raw/merged_data.h5ad")
    parser.add_argument("--out-dir", default="experiments/aivc_perturb_demo_day1")
    parser.add_argument("--target-genes", type=int, default=1024)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    adata = ad.read_h5ad(args.h5ad, backed="r")
    obs = adata.obs.copy()
    var = adata.var.copy()

    present_cols = [c for c in KEY_COLUMNS if c in obs.columns]
    missing_cols = [c for c in KEY_COLUMNS if c not in obs.columns]

    x_shape = tuple(int(x) for x in adata.shape)
    x_info = {"shape": list(x_shape), "type": type(adata.X).__name__}
    try:
        x_info["nnz"] = int(adata.X.nnz)
        x_info["density"] = float(adata.X.nnz / (adata.shape[0] * adata.shape[1]))
    except Exception:
        x_info["nnz"] = None
        x_info["density"] = None

    column_audit = {c: value_counts(obs[c]) for c in present_cols}

    control_candidates: dict[str, list[str]] = {}
    for col in ["Treat", "Drug"]:
        if col in obs.columns:
            vals = sorted({str(v) for v in obs[col].dropna().unique()})
            control_candidates[col] = [v for v in vals if CONTROL_RE.search(v)]

    condition_cols = [c for c in ["CellLines", "Drug", "Dose", "FixedTimePoint"] if c in obs.columns]
    condition_summary: dict[str, Any] = {"columns": condition_cols}
    if condition_cols:
        grouped = obs.groupby(condition_cols, observed=True).size().reset_index(name="n_cells")
        condition_summary.update(
            {
                "n_conditions": int(grouped.shape[0]),
                "n_cells_per_condition": {
                    "min": int(grouped["n_cells"].min()),
                    "median": float(grouped["n_cells"].median()),
                    "mean": float(grouped["n_cells"].mean()),
                    "max": int(grouped["n_cells"].max()),
                },
                "top_conditions": grouped.sort_values("n_cells", ascending=False).head(30).to_dict(orient="records"),
            }
        )

    split_feasibility = {}
    for axis in ["Drug", "CellLines", "Batch", "BioRep"]:
        if axis in obs.columns:
            split_feasibility[f"heldout_{axis}"] = {
                "n_groups": int(obs[axis].astype(str).nunique(dropna=False)),
                "min_cells_per_group": int(obs.groupby(obs[axis].astype(str), observed=True).size().min()),
                "median_cells_per_group": float(obs.groupby(obs[axis].astype(str), observed=True).size().median()),
            }

    gene_examples = [str(x) for x in list(adata.var_names[:30])]
    obs_examples = [str(x) for x in list(adata.obs_names[:10])]

    # Pick target genes by nonzero count variance proxy without loading whole dense matrix.
    target_gene_note = (
        "Day-1 draft recommends selecting 512-2000 target genes after a full pseudobulk pass. "
        "Use high-expression/high-variance genes and force-include marker/pathway genes that map to Reactome/STRING."
    )

    audit = {
        "source_h5ad": str(Path(args.h5ad)),
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "x": x_info,
        "obs_columns": list(obs.columns),
        "var_columns": list(var.columns),
        "present_key_columns": present_cols,
        "missing_key_columns": missing_cols,
        "column_audit": column_audit,
        "control_candidates": control_candidates,
        "condition_summary": condition_summary,
        "split_feasibility": split_feasibility,
        "gene_name_examples": gene_examples,
        "obs_name_examples": obs_examples,
        "layers": list(adata.layers.keys()),
        "obsm": list(adata.obsm.keys()),
        "uns_keys": list(adata.uns.keys()),
        "target_gene_note": target_gene_note,
    }

    task_contract = {
        "task_id": "aivc_drug_dose_time_perturb_response_demo",
        "research_question": "Given CellLine, Drug, Dose, FixedTimePoint and baseline expression context, predict target-gene perturbation response and rank drug-dose-time conditions.",
        "data_source": str(Path(args.h5ad)),
        "unit_of_prediction": "CellLines x Drug x Dose x FixedTimePoint pseudobulk condition",
        "input_columns": present_cols,
        "required_columns_status": {c: (c in obs.columns) for c in KEY_COLUMNS},
        "recommended_label": {
            "type": "target_gene_DEG_three_class",
            "classes": ["down", "unchanged", "up"],
            "construction": "Compare each treated pseudobulk condition against matched control/baseline within CellLine and FixedTimePoint when possible; threshold logFC to three classes.",
        },
        "recommended_splits": [
            "heldout_drug",
            "heldout_cellline_if_multiple_celllines_are_available",
            "heldout_batch_or_biorep_as_secondary_robustness_check",
        ],
        "reward_metric": "validation Macro-F1 on target-gene DEG classes; test Macro-F1 report-only",
        "first_search_space": {
            "roots": ["linear_or_logreg", "residual_mlp", "drug_dose_time_metadata_mlp", "pseudobulk_delta_mlp"],
            "source_backed_artifacts": ["Reactome pathway membership", "STRING target-gene graph", "RDKit Morgan fingerprint"],
            "optional_foundation_artifacts": ["ChemBERTa drug embedding", "UCE/scGPT/Geneformer/scFoundation cell embedding branch"],
            "heads": ["dense", "low_rank_target_head", "pathway_hierarchical_head", "graph_smoothed_head"],
            "fusion": ["concat", "gated_residual", "bilinear", "cross_attention", "MoE"],
        },
        "guardrails": [
            "No random-cell split for final claim",
            "No test metric in search reward",
            "No fallback/proxy foundation artifact",
            "Artifact branches must preserve dense parent branch and add auditable residual/fusion",
        ],
        "day1_status": "dataset_audited_task_contract_draft",
    }

    (out_dir / "dataset_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
    (out_dir / "task_contract_draft.json").write_text(json.dumps(task_contract, indent=2, ensure_ascii=False) + "\n")

    md = []
    md.append("# AIVC Perturbation Demo Day 1 Dataset Audit\n")
    md.append(f"Source: `{args.h5ad}`\n")
    md.append("## Dataset Shape\n")
    md.append(f"- Cells: `{adata.n_obs}`\n")
    md.append(f"- Genes: `{adata.n_vars}`\n")
    md.append("- X type: {}\n".format(x_info.get("type")))
    md.append("- X density: {}\n".format(x_info.get("density")))
    md.append("\n## Key Columns\n")
    md.append(f"- Present: `{present_cols}`\n")
    md.append(f"- Missing: `{missing_cols}`\n")
    md.append("\n## Column Cardinality\n")
    for c in present_cols:
        md.append(f"### {c}\n")
        md.append("- Unique values: {}\n".format(column_audit[c]["n_unique"]))
        md.append("- Top values:\n")
        for k, v in column_audit[c]["top"].items():
            md.append(f"  - `{k}`: {v}\n")
    md.append("\n## Control Candidates\n")
    md.append("```json\n" + json.dumps(control_candidates, indent=2, ensure_ascii=False) + "\n```\n")
    md.append("\n## Condition Feasibility\n")
    md.append("```json\n" + json.dumps(condition_summary, indent=2, ensure_ascii=False, default=jsonable) + "\n```\n")
    md.append("\n## Split Feasibility\n")
    md.append("```json\n" + json.dumps(split_feasibility, indent=2, ensure_ascii=False) + "\n```\n")
    md.append("\n## Recommended Demo Task\n")
    md.append("Predict target-gene DEG class for each `CellLines x Drug x Dose x FixedTimePoint` pseudobulk condition, then rank drug-dose-time conditions by predicted response strength.\n")
    md.append("\n## Day 1 Decision\n")
    md.append("This dataset is suitable for a real perturbation-response harness demo if matched control/baseline conditions can be identified from `Treat` or `Drug`. The next step is to build pseudobulk condition tables and DEG labels.\n")
    (out_dir / "dataset_audit.md").write_text("".join(md))

    print(json.dumps({
        "out_dir": str(out_dir),
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "present_key_columns": present_cols,
        "n_conditions": condition_summary.get("n_conditions"),
        "control_candidates": control_candidates,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
