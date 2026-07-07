from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


OFFICIAL_BEST_NODE = Path("/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py")
OFFICIAL_TASK_DIR = Path("data/cell_lines/official_k562_cls")
AIDO_DIR = Path("/home/Models/AIDO.Cell-100M")
STRING_GNN_DIR = Path("/home/Models/STRING_GNN")
MODELGENERATOR_AIDO_SOURCE = Path("/workspace/_external/ModelGenerator/huggingface/aido.cell")


def import_status(name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(name)
    except Exception as exc:
        return {"name": name, "available": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "available": bool(spec), "origin": spec.origin if spec else None}


def parse_constants(path: Path) -> dict[str, Any]:
    constants: dict[str, Any] = {}
    if not path.exists():
        return constants
    tree = ast.parse(path.read_text(errors="replace"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    try:
                        constants[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        constants[target.id] = ast.unparse(node.value) if hasattr(ast, "unparse") else "<expr>"
    return constants


def file_row(path: Path, required: bool = True) -> dict[str, Any]:
    return {
        "path": str(path),
        "required": required,
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        "is_dir": path.is_dir(),
    }


def model_dir_status(path: Path, expected_repo: str) -> dict[str, Any]:
    files = sorted(str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()) if path.exists() else []
    tokenizer_candidates = {
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "sentencepiece.bpe.model",
        "spiece.model",
    }
    weight_candidates = {"model.safetensors", "pytorch_model.bin", "model.bin"}
    warnings: list[str] = []
    if not path.exists():
        warnings.append("model directory missing")
    if not weight_candidates.intersection(files):
        warnings.append("no common model weight file detected")
    if expected_repo == "genbio-ai/AIDO.Cell-100M" and not tokenizer_candidates.intersection(files):
        warnings.append("no tokenizer files detected, but public VCHarness node calls AutoTokenizer.from_pretrained")
    if expected_repo == "genbio-ai/STRING_GNN" and not files:
        warnings.append("STRING_GNN directory absent; public HF model repo currently exposes no weights")
    return {
        "path": str(path),
        "expected_repo": expected_repo,
        "exists": path.exists(),
        "files": files,
        "has_config": "config.json" in files,
        "has_weight": bool(weight_candidates.intersection(files)),
        "tokenizer_files": sorted(tokenizer_candidates.intersection(files)),
        "warnings": warnings,
    }


def task_status(path: Path) -> dict[str, Any]:
    files = [path / name for name in ["train.tsv", "val.tsv", "test.tsv", "target_genes.tsv", "manifest.json"]]
    rows = {p.name: file_row(p) for p in files}
    manifest = {}
    if (path / "manifest.json").exists():
        manifest = json.loads((path / "manifest.json").read_text())
    return {
        "path": str(path),
        "files": rows,
        "manifest_summary": {
            "format": manifest.get("format"),
            "split_sizes": manifest.get("split_sizes"),
            "n_target_genes": manifest.get("n_target_genes"),
            "alignment": manifest.get("official_vcharness_alignment"),
        },
    }


def transformers_api_status() -> dict[str, Any]:
    result: dict[str, Any] = {}
    try:
        transformers = importlib.import_module("transformers")
        result["version"] = getattr(transformers, "__version__", "unknown")
    except Exception as exc:
        result["available"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    result["available"] = True
    try:
        pytorch_utils = importlib.import_module("transformers.pytorch_utils")
        result["has_find_pruneable_heads_and_indices"] = hasattr(pytorch_utils, "find_pruneable_heads_and_indices")
    except Exception as exc:
        result["pytorch_utils_error"] = f"{type(exc).__name__}: {exc}"
    return result


def attempt_transformers_load(aido_dir: Path, load_model_weights: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"attempted": True, "entrypoint": "transformers.Auto*"}
    try:
        transformers = importlib.import_module("transformers")
        result["transformers_version"] = getattr(transformers, "__version__", "unknown")
    except Exception as exc:
        result["status"] = "blocked"
        result["error"] = f"cannot import transformers: {type(exc).__name__}: {exc}"
        return result
    try:
        AutoConfig = getattr(transformers, "AutoConfig")
        cfg = AutoConfig.from_pretrained(str(aido_dir), trust_remote_code=True)
        result["auto_config"] = {"ok": True, "model_type": getattr(cfg, "model_type", None), "hidden_size": getattr(cfg, "hidden_size", None)}
    except Exception as exc:
        result["auto_config"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        AutoTokenizer = getattr(transformers, "AutoTokenizer")
        tok = AutoTokenizer.from_pretrained(str(aido_dir), trust_remote_code=True)
        result["auto_tokenizer"] = {"ok": True, "class": tok.__class__.__name__}
    except Exception as exc:
        result["auto_tokenizer"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if load_model_weights:
        try:
            AutoModel = getattr(transformers, "AutoModel")
            model = AutoModel.from_pretrained(str(aido_dir), trust_remote_code=True)
            result["auto_model"] = {"ok": True, "class": model.__class__.__name__}
        except Exception as exc:
            result["auto_model"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return result


def attempt_modelgenerator_aido_load(source_dir: Path, aido_dir: Path, load_model_weights: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {
        "attempted": True,
        "entrypoint": "ModelGenerator aido_cell CellFoundation* classes",
        "source_dir": str(source_dir),
        "source_dir_exists": source_dir.exists(),
    }
    if not source_dir.exists():
        result["status"] = "blocked"
        result["error"] = "ModelGenerator AIDO source directory missing"
        return result

    sys.path.insert(0, str(source_dir))
    try:
        from aido_cell.models import CellFoundationConfig, CellFoundationModel
        from aido_cell.models.modeling_cellfoundation import CellFoundationForMaskedLM
    except Exception as exc:
        result["status"] = "blocked"
        result["import_error"] = f"{type(exc).__name__}: {exc}"
        return result

    try:
        cfg = CellFoundationConfig.from_pretrained(str(aido_dir))
        result["config"] = {
            "ok": True,
            "model_type": getattr(cfg, "model_type", None),
            "hidden_size": getattr(cfg, "hidden_size", None),
            "num_hidden_layers": getattr(cfg, "num_hidden_layers", None),
            "num_attention_heads": getattr(cfg, "num_attention_heads", None),
            "max_position_embeddings": getattr(cfg, "max_position_embeddings", None),
        }
    except Exception as exc:
        result["config"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        return result

    if load_model_weights:
        for name, cls in [("CellFoundationModel", CellFoundationModel), ("CellFoundationForMaskedLM", CellFoundationForMaskedLM)]:
            try:
                model = cls.from_pretrained(str(aido_dir), config=cfg, low_cpu_mem_usage=True)
                result[name] = {"ok": True, "class": model.__class__.__name__}
                del model
            except Exception as exc:
                result[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    result["status"] = "ok" if all(v.get("ok", True) for k, v in result.items() if isinstance(v, dict)) else "blocked"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether the public VCHarness K562 best node can run in this environment.")
    parser.add_argument("--official-code", type=Path, default=OFFICIAL_BEST_NODE)
    parser.add_argument("--task-dir", type=Path, default=OFFICIAL_TASK_DIR)
    parser.add_argument("--aido-dir", type=Path, default=AIDO_DIR)
    parser.add_argument("--string-gnn-dir", type=Path, default=STRING_GNN_DIR)
    parser.add_argument("--modelgenerator-aido-source", type=Path, default=MODELGENERATOR_AIDO_SOURCE)
    parser.add_argument("--attempt-load", action="store_true")
    parser.add_argument("--attempt-modelgenerator-aido-load", action="store_true")
    parser.add_argument("--load-model-weights", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    imports = [
        import_status(name)
        for name in [
            "torch",
            "numpy",
            "pandas",
            "anndata",
            "scanpy",
            "lightning",
            "lightning.pytorch",
            "transformers",
            "peft",
            "safetensors",
        ]
    ]
    constants = parse_constants(args.official_code)
    checks = {
        "official_code": file_row(args.official_code),
        "official_constants": {k: constants.get(k) for k in ["N_GENES", "N_CLASSES", "AIDO_GENES", "AIDO_MODEL_DIR", "STRING_MODEL_DIR", "AIDO_HIDDEN", "STRING_HIDDEN", "NEIGHBOR_K", "N_ATTN_HEADS", "CLASS_FREQ"]},
        "task": task_status(args.task_dir),
        "aido_model_dir": model_dir_status(args.aido_dir, "genbio-ai/AIDO.Cell-100M"),
        "string_gnn_model_dir": model_dir_status(args.string_gnn_dir, "genbio-ai/STRING_GNN"),
        "modelgenerator_aido_source": file_row(args.modelgenerator_aido_source),
        "imports": imports,
        "transformers_api": transformers_api_status(),
    }
    if args.attempt_load:
        checks["transformers_load"] = attempt_transformers_load(args.aido_dir, load_model_weights=args.load_model_weights)
    if args.attempt_modelgenerator_aido_load:
        checks["modelgenerator_aido_load"] = attempt_modelgenerator_aido_load(
            args.modelgenerator_aido_source,
            args.aido_dir,
            load_model_weights=True,
        )

    blockers: list[str] = []
    for row in imports:
        if row["name"] in {"anndata", "scanpy", "lightning", "lightning.pytorch", "transformers", "peft"} and not row.get("available"):
            blockers.append(f"missing Python dependency: {row['name']}")
    api = checks["transformers_api"]
    if api.get("available") and not api.get("has_find_pruneable_heads_and_indices", False):
        blockers.append("transformers API incompatible with ModelGenerator AIDO.Cell source: missing find_pruneable_heads_and_indices")
    if checks["aido_model_dir"]["warnings"]:
        blockers.extend(f"AIDO model dir: {w}" for w in checks["aido_model_dir"]["warnings"])
    if checks["string_gnn_model_dir"]["warnings"]:
        blockers.extend(f"STRING_GNN model dir: {w}" for w in checks["string_gnn_model_dir"]["warnings"])
    if args.attempt_load:
        load = checks.get("transformers_load", {})
        if load.get("status") == "blocked":
            blockers.append(load.get("error", "transformers load blocked"))
        for key in ["auto_config", "auto_tokenizer", "auto_model"]:
            value = load.get(key)
            if isinstance(value, dict) and not value.get("ok", True):
                blockers.append(f"{key} failed: {value.get('error')}")
    if args.attempt_modelgenerator_aido_load:
        direct = checks.get("modelgenerator_aido_load", {})
        if direct.get("status") != "ok":
            blockers.append("ModelGenerator AIDO direct load failed")

    result = {
        "status": "blocked" if blockers else "compatible",
        "blockers": blockers,
        "checks": checks,
        "interpretation": (
            "This is a pre-training compatibility check. It distinguishes the public best-node "
            "AutoModel/AutoTokenizer entrypoint from the official ModelGenerator AIDO.Cell direct "
            "classes. Passing the direct AIDO load is necessary but not sufficient to run the public "
            "best node unchanged."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
