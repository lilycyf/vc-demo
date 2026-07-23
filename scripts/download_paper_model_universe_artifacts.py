from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, snapshot_download

JOBS: list[dict[str, Any]] = [
    {"module_ids": ["aido_cell_3m"], "repo_id": "genbio-ai/AIDO.Cell-3M", "local_name": "AIDO.Cell-3M", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "LICENSE*", "*.safetensors", ".gitattributes"]},
    {"module_ids": ["aido_cell_10m"], "repo_id": "genbio-ai/AIDO.Cell-10M", "local_name": "AIDO.Cell-10M", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "LICENSE*", "*.safetensors", "pytorch_model.bin", ".gitattributes"]},
    {"module_ids": ["aido_cell_100m"], "repo_id": "genbio-ai/AIDO.Cell-100M", "local_name": "AIDO.Cell-100M", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "LICENSE*", "*.png", "*.safetensors", ".gitattributes"]},
    {"module_ids": ["aido_dna"], "repo_id": "genbio-ai/AIDO.DNA-300M", "local_name": "AIDO.DNA-300M", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "LICENSE*", "*.safetensors", ".gitattributes"]},
    {"module_ids": ["aido_dna2"], "repo_id": "genbio-ai/AIDO.DNA-7B", "local_name": "AIDO.DNA-7B", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "LICENSE*", "*.safetensors", "*.index.json", ".gitattributes"]},
    {"module_ids": ["aido_protein", "aido_protein_16b"], "repo_id": "genbio-ai/AIDO.Protein-16B", "local_name": "AIDO.Protein-16B", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "LICENSE*", "pytorch_model*.bin", "*.index.json", ".gitattributes"]},
    {"module_ids": ["esm2_35m"], "repo_id": "facebook/esm2_t12_35M_UR50D", "local_name": "ESM2_t12_35M_UR50D", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "*.txt", "*.safetensors", ".gitattributes"]},
    {"module_ids": ["esm2_150m"], "repo_id": "facebook/esm2_t30_150M_UR50D", "local_name": "ESM2_t30_150M_UR50D", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "*.txt", "*.safetensors", ".gitattributes"]},
    {"module_ids": ["esm2_650m"], "repo_id": "facebook/esm2_t33_650M_UR50D", "local_name": "ESM2_t33_650M_UR50D", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "*.txt", "*.safetensors", ".gitattributes"]},
    {"module_ids": ["esm2_3b"], "repo_id": "facebook/esm2_t36_3B_UR50D", "local_name": "ESM2_t36_3B_UR50D", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "*.txt", "pytorch_model*.bin", "*.index.json", ".gitattributes"]},
    {"module_ids": ["scfoundation"], "repo_id": "genbio-ai/scFoundation", "local_name": "scFoundation_genbio", "repo_type": "model", "allow_patterns": ["*.md", "*.ckpt", ".gitattributes"]},
    {"module_ids": ["scfoundation"], "repo_id": "perturblab/scfoundation-cell", "local_name": "scfoundation-cell", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "*.safetensors", "*.bin", "*.ckpt", ".gitattributes"]},
    {"module_ids": ["scgpt"], "repo_id": "tdc/scGPT", "local_name": "scGPT_tdc", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "*.safetensors", "*.bin", ".gitattributes"]},
    {"module_ids": ["geneformer"], "repo_id": "nvidia/geneformer_V2_104M", "local_name": "Geneformer-V2-104M", "repo_type": "model", "allow_patterns": ["*.json", "*.md", "LICENSE*", "*.py", "*.safetensors", ".gitattributes"]},
    {"module_ids": ["transcriptformer"], "repo_id": "czi-ai/transcriptformer", "local_name": "TranscriptFormer_repo", "repo_type": "space_or_git", "allow_patterns": []},
    {"module_ids": ["scprint"], "repo_id": "jkobject/scPRINT", "local_name": "scPRINT", "repo_type": "model", "allow_patterns": ["*.md", "*.json", "LICENSE*", "*.ckpt", "*.safetensors", ".gitattributes"]},
    {"module_ids": ["genept_all", "genept_bp", "genept_cc", "genept_mf", "genept_ncbi", "genept_n_plus_u"], "repo_id": "honicky/genept-composable-embeddings", "local_name": "GenePT_composable_embeddings", "repo_type": "model", "allow_patterns": ["*.md", "*.parquet", ".gitattributes"]},
    {"module_ids": ["alphagenome"], "repo_id": "google/alphagenome-fold-0", "local_name": "AlphaGenome_fold_0", "repo_type": "model", "allow_patterns": ["*README*", "*.ipynb", "_METADATA", "d/*", "ocdbt.process_0/d/*", ".gitattributes"]},
    {"module_ids": ["alphagenome"], "repo_id": "google/alphagenome-all-folds", "local_name": "AlphaGenome_all_folds", "repo_type": "model", "allow_patterns": ["*README*", "*.ipynb", "_METADATA", "d/*", "ocdbt.process_0/d/*", ".gitattributes"]},
    {"module_ids": ["string_gnn_model_dir"], "repo_id": "genbio-ai/STRING_GNN", "local_name": "STRING_GNN", "repo_type": "model", "allow_patterns": ["*"], "required_files": ["config.json", "pytorch_model.bin", "model.safetensors", "graph_data.pt", "node_names.json"]},
]

