"""Task-neutral postselection boundaries and interrupted actual-fit recovery."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from vc_demo.harness.research_contract import file_digest, write_record
from vc_demo.harness.research_v2 import cli, postselection

loader = importlib.util.spec_from_file_location('base_research_engineering_fixtures', Path(__file__).with_name('test_research_v2.py'))
base = importlib.util.module_from_spec(loader)
loader.loader.exec_module(base)

ANALYSIS = '''import json
from pathlib import Path
import numpy as np
import joblib
from sklearn.linear_model import Ridge
def evaluate_analysis(request):
    out=Path(request['output_dir']);counter=out/'fit_counter.txt'
    count=int(counter.read_text())+1 if counter.exists() else 1
    counter.write_text(str(count))
    contract=request['analysis_contract'];dev=request['development_contract']
    x=np.array(json.loads(Path(contract['inputs']['features']['path']).read_text())['x'])
    query=json.loads(Path(contract['inputs']['query']['path']).read_text())
    m=Ridge(alpha=1).fit(x,dev['targets'])
    model=out/'model.joblib';joblib.dump(m,model)
    pred=out/'predictions.json';pred.write_text(json.dumps(m.predict(query['features']).tolist()))
    return {'metrics':{'report_only_value':917.129},'model_refits':1,'calibration_refits':0,
        'fit_audit':[{'train_groups':sorted(set(dev['groups'])),'validation_groups':query['groups']}],
        'output_files':[str(counter),str(model),str(pred)]}
'''


def setup(tmp_path, *, budget=1):
    session, spec, provider = base.setup(tmp_path, optimization=0)
    base.train_root(session, provider)
    source = tmp_path / 'analysis.py'
    source.write_text(ANALYSIS)
    dev = json.loads(Path(spec['development_contract']).read_text())
    query_path = Path(spec['confirmation_contract']['path'])
    query = json.loads(query_path.read_text())
    contract = tmp_path / 'analysis_contract.json'
    write_record(contract, {'inputs': {'features': spec['inputs']['features'],
        'query': {'path': str(query_path), 'sha256': file_digest(query_path)}},
        'allowed_training_groups': sorted(set(dev['groups'])), 'allowed_query_groups': sorted(set(query['groups']))})
    plan = {'protocol': 'postselection_v1', 'mode': 'registered_refits', 'data_scope': 'confirmation',
        'fit_unit': 'task_pipeline_fit', 'fit_budget': {'model': budget, 'calibration': 0}, 'target_policy': 'each_finalist',
        'fit_budget_scope': 'per_finalist',
        'contract': {'path': str(contract), 'sha256': file_digest(contract)},
        'provider': {'path': str(source), 'sha256': file_digest(source)}}
    session.plan_analysis('registered_diagnostic', plan, 'Investigate development residual structure without reselecting on confirmation', session.context()['evidence_id'])
    return session, spec, source, plan


def test_real_analysis_cli_is_report_only_cached_and_absent_from_research_context(tmp_path, capsys):
    s, spec, source, plan = setup(tmp_path)
    with pytest.raises(ValueError, match='Freeze'):
        s.analyze('root', 'registered_diagnostic')
    s.freeze(['root'])
    before = json.loads((s.run / 'session_state.json').read_text())
    context = s.context()
    cli.main(['--run-dir', str(s.run), 'analyze', '--node', 'root', '--analysis', 'registered_diagnostic'])
    result = json.loads(capsys.readouterr().out)
    assert result['model_refits'] == 1 and result['optimization_credit'] == 0
    assert result['metrics']['report_only_value'] == 917.129
    assert s.context()['evidence_id'] == context['evidence_id']
    assert '917.129' not in json.dumps(s.context())
    after = json.loads((s.run / 'session_state.json').read_text())
    assert after['nodes'] == before['nodes'] and after['budget_used'] == before['budget_used']
    assert s.verdict()['postselection_analysis_scope_complete'] is True
    assert s.analyze('root', 'registered_diagnostic') == result
    counter = s.run / 'nodes/root/analyses/registered_diagnostic/fit_counter.txt'
    assert counter.read_text() == '1'
    with pytest.raises(ValueError, match='closed'):
        s.plan_analysis('posthoc', plan, 'must not relabel posthoc work as predeclared', s.context()['evidence_id'])


def test_interrupted_analysis_recovers_receipt_without_another_actual_fit(tmp_path, monkeypatch):
    s, spec, source, plan = setup(tmp_path)
    s.freeze(['root'])
    real = postselection.freeze_record
    def crash(path, value):
        if str(path).endswith('/registered_diagnostic/root.json'):
            raise RuntimeError('simulated process boundary after durable receipt')
        return real(path, value)
    monkeypatch.setattr(postselection, 'freeze_record', crash)
    with pytest.raises(ValueError, match='simulated process boundary'):
        s.analyze('root', 'registered_diagnostic')
    monkeypatch.setattr(postselection, 'freeze_record', real)
    result = s.analyze('root', 'registered_diagnostic')
    assert result['model_refits'] == 1
    counter = s.run / 'nodes/root/analyses/registered_diagnostic/fit_counter.txt'
    assert counter.read_text() == '1'
    assert s.verdict()['postselection_analysis_attempts'] == 1


def test_fit_budget_violation_is_not_a_primary_training_failure_or_reward(tmp_path):
    s, spec, source, plan = setup(tmp_path, budget=0)
    s.freeze(['root'])
    before = json.loads((s.run / 'session_state.json').read_text())
    with pytest.raises(ValueError, match='budget'):
        s.analyze('root', 'registered_diagnostic')
    after = json.loads((s.run / 'session_state.json').read_text())
    assert before['nodes'] == after['nodes'] and before['budget_used'] == after['budget_used']
    assert s.verdict()['postselection_analysis_scope_complete'] is False


def test_scope_and_unregistered_analysis_are_rejected(tmp_path):
    s, spec, source, plan = setup(tmp_path)
    bad = copy.deepcopy(plan)
    bad['data_scope'] = 'all_exposed_secondary'
    with pytest.raises(ValueError, match='historically exposed'):
        s.plan_analysis('not_exposed', bad, 'negative scope test', s.context()['evidence_id'])
    s.freeze(['root'])
    with pytest.raises(ValueError, match='preregistered'):
        s.analyze('root', 'unknown')


def test_analysis_content_drift_cannot_be_silently_repaired_after_freezing(tmp_path):
    s, spec, source, plan = setup(tmp_path)
    s.freeze(['root'])
    source.write_text(ANALYSIS + '\n# modified after selection\n')
    with pytest.raises(ValueError, match='content changed'):
        s.analyze('root', 'registered_diagnostic')
