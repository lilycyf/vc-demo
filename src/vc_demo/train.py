from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from vc_demo.data import build_datasets
from vc_demo.metrics import macro_f1
from vc_demo.models import build_model


def load_config(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict[str, float]:
    model.eval()
    loss_fn = nn.CrossEntropyLoss()
    losses: list[float] = []
    preds: list[torch.Tensor] = []
    targets: list[torch.Tensor] = []
    with torch.no_grad():
        for batch in loader:
            x = batch["x"].to(device)
            y = batch["y"].to(device)
            logits = model(x)
            loss = loss_fn(logits.reshape(-1, logits.shape[-1]), y.reshape(-1))
            losses.append(loss.item())
            preds.append(logits.argmax(dim=-1).cpu())
            targets.append(y.cpu())
    pred = torch.cat(preds)
    target = torch.cat(targets)
    return {"loss": float(sum(losses) / max(len(losses), 1)), "macro_f1": macro_f1(pred, target)}


def resolve_model_dimensions(config: dict, sample: dict[str, torch.Tensor]) -> dict:
    config = json.loads(json.dumps(config))
    model_cfg = config.setdefault("model", {})
    x = sample["x"]
    y = sample["y"]
    if model_cfg.get("input_dim", "auto") == "auto":
        model_cfg["input_dim"] = int(x.shape[-1])
    if model_cfg.get("n_targets", "auto") == "auto":
        model_cfg["n_targets"] = int(y.shape[-1])
    if model_cfg.get("n_classes", "auto") == "auto":
        model_cfg["n_classes"] = int(config.get("data", {}).get("n_classes", 3))
    return config


def train(config: dict, output_dir: Path, max_epochs: int | None = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_size = int(config.get("training", {}).get("batch_size", 16))
    epochs = int(max_epochs or config.get("training", {}).get("epochs", 8))
    lr = float(config.get("training", {}).get("lr", 3e-4))
    weight_decay = float(config.get("training", {}).get("weight_decay", 1e-4))

    train_dataset, val_dataset, test_dataset = build_datasets(config)
    config = resolve_model_dimensions(config, train_dataset[0])
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    test_loader = DataLoader(test_dataset, batch_size=batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = nn.CrossEntropyLoss()

    best_val = -1.0
    history: list[dict] = []
    for epoch in range(1, epochs + 1):
        model.train()
        running = 0.0
        for batch in tqdm(train_loader, desc=f"epoch {epoch}/{epochs}", leave=False):
            x = batch["x"].to(device)
            y = batch["y"].to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = loss_fn(logits.reshape(-1, logits.shape[-1]), y.reshape(-1))
            loss.backward()
            optimizer.step()
            running += loss.item()
        val = evaluate(model, val_loader, device)
        row = {"epoch": epoch, "train_loss": running / max(len(train_loader), 1), "val_loss": val["loss"], "val_macro_f1": val["macro_f1"]}
        history.append(row)
        if val["macro_f1"] > best_val:
            best_val = val["macro_f1"]
            torch.save({"model": model.state_dict(), "config": config, "val": val}, output_dir / "best.pt")

    best = torch.load(output_dir / "best.pt", map_location=device)
    model.load_state_dict(best["model"])
    test = evaluate(model, test_loader, device)
    result = {
        "node_name": config.get("node_name", output_dir.name),
        "dataset_type": config.get("data", {}).get("dataset_type", "synthetic"),
        "device": str(device),
        "best_val_macro_f1": best_val,
        "test_macro_f1": test["macro_f1"],
        "test_loss": test["loss"],
        "history": history,
    }
    (output_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    memory = (
        f"# Node Memory: {result['node_name']}\n\n"
        f"- Best validation Macro-F1: {best_val:.4f}\n"
        f"- Test Macro-F1: {test['macro_f1']:.4f}\n"
        f"- Device: {device}\n"
    )
    (output_dir / "memory.md").write_text(memory, encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-epochs", type=int, default=None)
    args = parser.parse_args()
    result = train(load_config(args.config), args.output_dir, args.max_epochs)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
