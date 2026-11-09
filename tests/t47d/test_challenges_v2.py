"""Actual shared-controller analyses on explicitly synthetic CPU engineering data."""
import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from vc_demo.harness.research_contract import digest, file_digest, write_record
from vc_demo.harness.research_v2.session import Session
from vc_demo.harness.research_v2 import cli
from vc_demo.t47d_provider_v2 import provider
from vc_demo.t47d_provider_v2.analysis_registration import register_analyses, KINDS
from vc_demo.t47d_provider_v2.cell_sources import info
from vc_demo.t47d_provider_v2.data import save_inputs
from vc_demo.t47d_provider_v2.registration import make_task_spec, implementation
from vc_demo.t47d_lineage.data import TREATMENTS

loader = importlib.util.spec_from_file_location('heavy_engineering_fixtures', Path(__file__).with_name('test_heavy_provider_v2.py'))
heavy = importlib.util.module_from_spec(loader)
loader.loader.exec_module(heavy)
base = heavy.base


def analysis_fixture(tmp_path):
    p, c, cc, b, q = heavy.raw_fixture(tmp_path)
    groups = sorted(set(b['meta'].clone_id) | set(q['meta'].clone_id))
    rng = np.random.default_rng(234)
    counts, expression_rows, expression = [], [], []
    for i, clone in enumerate(groups):
        counts.append({'clone_id': clone, 'treatment': 'baseline', 'time_day': 0, 'cell_count': 10 + i})
        expression_rows.append({'clone_id': clone, 'treatment': 'baseline', 'time_day': 0})
        expression.append(rng.uniform(0, 2, 64))
        for j, treatment in enumerate(TREATMENTS):
            cutoff = [1, 4, 8, 99][(i + j) % 4]
            for day in (1, 4, 8, 26):
                counts.append({'clone_id': clone, 'treatment': treatment, 'time_day': day,
                               'cell_count': 0 if day >= cutoff else 8 + i + 3 * j})
                expression_rows.append({'clone_id': clone, 'treatment': treatment, 'time_day': day})
                expression.append(rng.uniform(0, 2, 64) + .01 * day + .1 * j)
        # Deliberately no heldout Month6 positives; undefined recall must stay undefined.
        counts.append({'clone_id': clone, 'treatment': 'combination', 'time_day': 180,
                       'cell_count': 4 if i < 2 else 0})
    counts = pd.DataFrame(counts)
    path = tmp_path / 'counts.csv'
    counts.to_csv(path, index=False)
    totals = counts.groupby(['treatment', 'time_day']).cell_count.sum().reset_index()
    lookup = counts.set_index(['clone_id', 'treatment', 'time_day']).cell_count.to_dict()
    population = totals.set_index(['treatment', 'time_day']).cell_count.to_dict()
    for bundle, contract, name in [(b, c, 'early.npz'), (q, cc, 'confirm_early.npz')]:
        y = []
        for r in bundle['meta'].itertuples():
            f0 = lookup[(r.clone_id, 'baseline', 0)] / population[('baseline', 0)]
            f26 = lookup[(r.clone_id, r.treatment, 26)] / population[(r.treatment, 26)]
            y.append(float(np.log2((f26 + 1e-5) / (f0 + 1e-5))))
        bundle['meta']['label'] = y
        contract['targets'] = y
    gmt = Path(p['hallmark']['path'])
    names = ['HALLMARK_ESTROGEN_RESPONSE_EARLY', 'HALLMARK_E2F_TARGETS', 'HALLMARK_EPITHELIAL_MESENCHYMAL_TRANSITION'] + [f'ENGINEERING_ONLY_{i}' for i in range(47)]
    memberships = [rng.choice(64, 8, replace=False) for _ in names]
    gmt.write_text('\n'.join(name + '\tfixture\t' + '\t'.join('GENE' + str(g) for g in genes) for name, genes in zip(names, memberships)) + '\n')
    p['hallmark']['sha256'] = file_digest(gmt)
    write_record(Path(p['development_inputs']['feature_schema']['path']), {'hallmark_sha256': file_digest(gmt)})
    p['development_inputs']['feature_schema']['sha256'] = file_digest(Path(p['development_inputs']['feature_schema']['path']))
    for bundle in (b, q):
        bundle['pathway'] = np.stack([bundle['expression'][:, :, loc].mean(2) for loc in memberships], axis=-1)
    p['development_inputs']['early_observations'] = dict(save_inputs(tmp_path / 'early.npz', b, np.arange(len(b['meta']))), scope='development')
    cc['early_observations'] = save_inputs(tmp_path / 'confirm_early.npz', q, np.arange(len(q['meta'])))
    write_record(Path(p['development_contract']), c)
    write_record(Path(p['confirmation_contract']['path']), cc)
    p['confirmation_contract']['sha256'] = file_digest(Path(p['confirmation_contract']['path']))
    events = counts.loc[counts.clone_id.isin(c['groups']) & counts.time_day.isin([1, 4, 8, 26])]
    events.to_csv(p['development_inputs']['training_events']['path'], index=False)
    p['development_inputs']['training_events']['sha256'] = file_digest(Path(p['development_inputs']['training_events']['path']))
    label_meta = tmp_path / 'label_meta.json'
    write_record(label_meta, {'counts': counts.loc[counts.clone_id.isin(c['groups']) & counts.time_day.isin([0, 1, 4, 8, 26])].to_dict('records'),
                            'population_totals': totals.loc[totals.time_day.isin([0, 1, 4, 8, 26])].to_dict('records')})
    rows = tmp_path / 'expression_rows.csv'
    pd.DataFrame(expression_rows).to_csv(rows, index=False)
    matrix = tmp_path / 'expression.npz'
    sparse.save_npz(matrix, sparse.csr_matrix(expression))
    p['postselection_sources'] = {'clone_condition_counts.csv': info(path), 'clone_expression_rows.csv': info(rows),
        'clone_mean_log_expression.npz': info(matrix), 'gene_order.csv': p['development_inputs']['gene_order'],
        'development_label_metadata.json': info(label_meta)}
    p['scope_groups'] = {'development': sorted(set(c['groups'])), 'confirmation': sorted(set(cc['groups']))}
    p.update(heavy.tf_artifacts(tmp_path))
    reference = tmp_path / 'author_reference_fixture.json'
    n = 240
    write_record(reference, {'engineering_barcode': {'Pseudotime': np.linspace(0, 1, n).tolist(),
        'RealTime': (np.arange(n) % 27).tolist(), 'Survival': (.2 + .1 * np.sin(np.arange(n) / 7)).tolist(),
        'program1': rng.normal(size=n).tolist(), 'program2': rng.normal(size=n).tolist(), 'last_dropped': [0.] * n}})
    p['dataset_sha256'] = digest(p['development_inputs'])
    spec = make_task_spec(p, budget={'coverage': 0, 'optimization': 0, 'confirmation': 1},
        policy={'parent_policy': 'global_queue', 'queue_capacity': 4, 'min_new_proposals': 1, 'bootstrap_draws': 20,
                'exploration': 1., 'uncertainty_weight': 1., 'cost_penalty_per_hour': .01},
        resources={'authorization_id': 'CPU SYNTHETIC ENGINEERING ONLY', 'deadline_utc': '2099-01-01T00:00:00+00:00'}, minimum_effect=0.)
    spec['task_id'] = 't47d_challenges_cpu_engineering_fixture'
    spec['benchmarks'] = ['root_historical_exact_ridge']
    spec['benchmark_recipes'] = {k: v for k, v in spec['benchmark_recipes'].items() if k in spec['benchmarks']}
    settings = {'seeds': [3], 'bootstrap_draws': 20, 'permutation_seed': 12, 'permutation_seeds': [13], 'alpha': 10.,
        'unseen_batch_policy': 'reference_baseline', 'cutoffs': [0, 1, 4], 'expression_days': [1, 4, 8, 26],
        'bootstrap_seed': 17, 'epsilons': [1e-5, 1e-4], 'top_k': 5, 'weights': [.25] * 4,
        'calibrator_C': 1., 'calibrator_seed': 3,
        'hazard_config': {'model': 'hazard', 'representation': 'pca', 'hazard_components': 2,
                          'hazard_max_fit_day': 26, 'hazard_penalizer': 2.},
        'tracsed_config': {'device': 'cpu', 'epochs': 1, 'batch_size': 32, 'author_seed': 42}, 'intervals': [1.]}
    plans = {}
    for kind in KINDS:
        dev = kind in {'ablations', 'last_snapshot', 'early_abundance', 'denominator_null'}
        fit = 0 if kind in {'secondary_metrics', 'biology_sensitivity'} else 60
        plans[kind] = {'kind': kind, 'settings': settings, 'data_scope': 'development' if dev else ('all_exposed_secondary' if kind == 'loco' else 'confirmation'),
            'mode': 'predict_only' if not fit and kind != 'secondary_metrics' else 'registered_refits',
            'fit_budget': {'model': fit, 'calibration': 2 if kind in {'secondary_metrics', 'resistance_month6'} else 0},
            'target_policy': 'each_finalist'}
    plans['author_reference'].update(extra_inputs={'reference_data': info(reference)}, allow_training_query_group_overlap=True)
    spec = register_analyses(spec, p, plans, tmp_path / 'analysis_contracts')
    return p, c, cc, spec


