from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from build_gene_embedding_dataset import load_gene_embedding_h5ad, load_split


def load_target_genes(data_dir: Path) -> np.ndarray:
    manifest = json.loads((data_dir / "manifest.json").read_text())
    files = manifest["files"]
    target_genes: np.ndarray | None = None
    for split, name in files.items():
        payload = load_split(data_dir / name)
        if "target_genes" not in payload:
            raise KeyError(f"{data_dir / name} does not contain target_genes")
        genes = payload["target_genes"].astype(str)
        if target_genes is None:
            target_genes = genes
        elif not np.array_equal(target_genes, genes):
            raise ValueError(f"target_genes differ between splits; first split vs {split}")
    if target_genes is None:
        raise ValueError(f"no split files found in {data_dir}")
    return target_genes


def align_gene_table(genes: np.ndarray, embedding_map: dict[str, np.ndarray], embedding_dim: int) -> tuple[np.ndarray, list[str]]:
    table = np.zeros((len(genes), embedding_dim), dtype="float32")
    missing: list[str] = []
    for idx, gene in enumerate(genes.astype(str)):
        vector = embedding_map.get(gene)
        if vector is None:
            missing.append(gene)
            continue
        table[idx] = vector
    return table, missing


def write_artifact_manifest(
    data_dir: Path,
    artifact_name: str,
    embedding_path: Path,
    gene_column: str,
    embedding_meta: dict[str, Any],
    target_path: Path,
    target_genes: np.ndarray,
    target_embeddings: np.ndarray,
    missing_target_genes: list[str],
) -> dict[str, Any]:
    coverage = 1.0 - (len(missing_target_genes) / float(len(target_genes)) if len(target_genes) else 0.0)
    manifest = {
        "format": "vc_demo_artifact_manifest.v1",
        "artifact_name": artifact_name,
        "artifact_family": "gene_embedding",
        "artifact_source": {
            "type": "h5ad",
            "path": str(embedding_path),
            "gene_column": gene_column,
            "embedding_meta": embedding_meta,
        },
        "target_gene_embeddings": {
            "path": str(target_path),
            "key": "target_gene_embeddings",
            "genes_key": "target_genes",
            "n_target_genes": int(len(target_genes)),
            "embedding_dim": int(target_embeddings.shape[1]),
            "coverage": coverage,
            "missing_target_genes": sorted(set(missing_target_genes)),
        },
        "perturbation_gene_embeddings": {
            "source": "split_npz:gene_embedding_features",
            "description": "Per-row perturbation-gene embedding already aligned into each split by scripts/build_gene_embedding_dataset.py.",
        },
        "usage_contract": {
            "frozen_by_default": True,
            "do_not_fabricate_missing_embeddings": True,
            "model_should_use_both_sides": "Combine perturbation/context features with target_gene_embeddings for target-level logits.",
        },
    }
    (data_dir / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def build(data_dir: Path, embedding_h5ad: Path, artifact_name: str, gene_column: str, output_name: str) -> dict[str, Any]:
    target_genes = load_target_genes(data_dir)
    embedding_map, embedding_meta = load_gene_embedding_h5ad(embedding_h5ad, gene_column)
    embedding_dim = int(embedding_meta["embedding_dim"])
    target_embeddings, missing = align_gene_table(target_genes, embedding_map, embedding_dim)
    target_path = data_dir / output_name
    np.savez_compressed(target_path, target_genes=target_genes.astype(str), target_gene_embeddings=target_embeddings.astype("float32"))
    return write_artifact_manifest(
        data_dir=data_dir,
        artifact_name=artifact_name,
        embedding_path=embedding_h5ad,
        gene_column=gene_column,
        embedding_meta=embedding_meta,
        target_path=target_path,
        target_genes=target_genes,
        target_embeddings=target_embeddings,
        missing_target_genes=missing,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build target-gene artifact tables aligned to a real_npz perturbation dataset.")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--embedding-h5ad", type=Path, required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--gene-column", default="symbol")
    parser.add_argument("--output-name", default="target_gene_embeddings.npz")
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args()
    manifest = build(args.data_dir, args.embedding_h5ad, args.artifact_name, args.gene_column, args.output_name)
    text = json.dumps(manifest, indent=2)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
