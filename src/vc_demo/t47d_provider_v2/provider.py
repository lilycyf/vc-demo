"""Faithful development/portable frozen-prediction bridge, without a search policy."""
from __future__ import annotations

import copy
from functools import partial
import importlib.util
import json
from pathlib import Path
import sys
import warnings

import joblib
import numpy as np
from sklearn.linear_model import Ridge

from vc_demo.harness.composition import CrossFittedResidualRegressor, CrossFittedStackingRegressor
from vc_demo.harness.research_contract import file_digest, digest
from vc_demo.t47d_provider_v2.data import read_inputs
from vc_demo.t47d_research.models import ResearchCandidate, NEURAL
from vc_demo.t47d_lineage.models import View as HistoricalView
from vc_demo.t47d_full.models import FullView


def configurations(parameters, training):
    config = copy.deepcopy(parameters['model_config'])
    for key, value in training.get('model_parameters', {}).items():
        if key in config and config[key] != value:
            raise ValueError('Conflicting effective model/training parameter: ' + key)
        config[key] = value
    if training.get('confirmation_fit_policy') != 'full_development_per_seed_before_freeze':
        raise ValueError('Declare final development fits before confirmation; never fit during confirmation')
    if training.get('seed_policy') != 'registered_seed_or_explicit_replicate':
        raise ValueError('Declare and apply the registered training-seed policy')
    return config


def _query_view(model, bundle):
    """Rebuild row-aligned early queries using fitted genes/projections/scalers only."""
    view = model.view
    if isinstance(view, HistoricalView):
        return
    if not isinstance(view, FullView):
        raise ValueError('Unknown frozen view; supply a reviewed portable model_builder')
    c = view.c
    rep = c.get('representation', 'pathway')
    if rep in {'pseudobulk', 'pca', 'expression', 'both', 'matched_no_artifact'}:
        source = bundle['pseudobulk'] if rep == 'pseudobulk' else bundle['expression']
        source = source[:, :, view.genes]
        if rep == 'both':
            source = np.concatenate([source, bundle['pathway']], axis=-1)
        if rep == 'matched_no_artifact':
            source = source @ view.random_projection
        if rep == 'pca':
            shape = source.shape
            source = view.pca.transform(source.reshape(-1, shape[-1])).reshape(shape[0], 3, -1)
    elif rep == 'pathway':
        source = bundle['pathway']
    else:
        raise ValueError('Legacy fold cache has no frozen query transform; implement a sealed portable model_builder now')
    if c.get('no_barcode_inputs'):
        source = np.asarray([model.query_treatment_means[t] for t in bundle['meta'].treatment])
    view.source = source
    if c.get('model') == 'additive_null':
        model.lookup = {(r.clone_id, r.treatment): i for i, r in bundle['meta'].iterrows()}


def native_roles(config):
    artifact = set()
    modules = set()
    for c in [config, *([config['parent_config']] if config.get('parent_config') else [])]:
        rep = c.get('historical_recipe', c).get('representation', 'pathway')
        if c.get('historical_recipe') and (c.get('remove_pathway') or c.get('representation') == 'matched_no_artifact'):
            rep = 'expression'
        if c['model'] == 'frequency':
            rep = 'early_abundance'
        if rep in {'pathway', 'both'} or (c['model'] in NEURAL and c.get('loss') == 'multitask'
                and not c.get('no_pathway_supervision') and not c.get('auxiliary_no_artifact')):
            artifact.add('hallmark')
        modules.add('model:' + c['model'])
        modules.add('representation:' + rep)
    return sorted(artifact), sorted(modules)


