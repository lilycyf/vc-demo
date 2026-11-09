"""Explicit registration helpers. Nothing here initializes or trains a study."""
from __future__ import annotations

import copy
import importlib.metadata
import json
from pathlib import Path

from vc_demo.harness.research_contract import file_digest
from vc_demo.harness.research_v2.identity import artifact_identity


TRAINING = {'confirmation_fit_policy': 'full_development_per_seed_before_freeze',
            'seed_policy': 'registered_seed_or_explicit_replicate', 'model_parameters': {}}


def execution_files():
    root = Path(__file__).resolve().parents[1]
    files = {'provider': str(root / 't47d_provider_v2' / 'provider.py')}
    for package in ('t47d_provider_v2', 't47d_research', 't47d_full', 't47d_lineage'):
        # Bind transitive legacy imports conservatively, without editing their sources.
        for path in sorted((root / package).glob('*.py')):
            if str(path) != files['provider']:
                files[package + ':' + path.stem] = str(path)
    files['composition'] = str(root / 'harness' / 'composition.py')
    return files


def artifacts_for(config, preparation):
    from .provider import native_roles
    roles, _ = native_roles(config)
    return {role: {k: v for k, v in preparation[role].items() if k != 'sha256'} for role in roles}


def implementation(config, preparation, *, training=None, model_builder=None, extra_code=None, artifacts=None):
    """Seal effective research choices, not a proxy family template."""
    files = execution_files()
    if model_builder is not None:
        files['model_builder'] = str(Path(model_builder).resolve())
        if artifacts is None:
            raise ValueError('Agent builders must explicitly declare actual consumed artifacts')
    if extra_code:
        if set(extra_code) & set(files):
            raise ValueError('Extra code roles cannot shadow the adapter or sealed model builder')
        files.update({k: str(Path(v).resolve()) for k, v in extra_code.items()})
    resources = artifacts_for(config, preparation) if artifacts is None else copy.deepcopy(artifacts)
    environment = {p: importlib.metadata.version(p) for p in
                   ('torch', 'pandas', 'joblib', 'xgboost', 'anndata')}
    recipe = {'parameters': {'model_config': copy.deepcopy(config)},
        'training': copy.deepcopy(TRAINING if training is None else training),
        'code_sha256': {r: file_digest(Path(p)) for r, p in files.items()},
        'input_sha256': {r: v['sha256'] for r, v in preparation['development_inputs'].items()},
        'artifact_sha256': {r: artifact_identity(v['path']) for r, v in resources.items()},
        'environment': environment}
    return {'execution': {'code_files': files, 'artifact_files': resources}, 'recipe': recipe}


def make_task_spec(preparation, *, budget, policy, resources, minimum_effect):
    """Register the full inherited baseline suite; require caller-owned budgets."""
    p = json.loads(Path(preparation).read_text()) if isinstance(preparation, (str, Path)) else preparation
    if p.get('schema_version') != 't47d_provider_v2' or p.get('prior_test_exposure') is not True:
        raise ValueError('Use source-backed preparation and retain historical test exposure')
    for path, info in p['source_files'].items():
        if file_digest(Path(path)) != info['sha256']:
            raise ValueError('Prepared source content changed: ' + path)
    configs = {
        'root_historical_exact_ridge': {'model': 'historical_ridge',
            'historical_recipe': copy.deepcopy(p['historical_ridge_config']),
            'composition': 'replace', 'representation': p['historical_ridge_config']['representation']},
        'root_frequency': {'model': 'frequency', 'representation': 'pathway', 'baseline_only': True},
        'root_ridge': {'model': 'ridge', 'representation': 'pathway', 'baseline_only': True, 'alpha': 100},
        'root_early_elastic': {'model': 'early_elastic', 'representation': 'pseudobulk', 'baseline_only': True},
        'root_pls': {'model': 'pls', 'representation': 'pathway', 'baseline_only': True, 'components': 3},
        'root_xgboost': {'model': 'xgboost', 'representation': 'pca'}}
    recipes = {name: implementation(config, p)['recipe'] for name, config in configs.items()}
    return {'schema_version': 'research_v2', 'task_id': 'T47D_GSE260703_clone_selection',
        'dataset_sha256': p['dataset_sha256'], 'split_sha256': p['split_sha256'],
        'label_semantics': p['task_contract']['label'] + '; sampling non-detection is not extinction; relative not absolute growth',
        'input_policy': 'clone-heldout; days 0/1/4 only; endpoint metadata excluded; all learned transformations train-fold-only',
        'prior_test_exposure': True,
        'metric': {'name': 'spearman', 'direction': 'maximize', 'aggregation': 'mean_seed',
                   'prediction_unit': 'clone_x_treatment', 'group_key': 'clone_id'},
        'development_contract': p['development_contract'],
        'confirmation_contract': p['confirmation_contract'], 'inputs': p['development_inputs'],
        'benchmarks': list(configs), 'benchmark_recipes': recipes, 'reference_benchmark': 'root_historical_exact_ridge',
        'budget': copy.deepcopy(budget), 'policy': copy.deepcopy(policy), 'resources': copy.deepcopy(resources),
        'minimum_effect': minimum_effect}
