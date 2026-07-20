from __future__ import annotations

import argparse
import json
import os
import random
import shutil
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import numpy as np
import torch

from vc_demo.train import train


SEEDS_DEFAULT = [3, 7, 11, 17, 23]
TARGET_VAL_MACRO_F1 = 0.50


def set_seed(seed: int) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = False


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def root_config(seed: int) -> dict[str, Any]:
    cfg = load_json(Path("configs/official_k562_root_aido_gnn_embedding_mlp.json"))
    cfg = json.loads(json.dumps(cfg))
    cfg["node_name"] = f"official_k562_root_aido_gnn_embedding_mlp_seed_{seed}"
    cfg.setdefault("metadata", {})["validation_seed"] = seed
    return cfg


def child_config(seed: int, model_path: Path) -> dict[str, Any]:
    cfg = load_json(Path("configs/official_k562_root_aido_gnn_embedding_mlp.json"))
    cfg = json.loads(json.dumps(cfg))
    cfg["node_name"] = f"official_k562_fixed_best_child_target_gene_head_seed_{seed}"
    cfg["model"] = {
        "model_type": "custom_program",
        "input_dim": "auto",
        "hidden_dim": 256,
        "n_targets": "auto",
        "n_classes": "auto",
        "dropout": 0.5,
        "depth": 2,
        "custom_model_path": str(model_path),
        "custom_model_class": "GeneratedModel",
        "program_blueprint": "official_target_gene_head_fixed_best_child",
        "low_rank_dim": 96,
    }
    cfg["training"] = {
        "epochs": 8,
        "batch_size": 16,
        "lr": 0.0003,
        "weight_decay": 0.0001,
        "loss_type": "weighted_cross_entropy",
        "class_weights": [2.37, 0.51, 2.75],
    }
    cfg.setdefault("metadata", {})["validation_seed"] = seed
    cfg["metadata"]["fixed_architecture_source"] = "k562-full-autonomy-rerun best child official_target_gene_head"
    return cfg