class PortableNative:
    def __init__(self, config):
        self.config = copy.deepcopy(config)

    def fit(self, bundle, idx, seed):
        c = self.config
        rep = c.get('historical_recipe', c).get('representation', 'pathway')
        if rep not in {'pathway', 'pseudobulk', 'pca', 'expression', 'both', 'matched_no_artifact'}:
            raise ValueError('Implement a portable train-only representation model_builder; do not reuse a legacy row cache')
        if c['model'] not in NEURAL | {'historical_ridge', 'frequency', 'ridge', 'early_elastic', 'pls', 'xgboost', 'additive_null'}:
            raise ValueError('Implement the actual model_builder; do not let an unknown model become a generic network')
        if c['model'] == 'historical_ridge' and c.get('historical_recipe', {}).get('model') != 'ridge':
            raise ValueError('Exact historical Ridge requires its complete genuine recipe')
        if c.get('composition', 'replace') != 'replace' or c.get('parent_config'):
            raise ValueError('Native component must be standalone; shared grouped OOF owns explicit composition')
        self.model = ResearchCandidate(c).fit(bundle, idx, seed)
        core = self.model.model
        if isinstance(getattr(core, 'view', None), FullView) and c.get('no_barcode_inputs'):
            source = core.view.source
            core.query_treatment_means = {t: source[[i for i in idx if bundle['meta'].iloc[i].treatment == t]].mean(0)
                                          for t in bundle['meta'].treatment.unique()}
        self.artifact_roles, self.module_roles = native_roles(c)
        self.losses = list(getattr(core, 'losses', []))
        return self

    def predict(self, bundle, idx):
        _query_view(self.model.model, bundle)
        return self.model.predict(bundle, idx)

    def close(self):
        self.model.close()


