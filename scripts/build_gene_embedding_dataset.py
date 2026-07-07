from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import h5py
import numpy as np


def decode_array(values: np.ndarray) -> list[str]:
    out: list[str] = []
    for value in values:
        if isinstance(value, bytes):
            out.append(value.decode("utf-8"))
        else:
            out.append(str(value))
    return out


def read_obs_column(handle: h5py.File, name: str) -> list[str]:
    obj = handle[f"obs/{name}"]
    if isinstance(obj, h5py.Dataset):
        return decode_array(obj[()])
    categories = decode_array(obj["categories"][()])
    codes = obj["codes"][()]
    values: list[str] = []
    for code in codes:
        idx = int(code)
        values.append(categories[idx] if idx >= 0 else "")
    return values


def read_h5ad_dense_matrix(handle: h5py.File) -> np.ndarray:
    x = handle["X"]
    if isinstance(x, h5py.Dataset):
        return np.asarray(x[()], dtype="float32")
    if {"data", "indices", "indptr"}.issubset(set(x.keys())):
        data = np.asarray(x["data"][()], dtype="float32")
        indices = np.asarray(x["indices"][()], dtype="int64")
        indptr = np.asarray(x["indptr"][()], dtype="int64")
        n_rows = len(indptr) - 1
        n_cols = int(handle["var/var_id"].shape[0]) if "var/var_id" in handle else int(indices.max()) + 1
        dense = np.zeros((n_rows, n_cols), dtype="float32")
        for row in range(n_rows):
            start, end = int(indptr[row]), int(indptr[row + 1])
            dense[row, indices[start:end]] = data[start:end]
        return dense
    raise ValueError("unsupported H5AD X layout; expected dense dataset or CSR group")


def load_gene_embedding_h5ad(path: Path, gene_column: str) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    with h5py.File(path, "r") as handle:
        matrix = read_h5ad_dense_matrix(handle)
        genes = read_obs_column(handle, gene_column)
    if matrix.shape[0] != len(genes):
        raise ValueError(f"embedding row/gene mismatch: {matrix.shape[0]} vs {len(genes)}")
    mapping: dict[str, np.ndarray] = {}
    duplicates = 0
    for gene, vector in zip(genes, matrix):
        key = gene.strip()
        if not key:
            continue
        if key in mapping:
            duplicates += 1
            continue
        mapping[key] = np.asarray(vector, dtype="float32")
    meta = {
        "path": str(path),
        "gene_column": gene_column,
        "rows": int(matrix.shape[0]),
        "embedding_dim": int(matrix.shape[1]),
        "unique_genes": len(mapping),
        "duplicate_gene_rows_ignored": duplicates,
    }
    return mapping, meta


