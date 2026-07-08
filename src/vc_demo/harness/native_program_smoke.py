from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from vc_demo.data import build_datasets
from vc_demo.models import build_model
from vc_demo.train import resolve_model_dimensions


def smoke_config(config: dict, *, batch_size: int = 2) -> dict:
    train_dataset, _, _ = build_datasets(config)
    config = resolve_model_dimensions(config, train_dataset[0])
    model = build_model(config)
    rows = [train_dataset[i]["x"] for i in range(min(batch_size, len(train_dataset)))]
    x = torch.stack(rows)
    logits = model(x)
    expected = (x.shape[0], int(config["model"]["n_targets"]), int(config["model"].get("n_classes", 3)))
    if tuple(logits.shape) != expected:
        raise AssertionError(f"forward output shape {tuple(logits.shape)} != expected {expected}")
    loss = logits.float().mean()
    loss.backward()
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"status": "passed", "node_name": config.get("node_name", ""), "model_type": config.get("model", {}).get("model_type"), "output_shape": list(logits.shape), "trainable_parameters": trainable}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile/forward/backward smoke for a vc_demo custom/native program model.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    result = smoke_config(config, batch_size=args.batch_size)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
