"""Prespecified frozen-pipeline controls; never use results to resume selection."""
from __future__ import annotations

import hashlib
import argparse
import json
import runpy
import subprocess
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from vc_demo.t47d_lineage.data import TREATMENTS, dump, load_bundle
from vc_demo.t47d_lineage.models import Candidate, View
from vc_demo.t47d_lineage.composition import ParentResidualCandidate


class ControlView(View):
    def fit(self, bundle, idx):
        super().fit(bundle, idx)
        if self.config.get("control") == "matched_random_projection" and self.config["representation"] in {"pathway", "both"}:
            self.projection = np.random.default_rng(20261106).normal(
                size=(len(self.genes), bundle["pathway"].shape[-1])) / np.sqrt(len(self.genes))
            z = bundle["expression"][idx][:, :, self.genes]
            if self.config.get("baseline_only",False):
                z = z[:,:1]
            z = self.scaler.transform(z.reshape(-1, len(self.genes))) @ self.projection
            self.project_scaler = StandardScaler().fit(z)
        return self

    def transform(self, bundle, idx):
        sequence, aux = super().transform(bundle, idx)
        if hasattr(self,"projection"):
            z = bundle["expression"][idx][:, :, self.genes]
            z = self.scaler.transform(z.reshape(-1, len(self.genes))) @ self.projection
            projected = self.project_scaler.transform(z).reshape(len(idx), 3, -1)
            if self.config["representation"]=="both":
                expr = bundle["expression"][idx][:,:,self.genes]
                expr = self.scaler.transform(expr.reshape(-1,len(self.genes))).reshape(len(idx),3,-1)
                projected = np.concatenate([expr,projected],axis=-1)
            sequence = projected
            if self.config.get("baseline_only",False):
                sequence = np.repeat(sequence[:,:1],3,axis=1)
        if self.config.get("control") == "pooled_time":
            sequence = np.repeat(sequence.mean(axis=1, keepdims=True), 3, axis=1)
            aux[:, :3] = aux[:, :3].mean(axis=1, keepdims=True)
            aux[:, 3:6] = aux[:, 3:6].mean(axis=1, keepdims=True)
        return sequence.astype(np.float32), aux.astype(np.float32)


class ControlCandidate(Candidate):
    def __init__(self, config):
        super().__init__(config)
        self.view = ControlView(config)


