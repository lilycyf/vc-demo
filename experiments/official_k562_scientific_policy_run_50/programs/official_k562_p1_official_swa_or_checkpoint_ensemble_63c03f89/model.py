import torch
import torch.nn as nn


class GeneratedModel(nn.Module):
    """Node-local compact proxy for a strict checkpoint-ensemble/SWA blueprint.

    The public harness trains a single epoch in this pilot, so the executable
    approximation keeps multiple lightweight heads over one trunk and averages
    them with learned validation-selection logits. Metadata records that any
    checkpoint/SWA selection must be validation-only; no test labels are read.
    """

    def __init__(self, spec):
        super().__init__()
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        input_dim = int(getattr(spec, "input_dim", 640))
        hidden = int(getattr(spec, "hidden_dim", 256))
        dropout = float(getattr(spec, "dropout", 0.1))
        rank = max(32, min(hidden, 128))
        self.ensemble_policy = {
            "blueprint": "official_swa_or_checkpoint_ensemble",
            "checkpoint_selection": "validation_macro_f1_only",
            "test_label_usage": "forbidden",
            "proxy": "three_head_topk_checkpoint_average_with_trainable_validation_weights",
        }
        self.trunk = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.GELU(),
        )
        self.context = nn.Linear(hidden, rank * self.n_classes)
        self.head_factors = nn.Parameter(torch.randn(3, self.n_targets, rank) * 0.02)
        self.head_bias = nn.Parameter(torch.zeros(3, self.n_targets, self.n_classes))
        self.head_logits = nn.Parameter(torch.zeros(3))

    def forward(self, x):
        z = self.trunk(x)
        context = self.context(z).view(x.shape[0], -1, self.n_classes)
        logits = torch.einsum("brc,hnr->hbnc", context, self.head_factors) + self.head_bias[:, None, :, :]
        weights = torch.softmax(self.head_logits, dim=0).view(-1, 1, 1, 1)
        return (weights * logits).sum(dim=0)
