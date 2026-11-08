from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from vc_demo.data import build_datasets
from vc_demo.metrics import macro_f1
from vc_demo.models import build_model
from vc_demo.harness.research_contract import evaluation_policy, task_data_config, file_digest, ResearchContractError, capture_execution_recipe


def load_config(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, config: dict) -> dict[str, float]:
    model.eval()
    loss_fn = build_loss(config, device)
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


class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0, weight: torch.Tensor | None = None) -> None:
        super().__init__()
        self.gamma = gamma
        self.weight = weight

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        ce = nn.functional.cross_entropy(logits, target, weight=self.weight, reduction="none")
        pt = torch.exp(-ce)
        return (((1.0 - pt) ** self.gamma) * ce).mean()


def build_loss(config: dict, device: torch.device) -> nn.Module:
    training_cfg = config.get("training", {})
    loss_type = str(training_cfg.get("loss_type", "cross_entropy"))
    if loss_type == "cross_entropy":
        return nn.CrossEntropyLoss()
    if loss_type == "weighted_cross_entropy":
        weights = training_cfg.get("class_weights", [1.0, 1.0, 1.0])
        return nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
    if loss_type == "focal_loss":
        weights = training_cfg.get("class_weights")
        weight_tensor = torch.tensor(weights, dtype=torch.float32, device=device) if weights else None
        return FocalLoss(gamma=float(training_cfg.get("focal_gamma", 2.0)), weight=weight_tensor)
    raise ValueError(f"unknown training.loss_type {loss_type!r}")


def resolve_model_dimensions(config: dict, sample: dict[str, torch.Tensor]) -> dict:
    config = json.loads(json.dumps(config))
    model_cfg = config.setdefault("model", {})
    data_cfg = config.get("data") or config.get("dataset", {})
    x = sample["x"]
    y = sample["y"]
    if model_cfg.get("input_dim", "auto") == "auto":
        model_cfg["input_dim"] = int(x.shape[-1])
    if model_cfg.get("n_targets", "auto") == "auto":
        model_cfg["n_targets"] = int(y.shape[-1])
    if model_cfg.get("n_classes", "auto") == "auto":
        model_cfg["n_classes"] = int(data_cfg.get("n_classes", 3))

    data_dir = Path(str(data_cfg.get("data_dir", "")))
    artifact_manifest = data_dir / "artifact_manifest.json"
    if model_cfg.get("artifact_manifest_path") == "auto" and artifact_manifest.exists():
        model_cfg["artifact_manifest_path"] = str(artifact_manifest)
    if artifact_manifest.exists() and not model_cfg.get("artifacts"):
        with artifact_manifest.open() as f:
            model_cfg["artifacts"] = json.load(f)
    return config


def train(config: dict, output_dir: Path, max_epochs: int | None = None) -> dict:
    task_data_config(config)
    phase, evaluate_test = evaluation_policy(config)
    if phase == 'confirmation':
        lock_path = Path(config['evaluation']['confirmation_lock_path'])
        lock = json.loads(lock_path.read_text())
        current = capture_execution_recipe(config, lock_path.parent, max_epochs=max_epochs)
        if current['fingerprint'] != lock['recipe_fingerprints'][config['node_name']]:
            raise ResearchContractError('Direct confirmation changed the frozen executable recipe')
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_size = int(config.get("training", {}).get("batch_size", 16))
    epochs = int(max_epochs or config.get("training", {}).get("epochs", 8))
    lr = float(config.get("training", {}).get("lr", 3e-4))
    weight_decay = float(config.get("training", {}).get("weight_decay", 1e-4))

    train_dataset, val_dataset, test_dataset = build_datasets(config)
    config = resolve_model_dimensions(config, train_dataset[0])
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    test_loader = DataLoader(test_dataset, batch_size=batch_size) if evaluate_test else None
    (output_dir / 'effective_config.json').write_text(json.dumps(config, indent=2))

    requested_device = str(config.get("training", {}).get("device", "auto")).lower()
    force_cpu = os.environ.get("VC_DEMO_FORCE_CPU", "").lower() in {"1", "true", "yes"} or requested_device == "cpu"
    cuda_usable = torch.cuda.is_available() and not force_cpu
    if cuda_usable and requested_device in {"auto", "cuda"}:
        capability = torch.cuda.get_device_capability()
        arch = f"sm_{capability[0]}{capability[1]}"
        supported_arches = set(torch.cuda.get_arch_list())
        if supported_arches and arch not in supported_arches:
            cuda_usable = False
    if requested_device == "cuda" and not cuda_usable and not force_cpu:
        raise RuntimeError("training.device='cuda' was requested, but CUDA is unavailable or unsupported by this PyTorch build")
    device = torch.device("cuda" if cuda_usable else "cpu")
    model = build_model(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay) if phase != 'confirmation' else None
    loss_fn = build_loss(config, device)

    best_val = -1.0
    history: list[dict] = []
    for epoch in range(1, epochs + 1) if phase != 'confirmation' else ():
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
        val = evaluate(model, val_loader, device, config)
        row = {"epoch": epoch, "train_loss": running / max(len(train_loader), 1), "val_loss": val["loss"], "val_macro_f1": val["macro_f1"]}
        history.append(row)
        if val["macro_f1"] > best_val:
            best_val = val["macro_f1"]
            torch.save({"model": model.state_dict(), "config": config, "val": val}, output_dir / "best.pt")

    checkpoint_path = output_dir / 'best.pt'
    if phase == 'confirmation':
        lock = json.loads(Path(config['evaluation']['confirmation_lock_path']).read_text())
        receipt = lock.get('checkpoints', {}).get(config.get('node_name'))
        if not receipt or file_digest(Path(receipt['path'])) != receipt['sha256']:
            raise ResearchContractError('Confirmation requires the unchanged selected checkpoint; retraining is forbidden')
        checkpoint_path = Path(receipt['path'])
    best = torch.load(checkpoint_path, map_location=device)
    best_val = float(best['val']['macro_f1'])
    model.load_state_dict(best["model"])
    test = evaluate(model, test_loader, device, config) if evaluate_test else None
    result = {
        "node_name": config.get("node_name", output_dir.name),
        "dataset_type": (config.get("data") or config.get("dataset", {})).get("dataset_type", "synthetic"),
        "device": str(device),
        "best_val_macro_f1": best_val,
        "test_macro_f1": test["macro_f1"] if test else None,
        "test_loss": test["loss"] if test else None,
        "evidence_phase": phase,
        "epochs_trained_this_invocation": epochs if phase != 'confirmation' else 0,
        "test_metric_source": "frozen_confirmation" if test else "withheld_until_confirmation",
        "history": history,
        "training": {"epochs": epochs, "batch_size": batch_size, "lr": lr, "weight_decay": weight_decay, "loss_type": config.get("training", {}).get("loss_type", "cross_entropy")},
    }
    (output_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    memory = (
        f"# Node Memory: {result['node_name']}\n\n"
        f"- Best validation Macro-F1: {best_val:.4f}\n"
        f"- Test Macro-F1: {test['macro_f1'] if test else 'withheld until confirmation'}\n"
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