SYMLINKS = {
    "AIDO.Cell-3M": "/home/Models/AIDO.Cell-3M",
    "AIDO.Cell-10M": "/home/Models/AIDO.Cell-10M",
    "AIDO.Cell-100M": "/home/Models/AIDO.Cell-100M",
    "AIDO.DNA-300M": "/home/Models/AIDO.DNA-300M",
    "AIDO.DNA-7B": "/home/Models/AIDO.DNA-7B",
    "AIDO.Protein-16B": "/home/Models/AIDO.Protein-16B",
    "ESM2_t12_35M_UR50D": "/home/Models/ESM2_t12_35M_UR50D",
    "ESM2_t30_150M_UR50D": "/home/Models/ESM2_t30_150M_UR50D",
    "ESM2_t33_650M_UR50D": "/home/Models/ESM2_t33_650M_UR50D",
    "ESM2_t36_3B_UR50D": "/home/Models/ESM2_t36_3B_UR50D",
    "scFoundation_genbio": "/home/Models/scFoundation",
    "scfoundation-cell": "/home/Models/scfoundation-cell",
    "scGPT_tdc": "/home/Models/scGPT",
    "Geneformer-V2-104M": "/home/Models/Geneformer-V2-104M",
    "scPRINT": "/home/Models/scPRINT",
    "GenePT_composable_embeddings": "/home/Models/GenePT_composable_embeddings",
    "AlphaGenome_fold_0": "/home/Models/AlphaGenome_fold_0",
    "AlphaGenome_all_folds": "/home/Models/AlphaGenome_all_folds",
}


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file() and not child.is_symlink():
                total += child.stat().st_size
        except OSError:
            pass
    return total


def list_files(path: Path, limit: int = 40) -> list[str]:
    if not path.exists():
        return []
    out = []
    for child in sorted(path.rglob("*")):
        if child.is_file():
            out.append(str(child.relative_to(path)))
            if len(out) >= limit:
                break
    return out


