from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vc_demo.harness.artifact_registry import audit_registry, load_registry
from vc_demo.official_k562.contract import validate_official_k562_task
from vc_demo.harness.paper_level_guardrails import config_proxy_violations


@dataclass(frozen=True)
class OfficialK562BackendSpec:
    data_dir: Path = Path("data/cell_lines/official_k562_cls")
    registry_path: Path = Path("configs/artifacts/k562_registry.json")
    root_configs: tuple[Path, ...] = (
        Path("configs/official_k562_root_aido_embedding_mlp.json"),
        Path("configs/official_k562_root_aido_gnn_embedding_mlp.json"),
        Path("configs/official_k562_public_best_node.json"),
    )
    # If empty, required artifacts are inferred from the selected root configs.
    # This lets loop-only K562 self-tests train embedding roots without being
    # blocked by the external public-best wrapper's STRING_GNN checkpoint.
    required_artifacts: tuple[str, ...] = ()


def _read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)



def _infer_required_artifacts_from_config(config_path: Path, cfg: dict[str, Any]) -> set[str]:
    required = {"official_essential_deg_with_split_h5ad"}
    data = cfg.get("data", {}) if isinstance(cfg.get("data"), dict) else {}
    model = cfg.get("model", {}) if isinstance(cfg.get("model"), dict) else {}
    execution = cfg.get("execution", {}) if isinstance(cfg.get("execution"), dict) else {}

    embedding_paths: list[str] = []
    if data.get("embedding_h5ad"):
        embedding_paths.append(str(data["embedding_h5ad"]))
    embedding_paths.extend(str(p) for p in data.get("embedding_h5ads", []) if p)
    for path in embedding_paths:
        lower = path.lower()
        if "aidocell_100m" in lower or "aido" in lower:
            required.add("official_k562_aido_cell_100m_embedding_h5ad")
        if "gnn_simple" in lower or "gnn" in lower:
            required.add("official_gnn_simple_embedding_h5ad")

    if execution.get("backend") == "external_static_node" or model.get("model_type") == "external_static_node":
        required.update({
            "official_aido_cell_100m_model_dir",
            "official_string_gnn_model_dir",
            "official_public_best_node_code",
        })

    artifact_usage = execution.get("artifact_usage", {})
    if isinstance(artifact_usage, dict):
        for key, value in artifact_usage.items():
            combined = f"{key} {value}".lower()
            if "aido.cell-100m" in combined or "/home/models/aido" in combined:
                required.add("official_aido_cell_100m_model_dir")
            if "string_gnn" in combined or "/home/models/string_gnn" in combined:
                required.add("official_string_gnn_model_dir")
            if "public_node_code" in combined or "vcharness" in combined:
                required.add("official_public_best_node_code")

    explicit = cfg.get("required_artifacts", [])
    if isinstance(explicit, list):
        required.update(str(item) for item in explicit)
    return required


def _infer_required_artifacts(root_configs: tuple[Path, ...], explicit: tuple[str, ...]) -> tuple[str, ...]:
    if explicit:
        return explicit
    required: set[str] = set()
    for config_path in root_configs:
        if config_path.exists():
            try:
                required.update(_infer_required_artifacts_from_config(config_path, _read_json(config_path)))
            except Exception:
                required.add("official_essential_deg_with_split_h5ad")
        else:
            required.add("official_essential_deg_with_split_h5ad")
    return tuple(sorted(required))

def _artifact_by_id(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in audit.get("artifacts", [])}


