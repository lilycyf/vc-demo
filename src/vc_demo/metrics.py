from __future__ import annotations

import torch


def macro_f1(pred: torch.Tensor, target: torch.Tensor, n_classes: int = 3) -> float:
    """Macro-F1 over flattened gene-level DEG classes."""
    pred = pred.reshape(-1)
    target = target.reshape(-1)
    scores: list[torch.Tensor] = []
    for cls in range(n_classes):
        tp = ((pred == cls) & (target == cls)).sum().float()
        fp = ((pred == cls) & (target != cls)).sum().float()
        fn = ((pred != cls) & (target == cls)).sum().float()
        precision = tp / (tp + fp + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        scores.append(2 * precision * recall / (precision + recall + 1e-8))
    return torch.stack(scores).mean().item()