def metadata_for_job(api: HfApi, job: dict[str, Any]) -> dict[str, Any]:
    try:
        info = api.model_info(job["repo_id"], files_metadata=True)
        files = []
        total = 0
        for sib in info.siblings:
            size = sib.size or 0
            total += size
            files.append({"path": sib.rfilename, "size": size})
        return {"ok": True, "private": info.private, "gated": str(getattr(info, "gated", None)), "file_count": len(files), "total_size_bytes": total, "largest_files": sorted(files, key=lambda f: f["size"], reverse=True)[:12]}
    except Exception as exc:
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def create_symlink(target_dir: Path, link: str) -> dict[str, Any]:
    link_path = Path(link)
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink() or link_path.exists():
        try:
            if link_path.resolve() == target_dir.resolve():
                return {"link": link, "target": str(target_dir), "status": "already_ok"}
        except OSError:
            pass
        if link_path.is_symlink():
            link_path.unlink()
        else:
            return {"link": link, "target": str(target_dir), "status": "exists_not_symlink_not_modified"}
    link_path.symlink_to(target_dir)
    return {"link": link, "target": str(target_dir), "status": "created"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", default="/workspace/models/search_space_artifacts")
    parser.add_argument("--run-dir", default="experiments/search_space_artifact_acquisition_sweep_v2")
    parser.add_argument("--skip-large", action="store_true")
    parser.add_argument("--large-threshold-gb", type=float, default=80.0)
    args = parser.parse_args()

    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")
    os.environ.setdefault("HF_HOME", "/workspace/.cache/huggingface")
    os.environ.setdefault("HF_HUB_CACHE", "/workspace/.cache/huggingface/hub")
    os.environ.setdefault("HF_XET_CACHE", "/workspace/.cache/huggingface/xet")
    os.environ.setdefault("TRANSFORMERS_CACHE", "/workspace/.cache/huggingface/transformers")
    base_dir = Path(args.base_dir)
    run_dir = Path(args.run_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    api = HfApi()
    results = []
    symlink_results = []

    for job in JOBS:
        started = time.time()
        local_dir = base_dir / job["local_name"]
        meta = metadata_for_job(api, job) if job["repo_type"] == "model" else {"ok": False, "error": "metadata lookup skipped for non-model git source"}
        result = {"job": job, "metadata": meta, "local_dir": str(local_dir), "started_at": datetime.now(timezone.utc).isoformat()}
        try:
            existing_size = dir_size(local_dir)
            if job["repo_type"] == "space_or_git":
                result["status"] = "not_downloaded_non_hf_model_source"
                result["blocker_reason"] = "This source is a code repository, not a directly snapshot_download-able HF model artifact in this script. Clone/build instructions are recorded instead."
            elif existing_size > 0 and meta.get("ok") and args.skip_large and meta.get("total_size_bytes", 0) > args.large_threshold_gb * 1e9:
                result["status"] = "already_present_large_repo_not_redownloaded"
                result["downloaded_size_bytes"] = existing_size
                result["file_sample"] = list_files(local_dir)
                result["blocker_reason"] = f"Local artifact exists; full repo metadata exceeds {args.large_threshold_gb} GB so no duplicate download was attempted."
            elif meta.get("ok") and args.skip_large and meta.get("total_size_bytes", 0) > args.large_threshold_gb * 1e9:
                result["status"] = "skipped_large_by_policy"
                result["blocker_reason"] = f"Estimated repo size exceeds {args.large_threshold_gb} GB for this RunPod volume; rerun on larger volume to acquire."
            else:
                kwargs = dict(repo_id=job["repo_id"], repo_type="model", local_dir=str(local_dir), local_dir_use_symlinks=False, resume_download=True, max_workers=8)
                if job.get("allow_patterns"):
                    kwargs["allow_patterns"] = job["allow_patterns"]
                path = snapshot_download(**kwargs)
                result["status"] = "downloaded_or_verified"
                result["snapshot_path"] = path
                result["downloaded_size_bytes"] = dir_size(local_dir)
                result["file_sample"] = list_files(local_dir)
                required = job.get("required_files") or []
                if required:
                    present = {p.name for p in local_dir.rglob("*") if p.is_file()}
                    missing_required = [name for name in required if name not in present]
                    result["missing_required_files"] = missing_required
                    if missing_required:
                        result["status"] = "blocked_unavailable_primary_artifact"
                        result["blocker_reason"] = "Public repo did not expose required model-dir files."
        except Exception as exc:
            result["status"] = "download_failed_or_blocked"
            result["error_type"] = type(exc).__name__
            result["error"] = str(exc)
        result["duration_seconds"] = round(time.time() - started, 3)
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        results.append(result)
        print(json.dumps({"repo_id": job["repo_id"], "local_name": job["local_name"], "status": result["status"], "size_gb": round(result.get("downloaded_size_bytes", 0)/1e9, 3), "duration_seconds": result["duration_seconds"]}, ensure_ascii=False), flush=True)

    successful_local_names = {
        item["job"]["local_name"]
        for item in results
        if item.get("status") in {"downloaded_or_verified", "already_present_large_repo_not_redownloaded"}
    }
    for local_name, link in SYMLINKS.items():
        target = base_dir / local_name
        if local_name in successful_local_names and target.exists():
            symlink_results.append(create_symlink(target, link))
        else:
            symlink_results.append({"link": link, "target": str(target), "status": "not_linked_not_verified"})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_dir": str(base_dir),
        "jobs": results,
        "symlinks": symlink_results,
        "policy": {
            "git_policy": "Do not commit model/data/checkpoint artifacts. Commit only this metadata and replay script.",
            "download_policy": "Download source-backed public artifacts when directly available. Mark incomplete/gated/non-equivalent sources as blocked with evidence.",
            "duplicate_weight_policy": "Prefer safetensors over duplicate pytorch/tensorflow weights; download PyTorch weights when safetensors are unavailable."
        }
    }
    (run_dir / "artifact_acquisition_matrix_v2.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    lines = ["# Search Space Artifact Acquisition Sweep v2", "", f"Generated: {payload['generated_at']}", "", f"Base dir: `{base_dir}`", "", "## Results", "", "| Module ids | Repo | Local path | Status | Size GB | Notes |", "|---|---|---|---|---:|---|"]
    for r in results:
        notes = r.get("blocker_reason") or r.get("error") or ""
        lines.append(f"| `{', '.join(r['job']['module_ids'])}` | `{r['job']['repo_id']}` | `{r['local_dir']}` | `{r['status']}` | {r.get('downloaded_size_bytes', 0)/1e9:.3f} | {notes} |")
    lines += ["", "## Symlinks", "", "| Link | Target | Status |", "|---|---|---|"]
    for s in symlink_results:
        lines.append(f"| `{s['link']}` | `{s['target']}` | `{s['status']}` |")
    lines += ["", "## Replay", "", "Run:", "", "```bash", "bash experiments/search_space_artifact_acquisition_sweep_v2/DOWNLOAD_REPLAY_V2.sh", "```", "", "Models are stored on the RunPod network volume under `/workspace/models/search_space_artifacts` and are intentionally not committed to GitHub."]
    (run_dir / "SEARCH_SPACE_ARTIFACT_ACQUISITION_MATRIX_V2.md").write_text("\n".join(lines) + "\n")

    replay = """#!/usr/bin/env bash
set -euo pipefail
cd /workspace/vc-demo
python scripts/download_paper_model_universe_artifacts.py \\
  --base-dir /workspace/models/search_space_artifacts \\
  --run-dir experiments/search_space_artifact_acquisition_sweep_v2
"""
    (run_dir / "DOWNLOAD_REPLAY_V2.sh").write_text(replay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
