"""CPU adapter engineering fixtures, never a new T47D scientific evaluation."""
import copy
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
import pytest

from vc_demo.harness.research_contract import digest, file_digest, write_record
from vc_demo.harness.research_v2.metrics import MetricSpec
from vc_demo.harness.research_v2.session import Session
from vc_demo.harness.research_v2 import cli as shared_cli
from vc_demo.t47d_provider_v2.data import read_inputs, save_inputs
from vc_demo.t47d_provider_v2 import provider
from vc_demo.t47d_provider_v2.registration import TRAINING, implementation, make_task_spec
from vc_demo.t47d_lineage.data import TREATMENTS
from vc_demo.t47d_lineage.models import Candidate as HistoricalCandidate


def fixture(tmp_path):
    rng = np.random.default_rng(7)
    n = 42
    group = [f'c{i // 3:02}' for i in range(n)]
    expression = rng.normal(size=(n, 3, 24)).astype('float32')
    pathway = rng.normal(size=(n, 3, 50)).astype('float32')
    aux = np.concatenate([rng.normal(size=(n, 6)), np.tile(np.eye(3), (n // 3, 1))], axis=1).astype('float32')
    meta = pd.DataFrame({'clone_id': group, 'treatment': list(TREATMENTS) * (n // 3)})
    meta['label'] = 2 * pathway[:, 0, 0] + aux[:, 0] + rng.normal(0, .2, n)
    bundle = {'meta': meta, 'expression': expression, 'pathway': pathway, 'aux': aux,
              'pseudobulk': np.log1p(np.abs(expression))}
    dev = np.arange(36)
    heldout = np.arange(36, n)
    inp = save_inputs(tmp_path / 'early.npz', bundle, dev)
    held = save_inputs(tmp_path / 'confirm_early.npz', bundle, heldout)
    g = np.array(group)[dev].tolist()
    unique = sorted(set(g))
    folds = [{'seed': seed, 'fold_id': str(k), 'train_groups': [x for x in unique if x not in unique[k::3]],
              'validation_groups': unique[k::3]} for seed in (3, 7) for k in range(3)]
    c = {'row_ids': [f'{group[i]}::{meta.iloc[i].treatment}' for i in dev], 'groups': g,
         'targets': meta.iloc[dev].label.tolist(), 'seeds': [3, 7], 'folds': folds,
         'fold_ids': [[next(f['fold_id'] for f in folds if f['seed'] == s and x in f['validation_groups'])
                       for s in (3, 7)] for x in g]}
    write_record(tmp_path / 'development.json', c)
    cc = {'row_ids': [f'{group[i]}::{meta.iloc[i].treatment}' for i in heldout],
          'groups': meta.iloc[heldout].clone_id.tolist(), 'targets': meta.iloc[heldout].label.tolist(),
          'seeds': [3, 7], 'early_observations': held, 'prior_test_exposure': True}
    write_record(tmp_path / 'confirmation.json', cc)
    gmt = tmp_path / 'hallmark.gmt'
    gmt.write_text('engineering fixture only: precomputed 50-channel test inputs, not a biological artifact\n')
    schema = tmp_path / 'schema.json'
    write_record(schema, {'hallmark_sha256': file_digest(gmt)})
    prep = {'schema_version': 't47d_provider_v2', 'prior_test_exposure': True, 'source_files': {},
            'dataset_sha256': file_digest(tmp_path / 'early.npz'), 'split_sha256': file_digest(tmp_path / 'development.json'),
            'task_contract': {'label': 'CPU engineering fixture only'},
            'historical_ridge_config': {'model': 'ridge', 'representation': 'pathway', 'baseline_only': True, 'alpha': 100.},
            'development_contract': str(tmp_path / 'development.json'),
            'confirmation_contract': {'path': str(tmp_path / 'confirmation.json'), 'sha256': file_digest(tmp_path / 'confirmation.json')},
            'development_inputs': {'early_observations': dict(inp, scope='development'),
                'feature_schema': {'path': str(schema), 'sha256': file_digest(schema), 'scope': 'public'}},
            'hallmark': {'path': str(gmt), 'sha256': file_digest(gmt), 'source': 'CPU engineering fixture, not science',
                        'status': 'derived', 'kind': 'gene_set_membership', 'alignment': 'fixed fixture channel order'}}
    return prep, c, cc, bundle


def request(tmp_path, prep, contract, config, *, composition='replace', model_builder=None, artifacts=None):
    actual = implementation(config, prep, model_builder=model_builder, artifacts=artifacts)
    metric = MetricSpec('spearman', 'maximize', 'mean_seed', 'clone_x_treatment', 'clone_id')
    out = tmp_path / ('nodes_' + digest(config)[:8])
    return {'phase': 'development', 'task_id': 't47d_adapter_engineering_fixture', 'node_id': 'fixture',
            'metric': metric.__dict__, 'metric_id': metric.identity, 'development_contract': contract,
            'inputs': prep['development_inputs'], 'recipe': actual['recipe'], 'execution': actual['execution'],
            'output_dir': str(out), 'replicate': None, 'composition': composition}


def confirmation(req, cc, result):
    return {'phase': 'confirmation_predict_only', 'confirmation_contract': cc,
            'checkpoint_files': {p: file_digest(Path(p)) for p in result['checkpoint_files']},
            'recipe': req['recipe'], 'execution': req['execution'], 'metric_id': req['metric_id']}


def test_registration_requires_explicit_budget_and_preserves_six_exact_baselines(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    spec = make_task_spec(p, budget={'coverage': 0, 'optimization': 1, 'confirmation': 2},
        policy={'parent_policy': 'global_queue', 'queue_capacity': 8, 'min_new_proposals': 1},
        resources={'authorization_id': 'CPU fixture only', 'deadline_utc': '2099-01-01T00:00:00+00:00'}, minimum_effect=.01)
    assert len(spec['benchmarks']) == 6 and spec['prior_test_exposure'] is True
    assert spec['reference_benchmark'] == 'root_historical_exact_ridge'
    historical = spec['benchmark_recipes']['root_historical_exact_ridge']
    assert historical['parameters']['model_config']['historical_recipe'] == p['historical_ridge_config']
    assert spec['metric']['aggregation'] == 'mean_seed'
    assert spec['budget']['optimization'] == 1
    assert not any('confirmation' in role for role in spec['inputs'])
    p['prior_test_exposure'] = False
    with pytest.raises(ValueError, match='exposure'):
        make_task_spec(p, budget={}, policy={}, resources={}, minimum_effect=0)


def test_input_contract_excludes_endpoint_and_labels_and_rejects_reordering(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    safe, rows = read_inputs(p['development_inputs']['early_observations'])
    assert list(safe['meta']) == ['clone_id', 'treatment', 'label']
    assert safe['meta'].label.isna().all()
    assert rows == c['row_ids']
    bad = copy.deepcopy(c)
    bad['row_ids'].reverse()
    req = request(tmp_path, p, bad, {'model': 'ridge', 'representation': 'pathway', 'alpha': 10})
    with pytest.raises(ValueError, match='row/group'):
        provider.evaluate_development(req)
    path = tmp_path / 'poisoned.npz'
    with np.load(p['development_inputs']['early_observations']['path']) as arrays:
        np.savez(path, **dict(arrays), n_day26=np.arange(36))
    with pytest.raises(ValueError, match='endpoint'):
        read_inputs({'path': str(path), 'sha256': file_digest(path)})


def test_exact_historical_scaling_and_encoding_match_old_model(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    config = {'model': 'historical_ridge', 'historical_recipe': p['historical_ridge_config'],
              'representation': 'pathway', 'composition': 'replace'}
    req = request(tmp_path, p, c, config)
    result = provider.evaluate_development(req)
    groups = np.asarray(c['groups'])
    for fold in c['folds']:
        train = np.flatnonzero(np.isin(groups, fold['train_groups']))
        valid = np.flatnonzero(np.isin(groups, fold['validation_groups']))
        old = HistoricalCandidate(p['historical_ridge_config']).fit(b, train, fold['seed'])
        actual = np.asarray(result['prediction_table']['predictions'])[valid, c['seeds'].index(fold['seed'])]
        np.testing.assert_allclose(actual, old.predict(b, valid), rtol=1e-10, atol=1e-10)
    assert result['diagnostics']['outer_fit_count'] == 6
    assert result['diagnostics']['extra_full_development_seed_fits'] == 2
    assert result['consumed_artifact_roles'] == ['hallmark']


@pytest.mark.parametrize('config', [
    {'model': 'ridge', 'representation': 'pca', 'alpha': 10},
    {'model': 'early_elastic', 'representation': 'pseudobulk', 'baseline_only': True},
    {'model': 'pls', 'representation': 'pathway', 'baseline_only': True, 'components': 3},
    {'model': 'xgboost', 'representation': 'pca'},
    {'model': 'additive_null', 'representation': 'pathway'},
    {'model': 'gated_pathway', 'representation': 'pathway', 'device': 'cpu', 'epochs': 2,
     'hidden': 8, 'loss': 'multitask', 'pathway_weight': .1, 'no_dense_parent': True},
    *[{'model': model, 'representation': rep, 'device': 'cpu', 'epochs': 2, 'hidden': 8, 'loss': 'huber'}
      for model, rep in [('gru', 'expression'), ('temporal_transformer', 'both'),
                         ('cross_attention', 'pathway'), ('bilinear', 'pathway'), ('moe', 'pca')]],
])
def test_native_models_frozen_prediction_never_refits_or_reads_confirmation_targets(tmp_path, monkeypatch, config):
    p, c, cc, b = fixture(tmp_path)
    req = request(tmp_path, p, c, config)
    result = provider.evaluate_development(req)
    def forbidden(*args, **kwargs):
        raise AssertionError('Frozen inference tried to fit')
    monkeypatch.setattr(provider.ResearchCandidate, 'fit', forbidden)
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    monkeypatch.setattr(StandardScaler, 'fit', forbidden)
    monkeypatch.setattr(PCA, 'fit', forbidden)
    confirm = confirmation(req, cc, result)
    before = {path: file_digest(Path(path)) for path in result['checkpoint_files']}
    a = provider.predict_confirmation(confirm)
    poisoned = copy.deepcopy(confirm)
    poisoned['confirmation_contract']['targets'] = [1e9] * len(cc['targets'])
    z = provider.predict_confirmation(poisoned)
    assert a['prediction_table']['predictions'] == z['prediction_table']['predictions']
    assert a['model_refits'] == a['calibration_refits'] == 0
    assert before == {path: file_digest(Path(path)) for path in result['checkpoint_files']}
    assert np.asarray(a['prediction_table']['predictions']).shape == (6, 2)


def test_outer_validation_target_poisoning_does_not_change_its_predictions(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    config = {'model': 'gated_pathway', 'representation': 'pathway', 'device': 'cpu', 'epochs': 2,
              'hidden': 8, 'loss': 'multitask', 'no_dense_parent': True}
    req = request(tmp_path, p, c, config)
    a = provider.evaluate_development(req)
    first = c['folds'][0]
    valid = np.flatnonzero(np.isin(c['groups'], first['validation_groups']))
    other = copy.deepcopy(req)
    other['output_dir'] = str(tmp_path / 'poisoned_labels_nodes')
    for i in valid:
        other['development_contract']['targets'][i] += 1000
    z = provider.evaluate_development(other)
    np.testing.assert_allclose(np.asarray(a['prediction_table']['predictions'])[valid, 0],
                               np.asarray(z['prediction_table']['predictions'])[valid, 0], rtol=0, atol=0)


def test_nested_residual_labels_do_not_redefine_auxiliary_selection_labels(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    early, _ = read_inputs(p['development_inputs']['early_observations'])
    y = np.asarray(c['targets'])
    outer_idx = np.arange(24)
    outer = provider._safe_bundle(early, outer_idx, y[outer_idx])
    inner_idx = np.arange(12)
    residual = y[inner_idx] - 10.
    inner = provider._safe_bundle(outer, inner_idx, residual)
    np.testing.assert_array_equal(inner['meta'].iloc[inner_idx].label, residual)
    np.testing.assert_array_equal(inner['truth_meta'].iloc[inner_idx].label, y[inner_idx])
    assert inner['meta'].iloc[12:].label.isna().all()
    assert inner['truth_meta'].iloc[12:].label.isna().all()


@pytest.mark.parametrize('composition', ['crossfit_stack', 'crossfit_residual'])
def test_real_nested_grouped_combination_is_portable_and_audited(tmp_path, composition):
    p, c, cc, b = fixture(tmp_path)
    config = {'model': 'ridge', 'representation': 'pca', 'alpha': 10, 'composition': composition,
              'parent_config': {'model': 'ridge', 'representation': 'pathway', 'alpha': 100},
              'inner_splits': 3, 'combiner_alpha': 1.}
    req = request(tmp_path, p, c, config, composition=composition)
    result = provider.evaluate_development(req)
    Session._composition_audit(result['composition_audit'], c)
    assert result['diagnostics']['outer_component_fit_count'] > len(c['folds'])
    for record in result['composition_audit']:
        assert record['inner_folds']
        outer = next(f for f in c['folds'] if (f['seed'], f['fold_id']) == (record['seed'], record['fold_id']))
        assert set(record['weight_fit_groups']).isdisjoint(outer['validation_groups'])
    output = provider.predict_confirmation(confirmation(req, cc, result))
    assert np.asarray(output['prediction_table']['predictions']).shape == (6, 2)


def test_missing_real_representation_is_implementation_work_not_fallback(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    req = request(tmp_path, p, c, {'model': 'ridge', 'representation': 'scvi'})
    with pytest.raises(ValueError, match='portable train-only'):
        provider.evaluate_development(req)
    req = request(tmp_path, p, c, {'model': 'unknown_foundation', 'representation': 'pathway'})
    with pytest.raises(ValueError, match='actual model_builder'):
        provider.evaluate_development(req)


@pytest.mark.parametrize('composition', ['replace', 'feature_fusion'])
def test_agent_custom_model_builder_is_not_overwritten_by_native_catalog(tmp_path, composition):
    p, c, cc, b = fixture(tmp_path)
    source = tmp_path / 'agent_model.py'
    source.write_text('''import numpy as np
from sklearn.linear_model import Ridge
class CustomResearchModel:
    def __init__(self,config): self.config=config
    def features(self,bundle,idx):
        x=bundle['aux'][idx,:6]
        if self.config.get('composition')=='feature_fusion':x=np.concatenate([x,bundle['expression'][idx].mean(1)],axis=1)
        return x
    def fit(self,bundle,idx,seed):
        assert bundle['meta'].loc[~bundle['meta'].index.isin(idx),'label'].isna().all()
        self.estimator=Ridge(alpha=self.config['agent_alpha']).fit(self.features(bundle,idx),bundle['meta'].iloc[idx].label)
        self.artifact_roles=[];self.module_roles=['agent:early_feature_fusion' if self.config.get('composition')=='feature_fusion' else 'agent:early_auxiliary_model']
        return self
    def predict(self,bundle,idx):return self.estimator.predict(self.features(bundle,idx))
def build_model(config,*,artifact_files):
    assert artifact_files=={}
    return CustomResearchModel(config)
''')
    config = {'model': 'agent_defined_model', 'agent_alpha': 3., 'composition': composition}
    req = request(tmp_path, p, c, config, composition=composition, model_builder=source, artifacts={})
    before = source.read_bytes()
    result = provider.evaluate_development(req)
    output = provider.predict_confirmation(confirmation(req, cc, result))
    assert source.read_bytes() == before
    assert result['consumed_artifact_roles'] == []
    assert result['consumed_module_roles'] == ['agent:early_feature_fusion' if composition == 'feature_fusion' else 'agent:early_auxiliary_model']
    assert output['model_refits'] == 0


def test_cached_pathways_cannot_claim_a_different_gmt(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    req = request(tmp_path, p, c, {'model': 'ridge', 'representation': 'pathway'})
    req['recipe']['artifact_sha256']['hallmark'] = 'another-gmt'
    with pytest.raises(ValueError, match='different GMT'):
        provider.evaluate_development(req)


def test_agent_builder_receives_real_sealed_artifact_locations_not_hardcoded_paths(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    asset = tmp_path / 'research_prior.json'
    write_record(asset, {'feature_scale': [2., 1., .5, 1., 1., 1.]})
    source = tmp_path / 'artifact_model.py'
    source.write_text('''import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
class ActualArtifactModel:
    def __init__(self,config,artifact_files):
        self.scale=np.array(json.loads(Path(artifact_files['feature_prior']['path']).read_text())['feature_scale'])
        self.config=config
    def fit(self,bundle,idx,seed):
        self.regressor=Ridge(alpha=self.config['alpha']).fit(bundle['aux'][idx,:6]*self.scale,bundle['meta'].iloc[idx].label)
        self.artifact_roles=['feature_prior'];self.module_roles=['agent:real_prior_scaled_regression']
        return self
    def predict(self,bundle,idx):return self.regressor.predict(bundle['aux'][idx,:6]*self.scale)
def build_model(config,*,artifact_files):return ActualArtifactModel(config,artifact_files)
''')
    artifacts = {'feature_prior': {'path': str(asset), 'kind': 'feature_prior', 'status': 'derived',
        'source': 'CPU unit fixture only, not foundation or biological evidence', 'alignment': 'six fixture auxiliary columns'}}
    req = request(tmp_path, p, c, {'model': 'agent_actual_prior', 'alpha': 2.}, model_builder=source, artifacts=artifacts)
    result = provider.evaluate_development(req)
    assert result['consumed_artifact_roles'] == ['feature_prior']
    output = provider.predict_confirmation(confirmation(req, cc, result))
    assert output['model_refits'] == 0


def test_frequency_does_not_claim_pathway_signal_merely_because_view_computes_it(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    config = {'model': 'frequency', 'representation': 'pathway', 'baseline_only': True}
    req = request(tmp_path, p, c, config)
    result = provider.evaluate_development(req)
    assert result['consumed_artifact_roles'] == []
    assert 'representation:early_abundance' in result['consumed_module_roles']
    changed = dict(b, pathway=np.full_like(b['pathway'], 100.))
    train = np.arange(24)
    x = provider.PortableNative(config).fit(b, train, 3).predict(b, np.arange(24, 36))
    z = provider.PortableNative(config).fit(changed, train, 3).predict(changed, np.arange(24, 36))
    np.testing.assert_allclose(x, z, rtol=0, atol=0)


def test_matched_no_artifact_auxiliary_control_does_not_claim_hallmark(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    config = {'model': 'gated_pathway', 'representation': 'matched_no_artifact', 'auxiliary_no_artifact': True,
              'loss': 'multitask', 'device': 'cpu', 'epochs': 2, 'hidden': 8}
    result = provider.evaluate_development(request(tmp_path, p, c, config))
    assert result['consumed_artifact_roles'] == []


def proposal(session, node, config, phase, parent=None):
    context = session.context()
    return {'id': node, 'phase': phase, 'parent_id': parent,
        'proposed_recipe': {'parameters': {'model_config': config}, 'training': TRAINING},
        'required_artifacts': {'hallmark': {'kind': 'gene_set_membership'}},
        'hypothesis': {'statement': 'Engineering interface fixture, not a scientific hypothesis result',
                      'expected_change': 'Exercise actual adapter', 'falsification': 'Contract mismatch',
                      'evidence_ids': [context['evidence_id']], 'composition': 'replace',
                      'parent_conditioning': 'Compare the real configured model against the exact fixture benchmark'},
        'estimate': {'metric_id': context['metric_id'], 'expected_gain': 0., 'uncertainty': .01,
                     'cost_seconds': {'acquisition': 0, 'cache_miss': 0, 'fit': 1, 'evaluation': 1},
                     'basis': 'hypothesis', 'rationale': 'CPU engineering assumption only'}}


def test_actual_shared_cli_uses_t47d_adapter_end_to_end_and_resumes_once(tmp_path):
    p, c, cc, b = fixture(tmp_path)
    spec = make_task_spec(p, budget={'coverage': 0, 'optimization': 1, 'confirmation': 2},
        policy={'parent_policy': 'global_queue', 'queue_capacity': 8, 'min_new_proposals': 1,
                'exploration': 1., 'uncertainty_weight': 1., 'cost_penalty_per_hour': .01, 'bootstrap_draws': 20},
        resources={'authorization_id': 'CPU fixture only; not full T47D', 'deadline_utc': '2099-01-01T00:00:00+00:00'}, minimum_effect=0.)
    # A deliberately reduced *engineering fixture*, never a production registration.
    spec['task_id'] = 't47d_adapter_cpu_engineering_fixture'
    spec['benchmarks'] = ['root_historical_exact_ridge']
    spec['benchmark_recipes'] = {k: v for k, v in spec['benchmark_recipes'].items() if k in spec['benchmarks']}
    run = tmp_path / 'run'
    sp = tmp_path / 'spec.json'
    write_record(sp, spec)
    def cli(*args, fresh=False):
        argv = ['scripts/run_research_harness.py', '--run-dir', str(run), *args]
        if fresh:
            output = subprocess.check_output([sys.executable, *argv], text=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=''))
        else:
            # Exercise the real parser/controller without repeated heavyweight imports.
            output_stream = io.StringIO()
            with patch.object(sys, 'argv', argv), redirect_stdout(output_stream):
                shared_cli.main()
            output = output_stream.getvalue()
        return json.loads(output)
    cli('init', '--spec', str(sp), fresh=True)
    session = Session(run)
    reference = spec['benchmark_recipes']['root_historical_exact_ridge']['parameters']['model_config']
    for name, config, phase in [('root_historical_exact_ridge', reference, 'benchmark'),
        ('agent_candidate', {'model': 'ridge', 'representation': 'pathway', 'alpha': 10}, 'optimization')]:
        proposal_path = tmp_path / (name + '_proposal.json')
        write_record(proposal_path, [proposal(session, name, config, phase,
                                             parent=None if phase == 'benchmark' else 'root_historical_exact_ridge')])
        cli('context')
        cli('propose', '--file', str(proposal_path))
        cli('select')
        impl = tmp_path / (name + '_implementation.json')
        write_record(impl, implementation(config, p))
        cli('seal', '--node', name, '--file', str(impl))
        cli('execute', '--node', name, fresh=(phase == 'optimization'))
        before = (run / 'session_state.json').read_bytes()
        cli('execute', '--node', name)
        state = json.loads((run / 'session_state.json').read_text())
        assert (run / 'session_state.json').read_bytes() == before
    assert state['budget_used']['optimization'] == 1
    assert state['nodes']['agent_candidate']['optimization_visits'] == 1
    paired = state['nodes']['agent_candidate']['paired_evidence']
    assert paired['metric_id'] == session.context()['metric_id']
    cli('freeze', '--nodes', 'root_historical_exact_ridge', 'agent_candidate')
    a = cli('confirm', '--node', 'agent_candidate', fresh=True)
    assert a['model_refits'] == a['calibration_refits'] == 0
    assert a['prior_test_exposure'] is True
    assert cli('confirm', '--node', 'agent_candidate') == a
    assert 'confirmation_metrics' not in json.dumps(cli('context'))
    cli('report')