def trained_session(tmp_path):
    p, c, cc, spec = analysis_fixture(tmp_path)
    session = Session.initialize(tmp_path / 'run', spec)
    name = 'root_historical_exact_ridge'
    config = spec['benchmark_recipes'][name]['parameters']['model_config']
    session.propose([base.proposal(session, name, config, 'benchmark')])
    session.select()
    actual = implementation(config, p)
    session.seal(name, actual['execution'], actual['recipe'])
    session.execute(name)
    session.freeze([name])
    return session, p, c, cc, name


def test_all_twelve_actual_challenges_share_generic_lifecycle_without_search_credit(tmp_path, capsys):
    s, p, c, cc, name = trained_session(tmp_path)
    before = json.loads((s.run / 'session_state.json').read_text())
    for kind in sorted(KINDS):
        cli.main(['--run-dir', str(s.run), 'analyze', '--node', name, '--analysis', kind])
        result = json.loads(capsys.readouterr().out)
        assert result['optimization_credit'] == 0 and result['metrics']
        assert s.analyze(name, kind) == result
    after = json.loads((s.run / 'session_state.json').read_text())
    assert after['nodes'] == before['nodes'] and after['budget_used'] == before['budget_used']
    assert s.verdict()['postselection_analysis_scope_complete'] is True
    assert s.context()['nodes'] == Session(s.run).context()['nodes']
    assert s.context()['next_action'] == 'predict_frozen_confirmation_without_refitting'
    confirmation = s.confirm(name)
    actual = np.asarray(json.loads(Path(confirmation['prediction_receipt']['path']).read_text())['predictions'])[:, :1]
    with np.load(s.run / 'nodes' / name / 'analyses/secondary_metrics/secondary_predictions.npz') as saved:
        np.testing.assert_allclose(saved['predictions'], actual, rtol=0, atol=0)
    assert s.context()['next_action'] == 'write_final_report_selection_remains_closed'
    resistance = s.analyze(name, 'resistance_month6')['metrics']
    assert resistance['heldout_positive_count'] == 0 and resistance['unseen_clone_escape_recall'] is None
    assert s.analyze(name, 'author_reference')['model_refits'] == 4
    ablations = s.analyze(name, 'ablations')['metrics']
    assert ablations['no_dense_parent_branch']['applicability'] == 'not_applicable'
    assert ablations['baseline_only']['applicability'] == 'not_applicable'


