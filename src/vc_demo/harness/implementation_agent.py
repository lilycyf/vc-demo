from __future__ import annotations

import argparse
import json
import py_compile
import traceback
from pathlib import Path
from typing import Any

from vc_demo.harness.model_blueprints import blueprint_by_id
from vc_demo.harness.program_agent import render_program_source
from vc_demo.harness.search_memory import record_event
from vc_demo.harness.state import read_json, write_json
from vc_demo.harness.train_pending import train_pending_node


def _generic_program_source(blueprint_id: str) -> str:
    templates = {
        "film_conditioned_residual": FILM_CONDITIONED_RESIDUAL,
        "target_factor_router": TARGET_FACTOR_ROUTER,
        "gated_multimodal_fusion": GATED_MULTIMODAL_FUSION,
        "uncertainty_calibrated_head": UNCERTAINTY_CALIBRATED_HEAD,
        "class_balanced_deg_classifier": CLASS_BALANCED_HEAD,
        "focal_loss_training_strategy": CLASS_BALANCED_HEAD,
    }
    return templates[blueprint_id]


def materialize_model(program_dir: Path, strategy: str) -> dict[str, Any]:
    model_path = program_dir / "model.py"
    try:
        source = render_program_source(strategy)
        source_kind = "harness_implemented_template"
    except Exception:
        try:
            source = _generic_program_source(strategy)
            source_kind = "implementation_agent_template"
        except KeyError:
            request = program_dir / "IMPLEMENTATION_REQUEST.md"
            task = program_dir / "CODEX_IMPLEMENTATION_TASK.md"
            task.write_text(render_codex_task(strategy, request), encoding="utf-8")
            return {"status": "requires_external_codex", "strategy": strategy, "task_path": str(task), "model_path": str(model_path)}
    model_path.write_text(source, encoding="utf-8")
    py_compile.compile(str(model_path), doraise=True)
    return {"status": "implemented", "strategy": strategy, "source_kind": source_kind, "model_path": str(model_path)}


def render_codex_task(strategy: str, request_path: Path) -> str:
    blueprint = blueprint_by_id(strategy)
    request_text = request_path.read_text(encoding="utf-8") if request_path.exists() else ""
    return "\n".join([
        f"# Codex Implementation Task: `{strategy}`",
        "",
        "Implement the pending node-local `model.py` for this blueprint.",
        "Do not modify data splits, labels, metrics, or artifact files.",
        "Do not fabricate missing artifacts. If the model requires a missing artifact, stop and update acquisition queue instead.",
        "",
        "## Blueprint",
        json.dumps(blueprint, indent=2),
        "",
        "## Original Request",
        request_text,
    ]) + "\n"


def pending_nodes(run_dir: Path) -> list[dict[str, Any]]:
    queue_path = run_dir / "implementation_queue.json"
    if not queue_path.exists():
        return []
    payload = read_json(queue_path)
    return list(payload.get("items", []))


def implement_pending(run_dir: Path, max_nodes: int | None = None, train: bool = False, max_epochs: int | None = None, repair_attempts: int = 1) -> dict[str, Any]:
    items = pending_nodes(run_dir)
    if max_nodes is not None:
        items = items[:max_nodes]
    results: list[dict[str, Any]] = []
    for item in items:
        node = str(item.get("node"))
        strategy = str(item.get("strategy"))
        program_dir = Path(str(item.get("program_dir")))
        attempt_rows: list[dict[str, Any]] = []
        result: dict[str, Any] = {"node": node, "strategy": strategy, "program_dir": str(program_dir)}
        for attempt in range(1, repair_attempts + 1):
            try:
                impl = materialize_model(program_dir, strategy)
                attempt_rows.append({"attempt": attempt, **impl})
                result.update(impl)
                if impl["status"] != "implemented":
                    break
                if train:
                    trained = train_pending_node(run_dir, node, max_epochs=max_epochs)
                    result["training"] = {"status": "trained", "best_val_macro_f1": trained["metrics"].get("best_val_macro_f1"), "test_macro_f1": trained["metrics"].get("test_macro_f1")}
                break
            except Exception as exc:
                attempt_rows.append({"attempt": attempt, "status": "failed", "error": "".join(traceback.format_exception_only(type(exc), exc)).strip(), "traceback": traceback.format_exc()[-8000:]})
                result.update({"status": "failed", "error": attempt_rows[-1]["error"]})
        result["attempts"] = attempt_rows
        results.append(result)
        record_event(run_dir, "implementation_agent", result)
    report = {"items": results, "trained": train}
    write_json(run_dir / "implementation_agent_report.json", report)
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize pending node-local model.py files and optionally train them.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--max-nodes", type=int, default=None)
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--repair-attempts", type=int, default=1)
    args = parser.parse_args()
    implement_pending(args.run_dir, args.max_nodes, args.train, args.max_epochs, args.repair_attempts)


