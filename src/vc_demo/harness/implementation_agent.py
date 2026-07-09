from __future__ import annotations

import argparse
import json
import py_compile
import time
import traceback
from pathlib import Path
from typing import Any

from vc_demo.harness.model_blueprints import blueprint_by_id
from vc_demo.harness.native_program_smoke import smoke_config
from vc_demo.harness.program_agent import render_program_source
from vc_demo.harness.search_memory import record_event
from vc_demo.harness.state import read_json, write_json
from vc_demo.harness.train_pending import train_pending_node



OFFICIAL_NATIVE_VARIANT_BY_BLUEPRINT = {
    "official_aido_full_finetune": "aido_lora_adapter",
    "official_aido_topk_layer_tuning": "aido_lora_adapter",
    "official_aido_cached_embedding_fusion": "aido_lora_adapter",
    "official_string_gnn_frozen_cache": "string_gnn_attention",
    "official_string_gnn_full_finetune": "string_gnn_attention",
    "official_string_neighborhood_attention": "string_gnn_attention",
    "official_string_laplacian_smoothing": "string_gnn_attention",
    "official_aido_string_concat_fusion": "aido_string_fusion",
    "official_aido_string_gated_fusion": "aido_string_fusion",
    "official_aido_string_cross_attention": "aido_string_fusion",
    "official_aido_string_bilinear_fusion": "aido_string_fusion",
    "official_multimodal_mixture_of_experts": "aido_string_fusion",
    "official_target_low_rank_head": "target_gene_head",
    "official_target_bilinear_head": "target_gene_head",
    "official_target_graph_conditioned_head": "string_gnn_attention",
    "official_weighted_ce_training": "target_gene_head",
    "official_focal_loss_training": "target_gene_head",
    "official_layerwise_lr_schedule": "aido_lora_adapter",
    "official_temperature_calibrated_head": "target_gene_head",
    "official_gene_dropout_augmentation": "target_gene_head",
}


