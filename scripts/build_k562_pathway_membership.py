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


def load_target_genes_from_tsv(path: Path) -> tuple[list[str], list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"missing official target gene table: {path}")
    symbols: list[str] = []
    gene_ids: list[str] = []
    with path.open(encoding="utf-8") as f:
        header = f.readline().strip().split("\t")
        try:
            symbol_i = header.index("symbol")
        except ValueError as exc:
            raise KeyError(f"{path} missing symbol column") from exc
        gene_id_i = header.index("gene_id") if "gene_id" in header else None
        for line in f:
            parts = line.rstrip("\n\r").split("\t")
            if len(parts) <= symbol_i:
                continue
            symbols.append(parts[symbol_i])
            gene_ids.append(parts[gene_id_i] if gene_id_i is not None and len(parts) > gene_id_i else "")
    if not symbols:
        raise ValueError(f"no target genes loaded from {path}")
    return symbols, gene_ids


def load_target_genes_from_npz(data_dir: Path) -> tuple[list[str], list[str]]:
    train = data_dir / "train.npz"
    if not train.exists():
        raise FileNotFoundError(f"missing train split: {train}")
    with np.load(train, allow_pickle=True) as z:
        if "target_genes" not in z.files:
            raise KeyError(f"{train} does not contain target_genes")
        symbols = [str(x) for x in z["target_genes"].tolist()]
    return symbols, ["" for _ in symbols]


def load_target_genes(target_genes_tsv: Path | None, data_dir: Path) -> tuple[list[str], list[str], str]:
    if target_genes_tsv and target_genes_tsv.exists():
        symbols, gene_ids = load_target_genes_from_tsv(target_genes_tsv)
        return symbols, gene_ids, str(target_genes_tsv)
    official = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
    if official.exists():
        symbols, gene_ids = load_target_genes_from_tsv(official)
        return symbols, gene_ids, str(official)
    symbols, gene_ids = load_target_genes_from_npz(data_dir)
    return symbols, gene_ids, str(data_dir / "train.npz")


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


