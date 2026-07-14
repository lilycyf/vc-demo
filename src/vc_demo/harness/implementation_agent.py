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


def materialize_model(program_dir: Path, strategy: str, allow_skip: bool = False) -> dict[str, Any]:
    model_path = program_dir / "model.py"
    try:
        source = render_program_source(strategy)
        source_kind = "harness_implemented_template"
    except Exception:
        blueprint = blueprint_by_id(strategy)
        if blueprint.get("official_k562"):
            request = program_dir / "IMPLEMENTATION_REQUEST.md"
            task = program_dir / "CODEX_IMPLEMENTATION_TASK.md"
            task.write_text(render_codex_task(strategy, request), encoding="utf-8")
            reason = "strict formal mode requires the active Codex to implement a real artifact-backed node-local model; compact/proxy native implementations are forbidden"
            if allow_skip:
                return {"status": "implementation_skipped", "strategy": strategy, "task_path": str(task), "model_path": str(model_path), "reason": reason}
            return {"status": "requires_realtime_implementation", "strategy": strategy, "task_path": str(task), "model_path": str(model_path), "reason": reason}
        try:
            source = _generic_program_source(strategy)
            source_kind = "implementation_agent_template"
        except KeyError:
            request = program_dir / "IMPLEMENTATION_REQUEST.md"
            task = program_dir / "CODEX_IMPLEMENTATION_TASK.md"
            task.write_text(render_codex_task(strategy, request), encoding="utf-8")
            reason = "no safe local template exists; the active Codex must implement a real node-local model or mark a precise artifact/contract blocker"
            if allow_skip:
                return {"status": "implementation_skipped", "strategy": strategy, "task_path": str(task), "model_path": str(model_path), "reason": reason}
            return {"status": "requires_realtime_implementation", "strategy": strategy, "task_path": str(task), "model_path": str(model_path), "reason": reason}
    model_path.write_text(source, encoding="utf-8")
    py_compile.compile(str(model_path), doraise=True)
    return {"status": "implemented", "strategy": strategy, "source_kind": source_kind, "model_path": str(model_path)}


def render_codex_task(strategy: str, request_path: Path) -> str:
    blueprint = blueprint_by_id(strategy)
    request_text = request_path.read_text(encoding="utf-8") if request_path.exists() else ""
    return "\n".join([
        f"# Codex Implementation Task: `{strategy}`",
        "",
        "Implement the pending node-local `model.py` for this blueprint as a parent-preserving child when possible.",
        "Treat the blueprint as a research delta, not as permission to discard the parent pipeline by default.",
        "Do not modify data splits, labels, metrics, or artifact files.",
        "Do not fabricate missing artifacts. If the model requires a missing artifact, stop and update acquisition queue instead.",
        "Do not implement a compact/proxy/simplified stand-in. Formal search requires a real artifact-backed implementation, but Codex may preserve parent dense/residual routes and compose the selected module competitively.",
        "Use parent_summary.json and search_memory motifs from the original request to retain useful branches unless replacement is explicitly requested.",
        "Do not import vc_demo.official_k562.native_models.OfficialK562NativeModel; that helper is smoke-only and forbidden for formal runs.",
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


def _write_implementation_queue(run_dir: Path, tree: dict[str, Any]) -> None:
    items = [
        {
            "node": name,
            "program_dir": node.get("program_dir"),
            "implementation_request_path": node.get("implementation_request_path"),
            "program_model_path": node.get("program_model_path"),
            "pipeline_manifest_path": node.get("pipeline_manifest_path"),
            "artifact_contract_path": node.get("artifact_contract_path"),
            "smoke_contract_path": node.get("smoke_contract_path"),
            "parent_summary_path": node.get("parent_summary_path"),
            "strategy": node.get("strategy"),
            "artifact_requirements": node.get("artifact_requirements", []),
            "scientific_selection": node.get("scientific_selection", {}),
            "structural_relation": node.get("structural_relation", ""),
        }
        for name, node in tree.get("nodes", {}).items()
        if node.get("status") == "needs_implementation"
    ]
    write_json(run_dir / "implementation_queue.json", {"items": items})


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
    _write_implementation_queue(run_dir, tree)


def mark_node_implementation_skipped(run_dir: Path, node_name: str, strategy: str, reason: str, task_path: str | None, attempts: list[dict[str, Any]]) -> None:
    tree_path = run_dir / "tree.json"
    tree = read_json(tree_path)
    node = tree.get("nodes", {}).get(node_name)
    if node:
        node.update({
            "status": "implementation_skipped",
            "stage": "skipped",
            "skip_reason": reason,
            "implementation_task_path": task_path or node.get("implementation_request_path"),
            "implementation_attempts": attempts,
            "requires_implementation": False,
        })
    write_json(tree_path, tree)
    _write_implementation_queue(run_dir, tree)


def pending_nodes(run_dir: Path) -> list[dict[str, Any]]:
    queue_path = run_dir / "implementation_queue.json"
    if not queue_path.exists():
        return []
    payload = read_json(queue_path)
    return list(payload.get("items", []))


def implement_pending(run_dir: Path, max_nodes: int | None = None, train: bool = False, max_epochs: int | None = None, repair_attempts: int = 3, allow_skip: bool = False) -> dict[str, Any]:
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
                impl = materialize_model(program_dir, strategy, allow_skip=allow_skip)
                row.update({"stage": "materialize", **impl})
                attempt_rows.append(row)
                append_jsonl(repair_log, {"time": time.time(), **row})
                result.update(impl)
                if impl["status"] != "implemented":
                    reason = str(impl.get("reason") or "no safe realtime implementation generated")
                    if impl["status"] == "requires_realtime_implementation":
                        row["status"] = "requires_realtime_implementation"
                        row["reason"] = reason
                        result.update({"status": "requires_realtime_implementation", "reason": reason, "task_path": impl.get("task_path"), "model_path": impl.get("model_path")})
                        append_jsonl(decision_trace, {"time": time.time(), "event": "requires_realtime_implementation", "node": node, "strategy": strategy, "task_path": impl.get("task_path"), "reason": reason})
                        break
                    row["status"] = "implementation_skipped"
                    row["skip_reason"] = reason
                    result.update({"status": "implementation_skipped", "skip_reason": reason, "task_path": impl.get("task_path"), "model_path": impl.get("model_path")})
                    mark_node_implementation_skipped(run_dir, node, strategy, reason, impl.get("task_path"), attempt_rows)
                    append_jsonl(decision_trace, {"time": time.time(), "event": "implementation_skipped", "node": node, "strategy": strategy, "task_path": impl.get("task_path"), "reason": reason})
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
    parser.add_argument("--allow-skip", action="store_true", help="Loop/self-test only: allow unimplemented nodes to be marked implementation_skipped instead of stopping for realtime Codex implementation.")
    args = parser.parse_args()
    implement_pending(args.run_dir, args.max_nodes, args.train, args.max_epochs, args.repair_attempts, allow_skip=args.allow_skip)


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
