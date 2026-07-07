from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np

REACTOME_GMT_URL = "https://reactome.org/download/current/ReactomePathways.gmt.zip"
USER_AGENT = "vc-demo pathway artifact builder; source-backed Reactome download"


def load_target_genes(data_dir: Path) -> list[str]:
    train = data_dir / "train.npz"
    if not train.exists():
        raise FileNotFoundError(f"missing train split: {train}")
    with np.load(train, allow_pickle=True) as z:
        if "target_genes" not in z.files:
            raise KeyError(f"{train} does not contain target_genes")
        return [str(x) for x in z["target_genes"].tolist()]


def download(url: str, output: Path) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return {
        "url": url,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }


def parse_reactome_gmt(zip_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if not names:
            raise ValueError(f"empty Reactome GMT zip: {zip_path}")
        text = zf.read(names[0]).decode("utf-8")
    for line in text.splitlines():
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if len(parts) < 3:
            continue
        name, stable_id, *genes = parts
        if not stable_id.startswith("R-HSA-"):
            continue
        rows.append({"name": name, "stable_id": stable_id, "genes": sorted(set(genes))})
    return rows


def build_membership(target_genes: list[str], pathways: list[dict[str, Any]], min_overlap: int) -> dict[str, Any]:
    target_index = {gene: i for i, gene in enumerate(target_genes)}
    target_set = set(target_index)
    kept: list[dict[str, Any]] = []
    columns: list[np.ndarray] = []
    for pathway in pathways:
        matched = sorted(set(pathway["genes"]) & target_set)
        if len(matched) < min_overlap:
            continue
        col = np.zeros(len(target_genes), dtype=np.uint8)
        for gene in matched:
            col[target_index[gene]] = 1
        columns.append(col)
        kept.append({
            "stable_id": pathway["stable_id"],
            "name": pathway["name"],
            "n_reactome_genes": len(pathway["genes"]),
            "n_target_genes": len(matched),
            "target_genes": matched,
        })
    if not columns:
        raise ValueError("no pathways overlap target genes after filtering")
    return {"membership": np.stack(columns, axis=1).astype(np.uint8), "pathways": kept}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Reactome pathway membership matrix aligned to K562 target genes.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/cell_lines/k562_concat_esm2_gene_embedding"))
    parser.add_argument("--output", type=Path, default=Path("data/artifacts/pathways/k562_target_pathway_membership.npz"))
    parser.add_argument("--summary", type=Path, default=Path("experiments/k562_pathway_membership_artifact_summary.json"))
    parser.add_argument("--source-url", default=REACTOME_GMT_URL)
    parser.add_argument("--min-overlap", type=int, default=2)
    args = parser.parse_args()

    target_genes = load_target_genes(args.data_dir)
    with TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "ReactomePathways.gmt.zip"
        source = download(args.source_url, zip_path)
        pathways = parse_reactome_gmt(zip_path)
    built = build_membership(target_genes, pathways, args.min_overlap)
    membership = built["membership"]
    kept = built["pathways"]
    covered = np.asarray(membership.sum(axis=1) > 0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        membership=membership,
        target_genes=np.asarray(target_genes, dtype="U64"),
        pathway_ids=np.asarray([p["stable_id"] for p in kept], dtype="U64"),
        pathway_names=np.asarray([p["name"] for p in kept], dtype="U256"),
        pathway_gene_counts=np.asarray([p["n_reactome_genes"] for p in kept], dtype=np.int32),
        pathway_target_gene_counts=np.asarray([p["n_target_genes"] for p in kept], dtype=np.int32),
    )
    summary = {
        "format": "vc_demo_pathway_membership_artifact.v1",
        "artifact_id": "pathway_membership_matrix",
        "provider": "Reactome",
        "source_url": args.source_url,
        "source_download": source,
        "source_file": "ReactomePathways.gmt inside ReactomePathways.gmt.zip",
        "species_filter": "Homo sapiens pathways only, identified by R-HSA stable IDs",
        "filtering_rule": f"Keep pathways with at least {args.min_overlap} genes overlapping the exact K562 target-gene list.",
        "data_dir": str(args.data_dir),
        "output": str(args.output),
        "n_target_genes": len(target_genes),
        "n_source_pathways": len(pathways),
        "n_kept_pathways": len(kept),
        "membership_shape": list(membership.shape),
        "covered_target_gene_count": int(covered.sum()),
        "target_gene_coverage": float(covered.mean()),
        "mean_pathways_per_target_gene": float(membership.sum(axis=1).mean()),
        "median_pathways_per_target_gene": float(np.median(membership.sum(axis=1))),
        "mean_target_genes_per_pathway": float(membership.sum(axis=0).mean()),
        "top_pathways_by_target_overlap": sorted(
            [{"stable_id": p["stable_id"], "name": p["name"], "n_target_genes": p["n_target_genes"]} for p in kept],
            key=lambda x: x["n_target_genes"],
            reverse=True,
        )[:20],
        "uncovered_target_genes": [gene for gene, has in zip(target_genes, covered.tolist()) if not has],
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