def build_membership(target_symbols: list[str], pathways: list[dict[str, Any]], min_overlap: int) -> dict[str, Any]:
    target_index = {gene: i for i, gene in enumerate(target_symbols)}
    target_set = set(target_index)
    kept: list[dict[str, Any]] = []
    columns: list[np.ndarray] = []
    for pathway in pathways:
        matched = sorted(set(pathway["genes"]) & target_set)
        if len(matched) < min_overlap:
            continue
        col = np.zeros(len(target_symbols), dtype=np.uint8)
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def update_registry(registry_path: Path, summary: dict[str, Any]) -> None:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    artifacts = registry.setdefault("artifacts", [])
    target_id = "pathway_memberships"
    aliases = {"pathway_membership_matrix", "pathway_memberships"}
    entry = None
    for artifact in artifacts:
        ids = {str(artifact.get("id", "")), *[str(x) for x in artifact.get("aliases", [])]}
        if ids & aliases:
            entry = artifact
            break
    if entry is None:
        entry = {"id": target_id}
        artifacts.append(entry)
    entry.update({
        "id": target_id,
        "aliases": sorted(aliases - {target_id}),
        "family": "pathway_prior",
        "provider": "Reactome",
        "status": "expected_present",
        "path": summary["output"],
        "source": "Reactome official GMT download aligned to exact official K562 target genes; built by scripts/build_k562_pathway_membership.py",
        "usable_for": ["target_gene", "pathway_pooling"],
        "required_for_blueprints": ["pathway_pooling_encoder", "official_pathway_pooling_reactome"],
        "do_not_fabricate": True,
        "source_url": summary["source_url"],
        "source_file": summary["source_file"],
        "source_sha256": summary["source_download"]["sha256"],
        "source_bytes": summary["source_download"]["bytes"],
        "artifact_sha256": summary["artifact_sha256"],
        "artifact_bytes": summary["artifact_bytes"],
        "target_gene_source": summary["target_gene_source"],
        "species_filter": summary["species_filter"],
        "filtering_rule": summary["filtering_rule"],
        "n_target_genes": summary["n_target_genes"],
        "expected_n_targets": summary["n_target_genes"],
        "n_source_pathways": summary["n_source_pathways"],
        "n_kept_pathways": summary["n_kept_pathways"],
        "membership_shape": summary["membership_shape"],
        "covered_target_gene_count": summary["covered_target_gene_count"],
        "target_gene_coverage": summary["target_gene_coverage"],
        "mean_pathways_per_target_gene": summary["mean_pathways_per_target_gene"],
        "summary_path": summary["summary_path"],
    })
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Reactome pathway membership matrix aligned to official K562 target genes.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/cell_lines/official_k562_cls"))
    parser.add_argument("--target-genes-tsv", type=Path, default=Path("data/cell_lines/official_k562_cls/target_genes.tsv"))
    parser.add_argument("--output", type=Path, default=Path("data/artifacts/pathways/k562_target_pathway_membership.npz"))
    parser.add_argument("--summary", type=Path, default=Path("experiments/k562_pathway_membership_artifact_summary.json"))
    parser.add_argument("--source-url", default=REACTOME_GMT_URL)
    parser.add_argument("--min-overlap", type=int, default=2)
    parser.add_argument("--registry", type=Path, default=Path("configs/artifacts/k562_registry.json"))
    parser.add_argument("--update-registry", action="store_true")
    args = parser.parse_args()

    target_symbols, target_gene_ids, target_source = load_target_genes(args.target_genes_tsv, args.data_dir)
    with TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "ReactomePathways.gmt.zip"
        source = download(args.source_url, zip_path)
        pathways = parse_reactome_gmt(zip_path)
    built = build_membership(target_symbols, pathways, args.min_overlap)
    membership = built["membership"]
    kept = built["pathways"]
    covered = np.asarray(membership.sum(axis=1) > 0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        membership=membership,
        membership_matrix=membership,
        target_genes=np.asarray(target_symbols, dtype="U64"),
        target_gene_symbols=np.asarray(target_symbols, dtype="U64"),
        target_gene_ids=np.asarray(target_gene_ids, dtype="U64"),
        pathway_ids=np.asarray([p["stable_id"] for p in kept], dtype="U64"),
        pathway_names=np.asarray([p["name"] for p in kept], dtype="U256"),
        pathway_gene_counts=np.asarray([p["n_reactome_genes"] for p in kept], dtype=np.int32),
        pathway_target_gene_counts=np.asarray([p["n_target_genes"] for p in kept], dtype=np.int32),
    )
    summary = {
        "format": "vc_demo_pathway_membership_artifact.v2",
        "artifact_id": "pathway_memberships",
        "aliases": ["pathway_membership_matrix"],
        "provider": "Reactome",
        "source_url": args.source_url,
        "source_download": source,
        "source_file": "ReactomePathways.gmt inside ReactomePathways.gmt.zip",
        "species_filter": "Homo sapiens pathways only, identified by R-HSA stable IDs",
        "filtering_rule": f"Keep pathways with at least {args.min_overlap} genes overlapping the exact official K562 target-gene list.",
        "target_gene_source": target_source,
        "data_dir": str(args.data_dir),
        "output": str(args.output),
        "summary_path": str(args.summary),
        "n_target_genes": len(target_symbols),
        "n_source_pathways": len(pathways),
        "n_kept_pathways": len(kept),
        "membership_shape": list(membership.shape),
        "covered_target_gene_count": int(covered.sum()),
        "target_gene_coverage": float(covered.mean()),
        "mean_pathways_per_target_gene": float(membership.sum(axis=1).mean()),
        "median_pathways_per_target_gene": float(np.median(membership.sum(axis=1))),
        "mean_target_genes_per_pathway": float(membership.sum(axis=0).mean()),
        "artifact_bytes": args.output.stat().st_size,
        "artifact_sha256": sha256_file(args.output),
        "top_pathways_by_target_overlap": sorted(
            [{"stable_id": p["stable_id"], "name": p["name"], "n_target_genes": p["n_target_genes"]} for p in kept],
            key=lambda x: x["n_target_genes"],
            reverse=True,
        )[:20],
        "uncovered_target_genes": [gene for gene, has in zip(target_symbols, covered.tolist()) if not has],
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.update_registry:
        update_registry(args.registry, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
