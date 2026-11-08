import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vc_demo.t47d_research.models import ResearchCandidate, StandaloneNeural
from vc_demo.t47d_research.study import normalize, root_nodes


def bundle():
    rng=np.random.default_rng(17)
    clones=np.repeat([f'c{i}' for i in range(9)],3)
    treatment=np.tile(['giredestrant','palbociclib','combination'],9)
    return {'expression':rng.normal(size=(27,3,24)).astype('float32'),
        'pathway':rng.normal(size=(27,3,50)).astype('float32'),
        'aux':rng.normal(size=(27,9)).astype('float32'),
        'meta':pd.DataFrame({'clone_id':clones,'treatment':treatment,
            'label':rng.normal(size=27),'split':['development']*18+['test']*9})}


@pytest.mark.parametrize('family',['gru','temporal_transformer','gated_pathway','cross_attention','bilinear','moe'])
def test_research_neural_models_predict_target_without_hidden_ridge(family):
    b=bundle();idx=np.arange(18)
    model=StandaloneNeural({'model':family,'representation':'both','epochs':2,'hidden':8,'device':'cpu'}).fit(b,idx,3)
    assert model.base is None
    assert len(model.losses)==2
    pred=model.predict(b,np.arange(18,27))
    assert pred.shape==(9,) and np.isfinite(pred).all()
    model.close()


@pytest.mark.parametrize('composition',['crossfit_residual','crossfit_stack'])
def test_task_composition_never_reads_heldout_targets(composition,tmp_path):
    a=bundle();b=copy.deepcopy(a);b['meta'].loc[18:,'label']=100000.
    parent={'model':'ridge','representation':'pathway','alpha':10,'composition':'replace'}
    config={'model':'ridge','representation':'both','alpha':1,'composition':composition,'parent_config':parent}
    ma=ResearchCandidate(config).fit(a,np.arange(18),3)
    mb=ResearchCandidate(config).fit(b,np.arange(18),3)
    np.testing.assert_allclose(ma.predict(a,np.arange(18,27)),mb.predict(b,np.arange(18,27)))
    stored=ma.model.core_.parent_.bundle if composition=='crossfit_residual' else ma.model.models_[0].bundle
    assert stored['meta'].loc[18:,'label'].isna().all()
    import joblib
    path=tmp_path/'frozen.joblib'
    joblib.dump(ma,path)
    restored=joblib.load(path)
    np.testing.assert_allclose(ma.predict(a,np.arange(18,27)),restored.predict(a,np.arange(18,27)))
    ma.close();mb.close()


def test_exact_historical_recipe_is_preserved_as_a_required_root():
    old=json.loads(Path('experiments/t47d_lineage_resistance_demo/tree.json').read_text())
    result=next(n for n in root_nodes() if n['id']=='root_historical_exact_ridge')
    assert result['config']['historical_recipe']==old['nodes']['root_2_ridge']['config']
    assert len(root_nodes())==6


def test_historical_root_is_exact_and_control_removes_query_identity():
    from vc_demo.t47d_lineage.composition import build_candidate
    b=bundle();idx=np.arange(18);query=np.arange(18,27)
    recipe={'model':'ridge','representation':'pathway','alpha':10,'baseline_only':True}
    c={'model':'historical_ridge','representation':'pathway','historical_recipe':recipe}
    old=build_candidate(recipe).fit(b,idx,3)
    current=ResearchCandidate(c).fit(b,idx,3)
    np.testing.assert_allclose(old.predict(b,query),current.predict(b,query),rtol=0,atol=0)
    c.update(no_barcode_inputs=True,no_clone_abundance=True)
    controlled=ResearchCandidate(c).fit(b,idx,3)
    changed=copy.deepcopy(b)
    changed['pathway'][query]*=100
    changed['expression'][query]*=100
    np.testing.assert_allclose(controlled.predict(b,query),controlled.predict(changed,query))


def test_classical_solver_does_not_claim_unused_epoch_budget():
    assert 'epochs' not in normalize({'model':'ridge','epochs':200})
    assert normalize({'model':'gru','epochs':7})['epochs']==7


def test_representation_identity_includes_content_not_only_size(monkeypatch,tmp_path):
    from vc_demo.t47d_research import runtime
    monkeypatch.chdir(tmp_path)
    source=Path('data/t47d_lineage/prepared/qc_counts.h5ad')
    source.parent.mkdir(parents=True);source.write_bytes(b'abcd')
    monkeypatch.setattr(runtime.importlib.metadata,'version',lambda name:'fixture-version')
    runtime.source_identity.cache_clear()
    b=bundle()
    first,_=runtime.cache_identity(b,np.arange(18),3)
    source.write_bytes(b'dcba');runtime.source_identity.cache_clear()
    second,_=runtime.cache_identity(b,np.arange(18),3)
    assert first!=second
    runtime.source_identity.cache_clear()