def load_split(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


def zscore_by_train(train: np.ndarray, arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    mean = train.mean(axis=0, keepdims=True)
    std = train.std(axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    return {split: ((value - mean) / std).astype("float32") for split, value in arrays.items()}


def align_embeddings(perturbations: np.ndarray, embedding_map: dict[str, np.ndarray], embedding_dim: int) -> tuple[np.ndarray, list[str]]:
    features = np.zeros((len(perturbations), embedding_dim), dtype="float32")
    missing: list[str] = []
    for idx, perturbation in enumerate(perturbations.astype(str)):
        vector = embedding_map.get(perturbation)
        if vector is None:
            missing.append(perturbation)
            continue
        features[idx] = vector
    return features, missing


def write_split(path: Path, template: dict[str, np.ndarray], features: np.ndarray, embedding_features: np.ndarray) -> None:
    payload = {key: value for key, value in template.items() if key not in {"features", "gene_embedding_features"}}
    payload["features"] = features.astype("float32")
    payload["gene_embedding_features"] = embedding_features.astype("float32")
    np.savez_compressed(path, **payload)


def build_dataset(
    source_dir: Path,
    output_dir: Path,
    embedding_path: Path,
    artifact_name: str,
    gene_column: str,
    feature_mode: str,
    zscore_embeddings: bool,
) -> dict[str, Any]:
    manifest = json.loads((source_dir / "manifest.json").read_text())
    files = manifest["files"]
    splits = {split: load_split(source_dir / name) for split, name in files.items()}
    embedding_map, embedding_meta = load_gene_embedding_h5ad(embedding_path, gene_column)
    embedding_dim = int(embedding_meta["embedding_dim"])

    raw_embeddings: dict[str, np.ndarray] = {}
    missing_by_split: dict[str, list[str]] = {}
    for split, payload in splits.items():
        emb, missing = align_embeddings(payload["perturbations"], embedding_map, embedding_dim)
        raw_embeddings[split] = emb
        missing_by_split[split] = missing
    embeddings = zscore_by_train(raw_embeddings["train"], raw_embeddings) if zscore_embeddings else raw_embeddings

    output_dir.mkdir(parents=True, exist_ok=True)
    split_reports: dict[str, Any] = {}
    for split, name in files.items():
        payload = splits[split]
        source_features = payload["features"].astype("float32")
        emb = embeddings[split].astype("float32")
        if feature_mode == "embedding_only":
            features = emb
        elif feature_mode == "source_plus_embedding":
            features = np.concatenate([source_features, emb], axis=1).astype("float32")
        elif feature_mode == "onehot_plus_embedding":
            onehot_dim = int(manifest.get("n_perturbations", source_features.shape[1]))
            features = np.concatenate([source_features[:, :onehot_dim], emb], axis=1).astype("float32")
        else:
            raise ValueError(f"unknown feature_mode {feature_mode!r}")
        write_split(output_dir / name, payload, features, emb)
        split_reports[split] = {
            "file": name,
            "n_rows": int(features.shape[0]),
            "source_feature_dim": int(source_features.shape[1]),
            "embedding_dim": int(emb.shape[1]),
            "output_feature_dim": int(features.shape[1]),
            "matched_perturbations": int(features.shape[0] - len(missing_by_split[split])),
            "missing_perturbations": sorted(set(missing_by_split[split])),
        }

    total_rows = sum(report["n_rows"] for report in split_reports.values())
    total_missing = sum(len(report["missing_perturbations"]) for report in split_reports.values())
    coverage = 1.0 - (float(total_missing) / float(total_rows) if total_rows else 0.0)
    out_manifest = dict(manifest)
    out_manifest.update(
        {
            "feature_set": f"{manifest.get('feature_set', 'source')}_plus_{artifact_name}",
            "feature_description": f"{feature_mode} using real gene embedding artifact {artifact_name}; perturbation gene symbols aligned to obs/{gene_column}.",
            "n_features": int(next(iter(split_reports.values()))["output_feature_dim"]),
            "artifact": {
                "name": artifact_name,
                "type": "gene_embedding_h5ad",
                "source_path": str(embedding_path),
                "gene_column": gene_column,
                "zscore_by_train": zscore_embeddings,
                "embedding_meta": embedding_meta,
                "coverage": coverage,
                "split_reports": split_reports,
            },
        }
    )
    (output_dir / "manifest.json").write_text(json.dumps(out_manifest, indent=2), encoding="utf-8")
    return out_manifest["artifact"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a real_npz dataset that consumes a real H5AD gene embedding artifact.")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--embedding-h5ad", type=Path, required=True)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--gene-column", default="symbol")
    parser.add_argument("--feature-mode", choices=["embedding_only", "source_plus_embedding", "onehot_plus_embedding"], default="source_plus_embedding")
    parser.add_argument("--no-zscore", action="store_true")
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args()

    artifact_report = build_dataset(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        embedding_path=args.embedding_h5ad,
        artifact_name=args.artifact_name,
        gene_column=args.gene_column,
        feature_mode=args.feature_mode,
        zscore_embeddings=not args.no_zscore,
    )
    text = json.dumps(artifact_report, indent=2)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
