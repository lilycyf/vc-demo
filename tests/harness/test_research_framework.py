import copy
import json
from argparse import Namespace
from pathlib import Path

import numpy as np
import pytest
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge

from vc_demo.harness.research_contract import (
    ResearchContractError, digest, file_digest, freeze_record, executable_recipe,
    register_benchmark, verify_benchmarks, write_record, freeze_selection,
    evaluation_policy, selection_context, validate_hypothesis, validate_protocol,
    task_data_config, capture_execution_recipe,
)
from vc_demo.harness.composition import (
    crossfit_predictions, ResidualCore, CrossFittedResidualRegressor, CrossFittedStackingRegressor,
)
from vc_demo.harness.research_feedback import paired_feedback, ResearchBudget, rank_hypotheses
from vc_demo.harness.feedback import build_framework_feedback
from vc_demo.harness.mcts import backpropagate


def recipe(tmp_path, name='r'):
    code=tmp_path/'model.py';data=tmp_path/'data.bin'
    code.write_text('MODEL=1\n');data.write_bytes(b'1234')
    value=executable_recipe({'node_name':name,'preprocessing':{'encoding':'one_hot','scale':True}},code_files=[code],data_files=[data])
    write_record(tmp_path/'execution_recipes'/(name+'.json'),value)
    return value,code,data


def lock(tmp_path):
    value,code,data=recipe(tmp_path)
    selected=tmp_path/'selected.json';write_record(selected,{'recipe_fingerprints':{'r':value['fingerprint']}})
    freeze_selection(tmp_path,selected)
    return selected,code,data


def test_full_recipe_changes_when_encoding_or_scale_changes(tmp_path):
    a,code,data=recipe(tmp_path)
    for change in ({'encoding':'chemical_indicators','scale':True},{'encoding':'one_hot','scale':False}):
        b=executable_recipe({'preprocessing':change},code_files=[code],data_files=[data])
        assert a['fingerprint']!=b['fingerprint']


def test_same_size_input_mutation_changes_identity(tmp_path):
    a,code,data=recipe(tmp_path);data.write_bytes(b'4321')
    b=executable_recipe(a['effective_config'],code_files=[code],data_files=[data])
    assert a['fingerprint']!=b['fingerprint']


def test_model_code_and_actual_epoch_override_are_fingerprinted(tmp_path):
    a,code,data=recipe(tmp_path);code.write_text('MODEL=2\n')
    b=executable_recipe(a['effective_config'],code_files=[code],data_files=[data],max_epochs=11)
    assert a['fingerprint']!=b['fingerprint']
    assert b['effective_config']['training']['epochs']==11


def test_frozen_contract_is_not_overwritten(tmp_path):
    p=tmp_path/'contract.json';freeze_record(p,{'metric':'rho'})
    with pytest.raises(ResearchContractError):freeze_record(p,{'metric':'mae'})
    assert json.loads(p.read_text())=={'metric':'rho'}


def test_benchmark_content_drift_is_rejected(tmp_path):
    value,code,data=recipe(tmp_path);register_benchmark(tmp_path,'strong',value)
    verify_benchmarks(tmp_path);code.write_text('MODEL=2\n')
    with pytest.raises(ResearchContractError):verify_benchmarks(tmp_path)


def test_historical_benchmark_cannot_be_silently_omitted(tmp_path):
    write_record(tmp_path/'research_protocol.json',{'required_benchmarks':{'historical':'abc'}})
    with pytest.raises(ResearchContractError,match='omitted'):verify_benchmarks(tmp_path)


def test_phase_boundary_requires_real_frozen_recipes(tmp_path):
    with pytest.raises(ResearchContractError):evaluation_policy({'evaluation':{'evaluate_test':True}})
    selected,_,_=lock(tmp_path)
    assert evaluation_policy({'node_name':'r','evaluation':{'phase':'confirmation'}},tmp_path)==('confirmation',True)
    with pytest.raises(ResearchContractError):evaluation_policy({'node_name':'unselected','evaluation':{'phase':'confirmation'}},tmp_path)
    with pytest.raises(ResearchContractError):evaluation_policy({},tmp_path)
    selected.write_text('{}')
    with pytest.raises(ResearchContractError):evaluation_policy({'node_name':'r','evaluation':{'phase':'confirmation'}},tmp_path)