def _builder(request):
    info = request['execution']['code_files']
    if 'model_builder' not in info:
        return PortableNative
    path = Path(info['model_builder'])
    if file_digest(path) != request['recipe']['code_sha256']['model_builder']:
        raise ValueError('Agent model_builder source changed')
    name = 't47d_v2_builder_' + file_digest(path)[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if not callable(getattr(module, 'build_model', None)):
        raise ValueError('A sealed model_builder must expose build_model(config, *, artifact_files)')
    # Locations belong to sealed execution, not scientific parameter strings or hardcoded paths.
    return partial(module.build_model, artifact_files=copy.deepcopy(request['execution'].get('artifact_files', {})))


def _safe_bundle(bundle, indices, targets):
    result = dict(bundle)
    result['meta'] = bundle['meta'].copy()
    result['meta']['label'] = np.nan
    result['meta'].loc[indices, 'label'] = np.asarray(targets)
    # Residual responses and true auxiliary-task responses have different semantics.
    result['truth_meta'] = bundle.get('truth_meta', result['meta']).copy()
    result['truth_meta'].loc[~result['truth_meta'].index.isin(indices), 'label'] = np.nan
    # No n_day26, fraction_day26 or raw source files enter a model.
    return result


class IndexEstimator:
    """A grouped-composition estimator with a portable bundle prediction interface."""
    def __init__(self, config, bundle, seed, builder, records):
        self.config, self.bundle, self.seed, self.builder, self.records = config, bundle, seed, builder, records

    def fit(self, x, y, groups=None):
        idx = np.asarray(x, dtype=int).ravel()
        b = _safe_bundle(self.bundle, idx, y)
        self.model = self.builder(copy.deepcopy(self.config)).fit(b, idx, self.seed)
        roles = getattr(self.model, 'artifact_roles', None)
        modules = getattr(self.model, 'module_roles', None)
        if roles is None or modules is None:
            raise ValueError('Real builders must report artifact_roles and module_roles from their actual implementation')
        losses = list(getattr(self.model, 'losses', []))
        fit_groups = sorted(set(b['meta'].iloc[idx].clone_id))
        self.records.append({'group_count': len(fit_groups), 'groups_sha256': digest(fit_groups),
            'artifact_roles': list(roles), 'module_roles': list(modules),
            'last_train_loss': float(losses[-1]) if losses else None,
            'training_steps': len(losses) if losses else None})
        self.bundle = b
        if hasattr(self.model, 'close'):
            self.model.close()
        return self

    def predict(self, x):
        pred = np.asarray(self.model.predict(self.bundle, np.asarray(x, dtype=int).ravel()))
        if pred.shape != (len(x),) or not np.isfinite(pred).all():
            raise ValueError('Invalid native task predictions')
        return pred


def _rebind(model, bundle):
    if isinstance(model, IndexEstimator):
        model.bundle = bundle
        return
    for attr in ('core_', 'parent_', 'mutation_'):
        if hasattr(model, attr):
            _rebind(getattr(model, attr), bundle)
    for child in getattr(model, 'models_', []):
        _rebind(child, bundle)


def _fit(config, bundle, idx, seed, builder, records):
    c = copy.deepcopy(config)
    composition = c.pop('composition', 'replace')
    parent = c.pop('parent_config', None)
    if composition in {'crossfit_residual', 'crossfit_stack'}:
        if not parent:
            raise ValueError('OOF composition must declare the actual parent component recipe')
        splits = c.pop('inner_splits', None)
        alpha = c.pop('combiner_alpha', None)
        if type(splits) != int or splits < 2 or alpha is None:
            raise ValueError('Declare inner_splits and combiner_alpha; no hidden combination defaults')
        if parent.get('parent_config') or parent.get('composition', 'replace') != 'replace':
            raise ValueError('Implement and audit a custom nested builder for nested component recipes')
        factories = [partial(IndexEstimator, component, bundle, seed, builder, records) for component in (parent, c)]
        if composition == 'crossfit_stack':
            model = CrossFittedStackingRegressor(factories, splits=splits, meta_factory=partial(Ridge, alpha=alpha))
        else:
            model = CrossFittedResidualRegressor(*factories, splits=splits, weight_factory=partial(Ridge, alpha=alpha))
        model.fit(np.asarray(idx).reshape(-1, 1), bundle['meta'].iloc[idx].label.to_numpy(),
                  bundle['meta'].iloc[idx].clone_id.to_numpy())
    elif composition in {'replace', 'feature_fusion', 'joint', 'ablation'} and parent is None:
        if composition != 'replace':
            c['composition'] = composition
        model = IndexEstimator(c, bundle, seed, builder, records).fit(
            np.asarray(idx).reshape(-1, 1), bundle['meta'].iloc[idx].label.to_numpy())
    else:
        raise ValueError('Actual composition must agree with the declared task recipe')
    return model


def _composition_record(model, fold):
    inner = []
    if isinstance(model, CrossFittedStackingRegressor):
        for values in model.fold_audit_:
            inner.extend(values)
    elif isinstance(model, CrossFittedResidualRegressor):
        for record in model.meta_fold_audit_:
            inner.append({k: record[k] for k in ('train_groups', 'validation_groups')})
            inner.extend(record['inner_folds'])
        inner.extend(model.core_.fold_audit_)
    else:
        return None
    return {'seed': fold['seed'], 'fold_id': fold['fold_id'], 'weight_training': 'grouped_oof',
            'weight_fit_groups': model.training_groups_, 'inner_folds': inner}


def evaluate_development(request):
    if request['phase'] != 'development':
        raise ValueError('Wrong provider phase')
    contract = request['development_contract']
    b, rows = read_inputs(request['inputs']['early_observations'])
    if rows != contract['row_ids'] or b['meta'].clone_id.tolist() != contract['groups']:
        raise ValueError('Early features disagree with registered row/group order')
    y = np.asarray(contract['targets'], dtype=float)
    if y.shape != (len(rows),) or not np.isfinite(y).all():
        raise ValueError('Invalid task responses')
    config = configurations(request['recipe']['parameters'], request['recipe']['training'])
    if 'hallmark' in request['recipe']['artifact_sha256']:
        schema_info = request['inputs']['feature_schema']
        if file_digest(Path(schema_info['path'])) != schema_info['sha256']:
            raise ValueError('Early feature schema changed')
        schema = json.loads(Path(schema_info['path']).read_text())
        if request['recipe']['artifact_sha256']['hallmark'] != schema['hallmark_sha256']:
            raise ValueError('A different GMT did not produce these cached pathway features')
    composition = config.get('composition', 'replace')
    if request['composition'] in {'crossfit_residual', 'crossfit_stack'} and request['composition'] != composition:
        raise ValueError('Hypothesis and actual nested OOF topology differ')
    if composition in {'crossfit_residual', 'crossfit_stack'} and request['composition'] != composition:
        raise ValueError('Declare the real OOF topology in the hypothesis')
    builder = _builder(request)
    output = Path(request['output_dir'])
    output.mkdir(parents=True, exist_ok=True)
    predictions = np.full((len(rows), len(contract['seeds'])), np.nan)
    records, audits, captured_warnings = [], [], []
    groups = np.asarray(contract['groups'])
    folds = []
    for fold in contract['folds']:
        train = np.flatnonzero(np.isin(groups, fold['train_groups']))
        valid = np.flatnonzero(np.isin(groups, fold['validation_groups']))
        if set(groups[train]) & set(groups[valid]) or set(groups[train]) | set(groups[valid]) != set(groups):
            raise ValueError('Outer train/validation groups do not partition development')
        seed = (request.get('replicate') or {}).get('training_seed', fold['seed'])
        training = _safe_bundle(b, train, y[train])
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter('always')
            model = _fit(config, training, train, seed, builder, records)
            _rebind(model, b)
            predictions[valid, contract['seeds'].index(fold['seed'])] = model.predict(valid.reshape(-1, 1))
        captured_warnings.extend(str(w.message) for w in seen)
        audit = _composition_record(model, fold)
        if audit:
            audits.append(audit)
        folds.append(copy.deepcopy(fold))
    if not np.isfinite(predictions).all():
        raise ValueError('Incomplete/nonfinite outer OOF predictions')
    outer_solver_fits = len(records)
    checkpoint_files = []
    all_rows = np.arange(len(rows))
    for declared_seed in contract['seeds']:
        seed = (request.get('replicate') or {}).get('training_seed', declared_seed)
        model = _fit(config, _safe_bundle(b, all_rows, y), all_rows, seed, builder, records)
        path = output / f'full_development_seed_{declared_seed}.joblib'
        joblib.dump({'seed': declared_seed, 'model': model, 'config': config,
                     'metric_id': request['metric_id'], 'development_groups': sorted(set(groups)),
                     'development_row_ids': rows}, path, compress=3)
        joblib.load(path)
        checkpoint_files.append(str(path))
    artifacts = sorted({r for item in records for r in item['artifact_roles']})
    declared = set(request['recipe']['artifact_sha256'])
    if set(artifacts) != declared:
        raise ValueError('Actual model consumed artifact roles differ from sealed dependencies')
    # Do not report generic training completion as proof of numerical convergence.
    table = {k: copy.deepcopy(contract[k]) for k in ('row_ids', 'groups', 'targets', 'seeds', 'fold_ids')}
    table.update(predictions=predictions.tolist(), metric_id=request['metric_id'], evidence_phase='development')
    return {'prediction_table': table, 'fit_audit': folds, 'checkpoint_files': checkpoint_files,
        'composition_audit': audits or None, 'consumed_artifact_roles': artifacts,
        'consumed_module_roles': sorted({r for item in records for r in item['module_roles']}),
        'diagnostics': {'solver': config['model'], 'converged': False if any('converg' in w.lower() for w in captured_warnings) else 'unknown',
            'train_loss': records[-1]['last_train_loss'], 'training_records': records,
            'inner_validation_policy': 'registered grouped OOF for composition; no outer validation tuning',
            'outer_fit_count': len(folds), 'outer_component_fit_count': outer_solver_fits,
            'total_component_fit_count': len(records), 'extra_full_development_seed_fits': len(contract['seeds']),
            'warnings': captured_warnings, 'effective_config': config,
            'confirmation_model_policy': 'full development models fitted before freezing; not fold ensembles'}}


def predict_confirmation(request):
    if request['phase'] != 'confirmation_predict_only':
        raise ValueError('Confirmation may only load frozen artifacts')
    # Import the same sealed custom class definitions for joblib, never fit them.
    _builder(request)
    contract = request['confirmation_contract']
    b, rows = read_inputs(contract['early_observations'])
    if rows != contract['row_ids'] or b['meta'].clone_id.tolist() != contract['groups']:
        raise ValueError('Frozen query row/group order changed')
    checkpoints = [Path(p) for p in request['checkpoint_files'] if str(p).endswith('.joblib')]
    for path in checkpoints:
        if file_digest(path) != request['checkpoint_files'][str(path)]:
            raise ValueError('Frozen checkpoint contents changed')
    fitted = [joblib.load(p) for p in checkpoints]
    if len(fitted) != len(contract['seeds']) or {r['seed'] for r in fitted} != set(contract['seeds']):
        raise ValueError('Incomplete or duplicated frozen per-seed models')
    predictions = []
    for seed in contract['seeds']:
        record = next(r for r in fitted if r['seed'] == seed)
        if record['config'] != configurations(request['recipe']['parameters'], request['recipe']['training']):
            raise ValueError('Frozen fitted recipe differs from selected recipe')
        if record['metric_id'] != request['metric_id'] or set(record['development_groups']) & set(contract['groups']):
            raise ValueError('Frozen model metric mismatch or development/confirmation overlap')
        model = record['model']
        _rebind(model, b)
        predictions.append(model.predict(np.arange(len(rows)).reshape(-1, 1)))
    table = {k: copy.deepcopy(contract[k]) for k in ('row_ids', 'groups', 'targets', 'seeds')}
    table.update(predictions=np.stack(predictions, axis=1).tolist(),
                 metric_id=request['metric_id'], evidence_phase='confirmation')
    return {'prediction_table': table, 'model_refits': 0, 'calibration_refits': 0}