def validate_official_k562_backend(spec: OfficialK562BackendSpec | None = None, *, strict: bool = True) -> dict[str, Any]:
    """Validate the repo-side backend used to run official K562 search.

    This is intentionally narrower than the public VCHarness best-node smoke. It
    checks the task contract, official root configs, and required public
    artifacts needed by the vc_demo MCTS harness roots. The external public best
    node remains a compatibility benchmark, while this backend is the bridge that
    lets vc_demo.program_run search on the official K562 data contract.
    """

    spec = spec or OfficialK562BackendSpec()
    issues: list[str] = []
    data_result = validate_official_k562_task(spec.data_dir, strict=False)
    if data_result.get("status") != "passed":
        issues.extend([f"data_contract:{issue}" for issue in data_result.get("issues", [])])

    registry = load_registry(spec.registry_path, "K562")
    audit = audit_registry(registry)
    artifacts = _artifact_by_id(audit)
    missing_required: list[dict[str, Any]] = []
    required_artifacts = _infer_required_artifacts(spec.root_configs, spec.required_artifacts)
    for artifact_id in required_artifacts:
        item = artifacts.get(artifact_id)
        if not item:
            issues.append(f"registry missing artifact id {artifact_id}")
            missing_required.append({"id": artifact_id, "reason": "not_in_registry"})
        elif not item.get("present"):
            issues.append(f"required artifact {artifact_id} is missing at {item.get('path')}")
            missing_required.append(item)

    root_results: list[dict[str, Any]] = []
    for config_path in spec.root_configs:
        row: dict[str, Any] = {"path": str(config_path), "present": config_path.exists()}
        if not config_path.exists():
            issues.append(f"missing root config {config_path}")
            root_results.append(row)
            continue
        cfg = _read_json(config_path)
        row["node_name"] = cfg.get("node_name")
        row["dataset_type"] = cfg.get("data", {}).get("dataset_type")
        row["data_dir"] = cfg.get("data", {}).get("data_dir")
        row["embedding_h5ad"] = cfg.get("data", {}).get("embedding_h5ad")
        row["embedding_h5ads"] = cfg.get("data", {}).get("embedding_h5ads", [])
        row["execution_backend"] = cfg.get("execution", {}).get("backend", "native_train")
        row["script_path"] = cfg.get("execution", {}).get("script_path", "")
        if row["dataset_type"] != "official_k562_tsv":
            issues.append(f"root config {config_path} is not official_k562_tsv")
        if Path(str(row["data_dir"] or "")) != spec.data_dir:
            issues.append(f"root config {config_path} uses data_dir={row['data_dir']} not {spec.data_dir}")
        for emb in [row.get("embedding_h5ad"), *row.get("embedding_h5ads", [])]:
            if emb and not Path(str(emb)).exists():
                issues.append(f"root config {config_path} embedding missing: {emb}")
        proxy_violations = config_proxy_violations(cfg)
        if proxy_violations:
            issues.append(f"root config {config_path} uses forbidden compact/proxy native implementation: {', '.join(proxy_violations)}")
            row["proxy_violations"] = proxy_violations
        if row["execution_backend"] == "external_static_node":
            script = cfg.get("execution", {}).get("script_path", "")
            static_dir = Path(str(cfg.get("execution", {}).get("static_dir", "")))
            script_path = Path(str(script)) if Path(str(script)).is_absolute() else static_dir / str(script)
            if not script_path.exists():
                issues.append(f"root config {config_path} external script missing: {script_path}")
        root_results.append(row)

    result = {
        "status": "passed" if not issues else "failed",
        "backend": "official_k562_tsv_mcts_harness",
        "data_contract": data_result,
        "registry_path": str(spec.registry_path),
        "required_artifacts": list(required_artifacts),
        "missing_required_artifacts": missing_required,
        "present_artifacts": audit.get("present_artifacts", []),
        "missing_artifacts": audit.get("missing_artifacts", []),
        "root_configs": root_results,
        "issues": issues,
        "notes": [
            "This backend lets vc_demo.harness.program_run search on the official K562 TSV task.",
            "The public VCHarness best node remains a separate compatibility benchmark and may use external node code.",
            "Strict artifact mode must block or acquire missing artifacts; do not train fallback nodes for claimed official artifacts.",
            "Formal paper-level runs forbid compact/proxy native implementations; use external public static benchmark or full artifact-backed implementations.",
        ],
    }
    if strict and issues:
        raise SystemExit(json.dumps(result, indent=2))
    return result


def write_backend_report(output: Path, result: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Official K562 Harness Backend Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Backend: `{result['backend']}`",
        f"- Registry: `{result['registry_path']}`",
        f"- Data contract status: `{result['data_contract'].get('status')}`",
        f"- Required artifacts: {', '.join(result['required_artifacts'])}",
        f"- Missing required artifacts: {', '.join(item.get('id', '') for item in result['missing_required_artifacts']) or 'none'}",
        "",
        "## Root Configs",
        "",
        "| Config | Node | Dataset | Data dir | Embeddings |",
        "|---|---|---|---|---|",
    ]
    for row in result.get("root_configs", []):
        embeddings = [row.get("embedding_h5ad") or "", *row.get("embedding_h5ads", [])]
        embeddings = [str(x) for x in embeddings if x]
        lines.append(f"| `{row.get('path')}` | `{row.get('node_name', '')}` | `{row.get('dataset_type', '')}` | `{row.get('data_dir', '')}` | `{', '.join(embeddings)}` |")
    lines.extend(["", "## Issues", ""])
    if result.get("issues"):
        lines.extend(f"- {issue}" for issue in result["issues"])
    else:
        lines.append("- none")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in result.get("notes", []))
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate the official K562 backend used by vc_demo MCTS search.")
    parser.add_argument("--data-dir", type=Path, default=OfficialK562BackendSpec.data_dir)
    parser.add_argument("--registry", type=Path, default=OfficialK562BackendSpec.registry_path)
    parser.add_argument("--root-configs", nargs="*", type=Path, default=list(OfficialK562BackendSpec.root_configs))
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--strict", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    spec = OfficialK562BackendSpec(data_dir=args.data_dir, registry_path=args.registry, root_configs=tuple(args.root_configs))
    result = validate_official_k562_backend(spec, strict=args.strict)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n")
    if args.output_md:
        write_backend_report(args.output_md, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