def test_confirmation_count_is_bounded(tmp_path):
    value,_,_=recipe(tmp_path)
    write_record(tmp_path/'research_budget_plan.json',{'confirmation_limit':0})
    p=tmp_path/'selection.json';write_record(p,{'recipe_fingerprints':{'r':value['fingerprint']}})
    with pytest.raises(ResearchContractError,match='budget'):freeze_selection(tmp_path,p)


def test_selected_checkpoint_content_is_frozen(tmp_path):
    value,_,_=recipe(tmp_path)
    checkpoint=tmp_path/'nodes'/'r'/'best.pt'
    checkpoint.parent.mkdir(parents=True);checkpoint.write_bytes(b'selected-weights')
    selected=tmp_path/'selected.json'
    write_record(selected,{'recipe_fingerprints':{'r':value['fingerprint']}})
    result=freeze_selection(tmp_path,selected)
    assert result['checkpoints']['r']['sha256']==file_digest(checkpoint)
    checkpoint.write_bytes(b'different-weights')
    assert result['checkpoints']['r']['sha256']!=file_digest(checkpoint)


def test_protocol_has_task_specific_metric_and_groups():
    protocol={'task_id':'continuous_grouped_task','dataset_sha256':'a'*64,'split_sha256':'b'*64,
        'label_semantics':'continuous response','metric':{'name':'mae','direction':'minimize'},
        'group_key':'independent_donor','input_policy':'baseline only'}
    assert validate_protocol(protocol)==protocol
    del protocol['group_key']
    with pytest.raises(ResearchContractError):validate_protocol(protocol)


def test_nested_heldout_values_and_legacy_feedback_are_scrubbed():
    x={'mean_test':.9,'heldout':{'secret':99},'successes':[{'val':.2,'test':.7}],
       'framework_feedback':{'format':'legacy','policy':{'from_test':1}},'config':{'lr':.01}}
    y=selection_context(x)
    assert y=={'successes':[{'val':.2}],'config':{'lr':.01}}


def tree_with_scores():
    return {'nodes':{'r':{'status':'trained','parent':'','best_val_macro_f1':.6,'test_macro_f1':.9},
        'c':{'status':'trained','parent':'r','strategy':'a_new_family','best_val_macro_f1':.61,'test_macro_f1':.1}}}


def test_test_poisoning_cannot_change_feedback(tmp_path):
    a=tree_with_scores();b=copy.deepcopy(a)
    b['nodes']['r']['test_macro_f1']=-999;b['nodes']['c']['test_macro_f1']=999
    fa=build_framework_feedback(tmp_path,a);fb=build_framework_feedback(tmp_path,b)
    fa.pop('created_at');fb.pop('created_at')
    assert fa==fb
    assert 'official_' not in json.dumps(fa['policy'])


def test_confirmation_nodes_cannot_enter_development_family_statistics(tmp_path):
    tree=tree_with_scores()
    tree['nodes']['heldout_result']={'status':'trained','parent':'r','strategy':'forbidden_family',
        'best_val_macro_f1':999,'evidence_phase':'confirmation'}
    result=build_framework_feedback(tmp_path,tree)
    assert 'forbidden_family' not in result['strategy_stats']


def test_metric_direction_is_not_hardcoded_to_f1(tmp_path):
    t=tree_with_scores();t['research_metric']={'name':'mae','direction':'minimize'}
    f=build_framework_feedback(tmp_path,t)
    assert 'root_dominance' in f['findings']
    assert f['family_stats']['a_new_family']['mean_delta_vs_parent']<0


