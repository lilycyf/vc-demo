from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np


@dataclass(frozen=True)
class OfficialK562Contract:
    cell_line: str = "K-562"
    fold: int = 0
    val_fraction: float = 0.10
    val_seed: int = 20260414
    n_genes: int = 6640
    n_classes: int = 3
    expected_train_rows: int = 1388
    expected_train_pool_rows: int = 1542
    label_values: tuple[int, int, int] = (-1, 0, 1)


def _decode(values: np.ndarray) -> list[str]:
    return [x.decode("utf-8") if isinstance(x, (bytes, bytearray)) else str(x) for x in values]


def _categorical(group: h5py.Group, key: str) -> list[str]:
    cats = _decode(group[f"{key}/categories"][()])
    codes = group[f"{key}/codes"][()]
    return [cats[int(code)] if int(code) >= 0 else "" for code in codes]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_official_h5ad(path: Path, contract: OfficialK562Contract) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with h5py.File(path, "r") as f:
        cell_lines = np.asarray(_categorical(f["obs"], "cell_line"))
        genes = np.asarray(_categorical(f["obs"], "gene"))
        gene_ids = np.asarray(_categorical(f["obs"], "gene_id"))
        split = np.asarray(f["obs/test_split"][()], dtype=int)
        target_symbols = _categorical(f["var"], "symbol")
        target_gene_ids = _decode(f["var/var_id"][()])
        x_shape = tuple(int(v) for v in f["X"].shape)
        if x_shape[1] != contract.n_genes:
            raise ValueError(f"official DEG matrix has {x_shape[1]} genes, expected {contract.n_genes}")
        row_idx = np.where(cell_lines == contract.cell_line)[0]
        labels = np.asarray(f["X"][row_idx, :], dtype=np.int8)
    return {
        "row_idx": row_idx,
        "genes": genes[row_idx],
        "gene_ids": gene_ids[row_idx],
        "test_split": split[row_idx],
        "labels": labels,
        "target_symbols": target_symbols,
        "target_gene_ids": target_gene_ids,
        "matrix_shape": x_shape,
    }


def _split_indices(test_split: np.ndarray, contract: OfficialK562Contract) -> dict[str, np.ndarray]:
    test_mask = test_split == int(contract.fold)
    train_pool = np.where(~test_mask)[0]
    rng = np.random.default_rng(contract.val_seed)
    shuffled = train_pool.copy()
    rng.shuffle(shuffled)
    val_n = int(round(len(train_pool) * float(contract.val_fraction)))
    val = np.sort(shuffled[:val_n])
    train = np.sort(shuffled[val_n:])
    test = np.where(test_mask)[0]
    return {"train": train, "val": val, "test": test, "train_pool": train_pool}


def _write_tsv(path: Path, genes: np.ndarray, gene_ids: np.ndarray, labels: np.ndarray, local_indices: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["pert_id", "symbol", "label"])
        for i in local_indices.tolist():
            writer.writerow([str(gene_ids[i]), str(genes[i]), json.dumps(labels[i].astype(int).tolist(), separators=(",", ":"))])


def _write_target_genes(path: Path, target_gene_ids: list[str], target_symbols: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["target_index", "gene_id", "symbol"])
        for i, (gene_id, symbol) in enumerate(zip(target_gene_ids, target_symbols)):
            writer.writerow([i, gene_id, symbol])


def _label_counts(labels: np.ndarray) -> dict[str, int]:
    vals, counts = np.unique(labels, return_counts=True)
    return {str(int(v)): int(c) for v, c in zip(vals, counts)}


