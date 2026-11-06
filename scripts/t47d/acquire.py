"""Download the public GEO inputs with resumable curl and provenance records."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE260nnn/GSE260703/"
FILES = {
    **{f"GSE260703_{name}.gz": "suppl/" for name in (
        "count_barcodes.csv", "count_features.csv", "count_matrix.mtx",
        "gfp_barcodes.csv", "gfp_features.csv", "gfp_matrix.mtx",
    )},
    "GSE260703_family.soft.gz": "soft/",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/t47d_lineage/raw")
    args = parser.parse_args()
    dest = Path(args.output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {"accession": "GSE260703", "source": BASE, "artifacts": []}
    for name, folder in FILES.items():
        path = dest / name
        partial = dest / (name + ".partial")
        url = BASE + folder + name
        if not path.exists():
            subprocess.run([
                "curl", "--fail", "--location", "--retry", "5", "--retry-delay", "3",
                "--connect-timeout", "30", "--max-time", "14400", "--continue-at", "-",
                "--output", str(partial), url,
            ], check=True)
            subprocess.run(["gzip", "--test", str(partial)], check=True)
            partial.replace(path)
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        item = {
            "id": name, "path": str(path), "source_url": url, "status": "original_public",
            "size_bytes": path.stat().st_size, "sha256": digest,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        manifest["artifacts"].append(item)
        (dest / "download_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps(item), flush=True)


if __name__ == "__main__":
    main()