def test_confirmation_evidence_file_is_rejected(tmp_path):
    write_record(tmp_path/'development_feedback.json',{'evidence_phase':'confirmation'})
    with pytest.raises(ValueError):build_framework_feedback(tmp_path,tree_with_scores())


def sample():
    rng=np.random.default_rng(4);x=rng.normal(size=(36,3));y=x[:,0]*2-x[:,1]+rng.normal(size=36)*.1
    return x,y,np.repeat(np.arange(12),3)


class Memorizer:
    def fit(self,x,y):self.values={tuple(a):b for a,b in zip(x,y)};self.targets_=y.copy();return self
    def predict(self,x):return np.array([self.values.get(tuple(a),0.) for a in x])


def test_oof_errors_are_not_in_sample_errors():
    x,y,g=sample();prediction,audit=crossfit_predictions(Memorizer,x,y,g)
    assert np.all(prediction==0)
    assert all(not set(f['train_groups'])&set(f['validation_groups']) for f in audit)
    model=ResidualCore(Memorizer,Memorizer).fit(x,y,g)
    np.testing.assert_allclose(model.mutation_.targets_,y)


def test_estimator_factory_must_not_reuse_state():
    x,y,g=sample();same=Memorizer()
    with pytest.raises(ValueError,match='reused'):crossfit_predictions(lambda:same,x,y,g)


@pytest.mark.parametrize('model',[CrossFittedResidualRegressor(lambda:Ridge(),lambda:Ridge()),
                                 CrossFittedStackingRegressor([lambda:Ridge(),lambda:DummyRegressor()])])
def test_crossfitted_composition_has_finite_out_of_sample_predictions(model):
    x,y,g=sample();model.fit(x,y,g)
    assert np.isfinite(model.predict(x[:2]+.03)).all()
    assert model.training_groups_==list(map(str,range(12))) or set(model.training_groups_)==set(map(str,range(12)))


def test_residual_weight_training_is_nested_and_group_disjoint():
    x,y,g=sample();m=CrossFittedResidualRegressor(lambda:Ridge(),lambda:Ridge()).fit(x,y,g)
    assert hasattr(m.combiner_,'coef_')
    for outer in m.meta_fold_audit_:
        excluded=set(outer['validation_groups'])
        for inner in outer['inner_folds']:
            assert not excluded & set(inner['train_groups'])
            assert not excluded & set(inner['validation_groups'])


def test_insufficient_groups_never_fall_back_to_training_residuals():
    with pytest.raises(ValueError,match='groups'):
        CrossFittedResidualRegressor(Ridge,Ridge).fit(np.ones((6,2)),np.arange(6.),np.repeat([0,1],3))


def test_paired_block_bootstrap_and_strata():
    y=np.arange(12.);g=np.repeat(np.arange(4),3)
    mae=lambda a,b:np.abs(a-b).mean()
    f=paired_feedback(y,y,y+1,g,mae,direction='minimize',strata=np.tile([0,1],6),draws=20)
    assert f['paired_delta']==1 and f['independent_groups']==4 and f['promotion_supported']
    assert f['delta_ci95']==[1.,1.]
    with pytest.raises(ValueError):paired_feedback(y,y,y,g,mae,evidence_phase='confirmation')


def test_coverage_cannot_take_optimization_or_confirmation_budget():
    b=ResearchBudget(coverage_limit=1,optimization_limit=2,confirmation_limit=1)
    b.consume('coverage')
    with pytest.raises(ValueError):b.consume('coverage')
    b.consume('optimization');b.consume('confirmation')
    with pytest.raises(ValueError):b.consume('optimization')


def test_artifact_presence_is_not_a_scientific_score():
    p={'id':'a','expected_gain':.1,'uncertainty':.2,'estimated_cost':2,'artifact_present':False}
    a=rank_hypotheses([p])[0]['scientific_priority'];p['artifact_present']=True
    assert a==rank_hypotheses([p])[0]['scientific_priority']
    with pytest.raises(ValueError):rank_hypotheses([{**p,'test_score':.9}])