def test_search_replenishes_global_pool_and_resume_does_not_repeat_rewards(monkeypatch,tmp_path):
    from vc_demo.t47d_research import study
    from vc_demo.harness.research_contract import digest,write_record
    b=bundle();b['contract']={'label':'explicit fixture target'}
    def load(run):
        write_record(run/'grouped_splits.json',{'unit':'clone','fixture':True})
        return b
    monkeypatch.setattr(study.legacy,'bundle',load)
    monkeypatch.setattr(study.runtime,'configure',lambda:None)
    monkeypatch.setattr(study.legacy,'manifest',lambda:[{'model':'ridge','representation':'pathway','alpha':a} for a in range(1,9)])
    monkeypatch.setattr(study.legacy,'required_choices',lambda space:[])
    monkeypatch.setattr(study,'root_nodes',lambda:[{'id':'root_historical_exact_ridge','name':'root_historical_exact_ridge',
        'config':{'model':'ridge','representation':'pathway'},'status':'candidate_queued','parent':None,
        'children':[],'visits':0,'value':0.,'depth':0}])
    monkeypatch.setattr(study,'recipe',lambda run,n:{'fingerprint':digest(n['config']),
        'code_sha256':{},'data_sha256':{},'artifact_sha256':{}})
    monkeypatch.setattr(study,'input_files',lambda:[])
    monkeypatch.setattr(study,'feedback',lambda *args:None)
    calls=[]
    def evaluate(run,n,bundle):
        calls.append(n['id'])
        return {'status':'trained','validation_reward':.2+len(calls)*.01,'validation_std':.01,
                'duration_seconds':1.,'evidence_phase':'search'}
    monkeypatch.setattr(study,'evaluate',evaluate)
    run=tmp_path/'run'
    study.search(run,2)
    first=json.loads((run/'tree.json').read_text())
    assert len(calls)==3
    assert sum(n['status']=='candidate_queued' for n in first['nodes'].values())>0
    trace=[json.loads(line) for line in (run/'mcts_trace.jsonl').read_text().splitlines()]
    assert sum(t['event']=='rollout_completed_regenerate_next' for t in trace)==2
    assert sum(t['event']=='proposal_generated' for t in trace)>4
    study.search(run,2)
    second=json.loads((run/'tree.json').read_text())
    assert len(calls)==3
    assert {k:n['visits'] for k,n in first['nodes'].items()}=={k:n['visits'] for k,n in second['nodes'].items()}


def test_primary_confirmation_only_predicts_with_frozen_models(monkeypatch,tmp_path):
    from vc_demo.t47d_research import experiment
    from vc_demo.harness.research_contract import write_record
    b=bundle()
    b['meta']['fraction_day26']=.02
    b['meta']['fraction_baseline']=.03
    write_record(tmp_path/'frozen_selection.json',{})
    write_record(tmp_path/'confirmation_lock.json',{'selection_path':str(tmp_path/'frozen_selection.json'),
        'selection_sha256':'frozen','recipes':{}})
    monkeypatch.setattr(experiment,'file_digest',lambda path:'frozen')
    monkeypatch.setattr(experiment.diagnostic,'block_bootstrap',lambda *args:{'fixture':True})
    calls=[]
    class FrozenModel:
        def fit(self,*args):
            raise AssertionError('Confirmation must never fit')
        def predict(self,b,idx):
            calls.append('predict')
            return np.linspace(-.4,.5,len(idx))
        def close(self):
            pass
    class FrozenCalibrator:
        def fit(self,*args):
            raise AssertionError('Confirmation must never calibrate')
        def predict_proba(self,x):
            return np.tile([.4,.6],(len(x),1))
    monkeypatch.setattr(experiment.joblib,'load',lambda p:FrozenCalibrator() if 'calibrator' in str(p) else FrozenModel())
    experiment.confirm(tmp_path,b,{'root':'root','child':'child','checkpoint_files':{}})
    outcome=json.loads((tmp_path/'confirmation_complete.json').read_text())
    assert len(calls)==2*len(experiment.CV_SEEDS)
    assert outcome['model_refits']==outcome['calibration_refits']==0
    assert outcome['further_search_allowed'] is False
