from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

HF_API = "https://huggingface.co/api/datasets/genbio-ai/foundation-models-perturbation/tree/main"
HF_RESOLVE = "https://huggingface.co/datasets/genbio-ai/foundation-models-perturbation/resolve/main"


def list_tree(path: str) -> list[dict]:
    url = f"{HF_API}/{path}" if path else HF_API
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def download(path: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    url = f"{HF_RESOLVE}/{urllib.parse.quote(path)}"
    if output.exists():
        print(json.dumps({"status": "exists", "path": str(output), "bytes": output.stat().st_size}, indent=2))
        return
    urllib.request.urlretrieve(url, output)
    print(json.dumps({"status": "downloaded", "source": url, "path": str(output), "bytes": output.stat().st_size}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="List or download public GenBio foundation-model perturbation artifacts.")
    parser.add_argument("--list", dest="list_path", default=None, help="List a path such as gene_embeddings or gnn")
    parser.add_argument("--path", default=None, help="Dataset-relative artifact path to download")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.list_path is not None:
        items = list_tree(args.list_path)
        print(json.dumps([{k: item.get(k) for k in ("type", "path", "size")} for item in items], indent=2))
        return
    if not args.path or not args.output:
        raise SystemExit("provide either --list PATH or --path ARTIFACT --output FILE")
    download(args.path, args.output)


if __name__ == "__main__":
    main()