def test_missing_artifact_or_planned_implementation_is_not_a_rank_penalty():
    from vc_demo.harness.program_run import cheap_screen_score
    p={'scientific_selection':{'score':.5},'requires_implementation':True}
    a=cheap_screen_score(p,{})
    b=cheap_screen_score(p,{'missing_required_artifacts':['future_checkpoint']})
    assert a['score']==b['score'] and b['missing_penalty']==0


def test_no_hardcoded_official_model_priority():
    from vc_demo.harness.program_agent import scientific_score
    a=scientific_score('official_aido_string_fusion',{},1)
    b=scientific_score('mixture_of_experts',{},1)
    assert a['score']==b['score'] and a['coverage_bonus']==0


def test_agent_defined_model_survives_materialization(tmp_path):
    from vc_demo.harness.implementation_agent import materialize_model
    p=tmp_path/'model.py';p.write_text('CUSTOM_ARCHITECTURE = True\n');before=p.read_bytes()
    result=materialize_model(tmp_path,'agent_defined_candidate')
    assert p.read_bytes()==before and result['source_kind']=='preserved_agent_program'


def test_parent_summary_never_includes_test_values():
    from vc_demo.harness.program_agent import render_parent_summary
    s=render_parent_summary('r',{'test_macro_f1':.999,'best_val_macro_f1':.2},{},
        {'successes':[{'test':.888,'val':.1}],'framework_feedback':{'format':'legacy','best_test':.777}})
    text=json.dumps(s)
    assert '.999' not in text and '.888' not in text and '.777' not in text


@pytest.mark.parametrize('status',['failed','pruned_not_selected','needs_implementation'])
def test_nontrained_backprop_is_rejected(status):
    with pytest.raises(ValueError):backpropagate({'nodes':{'r':{'status':status}}},'r',.4)


def test_confirmation_and_duplicate_rewards_never_backpropagate():
    t={'nodes':{'r':{'status':'trained','parent':'','visits':0,'value':0.}}}
    backpropagate(t,'r',.4)
    with pytest.raises(ValueError):backpropagate(t,'r',.4)
    t['nodes']['c']={'status':'trained','parent':'r','evidence_phase':'confirmation'}
    with pytest.raises(ValueError):backpropagate(t,'c',.8)


def test_real_task_cannot_fall_back_to_an_implicit_synthetic_dataset():
    with pytest.raises(ResearchContractError):task_data_config({})
    with pytest.raises(ResearchContractError):task_data_config({'data':{'dataset_type':'a'},'dataset':{'dataset_type':'b'}})


def test_agent_hypothesis_can_replace_parent_but_requires_falsification():
    p={'hypothesis':'learn a different representation','evidence_refs':['development_feedback.json'],
       'expected_change':'better within-group ranking','falsification':'no paired gain','composition':'replace','training_policy':{'solver':'closed_form'}}
    assert validate_hypothesis(p)['composition']=='replace'
    del p['falsification']
    with pytest.raises(ResearchContractError):validate_hypothesis(p)


def test_native_train_never_iterates_test_during_search(monkeypatch,tmp_path):
    import torch
    from torch import nn
    import vc_demo.train as training
    class Data:
        def __len__(self):return 4
        def __getitem__(self,i):return {'x':torch.tensor([i,1.,2.,3.]),'y':torch.tensor([i%3,(i+1)%3])}
    class Forbidden:
        def __len__(self):raise AssertionError('Test data accessed during search')
        def __getitem__(self,i):raise AssertionError('Test labels accessed during search')
    class Model(nn.Module):
        def __init__(self):super().__init__();self.linear=nn.Linear(4,6)
        def forward(self,x):return self.linear(x).reshape(len(x),2,3)
    monkeypatch.setattr(training,'build_datasets',lambda cfg:(Data(),Data(),Forbidden()))
    monkeypatch.setattr(training,'build_model',lambda cfg:Model())
    cfg={'node_name':'r','data':{'dataset_type':'synthetic','n_classes':3},
         'model':{'input_dim':4,'n_targets':2,'n_classes':3},'training':{'device':'cpu','epochs':1,'batch_size':2}}
    result=training.train(cfg,tmp_path)
    assert result['test_macro_f1'] is None and result['test_metric_source']=='withheld_until_confirmation'


