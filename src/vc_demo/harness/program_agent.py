from __future__ import annotations

import copy
import hashlib
import random
from pathlib import Path
from typing import Any

from vc_demo.harness.model_blueprints import blueprint_by_id, implemented_blueprint_ids
from vc_demo.harness.state import write_json


def propose_program_child(parent_config: dict[str, Any], parent_node: dict[str, Any], child_index: int, rng: random.Random, program_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parent_name = str(parent_config.get("node_name", parent_node.get("name", "node")))
    blueprint_id = _choose_blueprint(parent_name, parent_node, child_index, rng)
    blueprint = blueprint_by_id(blueprint_id)
    digest = hashlib.sha1(f"{parent_name}:{child_index}:{blueprint_id}".encode("utf-8")).hexdigest()[:8]
    child_name = f"{parent_name.split('_child_')[0]}_p{child_index}_{blueprint_id}_{digest}"
    child_dir = program_root / child_name
    child_dir.mkdir(parents=True, exist_ok=True)

    child = copy.deepcopy(parent_config)
    child.setdefault("model", {})
    child.setdefault("training", {})
    child["node_name"] = child_name

    model_cfg = child["model"]
    train_cfg = child["training"]
    old_model = model_cfg.get("model_type", "mlp")
    model_cfg["model_type"] = "custom_program"
    model_cfg["custom_model_path"] = str(child_dir / "model.py")
    model_cfg["custom_model_class"] = "GeneratedModel"
    model_cfg["program_blueprint"] = blueprint_id
    model_cfg["hidden_dim"] = _bounded_hidden(model_cfg.get("hidden_dim", 256), blueprint_id)
    model_cfg["depth"] = min(max(int(model_cfg.get("depth", 2) or 2), 1), 3)
    model_cfg["dropout"] = float(model_cfg.get("dropout", 0.1) if model_cfg.get("dropout") is not None else 0.1)
    if blueprint_id == "dual_path_gated_low_rank":
        model_cfg["low_rank_dim"] = min(max(int(model_cfg.get("low_rank_dim", 64) or 64), 32), 96)
    train_cfg["lr"] = min(float(train_cfg.get("lr", 3e-4) or 3e-4), 3e-4)
    train_cfg["weight_decay"] = min(float(train_cfg.get("weight_decay", 1e-4) or 1e-4), 1e-4)

    source = render_program_source(blueprint_id)
    (child_dir / "model.py").write_text(source, encoding="utf-8")
    (child_dir / "README.md").write_text(render_program_readme(child_name, blueprint, parent_name), encoding="utf-8")
    write_json(child_dir / "base_config.json", child)

    changes = [
        f"program_model:{old_model}->{blueprint_id}",
        f"blueprint_status:{blueprint['status']}",
        f"custom_model_path:{child_dir / 'model.py'}",
        f"hidden_dim:{parent_config.get('model', {}).get('hidden_dim')}->{model_cfg.get('hidden_dim')}",
        f"depth:{parent_config.get('model', {}).get('depth')}->{model_cfg.get('depth')}",
        f"lr:{parent_config.get('training', {}).get('lr')}->{train_cfg.get('lr')}",
    ]
    proposal = {
        "agent_type": "codex_program_node_agent",
        "node_kind": "program_node",
        "parent": parent_name,
        "child": child_name,
        "strategy": blueprint_id,
        "blueprint": blueprint,
        "hypothesis": hypothesis_for(blueprint_id),
        "changes": changes,
        "program_dir": str(child_dir),
        "program_model_path": str(child_dir / "model.py"),
        "limits": "Model choice is manifest-driven. Only implemented blueprints are executable; planned blueprints remain on the design list.",
    }
    child["proposal_note"] = f"codex_program_agent blueprint={blueprint_id}; " + "; ".join(changes)
    write_json(child_dir / "proposal.json", proposal)
    return child, proposal


def _choose_blueprint(parent_name: str, parent_node: dict[str, Any], child_index: int, rng: random.Random) -> str:
    choices = implemented_blueprint_ids()
    if not choices:
        raise ValueError("no implemented model blueprints are available")
    if child_index == 1:
        if "residual" in parent_name and "mixture_of_experts" in choices:
            return "mixture_of_experts"
        if "gated" in parent_name and "dual_path_gated_low_rank" in choices:
            return "dual_path_gated_low_rank"
    parent_offset = int(hashlib.sha1(parent_name.encode("utf-8")).hexdigest(), 16) % len(choices)
    if child_index <= len(choices):
        return choices[(parent_offset + child_index - 1) % len(choices)]
    parent_val = float(parent_node.get("best_val_macro_f1", 0.0) or 0.0)
    if parent_val >= 0.60 and "dual_path_gated_low_rank" in choices and rng.random() < 0.65:
        return "dual_path_gated_low_rank"
    return rng.choice(choices)

def _bounded_hidden(current: Any, blueprint_id: str) -> int:
    value = int(current or 256)
    if blueprint_id == "mixture_of_experts":
        return min(max(value, 256), 384)
    return min(max(value, 192), 384)


def render_program_source(blueprint_id: str) -> str:
    sources = {
        "dual_path_gated_low_rank": DUAL_PATH_GATED_LOW_RANK,
        "mixture_of_experts": MIXTURE_OF_EXPERTS,
    }
    try:
        return sources[blueprint_id]
    except KeyError as exc:
        raise ValueError(f"blueprint {blueprint_id!r} is not implemented and cannot be executed") from exc


def render_program_readme(child_name: str, blueprint: dict[str, Any], parent_name: str) -> str:
    lines = [
        f"# Program Node: {child_name}",
        "",
        f"- Parent: `{parent_name}`",
        f"- Blueprint: `{blueprint['id']}`",
        f"- Status: `{blueprint['status']}`",
        f"- Category: `{blueprint['category']}`",
        f"- Role: {blueprint['role']}",
        "",
        "This directory is a node-local architecture program generated by the harness.",
    ]
    return "\n".join(lines) + "\n"


def hypothesis_for(blueprint_id: str) -> str:
    mapping = {
        "dual_path_gated_low_rank": "A dual-path encoder with input-conditioned gating and a low-rank target head may share target-gene response structure while preserving perturbation-specific signal.",
        "mixture_of_experts": "A compact router over multiple experts may specialize decision surfaces for different perturbation feature regimes.",
    }
    return mapping[blueprint_id]


DUAL_PATH_GATED_LOW_RANK = """from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        rank = max(8, min(int(getattr(spec, \"low_rank_dim\", 64)), hidden))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.left = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(spec.dropout))
        self.right = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU())
        self.gate = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.Sigmoid())
        self.rank_head = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gate = self.gate(x)
        z = self.left(x) * gate + self.right(x) * (1.0 - gate)
        rank_logits = self.rank_head(z).view(x.shape[0], -1, self.n_classes)
        logits = torch.einsum(\"brc,nr->bnc\", rank_logits, self.target_factors)
        return logits + self.bias.unsqueeze(0)
"""


MIXTURE_OF_EXPERTS = """from __future__ import annotations

import torch
from torch import nn


def expert_block(input_dim: int, hidden: int, dropout: float) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(input_dim, hidden),
        nn.LayerNorm(hidden),
        nn.GELU(),
        nn.Dropout(dropout),
        nn.Linear(hidden, hidden),
        nn.GELU(),
    )


class GeneratedModel(nn.Module):
    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.experts = nn.ModuleList([expert_block(spec.input_dim, hidden, spec.dropout) for _ in range(3)])
        self.router = nn.Sequential(nn.Linear(spec.input_dim, hidden), nn.GELU(), nn.Linear(hidden, 3), nn.Softmax(dim=-1))
        self.norm = nn.LayerNorm(hidden)
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        weights = self.router(x)
        stacked = torch.stack([expert(x) for expert in self.experts], dim=1)
        z = torch.sum(stacked * weights.unsqueeze(-1), dim=1)
        logits = self.head(self.norm(z))
        return logits.view(x.shape[0], self.n_targets, self.n_classes)
"""