def test_analysis_registration_rejects_mislabelled_data_scope(tmp_path):
    p, c, cc, spec = analysis_fixture(tmp_path)
    with pytest.raises(ValueError, match='must not open'):
        register_analyses(spec, p, {'bad': {'kind': 'denominator_null', 'data_scope': 'confirmation'}}, tmp_path / 'bad')


@pytest.mark.parametrize('kind', ['scvi', 'cellrank', 'pseudotime'])
def test_heavy_representation_actual_shared_session_development_and_frozen_query(tmp_path, kind):
    p, c, cc, b, q = heavy.raw_fixture(tmp_path)
    c['seeds'] = [3]
    c['folds'] = [f for f in c['folds'] if f['seed'] == 3]
    c['fold_ids'] = [[x[0]] for x in c['fold_ids']]
    cc['seeds'] = [3]
    write_record(Path(p['development_contract']), c)
    write_record(Path(p['confirmation_contract']['path']), cc)
    p['confirmation_contract']['sha256'] = file_digest(Path(p['confirmation_contract']['path']))
    config = heavy.representation_config(kind)
    if kind == 'pseudotime':
        config.update(model='gru', device='cpu', epochs=1, hidden=8, loss='multitask')
    spec = make_task_spec(p, budget={'coverage': 0, 'optimization': 0, 'confirmation': 1},
        policy={'parent_policy': 'global_queue', 'queue_capacity': 4, 'min_new_proposals': 1,
                'exploration': 1., 'uncertainty_weight': 1., 'cost_penalty_per_hour': .01},
        resources={'authorization_id': 'CPU SYNTHETIC ENGINEERING ONLY', 'deadline_utc': '2099-01-01T00:00:00+00:00'}, minimum_effect=0.)
    # A specialist engineering benchmark, not a new production baseline suite.
    spec['benchmarks'] = ['heavy_fixture']
    spec['benchmark_recipes'] = {'heavy_fixture': implementation(config, p)['recipe']}
    spec['reference_benchmark'] = 'heavy_fixture'
    s = Session.initialize(tmp_path / 'run', spec)
    candidate = base.proposal(s, 'heavy_fixture', config, 'benchmark')
    candidate['required_artifacts'] = {role: {'kind': value['kind']} for role, value in implementation(config, p)['execution']['artifact_files'].items()}
    s.propose([candidate])
    s.select()
    actual = implementation(config, p)
    s.seal('heavy_fixture', actual['execution'], actual['recipe'])
    s.execute('heavy_fixture')
    s.freeze(['heavy_fixture'])
    report = s.confirm('heavy_fixture')
    assert report['model_refits'] == report['calibration_refits'] == 0
    assert s.confirm('heavy_fixture') == report
    assert s.verdict()['trained_measurements'] == 1