def test_search_summary_renders_withheld_metrics(tmp_path):
    from vc_demo.harness.report import write_summary
    config=tmp_path/'root.json';write_record(config,{'data':{'dataset_type':'synthetic'},'model':{}})
    tree={'nodes':{'r':{'status':'trained','config':str(config),'iteration':0,'best_val_macro_f1':.4,'test_macro_f1':None}}}
    write_summary(tree,tmp_path/'summary.md',[],'budget exhausted')
    assert 'withheld' in (tmp_path/'summary.md').read_text()


def test_executor_confirmation_uses_frozen_weights_without_retraining(monkeypatch,tmp_path):
    import torch
    from torch import nn
    import vc_demo.train as training
    from vc_demo.harness.executor import run_node
    class Data:
        def __len__(self):return 4
        def __getitem__(self,i):return {'x':torch.tensor([float(i),1.,2.,3.]),'y':torch.tensor([i%3,(i+1)%3])}
    class Forbidden:
        def __len__(self):raise AssertionError('Search opened test')
        def __getitem__(self,i):raise AssertionError('Search opened test')
    class Model(nn.Module):
        def __init__(self):super().__init__();self.linear=nn.Linear(4,6)
        def forward(self,x):return self.linear(x).reshape(len(x),2,3)
    monkeypatch.setattr(training,'build_datasets',lambda cfg:(Data(),Data(),
        Data() if cfg.get('evaluation',{}).get('phase')=='confirmation' else Forbidden()))
    monkeypatch.setattr(training,'build_model',lambda cfg:Model())
    cfg={'node_name':'r','data':{'dataset_type':'synthetic','n_classes':3},
        'model':{'input_dim':4,'n_targets':2,'n_classes':3},'training':{'device':'cpu','epochs':1,'batch_size':2}}
    search=run_node(cfg,tmp_path,None,1)
    assert search['test_macro_f1'] is None
    selection=tmp_path/'selected.json'
    write_record(selection,{'recipe_fingerprints':{'r':search['executable_recipe_fingerprint']}})
    freeze_selection(tmp_path,selection)
    before=file_digest(tmp_path/'nodes'/'r'/'best.pt')
    def forbidden_optimizer(*args,**kwargs):raise AssertionError('Confirmation retrained')
    monkeypatch.setattr(torch.optim,'AdamW',forbidden_optimizer)
    cfg['evaluation']={'phase':'confirmation'}
    confirmed=run_node(cfg,tmp_path,None,1)
    assert confirmed['test_macro_f1'] is not None
    assert file_digest(tmp_path/'nodes'/'r'/'best.pt')==before
    assert (tmp_path/'confirmation'/'r'/'metrics.json').exists()
    assert json.loads((tmp_path/'nodes'/'r'/'metrics.json').read_text())['test_macro_f1'] is None
    cfg['training']['lr']=.1
    with pytest.raises(ResearchContractError):run_node(cfg,tmp_path,None,1)


def test_acquisition_does_not_accept_blank_or_empty_model_paths(tmp_path):
    from vc_demo.harness.artifact_acquisition import resolve_item
    from vc_demo.harness.artifact_registry import path_is_present
    directory=tmp_path/'empty_model';directory.mkdir()
    assert not path_is_present(directory)
    (directory/'.gitattributes').write_text('not a checkpoint')
    assert not path_is_present(directory)
    assert not path_is_present(Path('.'))
    output=tmp_path/'tasks';output.mkdir()
    for path in ('',str(directory)):
        result=resolve_item({'artifact_id':'absent','expected_path':path},{},{'artifacts':[]},
                            output,False,'unseen_task',tmp_path/'registry.json')
        assert result['status']=='requires_codex_research_download_or_build'
        assert not result['present_after']


