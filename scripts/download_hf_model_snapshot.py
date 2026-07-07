from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


HF_MODEL_API = "https://huggingface.co/api/models"
HF_RESOLVE = "https://huggingface.co"


def model_info(repo_id: str) -> dict[str, Any]:
    with urllib.request.urlopen(f"{HF_MODEL_API}/{repo_id}", timeout=60) as response:
        return json.load(response)


def head_size(repo_id: str, filename: str) -> int | None:
    url = f"{HF_RESOLVE}/{repo_id}/resolve/main/{urllib.parse.quote(filename)}"
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        length = response.headers.get("content-length")
        return int(length) if length else None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(repo_id: str, filename: str, output_dir: Path) -> dict[str, Any]:
    output = output_dir / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    url = f"{HF_RESOLVE}/{repo_id}/resolve/main/{urllib.parse.quote(filename)}"
    if not output.exists():
        urllib.request.urlretrieve(url, output)
    return {
        "filename": filename,
        "path": str(output),
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "source": url,
    }


def select_files(info: dict[str, Any], include: list[str], skip: set[str]) -> list[str]:
    available = [item.get("rfilename", "") for item in info.get("siblings", [])]
    if include:
        missing = [name for name in include if name not in available]
        if missing:
            raise FileNotFoundError(f"requested files not in model repo: {missing}; available={available}")
        return [name for name in include if name not in skip]
    return [name for name in available if name and name not in skip]


def validate_model_dir(path: Path, repo_id: str) -> dict[str, Any]:
    files = sorted(str(p.relative_to(path)) for p in path.rglob("*") if p.is_file())
    has_config = "config.json" in files
    has_weight = any(name in files for name in ["model.safetensors", "pytorch_model.bin"])
    tokenizer_files = {
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "sentencepiece.bpe.model",
        "spiece.model",
    }
    present_tokenizer = sorted(tokenizer_files.intersection(files))
    warnings: list[str] = []
    if not has_config:
        warnings.append("missing config.json")
    if not has_weight:
        warnings.append("missing model weight file")
    if repo_id == "genbio-ai/AIDO.Cell-100M" and not present_tokenizer:
        warnings.append("no tokenizer files detected; public VCHarness code calls AutoTokenizer.from_pretrained, so runtime equivalence is not yet proven")
    if repo_id == "genbio-ai/STRING_GNN" and len(files) <= 1:
        warnings.append("STRING_GNN repo exposes no model weights through the Hugging Face API snapshot")
    return {
        "path": str(path),
        "repo_id": repo_id,
        "files": files,
        "has_config": has_config,
        "has_weight": has_weight,
        "tokenizer_files": present_tokenizer,
        "warnings": warnings,
        "status": "usable_with_warnings" if has_config and has_weight else "blocked_or_incomplete",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Download selected files from a public Hugging Face model repo without git-lfs.")
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--include", nargs="*", default=[])
    parser.add_argument("--skip", nargs="*", default=[])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    info = model_info(args.repo_id)
    selected = select_files(info, args.include, set(args.skip))
    plan = []
    for name in selected:
        size = head_size(args.repo_id, name)
        plan.append({"filename": name, "bytes": size})
    if args.dry_run:
        result = {"repo_id": args.repo_id, "sha": info.get("sha"), "selected": plan, "dry_run": True}
    else:
        downloads = [download_file(args.repo_id, name, args.output_dir) for name in selected]
        validation = validate_model_dir(args.output_dir, args.repo_id)
        result = {
            "repo_id": args.repo_id,
            "sha": info.get("sha"),
            "private": info.get("private"),
            "gated": info.get("gated"),
            "downloads": downloads,
            "validation": validation,
        }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
