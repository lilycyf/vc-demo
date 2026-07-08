from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_train_labels(train_tsv: Path) -> tuple[Counter[int], int, int, int]:
    counts: Counter[int] = Counter()
    rows = 0
    label_width = None
    with train_tsv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            labels = ast.literal_eval(row["label"])
            if label_width is None:
                label_width = len(labels)
            elif len(labels) != label_width:
                raise ValueError(f"inconsistent label width in {train_tsv}: expected {label_width}, found {len(labels)}")
            counts.update(int(x) for x in labels)
            rows += 1
    if label_width is None:
        raise ValueError(f"no rows found in {train_tsv}")
    return counts, rows, label_width, rows * label_width


def derive_weights(counts: Counter[int], labels: list[int]) -> dict[str, Any]:
    total = float(sum(counts[label] for label in labels))
    n_classes = float(len(labels))
    frequencies = {str(label): counts[label] / total for label in labels}
    balanced = {str(label): total / (n_classes * max(float(counts[label]), 1.0)) for label in labels}
    inv = {str(label): 1.0 / max(frequencies[str(label)], 1e-12) for label in labels}
    mean_inv = sum(inv.values()) / len(inv)
    mean_normalized_inverse = {label: value / mean_inv for label, value in inv.items()}
    sqrt_inv = {label: value ** 0.5 for label, value in inv.items()}
    mean_sqrt = sum(sqrt_inv.values()) / len(sqrt_inv)
    sqrt_inverse_mean_normalized = {label: value / mean_sqrt for label, value in sqrt_inv.items()}
    return {
        "frequencies": frequencies,
        "balanced_class_weights": balanced,
        "inverse_frequency_mean_normalized": mean_normalized_inverse,
        "sqrt_inverse_frequency_mean_normalized": sqrt_inverse_mean_normalized,
    }


def update_registry(registry_path: Path, artifact_path: Path, summary: dict[str, Any]) -> None:
    registry = read_json(registry_path)
    artifacts = registry.setdefault("artifacts", [])
    entry = None
    for artifact in artifacts:
        ids = {str(artifact.get("id", "")), *[str(alias) for alias in artifact.get("aliases", [])]}
        if "class_distribution" in ids:
            entry = artifact
            break
    if entry is None:
        entry = {"id": "class_distribution"}
        artifacts.append(entry)
    entry.update({
        "family": "class_distribution",
        "provider": "derived_from_official_k562_train_split",
        "status": "derived_present",
        "path": str(artifact_path),
        "source": "derived_by:scripts/build_k562_class_distribution.py from data/cell_lines/official_k562_cls/train.tsv only",
        "usable_for": ["loss_weighting", "focal_loss_alpha", "class_balanced_training"],
        "required_for_blueprints": [
            "official_class_imbalance_training",
            "official_weighted_ce_training",
            "official_focal_loss_training",
            "class_balanced_deg_classifier",
            "focal_loss_training_strategy",
        ],
        "do_not_fabricate": True,
        "provenance": "derived_from_train_labels_only_no_val_or_test",
        "split_used": "train",
        "forbidden_splits": ["val", "test"],
        "raw_label_counts": summary["raw_label_counts"],
        "training_label_counts": summary["training_label_counts"],
        "raw_label_order": summary["raw_label_order"],
        "training_label_order": summary["training_label_order"],
        "n_train_rows": summary["n_train_rows"],
        "n_targets": summary["n_targets"],
        "n_label_values": summary["n_label_values"],
        "artifact_sha256": summary["artifact_sha256"],
        "artifact_bytes": summary["artifact_bytes"],
        "summary_path": str(artifact_path),
    })
    write_json(registry_path, registry)


def main() -> None:
    parser = argparse.ArgumentParser(description="Derive K562 class distribution artifact from official train split labels only.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/cell_lines/official_k562_cls"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=Path("configs/artifacts/k562_registry.json"))
    parser.add_argument("--update-registry", action="store_true")
    args = parser.parse_args()

    manifest_path = args.data_dir / "manifest.json"
    train_tsv = args.data_dir / "train.tsv"
    target_genes = args.data_dir / "target_genes.tsv"
    if not manifest_path.exists() or not train_tsv.exists() or not target_genes.exists():
        raise FileNotFoundError("official K562 manifest/train.tsv/target_genes.tsv are required")
    manifest = read_json(manifest_path)
    counts, rows, width, total_labels = count_train_labels(train_tsv)
    raw_label_order = [int(x) for x in manifest.get("label_values", [-1, 0, 1])]
    remap = {int(k): int(v) for k, v in manifest.get("label_remap_for_training", {"-1": 0, "0": 1, "1": 2}).items()}
    training_counts = {str(remap[label]): int(counts[label]) for label in raw_label_order}
    weights = derive_weights(counts, raw_label_order)
    payload: dict[str, Any] = {
        "format": "vc_demo.class_distribution.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cell_line": manifest.get("cell_line", "K-562"),
        "source": {
            "manifest": str(manifest_path),
            "train_tsv": str(train_tsv),
            "target_genes_tsv": str(target_genes),
            "manifest_source": manifest.get("source", {}),
        },
        "provenance": "derived_from_official_train_split_labels_only",
        "split_used": "train",
        "forbidden_splits": ["val", "test"],
        "n_train_rows": rows,
        "n_targets": width,
        "total_train_labels": total_labels,
        "n_label_values": len(raw_label_order),
        "raw_label_order": raw_label_order,
        "training_label_order": [remap[label] for label in raw_label_order],
        "label_remap_for_training": {str(k): v for k, v in remap.items()},
        "raw_label_counts": {str(label): int(counts[label]) for label in raw_label_order},
        "training_label_counts": training_counts,
        "weights": weights,
        "recommended": {
            "weighted_cross_entropy_class_weights_training_order": [weights["balanced_class_weights"][str(label)] for label in raw_label_order],
            "focal_loss_alpha_training_order": [weights["sqrt_inverse_frequency_mean_normalized"][str(label)] for label in raw_label_order],
            "notes": "Training order follows label_remap_for_training: -1->0, 0->1, 1->2. Weights are train-only and must not be tuned on val/test.",
        },
        "manifest_train_counts_match": manifest.get("label_counts_by_split", {}).get("train", {}) == {str(label): int(counts[label]) for label in raw_label_order},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, payload)
    payload["artifact_sha256"] = sha256_file(args.output)
    payload["artifact_bytes"] = args.output.stat().st_size
    write_json(args.output, payload)
    if args.update_registry:
        update_registry(args.registry, args.output, payload)
    print(json.dumps({
        "output": str(args.output),
        "artifact_sha256": payload["artifact_sha256"],
        "artifact_bytes": payload["artifact_bytes"],
        "n_train_rows": rows,
        "n_targets": width,
        "raw_label_counts": payload["raw_label_counts"],
        "manifest_train_counts_match": payload["manifest_train_counts_match"],
    }, indent=2))


if __name__ == "__main__":
    main()