def test_realtime_resolver_receives_active_task_and_registry(monkeypatch,tmp_path):
    from vc_demo.harness import program_run
    monkeypatch.setattr(program_run,'load_registry',lambda *a:{'artifacts':[]})
    monkeypatch.setattr(program_run,'source_map',lambda *a:{})
    calls=[]
    def resolve(*args,**kwargs):calls.append(kwargs);return {'status':'research_required'}
    monkeypatch.setattr(program_run,'resolve_item',resolve)
    args=Namespace(cell_line='unseen_task',artifact_registry=tmp_path/'registry.json')
    program_run.attempt_realtime_artifact_acquisition(tmp_path,args,'child',{'strategy':'new'},
        {'missing_required_artifacts':['missing']})
    assert calls[0]['cell_line']=='unseen_task'
    assert calls[0]['registry_path']==args.artifact_registry


def test_verified_unavailable_artifact_does_not_stop_other_queued_research(tmp_path):
    import runpy
    runner=runpy.run_path('scripts/run_generic_cellline_transfer_test.py')
    write_record(tmp_path/'tree.json',{'nodes':{'next':{'status':'candidate_queued'}}})
    write_record(tmp_path/'acquisition_queue.json',{'items':[{'artifact_id':'unavailable'}]})
    proceed=runner['full_run_continue_reason']
    assert not proceed(tmp_path,None,5)[0]
    evidence=tmp_path/'source_checks.md';evidence.write_text('Primary source checked; public files incomplete.')
    write_record(tmp_path/'artifact_acquisition'/'verified_blockers.json',{'items':[{
        'artifact_id':'unavailable','status':'blocked_unavailable_primary_artifact',
        'sources_checked':['https://example.org/primary'],
        'evidence_files':{str(evidence):file_digest(evidence)}}]})
    assert proceed(tmp_path,None,5)[0]
    evidence.write_text('Changed evidence')
    assert not proceed(tmp_path,None,5)[0]


def test_backprop_rejects_invalid_ancestor_path_without_partial_updates():
    tree={'nodes':{'a':{'status':'trained','parent':'a','visits':0,'value':0}}}
    with pytest.raises(ValueError):backpropagate(tree,'a',.5)
    assert tree['nodes']['a']['visits']==0


def test_resume_patience_counts_only_completed_optimization_evidence():
    from vc_demo.harness.program_run import development_progress
    tree=tree_with_scores()
    tree['nodes']['c']['iteration']=1
    tree['nodes']['coverage']={'status':'trained','parent':'r','budget_phase':'coverage',
        'iteration':2,'best_val_macro_f1':.62}
    tree['nodes']['lower']={'status':'trained','parent':'r','iteration':3,'best_val_macro_f1':.60}
    tree['nodes']['unavailable']={'status':'requires_artifact_acquisition','parent':'r','iteration':4}
    tree['nodes']['unselected']={'status':'pruned_not_selected','parent':'r','iteration':5}
    assert development_progress(tree,.001)==(.62,1)
    restored=json.loads(json.dumps(tree))
    assert development_progress(restored,.001)==(.62,1)


def test_registered_protocol_cannot_be_edited_outside_registration(tmp_path):
    from vc_demo.harness.research_contract import register_protocol, verify_protocol
    protocol={'task_id':'task','dataset_sha256':'a'*64,'split_sha256':'b'*64,
        'label_semantics':'continuous','metric':{'name':'mae','direction':'minimize'},
        'group_key':'donor','input_policy':'baseline only'}
    register_protocol(tmp_path,protocol)
    assert verify_protocol(tmp_path)==protocol
    protocol['input_policy']='all timepoints'
    write_record(tmp_path/'research_protocol.json',protocol)
    with pytest.raises(ResearchContractError,match='changed'):verify_protocol(tmp_path)
