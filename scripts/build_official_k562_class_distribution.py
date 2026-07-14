from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build train-only class distribution for the official K562 DEG task.")
    parser.add_argument("--train-tsv", type=Path, default=Path("data/cell_lines/official_k562_cls/train.tsv"))
    parser.add_argument("--output", type=Path, default=Path("data/artifacts/official_k562/class_distribution_train.json"))
    args = parser.parse_args()

    if not args.train_tsv.exists():
        raise FileNotFoundError(f"missing official K562 train TSV: {args.train_tsv}")

    counts: Counter[int] = Counter()
    n_rows = 0
    n_targets = None
    with args.train_tsv.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if "label" not in (reader.fieldnames or []):
            raise ValueError(f"{args.train_tsv} must contain a label column")
        for row in reader:
            labels = [int(x) for x in json.loads(row["label"])]
            if n_targets is None:
                n_targets = len(labels)
            elif len(labels) != n_targets:
                raise ValueError("label vectors are not all the same length")
            counts.update(labels)
            n_rows += 1

    total = sum(counts.values())
    payload = {
        "artifact_id": "class_distribution",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(args.train_tsv),
        "split": "train",
        "leakage_guardrail": "Derived only from official train split labels; validation/test labels are not read.",
        "n_train_rows": n_rows,
        "n_target_genes": n_targets,
        "raw_label_counts": {str(k): int(counts.get(k, 0)) for k in sorted(counts)},
        "raw_label_frequencies": {str(k): (float(counts.get(k, 0)) / float(total) if total else 0.0) for k in sorted(counts)},
        "training_label_mapping": {"-1": 0, "0": 1, "1": 2},
        "training_class_counts": {str(k + 1): int(counts.get(k, 0)) for k in (-1, 0, 1)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "n_train_rows": n_rows, "n_target_genes": n_targets, "counts": payload["raw_label_counts"]}, indent=2))


if __name__ == "__main__":
    main()
