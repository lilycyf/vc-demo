"""T47D task plugin using the existing harness UCT/backpropagation core."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from vc_demo.harness.mcts import backpropagate, select_parent
from vc_demo.t47d_lineage.data import CV_SEEDS, TREATMENTS, dump, load_bundle
from vc_demo.t47d_lineage.models import Candidate


def correlation(y, pred):
    if len(y) < 3 or np.ptp(y) == 0 or np.ptp(pred) == 0:
        return None
    return float(spearmanr(y, pred).statistic)


def metrics(y, pred):
    if not np.isfinite(pred).all():
        raise ValueError("Non-finite predictions")
    return {"spearman": correlation(y, pred), "mae": float(np.mean(np.abs(y - pred)))}


def cross_validate(bundle, config):
    meta = bundle["meta"]
    dev = np.flatnonzero(meta.split.eq("development"))
    seed_predictions, fold_records = {}, []
    for split in bundle["splits"]["folds"]:
        train = np.flatnonzero(meta.clone_id.isin(split["train_clones"]))
        valid = np.flatnonzero(meta.clone_id.isin(split["validation_clones"]))
        assert not set(meta.iloc[train].clone_id) & set(meta.iloc[valid].clone_id)
        assert not meta.iloc[train].split.eq("test").any()
        candidate = Candidate(config).fit(bundle, train, split["seed"])
        pred = candidate.predict(bundle, valid)
        result = metrics(meta.iloc[valid].label.to_numpy(), pred)
        fold_records.append({"seed": split["seed"], "fold": split["fold"], **result})
        seed_predictions.setdefault(split["seed"], {}).update(zip(valid.tolist(), pred.tolist()))
    scores, maes, records = [], [], []
    for seed in CV_SEEDS:
        if set(seed_predictions[seed]) != set(dev):
            raise ValueError("OOF prediction coverage is incomplete")
        pred = np.array([seed_predictions[seed][int(i)] for i in dev])
        result = metrics(meta.iloc[dev].label.to_numpy(), pred)
        if result["spearman"] is None:
            raise ValueError("Undefined seed-level OOF Spearman; cannot backpropagate")
        scores.append(result["spearman"])
        maes.append(result["mae"])
        records.append({"seed": seed, **result})
    return {"validation_reward": float(np.mean(scores)), "reward_metric": "validation_spearman",
            "validation_std": float(np.std(scores, ddof=1)), "validation_mae": float(np.mean(maes)),
            "seed_metrics": records, "fold_metrics": fold_records, "formal_fold_fits": len(fold_records)}


def roots():
    return [
        {"model": "frequency", "representation": "expression", "baseline_only": True, "alpha": 10.},
        {"model": "ridge", "representation": "pathway", "baseline_only": True, "alpha": 100.},
        {"model": "elastic", "representation": "expression", "baseline_only": True, "alpha": 10.},
        {"model": "pls", "representation": "pathway", "baseline_only": True, "components": 3},
        {"model": "xgboost", "representation": "expression", "baseline_only": False, "alpha": 10., "depth": 2},
    ]


def search_space():
    implemented = []
    for model in ["ridge", "elastic", "pls", "xgboost", "gru", "transformer", "gated_residual"]:
        for representation in ["expression", "pathway", "both", "pca"]:
            for alpha in [1., 10., 100.]:
                losses = ["huber", "mse"] if model in {"gru", "transformer", "gated_residual"} else ["mse"]
                for loss in losses:
                    cfg = {"model": model, "representation": representation, "alpha": alpha,
                           "loss": loss, "genes": 128, "epochs": 80}
                    implemented.append(cfg)
    planned = [
        {"id": "scvi_state_encoder", "required_artifact": "train-fold scVI latent", "source": "https://github.com/scverse/scvi-tools"},
        {"id": "cellrank_time_kernel", "required_artifact": "train-clone temporal transition kernel", "source": "https://github.com/theislab/cellrank"},
        {"id": "tracsed_reference_backend", "required_artifact": "rebuilt Slingshot/selection JSON and exact author model", "source": "https://github.com/Genentech/TraCSED"},
        {"id": "distribution_distance_encoder", "required_artifact": "train-reference early-cell distributions", "source": "https://github.com/scverse/pertpy"},
        {"id": "survival_or_hazard_head", "required_artifact": "explicit censoring and event definition", "source": "https://github.com/sebp/scikit-survival"},
        {"id": "cross_treatment_attention", "required_artifact": "aligned early clone-treatment tensor", "source": "https://pytorch.org/"},
    ]
    return {"implemented_candidates": implemented, "implemented_candidate_count": len(implemented),
            "planned_families": planned, "planned_status": "declared_not_yet_executable_or_evaluated",
            "scope": "No foundation checkpoint proxy. Planned families are not counted as executable coverage."}


def log(run, event, **fields):
    with (run / "mcts_trace.jsonl").open("a") as stream:
        stream.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "event": event, **fields}) + "\n")


def node_id(parent, config):
    key = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:10]
    return f"{parent[:28]}__{config['model']}__{key}"


def materialize(run, node):
    dest = run / "programs" / node["id"]
    dest.mkdir(parents=True, exist_ok=True)
    dump(dest / "pipeline.json", {"config": node["config"], "parent": node.get("parent"),
                                  "backend": "native_regression", "mutation": "explicit estimator/representation research variant",
                                  "artifact_usage": "real Hallmark memberships" if node["config"]["representation"] in {"pathway", "both"} else "GEO expression",
                                  "fallback": False, "proxy": False})
    dump(dest / "artifact_contract.json", {"required": ["GSE260703", "verified clone mapping", "frozen group splits"],
                                           "missing": [], "checkpoint_substitution": "forbidden"})
    (dest / "model.py").write_text(
        "from vc_demo.t47d_lineage.models import Candidate\n"
        "\ndef build_model(config):\n    return Candidate(config)\n")
    subprocess.run([sys.executable, "-m", "py_compile", str(dest / "model.py")], check=True)


def evaluate(run, tree, node, bundle):
    node["status"] = "selected"
    materialize(run, node)
    start = time.monotonic()
    train_clones = bundle["splits"]["folds"][0]["train_clones"]
    sample = np.flatnonzero(bundle["meta"].clone_id.isin(train_clones))[:9]
    smoke_model = Candidate(node["config"]).fit(bundle, sample[:6], 3)
    pred = smoke_model.predict(bundle, sample[6:8])
    if pred.shape != (2,) or not np.isfinite(pred).all():
        raise ValueError("Native fit/predict smoke failed")
    dump(run / "programs" / node["id"] / "smoke.json", {"passed": True, "shape": [2], "scientific_result": False})
    result = cross_validate(bundle, node["config"])
    node.update(result, status="trained", duration_seconds=time.monotonic() - start)
    if node["status"] != "trained":
        raise ValueError("Only trained rollout rewards may backpropagate")
    backpropagate(tree, node["id"], result["validation_reward"])
    log(run, "backpropagation", node=node["id"], reward=result["validation_reward"],
        path=tree["mcts"]["last_backpropagation"]["path"], status="trained")
    print(json.dumps({"node": node["id"], "validation_spearman": result["validation_reward"],
                      "duration_seconds": node["duration_seconds"]}), flush=True)


def propose(run, tree, space, count=4):
    parent, components = select_parent(tree, math.sqrt(2), 8, policy="uct")
    log(run, "parent_selection", parent=parent, components=components)
    used = {json.dumps(n["config"], sort_keys=True) for n in tree["nodes"].values() if n.get("parent") == parent}
    choices = [c for c in space["implemented_candidates"] if json.dumps(c, sort_keys=True) not in used]
    key = int(hashlib.sha256((parent + str(len(used))).encode()).hexdigest()[:8], 16)
    np.random.default_rng(key).shuffle(choices)
    for cfg in choices[:count]:
        name = node_id(parent, cfg)
        if name in tree["nodes"]:
            continue
        tree["nodes"][name] = {"id": name, "parent": parent, "config": cfg,
                               "status": "candidate_queued", "children": [], "visits": 0, "value": 0.,
                               "depth": tree["nodes"][parent].get("depth", 0) + 1}
        tree["nodes"][parent]["children"].append(name)
        log(run, "proposal_generated", node=name, parent=parent, config=cfg)


def rank_queue(tree):
    trained = [n for n in tree["nodes"].values() if n["status"] == "trained"]
    model_counts = {m: sum(n["config"]["model"] == m for n in trained) for m in {n["config"]["model"] for n in tree["nodes"].values()}}
    ranked = []
    for n in tree["nodes"].values():
        if n["status"] != "candidate_queued":
            continue
        parent = tree["nodes"][n["parent"]]
        novelty = .12 / (1 + model_counts.get(n["config"]["model"], 0))
        score = parent["validation_reward"] - .25 * parent.get("validation_std", 0) + novelty
        ranked.append((score, n["id"]))
    return sorted(ranked, reverse=True)


def bootstrap(meta, pred, draws=2000):
    groups = sorted(meta.clone_id.unique())
    rng = np.random.default_rng(20261106)
    values = []
    for _ in range(draws):
        chosen = rng.choice(groups, len(groups), replace=True)
        index = np.concatenate([np.flatnonzero(meta.clone_id.eq(c)) for c in chosen])
        value = correlation(meta.iloc[index].label.to_numpy(), pred[index])
        if value is not None:
            values.append(value)
    return {"unit": "clone block, all treatments together", "valid_draws": len(values),
            "spearman_ci95": np.percentile(values, [2.5, 97.5]).tolist() if values else None}


def finalize(run, tree, bundle, stop_reason):
    trained = [n for n in tree["nodes"].values() if n["status"] == "trained"]
    root = max((n for n in trained if not n.get("parent")), key=lambda n: n["validation_reward"])
    children = [n for n in trained if n.get("parent")]
    child = max(children, key=lambda n: n["validation_reward"]) if children else None
    selection = {"selected_at": datetime.now(timezone.utc).isoformat(), "root": root["id"],
                 "child": child["id"] if child else None, "selection_basis": "validation only; no test metric read",
                 "configurations": {n["id"]: n["config"] for n in [root, child] if n}}
    dump(run / "frozen_selection.json", selection)
    meta = bundle["meta"]
    dev, test = np.flatnonzero(meta.split.eq("development")), np.flatnonzero(meta.split.eq("test"))
    test_meta = meta.iloc[test].reset_index(drop=True)
    evaluations = {}
    for node in [root, child]:
        if not node:
            continue
        predictions, seed_metrics = [], []
        for seed in CV_SEEDS:
            model = Candidate(node["config"]).fit(bundle, dev, seed)
            p = model.predict(bundle, test)
            predictions.append(p)
            seed_metrics.append({"seed": seed, **metrics(test_meta.label.to_numpy(), p)})
            if seed == CV_SEEDS[0]:
                if hasattr(model, "network"):
                    model.network = model.network.cpu()
                    import torch
                    model.device = torch.device("cpu")
                dest = run / "nodes" / node["id"]
                dest.mkdir(parents=True, exist_ok=True)
                joblib.dump(model, dest / "frozen_model.joblib")
        pred = np.mean(predictions, axis=0)
        output = test_meta.assign(prediction=pred)
        output.to_csv(run / (node["id"] + "_locked_test_predictions.csv"), index=False)
        evaluations[node["id"]] = {"seed_metrics": seed_metrics, "ensemble": metrics(test_meta.label.to_numpy(), pred),
                                    "bootstrap": bootstrap(test_meta, pred),
                                    "within_treatment": {t: metrics(test_meta.loc[test_meta.treatment.eq(t), "label"].to_numpy(), pred[test_meta.treatment.eq(t)]) for t in TREATMENTS}}
    ablations = {}
    if child:
        for name, changes in {
            "baseline_only_no_temporal": {"baseline_only": True},
            "no_pathway": {"representation": "expression"},
            "no_treatment_indicator": {"no_treatment": True},
            "no_abundance_inputs": {"no_clone_abundance": True},
        }.items():
            cfg = {**child["config"], **changes}
            ablations[name] = cross_validate(bundle, cfg)
    dump(run / "ablation_metrics.json", ablations)
    long_term = {"status": "not_yet_evaluated", "reason": "Requires separate frozen day26-to-Month6 transport analysis; no early forecasting claim is inferred from observation alone"}
    trace = [json.loads(line) for line in (run / "mcts_trace.jsonl").read_text().splitlines()]
    backprops = [e for e in trace if e["event"] == "backpropagation"]
    checks = {
        "backprop_nontrained": sum(e.get("status") != "trained" or tree["nodes"][e["node"]]["status"] != "trained" for e in backprops),
        "pruned_training": sum(tree["nodes"][e["node"]]["status"] == "pruned_not_selected" for e in backprops),
        "test_overlap": sum(bool(set(f["train_clones"]) & set(bundle["splits"]["test_clones"])) for f in bundle["splits"]["folds"]),
        "fallback": sum(bool(json.loads(p.read_text()).get("fallback")) for p in (run / "programs").glob("*/pipeline.json")),
        "proxy": sum(bool(json.loads(p.read_text()).get("proxy")) for p in (run / "programs").glob("*/pipeline.json")),
    }
    if any(checks.values()):
        raise ValueError(f"Run audit failed: {checks}")
    dump(run / "guardrail_audit.json", {"checks": checks, "passed": True, "evidence": "tree, MCTS trace, frozen splits, program contracts"})
    summary = {"stop_reason": stop_reason, "trained_roots": sum(not n.get("parent") for n in trained),
               "trained_selected_rollouts": len(children), "generated_proposals": sum(bool(n.get("parent")) for n in tree["nodes"].values()),
               "pruned": sum(n["status"] == "pruned_not_selected" for n in tree["nodes"].values()),
               "failed": sum(n["status"] == "failed" for n in tree["nodes"].values()),
               "best_root": {"id": root["id"], "validation": root["validation_reward"], "test": evaluations[root["id"]]},
               "best_child": {"id": child["id"], "validation": child["validation_reward"], "test": evaluations[child["id"]]} if child else None,
               "child_beats_root": bool(child and child["validation_reward"] > root["validation_reward"]),
               "guardrails": checks,
               "incomplete_components": ["exact TraCSED reference rebuild", "scVI/CellRank/pertpy/hazard planned families", "long-term transport", "full eight-ablation panel"],
               "claim": "completed early-endpoint executable-subset search, not complete paper-method replication"}
    dump(run / "search_results.json", summary)
    dump(run / "long_term_escape_report.json", long_term)
    lines = ["# T47D Lineage Harness: First-Stage Report", "", f"Stop reason: {stop_reason}",
             f"Clones: {bundle['contract']['clone_count']}; held-out clones: {len(bundle['splits']['test_clones'])}.",
             f"Formal roots: {summary['trained_roots']}; selected rollouts: {len(children)}.",
             "Reward: five-seed mean grouped OOF Spearman; test was opened after frozen selection.", "",
             "| Candidate | Validation Spearman | Locked-test ensemble Spearman |", "|---|---:|---:|"]
    for n in [root, child]:
        if n:
            lines.append(f"| {n['id']} | {n['validation_reward']:.4f} | {evaluations[n['id']]['ensemble']['spearman']:.4f} |")
    lines += ["", "## Limits", "", "- Relative clone selection is not absolute growth, clinical resistance, or causal state reversal.",
              "- Endpoint non-detection is not proof of extinction. Cohort uses baseline-only eligibility.",
              "- Validation-based search is subject to selection optimism; test has only ten independent clone groups.",
              "- Hallmark scoring is mean log expression, not an exact replication of the paper's R workflow.",
              "- Exact TraCSED, scVI, CellRank, full ablations, and long-term transport remain uncompleted; no proxy is counted as their implementation.",
              "- Framework completion and scientific superiority are separate outcomes.", "", "## Search Tree", "", "```mermaid", "flowchart TD"]
    for i, n in enumerate(tree["nodes"].values()):
        n["diagram_key"] = f"n{i}"
    for n in tree["nodes"].values():
        if n["status"] == "trained":
            lines.append(f"  {n['diagram_key']}[\"{n['config']['model']} / {n['config']['representation']} / rho {n['validation_reward']:.3f}\"]")
            if n.get("parent"):
                lines.append(f"  {tree['nodes'][n['parent']]['diagram_key']} --> {n['diagram_key']}")
    lines += ["```", "", "## Sources", "", "- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE260703",
              "- https://github.com/Genentech/TraCSED", "- https://pmc.ncbi.nlm.nih.gov/articles/PMC11723929/",
              "- https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/h.all.v2025.1.Hs.symbols.gmt"]
    (run / "final_report.md").write_text("\n".join(lines) + "\n")
    dump(run / "tree.json", tree)
    print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="experiments/t47d_lineage_resistance_demo")
    parser.add_argument("--prepared", default="data/t47d_lineage/prepared")
    parser.add_argument("--pathways", default="data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt")
    parser.add_argument("--selected-rollouts", type=int, default=24)
    parser.add_argument("--max-runtime-hours", type=float, default=20)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    run = Path(args.run_dir)
    run.mkdir(parents=True, exist_ok=True)
    if (run / "frozen_selection.json").exists():
        raise SystemExit("This run has opened its locked test; start a new registered run rather than resuming search")
    if (run / "tree.json").exists() and not args.resume:
        raise SystemExit("Existing search state: --resume is required")
    space = search_space()
    dump(run / "search_space_manifest.json", space)
    bundle = load_bundle(args.prepared, args.pathways, run)
    code_paths = [Path(__file__), *Path("src/vc_demo/t47d_lineage").glob("*.py")]
    source_hashes = {str(p): hashlib.file_digest(p.open("rb"), "sha256").hexdigest() for p in code_paths}
    provenance = {"base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  "source_hashes": source_hashes, "selected_rollout_budget": args.selected_rollouts,
                  "wall_budget_hours": args.max_runtime_hours, "started_at_unix": time.time(),
                  "python_version": sys.version, "gpu": subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], text=True).strip()}
    manifest_path = run / "run_manifest.json"
    if args.resume:
        previous = json.loads(manifest_path.read_text())
        if previous["source_hashes"] != source_hashes:
            raise ValueError("Implementation changed after search began; require an explicit new run, not silent resume")
        provenance = previous
    else:
        dump(manifest_path, provenance)
        freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
        (run / "requirements.lock.txt").write_text(freeze)
    start = provenance["started_at_unix"]
    tree = json.loads((run / "tree.json").read_text()) if args.resume else {"nodes": {}, "root_nodes": [], "events": []}
    for i, config in enumerate(roots()):
        name = f"root_{i+1}_{config['model']}"
        if name in tree["nodes"]:
            continue
        node = {"id": name, "config": config, "status": "created", "children": [], "visits": 0, "value": 0., "depth": 0}
        tree["nodes"][name] = node
        tree["root_nodes"].append(name)
        evaluate(run, tree, node, bundle)
        dump(run / "tree.json", tree)
    rootmetrics = {k: tree["nodes"][k] for k in tree["root_nodes"]}
    dump(run / "root_metrics.json", rootmetrics)
    best, stale = max(n["validation_reward"] for n in tree["nodes"].values() if n["status"] == "trained"), 0
    stop = "selected rollout budget exhausted"
    while sum(n["status"] == "trained" and bool(n.get("parent")) for n in tree["nodes"].values()) < args.selected_rollouts:
        if time.time() - start > args.max_runtime_hours * 3600:
            stop = "approved compute time reached; partial search"
            break
        propose(run, tree, space)
        queue = rank_queue(tree)
        if not queue:
            stop = "no executable queued candidate remains"
            break
        for score, name in queue[48:]:
            tree["nodes"][name]["status"] = "pruned_not_selected"
            log(run, "global_prune", node=name, reason="global queue capacity 48", priority=score)
        score, name = queue[0]
        node = tree["nodes"][name]
        log(run, "global_queue_selected", node=name, priority=score, candidate_count=len(queue),
            reason="parent validation, uncertainty penalty, model-family coverage; no artifact-present bonus")
        try:
            evaluate(run, tree, node, bundle)
        except Exception as error:
            node.update(status="failed", error=str(error), traceback=traceback.format_exc())
            log(run, "training_failed", node=name, error=str(error), backpropagated=False)
            dump(run / "tree.json", tree)
            raise
        reward = node["validation_reward"]
        stale = 0 if reward > best else stale + 1
        best = max(best, reward)
        dump(run / "tree.json", tree)
        # Replenishment occurs after every completed rollout, before next global selection.
        log(run, "rollout_complete", node=name, next_action="generate_new_pool_then_select_global_queue")
        trained_children = sum(n["status"] == "trained" and bool(n.get("parent")) for n in tree["nodes"].values())
        if trained_children >= 20 and stale >= 12:
            stop = "no improvement for 12 selected rollouts after minimum 20"
            break
    for node in tree["nodes"].values():
        if node["status"] == "candidate_queued":
            node.update(status="pruned_not_selected", prune_reason="registered search budget or stop criterion reached")
    dump(run / "tree.json", tree)
    finalize(run, tree, bundle, stop)


if __name__ == "__main__":
    main()