def _official_native_program_source(blueprint_id: str) -> str:
    variant = OFFICIAL_NATIVE_VARIANT_BY_BLUEPRINT[blueprint_id]
    return (
        "from __future__ import annotations\n\n"
        "from vc_demo.official_k562.native_models import OfficialK562NativeModel\n\n\n"
        "class GeneratedModel(OfficialK562NativeModel):\n"
        f"    implementation_blueprint = {blueprint_id!r}\n"
        f"    native_variant = {variant!r}\n\n"
        "    def __init__(self, spec):\n"
        f"        super().__init__(spec, variant={variant!r})\n"
    )


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
            source = _official_native_program_source(strategy)
            source_kind = "implementation_agent_official_native_proxy"
        except KeyError:
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


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def node_tree_record(run_dir: Path, node_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    tree_path = run_dir / "tree.json"
    tree = read_json(tree_path)
    try:
        node = tree["nodes"][node_name]
    except KeyError as exc:
        raise KeyError(f"node {node_name!r} not found in {tree_path}") from exc
    return tree, node


def pending_missing_artifacts(program_dir: Path, item: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    contract_path = Path(str(item.get("artifact_contract_path") or program_dir / "artifact_contract.json"))
    if contract_path.exists():
        contract = read_json(contract_path)
        missing.extend(str(x) for x in contract.get("missing_required_artifacts", []) or [])
    missing.extend(str(x) for x in item.get("missing_required_artifacts", []) or [])
    return sorted(set(x for x in missing if x))


def mark_node_failed(run_dir: Path, node_name: str, error: str, strategy: str, stage: str, attempts: list[dict[str, Any]]) -> None:
    tree_path = run_dir / "tree.json"
    tree = read_json(tree_path)
    node = tree.get("nodes", {}).get(node_name)
    if node:
        node.update({"status": "failed", "error": error, "failure_stage": stage, "implementation_attempts": attempts, "requires_implementation": False})
    failures_path = run_dir / "failures.json"
    failures = read_json(failures_path).get("failures", []) if failures_path.exists() else []
    failures.append({"node": node_name, "error": error, "strategy": strategy, "stage": stage, "attempts": attempts})
    write_json(tree_path, tree)
    write_json(failures_path, {"failures": failures})


def pending_nodes(run_dir: Path) -> list[dict[str, Any]]:
    queue_path = run_dir / "implementation_queue.json"
    if not queue_path.exists():
        return []
    payload = read_json(queue_path)
    return list(payload.get("items", []))


def implement_pending(run_dir: Path, max_nodes: int | None = None, train: bool = False, max_epochs: int | None = None, repair_attempts: int = 3) -> dict[str, Any]:
    items = pending_nodes(run_dir)
    if max_nodes is not None:
        items = items[:max_nodes]
    results: list[dict[str, Any]] = []
    repair_log = run_dir / "repair_log.jsonl"
    decision_trace = run_dir / "agent_decision_trace.jsonl"
    for item in items:
        node = str(item.get("node"))
        strategy = str(item.get("strategy"))
        program_dir = Path(str(item.get("program_dir")))
        result: dict[str, Any] = {"node": node, "strategy": strategy, "program_dir": str(program_dir), "policy": "strict_auto_materialize_smoke_train"}
        attempt_rows: list[dict[str, Any]] = []
        missing = pending_missing_artifacts(program_dir, item)
        append_jsonl(decision_trace, {"time": time.time(), "event": "implementation_selected", "node": node, "strategy": strategy, "missing_required_artifacts": missing})
        if missing:
            result.update({"status": "blocked_missing_artifact", "missing_required_artifacts": missing})
            attempt_rows.append({"attempt": 0, "stage": "artifact_gate", "status": "blocked", "missing_required_artifacts": missing})
            results.append({**result, "attempts": attempt_rows})
            append_jsonl(repair_log, {"time": time.time(), "node": node, "strategy": strategy, "stage": "artifact_gate", "status": "blocked", "missing_required_artifacts": missing})
            record_event(run_dir, "implementation_agent", {**result, "attempts": attempt_rows})
            continue
        for attempt in range(1, repair_attempts + 1):
            row: dict[str, Any] = {"attempt": attempt, "node": node, "strategy": strategy}
            try:
                impl = materialize_model(program_dir, strategy)
                row.update({"stage": "materialize", **impl})
                attempt_rows.append(row)
                append_jsonl(repair_log, {"time": time.time(), **row})
                result.update(impl)
                if impl["status"] != "implemented":
                    append_jsonl(decision_trace, {"time": time.time(), "event": "requires_external_codex", "node": node, "strategy": strategy, "task_path": impl.get("task_path")})
                    break
                model_path = Path(str(impl["model_path"]))
                py_compile.compile(str(model_path), doraise=True)
                tree, tree_node = node_tree_record(run_dir, node)
                config_path = Path(str(tree_node["config"]))
                config = read_json(config_path)
                smoke = smoke_config(config)
                smoke_path = program_dir / f"native_smoke_attempt_{attempt}.json"
                write_json(smoke_path, smoke)
                smoke_row = {"attempt": attempt, "stage": "native_smoke", "status": "passed", "smoke_path": str(smoke_path), **smoke}
                attempt_rows.append(smoke_row)
                append_jsonl(repair_log, {"time": time.time(), "node": node, "strategy": strategy, **smoke_row})
                if train:
                    trained = train_pending_node(run_dir, node, max_epochs=max_epochs)
                    metrics = trained["metrics"]
                    result["training"] = {"status": "trained", "best_val_macro_f1": metrics.get("best_val_macro_f1"), "test_macro_f1": metrics.get("test_macro_f1")}
                    append_jsonl(decision_trace, {"time": time.time(), "event": "trained_and_backpropagated", "node": node, "strategy": strategy, "best_val_macro_f1": metrics.get("best_val_macro_f1"), "test_macro_f1": metrics.get("test_macro_f1")})
                result["status"] = "trained" if train else "implemented"
                break
            except Exception as exc:
                error = "".join(traceback.format_exception_only(type(exc), exc)).strip()
                fail_row = {"attempt": attempt, "stage": "repairable_failure", "status": "failed", "error": error, "traceback": traceback.format_exc()[-8000:]}
                attempt_rows.append(fail_row)
                append_jsonl(repair_log, {"time": time.time(), "node": node, "strategy": strategy, **fail_row})
                result.update({"status": "failed", "error": error})
                if attempt >= repair_attempts:
                    mark_node_failed(run_dir, node, error, strategy, "implementation_loop", attempt_rows)
                    append_jsonl(decision_trace, {"time": time.time(), "event": "implementation_failed", "node": node, "strategy": strategy, "error": error})
        result["attempts"] = attempt_rows
        results.append(result)
        record_event(run_dir, "implementation_agent", result)
    report = {"items": results, "trained": train, "repair_attempts": repair_attempts, "repair_log": str(repair_log), "agent_decision_trace": str(decision_trace)}
    write_json(run_dir / "implementation_agent_report.json", report)
    print(json.dumps(report, indent=2))
    return report

def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize pending node-local model.py files and optionally train them.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--max-nodes", type=int, default=None)
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--repair-attempts", type=int, default=3)
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
