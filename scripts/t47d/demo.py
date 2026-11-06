"""Reproducible first-stage entrypoint; full-study gaps stay explicitly tracked."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def invoke(*args):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path("src").resolve()) + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("OPENBLAS_NUM_THREADS", "2")
    subprocess.run([sys.executable, *args], check=True, env=env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="experiments/t47d_lineage_resistance_demo")
    parser.add_argument("--selected-rollouts", type=int, default=24)
    parser.add_argument("--max-runtime-hours", type=float, default=20)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if not 20 <= args.selected_rollouts <= 40:
        raise SystemExit("Registered first-stage range: 20-40 selected rollouts")
    if not 0 < args.max_runtime_hours <= 20:
        raise SystemExit("First-stage approved search ceiling is 20 hours; setup/shutdown reserve is separate")
    run = Path(args.run_dir)
    invoke("scripts/t47d/acquire.py")
    gmt = Path("data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt")
    if not gmt.exists():
        gmt.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl","--fail","--location","--retry","3","--output",str(gmt),
                        "https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/h.all.v2025.1.Hs.symbols.gmt"],check=True)
    prepared = Path("data/t47d_lineage/prepared")
    if not (prepared/"dataset_manifest.json").exists():
        invoke("scripts/t47d/prepare.py", "--run-dir", str(run))
    else:
        run.mkdir(parents=True, exist_ok=True)
        import shutil
        for filename in ("sample_manifest.csv","clone_assignment_audit.json","artifact_registry.json"):
            if not (run/filename).exists():
                if filename=="sample_manifest.csv":
                    import importlib.util
                    spec=importlib.util.spec_from_file_location("t47d_prepare", "scripts/t47d/prepare.py")
                    module=importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    module.read_samples(Path("data/t47d_lineage/raw/GSE260703_family.soft.gz")).to_csv(run/filename,index=False)
                elif filename=="clone_assignment_audit.json":
                    shutil.copyfile(prepared/"dataset_manifest.json",run/filename)
                else:
                    shutil.copyfile("data/t47d_lineage/raw/download_manifest.json",run/filename)
    invoke("-m","pytest","tests/t47d","-q")
    if not (run/"frozen_selection.json").exists():
        command=["scripts/t47d/run.py","--run-dir",str(run),"--selected-rollouts",str(args.selected_rollouts),
                 "--max-runtime-hours",str(args.max_runtime_hours),"--parent-policy","preserve"]
        if args.resume:
            command.append("--resume")
        invoke(*command)
    invoke("scripts/t47d/analyze.py","--run-dir",str(run))
    invoke("scripts/t47d/write_status.py","--run-dir",str(run))
    print(json.dumps({"first_stage_report":str(run/"final_report.md"),
                      "full_paper_reference_complete":False,
                      "gpu_stop":"Stop in console before ending supervision; this program does not have account API authorization"}))


if __name__=="__main__":
    main()