FILM_CONDITIONED_RESIDUAL = '''from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    def __init__(self, spec):
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.input = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU())
        self.mod = nn.Linear(int(spec.input_dim), hidden * 2)
        self.blocks = nn.ModuleList([nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, hidden * 2), nn.GELU(), nn.Dropout(float(spec.dropout)), nn.Linear(hidden * 2, hidden)) for _ in range(max(1, int(spec.depth)))])
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.input(x)
        gamma, beta = self.mod(x).chunk(2, dim=-1)
        gamma = torch.tanh(gamma)
        for block in self.blocks:
            z = z + block(z) * (1.0 + gamma) + beta * 0.05
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
'''

TARGET_FACTOR_ROUTER = '''from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    def __init__(self, spec):
        super().__init__()
        hidden = int(spec.hidden_dim)
        rank = max(16, min(int(getattr(spec, "low_rank_dim", 64)), hidden, 128))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.encoder = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(float(spec.dropout)), nn.Linear(hidden, hidden), nn.GELU())
        self.route = nn.Sequential(nn.Linear(hidden, rank), nn.Softmax(dim=-1))
        self.class_factors = nn.Linear(hidden, rank * self.n_classes)
        self.target_factors = nn.Parameter(torch.empty(self.n_targets, rank))
        nn.init.normal_(self.target_factors, std=0.02)
        self.bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        routed = self.class_factors(z).view(x.shape[0], -1, self.n_classes) * self.route(z).unsqueeze(-1)
        return torch.einsum("brc,nr->bnc", routed, self.target_factors) + self.bias.unsqueeze(0)
'''

GATED_MULTIMODAL_FUSION = '''from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    def __init__(self, spec):
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.cell = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU())
        self.prior = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU())
        self.gate = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.Sigmoid())
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        g = self.gate(x)
        z = self.cell(x) * g + self.prior(x) * (1.0 - g)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes)
'''

UNCERTAINTY_CALIBRATED_HEAD = '''from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    def __init__(self, spec):
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.encoder = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(float(spec.dropout)), nn.Linear(hidden, hidden), nn.GELU())
        self.mean = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.temperature = nn.Sequential(nn.Linear(hidden, self.n_targets), nn.Softplus())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        logits = self.mean(z).view(x.shape[0], self.n_targets, self.n_classes)
        temp = self.temperature(z).view(x.shape[0], self.n_targets, 1).clamp_min(0.25) + 0.75
        return logits / temp
'''

CLASS_BALANCED_HEAD = '''from __future__ import annotations

import torch
from torch import nn


class GeneratedModel(nn.Module):
    def __init__(self, spec):
        super().__init__()
        hidden = int(spec.hidden_dim)
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.encoder = nn.Sequential(nn.Linear(int(spec.input_dim), hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(float(spec.dropout)), nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU())
        self.head = nn.Linear(hidden, self.n_targets * self.n_classes)
        self.class_bias = nn.Parameter(torch.tensor([0.1, -0.2, 0.1], dtype=torch.float32).view(1, 1, 3))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        return self.head(z).view(x.shape[0], self.n_targets, self.n_classes) + self.class_bias[:, :, : self.n_classes]
'''


if __name__ == "__main__":
    main()