def build_official_k562_task(source_h5ad: Path, output_dir: Path, contract: OfficialK562Contract | None = None) -> dict[str, Any]:
    contract = contract or OfficialK562Contract()
    payload = _read_official_h5ad(source_h5ad, contract)
    splits = _split_indices(payload["test_split"], contract)
    output_dir.mkdir(parents=True, exist_ok=True)
    for split in ["train", "val", "test"]:
        _write_tsv(output_dir / f"{split}.tsv", payload["genes"], payload["gene_ids"], payload["labels"], splits[split])
    _write_target_genes(output_dir / "target_genes.tsv", payload["target_gene_ids"], payload["target_symbols"])

    split_counts = {name: int(len(idx)) for name, idx in splits.items() if name != "train_pool"}
    label_counts_by_split = {name: _label_counts(payload["labels"][idx]) for name, idx in splits.items() if name != "train_pool"}
    class_counts = label_counts_by_split["train"]
    total = sum(class_counts.values())
    class_freq = {k: (v / total if total else 0.0) for k, v in class_counts.items()}
    manifest = {
        "format": "official_k562_tsv",
        "schema_version": "vc_demo.official_k562.v1",
        "source": {
            "name": "genbio-ai/foundation-models-perturbation essential/essential_deg_with_split.h5ad",
            "url": "https://huggingface.co/datasets/genbio-ai/foundation-models-perturbation",
            "path": str(source_h5ad),
            "sha256": _sha256(source_h5ad),
            "bytes": source_h5ad.stat().st_size,
        },
        "contract": asdict(contract),
        "cell_line": contract.cell_line,
        "fold": contract.fold,
        "val_fraction": contract.val_fraction,
        "val_seed": contract.val_seed,
        "n_obs_all_cell_lines": int(payload["matrix_shape"][0]),
        "n_perturbations_cell_line": int(len(payload["row_idx"])),
        "n_target_genes": int(len(payload["target_gene_ids"])),
        "n_classes": contract.n_classes,
        "label_values": list(contract.label_values),
        "label_remap_for_training": {"-1": 0, "0": 1, "1": 2},
        "split_sizes": split_counts,
        "train_pool_rows_before_val_split": int(len(splits["train_pool"])),
        "label_counts_by_split": label_counts_by_split,
        "train_class_frequency_raw_labels": class_freq,
        "files": {"train": "train.tsv", "val": "val.tsv", "test": "test.tsv", "target_genes": "target_genes.tsv"},
        "official_vcharness_alignment": {
            "matches_n_genes_6640": int(len(payload["target_gene_ids"])) == 6640,
            "matches_train_rows_1388": split_counts["train"] == contract.expected_train_rows,
            "matches_train_pool_rows_1542": int(len(splits["train_pool"])) == contract.expected_train_pool_rows,
            "tsv_columns_match_public_node_code": ["pert_id", "symbol", "label"],
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _read_tsv_labels(path: Path) -> list[list[int]]:
    labels: list[list[int]] = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"pert_id", "symbol", "label"}
        if set(reader.fieldnames or []) != required:
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{path} missing TSV columns: {sorted(missing)}")
        for row in reader:
            labels.append([int(x) for x in json.loads(row["label"])])
    return labels


def validate_official_k562_task(data_dir: Path, strict: bool = True) -> dict[str, Any]:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    issues: list[str] = []
    split_sizes: dict[str, int] = {}
    label_counts: dict[str, dict[str, int]] = {}
    n_genes_seen: set[int] = set()
    for split in ["train", "val", "test"]:
        path = data_dir / f"{split}.tsv"
        if not path.exists():
            issues.append(f"missing {path}")
            continue
        labels = _read_tsv_labels(path)
        split_sizes[split] = len(labels)
        for label in labels:
            n_genes_seen.add(len(label))
        if labels:
            label_counts[split] = _label_counts(np.asarray(labels, dtype=np.int16))
    target_genes = data_dir / "target_genes.tsv"
    target_rows = 0
    if target_genes.exists():
        with target_genes.open(newline="") as f:
            target_rows = sum(1 for _ in csv.DictReader(f, delimiter="\t"))
    else:
        issues.append(f"missing {target_genes}")

    expected = OfficialK562Contract()
    if n_genes_seen != {expected.n_genes}:
        issues.append(f"label vectors must all have length {expected.n_genes}; observed={sorted(n_genes_seen)}")
    if target_rows != expected.n_genes:
        issues.append(f"target_genes.tsv must contain {expected.n_genes} rows; observed={target_rows}")
    if split_sizes.get("train") != expected.expected_train_rows:
        issues.append(f"train split must contain {expected.expected_train_rows} rows for official fold-0 contract; observed={split_sizes.get('train')}")
    if manifest.get("n_target_genes") != expected.n_genes:
        issues.append("manifest n_target_genes does not match official 6640-gene contract")
    alignment = manifest.get("official_vcharness_alignment", {})
    for key in ["matches_n_genes_6640", "matches_train_rows_1388", "matches_train_pool_rows_1542"]:
        if not alignment.get(key):
            issues.append(f"manifest alignment flag is false: {key}")

    result = {
        "status": "passed" if not issues else "failed",
        "data_dir": str(data_dir),
        "split_sizes": split_sizes,
        "target_gene_rows": target_rows,
        "n_genes_seen": sorted(n_genes_seen),
        "label_counts_by_split": label_counts,
        "issues": issues,
    }
    if strict and issues:
        raise SystemExit(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or validate the official K562 Essential DEG task contract.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build")
    build.add_argument("--source-h5ad", type=Path, default=Path("data/artifacts/official_k562/essential_deg_with_split.h5ad"))
    build.add_argument("--output-dir", type=Path, default=Path("data/cell_lines/official_k562_cls"))
    build.add_argument("--fold", type=int, default=0)
    build.add_argument("--val-fraction", type=float, default=0.10)
    build.add_argument("--val-seed", type=int, default=20260414)
    validate = sub.add_parser("validate")
    validate.add_argument("--data-dir", type=Path, default=Path("data/cell_lines/official_k562_cls"))
    validate.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.cmd == "build":
        contract = OfficialK562Contract(fold=args.fold, val_fraction=args.val_fraction, val_seed=args.val_seed)
        result = build_official_k562_task(args.source_h5ad, args.output_dir, contract)
    else:
        result = validate_official_k562_task(args.data_dir, strict=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
