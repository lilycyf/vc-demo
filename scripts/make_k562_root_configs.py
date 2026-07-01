from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOTS = [
    {"name": "root_onehot_mlp", "data_dir": "data/cell_lines/k562_onehot", "hidden_dim": 256, "depth": 2, "dropout": 0.1, "lr": 3e-4, "weight_decay": 1e-4},
    {"name": "root_delta_mlp", "data_dir": "data/cell_lines/k562_delta", "hidden_dim": 256, "depth": 2, "dropout": 0.1, "lr": 3e-4, "weight_decay": 1e-4},
    {"name": "root_concat_mlp", "data_dir": "data/cell_lines/k562_concat", "hidden_dim": 384, "depth": 2, "dropout": 0.1, "lr": 3e-4, "weight_decay": 1e-4},
    {"name": "root_concat_regularized_mlp", "data_dir": "data/cell_lines/k562_concat", "hidden_dim": 384, "depth": 3, "dropout": 0.2, "lr": 2e-4, "weight_decay": 5e-4},
]


def config_for(root: dict) -> dict:
    return {
        "node_name": root["name"],
        "data": {
            "dataset_type": "real_npz",
            "cell_line": "K562",
            "data_dir": root["data_dir"],
            "feature_key": "features",
            "label_key": "labels",
            "split_key": "split",
            "n_classes": 3,
        },
        "model": {
            "input_dim": "auto",
            "hidden_dim": root["hidden_dim"],
            "n_targets": "auto",
            "n_classes": "auto",
            "dropout": root["dropout"],
            "depth": root["depth"],
        },
        "training": {
            "batch_size": 16,
            "epochs": 8,
            "lr": root["lr"],
            "weight_decay": root["weight_decay"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Write K562 multi-feature root configs.")
    parser.add_argument("--output-dir", type=Path, default=Path("configs/k562_roots"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for root in ROOTS:
        path = args.output_dir / f"{root['name']}.json"
        path.write_text(json.dumps(config_for(root), indent=2), encoding="utf-8")
        written.append(str(path))
    print(json.dumps({"written": written}, indent=2))


if __name__ == "__main__":
    main()