def build_control(config):
    if "parent_config" not in config:
        return ControlCandidate(config)
    composed = ParentResidualCandidate(config)
    composed.parent = build_control({**config["parent_config"],"control":config.get("control")})
    mutation = {k:v for k,v in config.items() if k not in {"parent_config","composition","residual_weight"}}
    composed.mutation = ControlCandidate(mutation)
    return composed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="experiments/t47d_lineage_resistance_demo")
    parser.add_argument("--prepared", default="data/t47d_lineage/prepared")
    parser.add_argument("--pathways", default="data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt")
    args = parser.parse_args()
    run, prepared, gmt = map(Path, (args.run_dir, args.prepared, args.pathways))
    if not (run / "frozen_selection.json").exists():
        raise ValueError("Selection must be frozen before this analysis")
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    protected = {n: hashlib.file_digest((run/n).open("rb"), "sha256").hexdigest()
                 for n in ("tree.json", "mcts_trace.jsonl", "frozen_selection.json")}
    bundle = load_bundle(prepared, gmt, run)
    results = json.loads((run / "search_results.json").read_text())
    tree = json.loads((run / "tree.json").read_text())
    root = tree["nodes"][results["best_root"]["id"]]
    child = tree["nodes"][results["best_child"]["id"]]
    namespace = runpy.run_path("scripts/t47d/run.py")
    cv = namespace["cross_validate"]
    cv.__globals__["Candidate"] = build_control
    controls = {}
    for name in ("matched_random_projection", "pooled_time"):
        controls[name] = cv(bundle, {**child["config"], "control": name})
    shuffled = dict(bundle)
    symbols = pd.read_csv(prepared/"gene_order.csv").gene_symbol.fillna("").to_numpy()
    permutation = np.random.default_rng(20261106).permutation(len(symbols))
    memberships = [np.flatnonzero(np.isin(symbols, line.split("\t")[2:])) for line in gmt.read_text().splitlines()]
    memberships = [m for m in memberships if len(m) >= 5]
    shuffled["pathway"] = np.stack([bundle["expression"][:, :, permutation[m]].mean(axis=-1) for m in memberships], axis=-1)
    controls["shuffled_membership_same_sizes_and_overlap"] = cv(shuffled, child["config"])
    dump(run/"matched_artifact_controls.json", controls)
    counts = pd.read_csv(prepared/"clone_condition_counts.csv")
    by_key = counts.set_index(["clone_id", "treatment", "time_day"]).cell_count.to_dict()
    totals = counts.groupby(["treatment", "time_day"]).cell_count.sum().to_dict()
    meta = bundle["meta"]
    test = np.flatnonzero(meta.split.eq("test"))
    sensitivity = {}
    denominator_diagnostic = {}
    suppression = meta.pivot(index="clone_id", columns="treatment", values="label")
    suppression["combo_suppression_log2"] = suppression[["giredestrant", "palbociclib"]].max(axis=1) - suppression.combination
    suppression["mono_positive_combo_negative"] = suppression[["giredestrant", "palbociclib"]].max(axis=1).gt(0) & suppression.combination.lt(0)
    suppression.to_csv(run/"combination_suppression.csv")
    long_term = {"protocol": "frozen day26 predictions compared with Month6 observations; no refit or selection on Month6",
                 "positive_definition": "at least 3 QC-passing single-barcode Month6 cells, not proof of drug resistance",
                 "evaluations": {}}
    for node in (root, child):
        namespace["load_program"](run/"programs"/node["id"]/"model.py")
        model = joblib.load(run/"nodes"/node["id"]/"frozen_model.joblib")
        pred = model.predict(bundle, test)
        table = meta.iloc[test].copy()
        rng = np.random.default_rng(20261106)
        null = []
        for _ in range(1000):
            endpoint = table.fraction_day26.to_numpy().copy()
            for treatment in TREATMENTS:
                positions = np.flatnonzero(table.treatment.eq(treatment))
                endpoint[positions] = rng.permutation(endpoint[positions])
            shuffled_y = np.log2((endpoint+1e-5)/(table.fraction_baseline.to_numpy()+1e-5))
            score = namespace["correlation"](shuffled_y,pred)
            if score is not None:
                null.append(score)
        denominator_diagnostic[node["id"]]={"observed_spearman":namespace["correlation"](table.label.to_numpy(),pred),
                "null_mean":float(np.mean(null)),"null_interval95":np.percentile(null,[2.5,97.5]).tolist(),
                "null_definition":"shuffle endpoint fractions within treatment, retain baseline denominator and frozen predictions",
                "status":"post-hoc diagnostic of mathematical coupling, not a confirmatory p-value",
                "test_rows_with_nondetected_endpoint":int(table.endpoint_sampling_zero.sum())}
        sensitivity[node["id"]] = {}
        for eps in (1e-6, 1e-5, 1e-4):
            y = np.log2((table.fraction_day26.to_numpy()+eps)/(table.fraction_baseline.to_numpy()+eps))
            sensitivity[node["id"]][str(eps)] = namespace["metrics"](y, pred)
        combo = np.flatnonzero(meta.treatment.eq("combination"))
        p = model.predict(bundle, combo)
        cmeta = meta.iloc[combo].copy()
        cmeta["prediction"] = p
        cmeta["month6_count"] = [by_key.get((c,"combination",180),0) for c in cmeta.clone_id]
        cmeta["month6_fraction"] = cmeta.month6_count / totals[("combination",180)]
        cmeta["observed_persistent"] = cmeta.month6_count.ge(3)
        cmeta.to_csv(run/(node["id"]+"_month6_transport.csv"),index=False)
        for scope, subset in (("all_eligible_clones",cmeta),("heldout_clones",cmeta[cmeta.split.eq("test")])):
            positives = set(subset.loc[subset.observed_persistent,"clone_id"])
            ranked = subset.sort_values("prediction",ascending=False)
            best5 = set(ranked.head(5).clone_id)
            long_term["evaluations"][node["id"]+"/"+scope] = {"clones":len(subset),"persistent_clones":sorted(positives),
                    "top5_recall":len(best5&positives)/len(positives) if positives else None,
                    "interpretation":"out-of-horizon transport, not calibrated 6-month forecast"}
    dump(run/"pseudocount_sensitivity.json",sensitivity)
    dump(run/"denominator_coupling_diagnostic.json",denominator_diagnostic)
    long_term["all_observed_month6_barcodes"] = int(counts.query("time_day == 180").clone_id.nunique())
    long_term["month6_population_cells"] = int(totals[("combination",180)])
    month6_records = counts.query("time_day == 180")[["clone_id","cell_count"]].copy()
    month6_records["in_primary_eligible_cohort"] = month6_records.clone_id.isin(meta.clone_id)
    long_term["observed_month6_barcode_records"] = month6_records.to_dict(orient="records")
    dump(run/"long_term_escape_report.json",long_term)
    rows = pd.read_csv(prepared/"clone_expression_rows.csv")
    programs = ("HALLMARK_ESTROGEN_RESPONSE_EARLY", "HALLMARK_ESTROGEN_RESPONSE_LATE", "HALLMARK_E2F_TARGETS", "HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION")
    from scipy import sparse
    expression = sparse.load_npz(prepared/"clone_mean_log_expression.npz")
    definitions = {line.split("\t")[0]:line.split("\t")[2:] for line in gmt.read_text().splitlines()}
    trend = rows.copy()
    for name in programs:
        members = np.flatnonzero(np.isin(symbols,definitions[name]))
        trend[name] = np.asarray(expression[:,members].mean(axis=1)).ravel()
    trend.to_csv(run/"descriptive_program_trends.csv",index=False)
    applicability = {
        "no_clone_barcode": {"status":"not_identifiable", "reason":"Clone identity is absent from model features; removing outcome mapping destroys the endpoint, not a valid model ablation"},
        "baseline_only": {"status":"evaluated", "evidence":"ablation_metrics.json"},
        "no_temporal_dynamics": {"status":"evaluated", "evidence":"matched_artifact_controls.json pooled_time"},
        "no_pathway": {"status":"evaluated", "evidence":"ablation_metrics.json"},
        "shuffled_pathway_membership": {"status":"evaluated", "evidence":"matched_artifact_controls.json; global gene-identity permutation, not pathway renaming"},
        "matched_capacity_no_artifact": {"status":"evaluated", "evidence":"same PLS components and 50-dimensional projection, train-only genes/scalers"},
        "no_treatment_interaction": {"status":"not_applicable_to_selected_model", "reason":"Selected PLS has no explicit cross-treatment interaction module; no-treatment-indicator control is separately reported"},
        "no_dense_parent": {"status":"not_applicable_to_selected_model", "reason":"Selected PLS is not a parent-plus-dense residual model"},
    }
    if child["config"].get("parent_config"):
        applicability["no_dense_parent"]={"status":"not_yet_evaluated", "reason":"Requires an explicit removal of inherited parent and internal dense routes, not a renamed no-parent proxy"}
    dump(run/"ablation_applicability.json",applicability)
    events = [json.loads(line) for line in (run/"mcts_trace.jsonl").read_text().splitlines()]
    order = [e["node"] for e in events if e["event"]=="backpropagation" and tree["nodes"][e["node"]].get("parent")]
    nodes = [tree["nodes"][name] for name in order]
    values = [n["validation_reward"] for n in nodes]
    fig,axes = plt.subplots(1,2,figsize=(12,4),layout="constrained")
    axes[0].plot(range(1,len(values)+1),values,"o-",color="#146f72",label="Selected rollout")
    axes[0].axhline(root["validation_reward"],color="#b34739",label="Best root")
    axes[0].set(xlabel="Selected rollout",ylabel="Grouped validation Spearman",title="Validation-only search")
    from matplotlib.ticker import MaxNLocator
    axes[0].xaxis.set_major_locator(MaxNLocator(integer=True))
    axes[0].legend()
    names=["selected child",*controls]
    scores=[child["validation_reward"],*[v["validation_reward"] for v in controls.values()]]
    axes[1].barh(range(len(names)),scores,color=["#146f72","#6c8c45","#89739b","#bc7544"])
    axes[1].set_yticks(range(len(names)),["Selected child","Matched random projection","Pooled early time","Shuffled membership"])
    axes[1].set(xlabel="Grouped validation Spearman",title="Frozen-pipeline controls")
    fig.savefig(run/"first_stage_summary.png",dpi=160)
    plt.close(fig)
    diagnosis = {
        "root_minus_child_validation":root["validation_reward"]-child["validation_reward"],
        "sample_size":"46 clones; 36 development and 10 heldout; 138 treatment rows are not independent",
        "implementation_issue":"First-stage replacement-policy proposals did not inherit a useful parent" if not child["config"].get("parent_config") else "Parent composition is explicit; no mandatory replacement issue inferred",
        "model_space_issue":"Original replacement grammar did not preserve baseline_only; subsequent code adds parent-preserving composition without rewriting old results",
        "regularization_issue":"Fixed 128-gene and 80-epoch settings are narrower than a flexible small-n search grammar",
        "coverage":"7 estimator families exercised; scVI/CellRank/TraCSED extensions remain unevaluated",
        "statistical_caveat":"Repeated CV seeds change partitions; deterministic frozen Ridge/PLS refits give identical predictions and are not five independent replications",
        "causal_caveat":"No causal resistant-to-sensitive state conversion established by this relative-abundance study",
    }
    dump(run/"root_dominance_audit.json",diagnosis)
    for name,digest in protected.items():
        assert hashlib.file_digest((run/name).open("rb"),"sha256").hexdigest()==digest
    dump(run/"fixed_analysis_manifest.json",{"source_commit":source_commit,"analysis_script_sha256":hashlib.file_digest(Path(__file__).open("rb"),"sha256").hexdigest(),"protected_search_hashes":protected,
            "search_or_selection_changed":False,"controls_not_promoted_by_test":True})
    block = ["", "## Frozen-Pipeline Follow-Up", "", "![Validation and matched controls](first_stage_summary.png)", "",
             "No search was resumed and no candidate was promoted using test or Month-6 observations.",
             "See matched_artifact_controls.json, pseudocount_sensitivity.json, long_term_escape_report.json, combination_suppression.csv, and root_dominance_audit.json.",
             "Five frozen Ridge/PLS seed refits are deterministic, not independent biological replications.",
             "A separate exploratory denominator-coupling diagnostic shuffles endpoint fractions while retaining baseline abundance. Relative-selection predictability must not be equated with independent future-fate prediction.",
             "Eight-ablation applicability is explicitly recorded, including three controls that do not apply to the selected model/task."]
    report = run/"final_report.md"
    original = report.read_text().split("\n## Frozen-Pipeline Follow-Up",1)[0].rstrip()
    original = original.replace("Exact TraCSED, scVI, CellRank, full ablations, and long-term transport remain uncompleted; no proxy is counted as their implementation.",
                                "At search freeze, paper-reference extensions and follow-up analyses were not complete. The follow-up below records which analyses were subsequently added; no proxy is counted as a paper method.")
    report.write_text(original+"\n"+"\n".join(block)+"\n")
    print(json.dumps({"controls":{k:v["validation_reward"] for k,v in controls.items()},
                      "mono_positive_combo_negative":int(suppression.mono_positive_combo_negative.sum()),
                      "long_term":long_term}),flush=True)


if __name__=="__main__":
    main()