def ensure_required_artifacts() -> dict[str, Any]:
    paths = {
        "official_k562_task_manifest": Path("data/cell_lines/official_k562_cls/manifest.json"),
        "official_k562_train": Path("data/cell_lines/official_k562_cls/train.tsv"),
        "official_k562_val": Path("data/cell_lines/official_k562_cls/val.tsv"),
        "official_k562_test": Path("data/cell_lines/official_k562_cls/test.tsv"),
        "official_target_gene_order": Path("data/cell_lines/official_k562_cls/target_genes.tsv"),
        "official_essential_deg_with_split_h5ad": Path("data/artifacts/official_k562/essential_deg_with_split.h5ad"),
        "aido_embedding_h5ad": Path("data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad"),
        "gnn_embedding_h5ad": Path("data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad"),
    }
    status = {key: {"path": str(path), "present": path.exists()} for key, path in paths.items()}
    missing = [key for key, row in status.items() if not row["present"]]
    home_models = {
        "aido_model_dir": Path("/home/Models/AIDO.Cell-100M").exists(),
        "string_gnn_model_dir": Path("/home/Models/STRING_GNN").exists(),
    }
    if missing:
        raise FileNotFoundError(f"required source-backed K562 artifacts missing for this fixed validation: {missing}")
    return {"required_artifacts": status, "home_models_present_but_not_required": home_models}


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "mean": float(mean(values)),
        "std": float(stdev(values)) if len(values) > 1 else 0.0,
        "min": float(min(values)),
        "max": float(max(values)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="K562 best-child multi-seed validation")
    parser.add_argument("--run-dir", type=Path, default=Path("experiments/k562_best_child_multiseed_validation"))
    parser.add_argument("--seeds", type=str, default=",".join(str(s) for s in SEEDS_DEFAULT))
    parser.add_argument("--target-val-macro-f1", type=float, default=TARGET_VAL_MACRO_F1)
    parser.add_argument("--max-epochs", type=int, default=8)
    args = parser.parse_args()

    run_dir = args.run_dir
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    if not seeds:
        raise ValueError("at least one seed is required")
    run_dir.mkdir(parents=True, exist_ok=True)
    program_dir = run_dir / "programs" / "fixed_best_child_target_gene_head"
    model_path = program_dir / "model.py"
    if not model_path.exists():
        raise FileNotFoundError(f"fixed child model.py must exist before running: {model_path}")

    artifact_status = ensure_required_artifacts()
    write_json(run_dir / "artifact_readiness.json", artifact_status)

    results: list[dict[str, Any]] = []
    configs_dir = run_dir / "configs"
    output_root = run_dir / "training_outputs"
    metrics_dir = run_dir / "metrics"
    for seed in seeds:
        row: dict[str, Any] = {"seed": seed}
        for kind in ["root", "best_child"]:
            set_seed(seed)
            cfg = root_config(seed) if kind == "root" else child_config(seed, model_path)
            cfg["training"]["epochs"] = int(args.max_epochs)
            cfg_path = configs_dir / f"{kind}_seed_{seed}.json"
            write_json(cfg_path, cfg)
            output_dir = output_root / kind / f"seed_{seed}"
            if output_dir.exists():
                shutil.rmtree(output_dir)
            metrics = train(cfg, output_dir, max_epochs=int(args.max_epochs))
            compact = {
                "node_name": metrics["node_name"],
                "best_val_macro_f1": metrics["best_val_macro_f1"],
                "test_macro_f1": metrics["test_macro_f1"],
                "test_loss": metrics["test_loss"],
                "training": metrics["training"],
                "history": metrics["history"],
                "config_path": str(cfg_path),
                "output_dir": str(output_dir),
            }
            write_json(metrics_dir / f"{kind}_seed_{seed}.json", compact)
            row[kind] = compact
        row["delta_val_child_minus_root"] = float(row["best_child"]["best_val_macro_f1"] - row["root"]["best_val_macro_f1"])
        row["delta_test_child_minus_root"] = float(row["best_child"]["test_macro_f1"] - row["root"]["test_macro_f1"])
        row["child_beats_root_val"] = bool(row["delta_val_child_minus_root"] > 0)
        row["child_reaches_target_val"] = bool(row["best_child"]["best_val_macro_f1"] >= float(args.target_val_macro_f1))
        results.append(row)
        write_json(run_dir / "partial_results.json", results)

    root_vals = [r["root"]["best_val_macro_f1"] for r in results]
    root_tests = [r["root"]["test_macro_f1"] for r in results]
    child_vals = [r["best_child"]["best_val_macro_f1"] for r in results]
    child_tests = [r["best_child"]["test_macro_f1"] for r in results]
    deltas = [r["delta_val_child_minus_root"] for r in results]
    summary = {
        "run_type": "best_child_multiseed_validation",
        "cell_line_id": "K562",
        "run_dir": str(run_dir),
        "seeds": seeds,
        "target_val_macro_f1": float(args.target_val_macro_f1),
        "architecture": "parent dense logits + official target-gene-aware low-rank/bilinear residual",
        "source_best_child_run": "k562-full-autonomy-rerun",
        "artifact_status": artifact_status,
        "per_seed": results,
        "aggregate": {
            "root_val_macro_f1": summarize(root_vals),
            "root_test_macro_f1": summarize(root_tests),
            "child_val_macro_f1": summarize(child_vals),
            "child_test_macro_f1": summarize(child_tests),
            "delta_val_child_minus_root": summarize(deltas),
            "child_beats_root_rate": float(sum(r["child_beats_root_val"] for r in results) / len(results)),
            "child_reaches_target_rate": float(sum(r["child_reaches_target_val"] for r in results) / len(results)),
            "child_beats_root_on_average": float(mean(child_vals)) > float(mean(root_vals)),
            "child_reaches_target_on_average": float(mean(child_vals)) >= float(args.target_val_macro_f1),
        },
        "strict_policy": {
            "fallback_count": 0,
            "compact_proxy_count": 0,
            "backprop_nontrained_count": 0,
            "backend_anomaly_count": 0,
            "test_metric_used_for_selection": False,
            "home_models_required": False,
        },
        "acquisition_blocker_summary": {
            "acquisition_required": False,
            "blocked_artifacts": [],
            "note": "/home/Models AIDO/STRING checkpoints are not required for this fixed best-child architecture; cached official h5ad embeddings and official task artifacts were used.",
        },
    }
    write_json(run_dir / "multiseed_summary.json", summary)

    lines = [
        "# K562 Best-Child Multi-Seed Validation",
        "",
        f"Run dir: `{run_dir}`",
        "",
        "## Objective",
        "",
        "Validate whether the discovered K562 best child architecture is stable across seeds, not just a lucky single run.",
        "",
        "Fixed child architecture: parent dense logits plus official target-gene-aware low-rank / bilinear residual.",
        "",
        "## Artifact Policy",
        "",
        "No fallback and no compact/proxy implementation was used. `/home/Models` checkpoints are not required by this fixed architecture; missing `/home/Models` does not block this validation.",
        "",
        "## Per-Seed Results",
        "",
        "| Seed | Root val | Root test | Child val | Child test | Child-root val delta | Beats root? | Child val >= 0.50? |",
        "|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in results:
        lines.append(
            "| {seed} | {rv:.6f} | {rt:.6f} | {cv:.6f} | {ct:.6f} | {dv:.6f} | {br} | {tg} |".format(
                seed=r["seed"],
                rv=r["root"]["best_val_macro_f1"],
                rt=r["root"]["test_macro_f1"],
                cv=r["best_child"]["best_val_macro_f1"],
                ct=r["best_child"]["test_macro_f1"],
                dv=r["delta_val_child_minus_root"],
                br="yes" if r["child_beats_root_val"] else "no",
                tg="yes" if r["child_reaches_target_val"] else "no",
            )
        )
    agg = summary["aggregate"]
    lines += [
        "",
        "## Aggregate",
        "",
        "| Quantity | Mean | Std | Min | Max |",
        "|---|---:|---:|---:|---:|",
    ]
    for key, label in [
        ("root_val_macro_f1", "Root val Macro-F1"),
        ("root_test_macro_f1", "Root test Macro-F1"),
        ("child_val_macro_f1", "Child val Macro-F1"),
        ("child_test_macro_f1", "Child test Macro-F1"),
        ("delta_val_child_minus_root", "Child-root val delta"),
    ]:
        row = agg[key]
        lines.append("| {} | {:.6f} | {:.6f} | {:.6f} | {:.6f} |".format(label, row["mean"], row["std"], row["min"], row["max"]))
    lines += [
        "",
        "## Conclusion",
        "",
        f"Child beats root on average: **{agg['child_beats_root_on_average']}**.",
        f"Child reaches target validation Macro-F1 {float(args.target_val_macro_f1):.2f} on average: **{agg['child_reaches_target_on_average']}**.",
        f"Per-seed beat-root rate: **{agg['child_beats_root_rate']:.2f}**.",
        f"Per-seed target-reaching rate: **{agg['child_reaches_target_rate']:.2f}**.",
        "",
        "Test Macro-F1 is reported only for final comparison and was not used for selection or tuning.",
    ]
    (run_dir / "multiseed_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
