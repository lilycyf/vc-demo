"""Task-neutral research boundaries and content-addressed executable recipes."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


class ResearchContractError(ValueError):
    pass


def digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_digest(path: Path) -> str:
    if not path.is_file():
        raise ResearchContractError(f"Required recipe file is missing: {path}")
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write_record(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    import uuid
    temporary = path.with_suffix(path.suffix + '.' + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def freeze_record(path: Path, value: dict[str, Any]) -> str:
    import fcntl
    identity = digest(value)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.with_suffix(path.suffix+'.lock').open('a') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        if path.exists():
            existing = json.loads(path.read_text())
            if digest(existing) != identity:
                raise ResearchContractError(f"Frozen contract changed: {path}; register a new run, do not overwrite")
        else:
            write_record(path, value)
    return identity


_REPORT_KEYS = {
    "test", "test_macro_f1", "test_loss", "test_metrics", "best_test_macro_f1",
    "best_root_test", "best_child_test", "best_root_test_macro_f1", "parent_test_macro_f1",
    "mean_test", "std_test", "heldout_metrics", "confirmation_metrics", "test_lift",
}


def selection_context(value: Any) -> Any:
    """Return only development-facing information, including nested legacy state."""
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            lower = str(key).lower()
            if lower in _REPORT_KEYS or set(lower.split('_')) & {'test','heldout','confirmation'}:
                continue
            if key == "framework_feedback" and isinstance(item, dict) and item.get("evidence_phase") != "development":
                continue
            clean[key] = selection_context(item)
        return clean
    if isinstance(value, list):
        return [selection_context(item) for item in value]
    return copy.deepcopy(value)


def task_data_config(config):
    data,dataset=config.get('data'),config.get('dataset')
    if data and dataset and data!=dataset:raise ResearchContractError('Conflicting data/dataset contracts')
    result=data or dataset
    if not isinstance(result,dict) or not result.get('dataset_type'):
        raise ResearchContractError('Dataset adapter must be explicit; implicit synthetic fallback is forbidden')
    return result


def assert_search_open(run_dir: Path) -> None:
    if (run_dir / "confirmation_lock.json").exists():
        raise ResearchContractError("Confirmation was opened; this run is closed to further model selection")


def freeze_selection(run_dir: Path, selection: Path) -> dict[str, Any]:
    if not selection.is_file():
        raise ResearchContractError("Freeze the selected recipe(s) before opening confirmation")
    chosen=json.loads(selection.read_text()).get('recipe_fingerprints',{})
    if not chosen:raise ResearchContractError('Selection must name actual executable recipe_fingerprints')
    budget_path=run_dir/'research_budget_plan.json'
    if budget_path.exists() and len(chosen)>json.loads(budget_path.read_text())['confirmation_limit']:
        raise ResearchContractError('Frozen models exceed the declared confirmation budget')
    recipes={}
    checkpoints={}
    for name,expected in chosen.items():
        path=run_dir/'execution_recipes'/(name+'.json')
        if Path(name).name!=name or not path.is_file():raise ResearchContractError('Selected recipe is missing or unsafe')
        recipe=json.loads(path.read_text())
        if recipe['fingerprint']!=expected:raise ResearchContractError('Selected fingerprint does not match executed recipe')
        assert_recipe_files(recipe);recipes[name]=recipe
        checkpoint=run_dir/'nodes'/name/'best.pt'
        if checkpoint.is_file():
            checkpoints[name]={'path':str(checkpoint.resolve()),'sha256':file_digest(checkpoint)}
    result = {"format": "vc_demo_confirmation_lock.v1", "selection_path": str(selection.resolve()),
              "selection_sha256": file_digest(selection), "recipe_fingerprints":chosen,
              "recipes":recipes,"checkpoints":checkpoints,"further_search_allowed": False}
    freeze_record(run_dir / "confirmation_lock.json", result)
    return result


def evaluation_policy(config: dict[str, Any], run_dir: Path | None = None) -> tuple[str, bool]:
    evaluation = config.get("evaluation", {})
    phase = evaluation.get("phase", "search")
    if phase not in {"search", "coverage", "confirmation"}:
        raise ResearchContractError(f"Unknown evaluation phase: {phase}")
    requested = evaluation.get("evaluate_test", phase == "confirmation")
    if phase != "confirmation":
        if requested:
            raise ResearchContractError("Test metrics cannot be requested during search or coverage")
        if run_dir is not None:
            assert_search_open(run_dir)
        return phase, False
    lock_path = Path(evaluation.get("confirmation_lock_path", str(run_dir / "confirmation_lock.json") if run_dir else ""))
    if not lock_path.is_file():
        raise ResearchContractError("Confirmation requires a frozen-selection lock")
    lock = json.loads(lock_path.read_text())
    if file_digest(Path(lock["selection_path"])) != lock["selection_sha256"]:
        raise ResearchContractError("Frozen selection changed after confirmation was opened")
    if str(config.get('node_name')) not in lock.get('recipe_fingerprints',{}):
        raise ResearchContractError('This model was not selected before confirmation')
    return phase, bool(requested)


def executable_recipe(config: dict[str, Any], *, code_files: list[Path], data_files: list[Path],
                      artifact_files: list[Path] = (), environment: dict[str, Any] | None = None,
                      max_epochs: int | None = None) -> dict[str, Any]:
    effective = copy.deepcopy(config)
    effective.pop("node_name", None)
    effective.pop("output_dir", None)
    evaluation = effective.setdefault("evaluation", {})
    for key in ("phase", "evaluate_test", "confirmation_lock_path"):
        evaluation.pop(key, None)
    if max_epochs is not None:
        if max_epochs < 1:
            raise ResearchContractError("Training budget must be positive")
        effective.setdefault("training", {})["epochs"] = max_epochs
    files = lambda paths: {str(p.resolve()): file_digest(p) for p in sorted(set(map(Path, paths)))}
    value = {"format": "vc_demo_executable_recipe.v1", "effective_config": effective,
             "code_sha256": files(code_files), "data_sha256": files(data_files),
             "artifact_sha256": files(artifact_files), "environment": environment or {}}
    return {**value, "fingerprint": digest(value)}


def assert_recipe_files(recipe: dict[str, Any]) -> None:
    for group in ("code_sha256", "data_sha256", "artifact_sha256"):
        for name, expected in recipe.get(group, {}).items():
            if file_digest(Path(name)) != expected:
                raise ResearchContractError(f"Recipe content drift in {group}: {name}")


def register_benchmark(run_dir: Path, name: str, recipe: dict[str, Any]) -> None:
    if not name or Path(name).name != name:
        raise ResearchContractError("Benchmark name must be a single safe path component")
    freeze_record(run_dir / "benchmarks" / (name + ".json"), recipe)


def verify_benchmarks(run_dir: Path) -> None:
    for path in (run_dir / "benchmarks").glob("*.json"):
        assert_recipe_files(json.loads(path.read_text()))
    protocol_path=run_dir/'research_protocol.json'
    if protocol_path.exists():
        protocol=json.loads(protocol_path.read_text())
        for name,expected in protocol.get('required_benchmarks',{}).items():
            path=run_dir/'benchmarks'/(name+'.json')
            if not path.is_file():raise ResearchContractError('Required historical benchmark was omitted: '+name)
            if json.loads(path.read_text())['fingerprint']!=expected:
                raise ResearchContractError('Required benchmark recipe differs: '+name)


def capture_execution_recipe(config: dict[str, Any], run_dir: Path, *, is_benchmark=False, max_epochs=None):
    """Bind a real executor invocation to its inputs, code and effective budget."""
    import importlib.metadata
    if not is_benchmark:verify_benchmarks(run_dir)
    data=task_data_config(config)
    research=config.get('research',{})
    data_files=[Path(p) for p in research.get('data_files',[])]
    data_dir=Path(str(data.get('data_dir','')))
    if str(data.get('data_dir','')):
        if not data_dir.is_dir():raise ResearchContractError('Declared data directory is missing')
        for pattern in ('*.npz','*.tsv','*manifest.json','*contract.json','*splits.json'):
            data_files.extend(data_dir.glob(pattern))
    for key in ('train_path','val_path','test_path','train_tsv','val_tsv','test_tsv','embedding_h5ad'):
        if data.get(key):data_files.append(Path(data[key]))
    data_files.extend(Path(p) for p in data.get('embedding_h5ads',[]))
    if data.get('dataset_type')!='synthetic' and not data_files:
        raise ResearchContractError('Real tasks must declare content-addressed input files')
    code_files=list(Path('src/vc_demo').rglob('*.py'))
    code_files.extend(Path(p) for p in research.get('code_files',[]))
    custom=config.get('model',{}).get('custom_model_path')
    if custom:code_files.append(Path(custom))
    artifacts=[Path(p) for p in research.get('artifact_files',[])]
    def declared_paths(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if isinstance(item,str) and item and key.endswith(('_path','_dir','_file')) and item!='auto':
                    p=Path(item)
                    if not p.exists():raise ResearchContractError('Declared artifact missing: '+item)
                    artifacts.extend([p] if p.is_file() else [f for f in p.rglob('*') if f.is_file()])
                elif isinstance(item,(dict,list)):declared_paths(item)
        elif isinstance(value,list):
            for item in value:declared_paths(item)
    declared_paths(config.get('model',{}).get('artifacts',{}))
    effective=copy.deepcopy(config)
    training=effective.setdefault('training',{})
    for key,value in {'epochs':8,'batch_size':16,'lr':3e-4,'weight_decay':1e-4,'loss_type':'cross_entropy'}.items():
        training.setdefault(key,value)
    versions={}
    for package in ('numpy','torch','scikit-learn'):
        try:versions[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:continue
    recipe=executable_recipe(effective,code_files=code_files,data_files=data_files,
        artifact_files=artifacts,environment=versions,max_epochs=max_epochs)
    name=str(config['node_name'])
    if Path(name).name!=name:raise ResearchContractError('Invalid node name')
    if is_benchmark:register_benchmark(run_dir,name,recipe)
    freeze_record(run_dir/'execution_recipes'/(name+'.json'),recipe)
    return recipe


def validate_hypothesis(proposal: dict[str, Any]) -> dict[str, Any]:
    required = ("hypothesis", "evidence_refs", "expected_change", "falsification", "composition", "training_policy")
    missing = [key for key in required if not proposal.get(key)]
    if missing:
        raise ResearchContractError("Incomplete research proposal: " + ", ".join(missing))
    if proposal["composition"] not in {"replace", "feature_fusion", "joint", "crossfit_residual", "crossfit_stack", "ablation"}:
        raise ResearchContractError("Unknown composition relation")
    return selection_context(proposal)


def validate_protocol(protocol: dict[str, Any]) -> dict[str, Any]:
    required = ("task_id", "dataset_sha256", "split_sha256", "label_semantics", "metric", "group_key", "input_policy")
    missing = [name for name in required if not protocol.get(name)]
    if missing:
        raise ResearchContractError("Missing task protocol fields: " + ", ".join(missing))
    if protocol["metric"].get("direction") not in {"maximize", "minimize"}:
        raise ResearchContractError("Metric direction must be explicit")
    return copy.deepcopy(protocol)


def register_protocol(run_dir: Path, protocol: dict[str, Any]) -> None:
    assert_search_open(run_dir)
    protocol = validate_protocol(protocol)
    freeze_record(run_dir / 'research_protocol.json', protocol)
    freeze_record(run_dir / 'research_protocol_identity.json', {'sha256': digest(protocol)})


def verify_protocol(run_dir: Path) -> dict[str, Any]:
    path = run_dir / 'research_protocol.json'
    identity = run_dir / 'research_protocol_identity.json'
    if not path.is_file() or not identity.is_file():
        raise ResearchContractError('Register the task protocol using research_contract --protocol before search')
    protocol = validate_protocol(json.loads(path.read_text()))
    if digest(protocol) != json.loads(identity.read_text()).get('sha256'):
        raise ResearchContractError('Registered scientific task contract changed; use a new run')
    return protocol


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--freeze-selection", type=Path)
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args()
    if args.protocol:
        protocol = validate_protocol(json.loads(args.protocol.read_text()))
        register_protocol(args.run_dir, protocol)
    if args.freeze_selection:
        freeze_selection(args.run_dir, args.freeze_selection)
    verify_benchmarks(args.run_dir)
    print(json.dumps({"passed": True, "run_dir": str(args.run_dir)}))


if __name__ == "__main__":
    main()
