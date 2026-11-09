import copy
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from vc_demo.harness.research_contract import file_digest, write_record
from vc_demo.harness.research_v2.identity import artifact_identity, semantic_identity
from vc_demo.harness.research_v2.metrics import MetricSpec, paired_evidence
from vc_demo.harness.research_v2.policy import backpropagate, eligible_parents, priority
from vc_demo.harness.research_v2.session import Session
from vc_demo.harness.research_v2.verdicts import control_verdict


PROVIDER = '''import json
from pathlib import Path
import joblib
import numpy as np
from functools import partial
from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.linear_model import Ridge, LogisticRegression
from vc_demo.harness.composition import CrossFittedResidualRegressor, CrossFittedStackingRegressor

class SavedEnsemble:
    def __init__(self,models):self.models=models

def evaluate_development(request):
    c=request['development_contract'];p=request['recipe']['parameters']
    x=np.array(json.loads(Path(request['inputs']['features']['path']).read_text())['x'])
    y=np.array(c['targets']);groups=np.array(c['groups']);seeds=c['seeds']
    classification=request['metric']['name']=='macro_f1'
    shape=(len(y),len(seeds),2) if classification else (len(y),len(seeds))
    pred=np.zeros(shape);models=[];combination=[]
    output=Path(request['output_dir']);counter=output/'fit_counter.txt'
    count=int(counter.read_text()) if counter.exists() else 0
    for fold in c['folds']:
        train=np.flatnonzero(np.isin(groups,fold['train_groups']))
        valid=np.flatnonzero(np.isin(groups,fold['validation_groups']))
        seed=fold['seed'];j=seeds.index(seed)
        actual_seed=(request.get('replicate') or {}).get('training_seed',seed)
        np.random.seed(actual_seed)
        if classification:model=(DummyClassifier() if p['kind']=='dummy_classifier' else LogisticRegression(C=p['alpha'],max_iter=1000,random_state=actual_seed))
        elif p['kind']=='dummy':model=DummyRegressor()
        elif p['kind']=='stack':model=CrossFittedStackingRegressor([partial(DummyRegressor),partial(Ridge,alpha=p['alpha'])],splits=3,meta_factory=partial(Ridge,alpha=1.))
        elif p['kind']=='residual':model=CrossFittedResidualRegressor(partial(DummyRegressor),partial(Ridge,alpha=p['alpha']),splits=3,weight_factory=partial(Ridge,alpha=1.))
        else:model=Ridge(alpha=p.get('alpha',1.))
        if p['kind'] in {'stack','residual'}:
            model.fit(x[train],y[train],groups=groups[train])
            inner=[]
            if p['kind']=='stack':
                for records in model.fold_audit_:inner.extend(records)
            else:
                for f in model.meta_fold_audit_:
                    inner.append({k:f[k] for k in ('train_groups','validation_groups')})
                    inner.extend(f['inner_folds'])
            combination.append({'seed':seed,'fold_id':fold['fold_id'],'weight_training':'grouped_oof',
                'weight_fit_groups':model.training_groups_,'inner_folds':inner})
        else:model.fit(x[train],y[train])
        count+=1
        counter.write_text(str(count))
        pred[valid,j]=model.predict_proba(x[valid]) if classification else model.predict(x[valid])
        models.append((seed,model))
    path=output/'model.joblib';joblib.dump(SavedEnsemble(models),path)
    table={key:c[key] for key in ('row_ids','groups','targets','seeds','fold_ids')}
    table.update(predictions=pred.tolist(),metric_id=request['metric_id'],evidence_phase='development')
    if p.get('bad_metric'):table['metric_id']='wrong-metric'
    return {'prediction_table':table,'fit_audit':c['folds'],'checkpoint_files':[str(path)],
        'diagnostics':{'solver':p['kind'],'converged':True,'train_loss':None,
            'inner_validation_policy':'none; fixed solver before outer OOF','outer_fit_count':len(c['folds']),
            'total_solver_fit_count':len(c['folds'])*(9 if p['kind']=='stack' else 21 if p['kind']=='residual' else 1)},
        'consumed_artifact_roles':[],'composition_audit':combination or None,'consumed_module_roles':['module:'+p['kind']]}

def predict_confirmation(request):
    c=request['confirmation_contract'];x=np.array(c['features'])
    classification=request['metric']['name']=='macro_f1'
    models=joblib.load(next(iter(request['checkpoint_files']))).models
    predictions=[]
    for seed in c['seeds']:
        values=[m.predict_proba(x) if classification else m.predict(x) for s,m in models if s==seed]
        predictions.append(np.mean(values,axis=0))
    table={key:c[key] for key in ('row_ids','groups','targets','seeds')}
    table.update(predictions=np.stack(predictions,axis=1).tolist(),metric_id=request['metric_id'],evidence_phase='confirmation')
    return {'prediction_table':table,'model_refits':0,'calibration_refits':0}
'''


def setup(tmp_path, *, coverage=0, optimization=1, classification=False, constant=False, parent_policy='uct_parent_scheduler'):
    tmp_path.mkdir(exist_ok=True,parents=True)
    x=np.linspace(-1,1,24).reshape(-1,1)
    y=(x[:,0]>0).astype(int) if classification else np.ones(24)*.7 if constant else 3*x[:,0]+.2
    groups=[f'g{i//2}' for i in range(24)];seeds=[3,7]
    folds=[]
    unique=sorted(set(groups))
    for seed in seeds:
        for k in range(3):
            valid=unique[k::3]
            folds.append({'seed':seed,'fold_id':str(k),'train_groups':[g for g in unique if g not in valid],
                'validation_groups':valid})
    contract={'row_ids':[f'r{i}' for i in range(24)],'groups':groups,'targets':y.tolist(),'seeds':seeds,'folds':folds}
    contract['fold_ids']=[[next(f['fold_id'] for f in folds if f['seed']==seed and group in f['validation_groups'])
                          for seed in seeds] for group in groups]
    data=tmp_path/'features.json';write_record(data,{'x':x.tolist()})
    source=tmp_path/'development.json';write_record(source,contract)
    provider=tmp_path/'provider.py';provider.write_text(PROVIDER)
    confirmation=tmp_path/'confirmation.json'
    write_record(confirmation,{'row_ids':['h0','h1'],'groups':['outside0','outside1'],'targets':[0,1] if classification else [-.7,1.1],
        'seeds':seeds,'features':[[-.3],[.3]]})
    metric=MetricSpec('macro_f1' if classification else 'mae','maximize' if classification else 'minimize',
        'mean_seed','observation','group',labels=(0,1) if classification else ())
    spec={'schema_version':'research_v2','task_id':'cpu_contract_fixture','dataset_sha256':file_digest(data),
        'split_sha256':file_digest(source),'label_semantics':'engineering fixture only, not scientific task results',
        'input_policy':'grouped development OOF; no confirmation features/labels in provider requests',
        'prior_test_exposure':False,'metric':metric.__dict__,'development_contract':str(source),
        'confirmation_contract':{'path':str(confirmation),'sha256':file_digest(confirmation)},
        'inputs':{'features':{'path':str(data),'sha256':file_digest(data),'scope':'development'}},
        'benchmarks':['root'],'reference_benchmark':'root','budget':{'coverage':coverage,'optimization':optimization,'confirmation':2},
        'benchmark_recipes':{'root':{'parameters':{'kind':'dummy_classifier' if classification else 'dummy'},
            'training':{'policy':'fixed solver; no validation tuning'},'code_sha256':{'provider':file_digest(provider)},
            'input_sha256':{'features':file_digest(data)},'artifact_sha256':{},'environment':{}}},
        'minimum_effect':0.,'policy':{'parent_policy':parent_policy,'queue_capacity':8,'min_new_proposals':1,
            'parent_active_limit':2,'exploration':1.,'uncertainty_weight':1.,'cost_penalty_per_hour':.01,'bootstrap_draws':30},
        'resources':{'authorization_id':'CPU unit/integration fixture; no cloud experiment','deadline_utc':'2099-01-01T00:00:00+00:00'}}
    session=Session.initialize(tmp_path/'run',spec)
    return session,spec,provider


def proposal(session,name,*,phase='optimization',kind='ridge',alpha=1.,parent='root',composition='replace',bad=False):
    context=session.context()
    parameters={'kind':kind}
    if kind in {'ridge','logistic','stack','residual'}:parameters['alpha']=alpha
    if bad:parameters['bad_metric']=True
    return {'id':name,'phase':phase,'parent_id':parent if phase!='benchmark' else None,
        'proposed_recipe':{'parameters':parameters,'training':{'policy':'fixed solver; no validation tuning'}},
        'required_artifacts':{},'hypothesis':{'statement':'Evaluate the declared model using group-only training.',
            'expected_change':'Improve paired development error; a null effect keeps the exact baseline.',
            'falsification':'No practical paired gain versus the registered reference.',
            'evidence_ids':[context['evidence_id']],'composition':composition,
            'parent_conditioning':'Test whether modeling the available feature explains parent residual error.',
            'parent_override_reason':'Use the unchanged baseline as a controlled reference rather than the top UCT suggestion.'},
        'estimate':{'metric_id':context['metric_id'],'expected_gain':.01,'uncertainty':.02,
            'cost_seconds':{'acquisition':0,'cache_miss':0,'fit':1,'evaluation':1},
            'basis':'hypothesis','rationale':'Unmeasured engineering-fixture assumption, not a confidence interval.'}}


def seal(session,node,provider,*,artifact_files=None):
    spec,state=session._load();n=state['nodes'][node]
    recipe={**n['proposed_recipe'],'code_sha256':{'provider':file_digest(provider)},
        'input_sha256':{k:v['sha256'] for k,v in spec['inputs'].items()},
        'artifact_sha256':{k:artifact_identity(v['path']) for k,v in (artifact_files or {}).items()},'environment':{}}
    return session.seal(node,{'code_files':{'provider':str(provider)},'artifact_files':artifact_files or {}},recipe)


def train_root(session,provider,classification=False):
    p=proposal(session,'root',phase='benchmark',kind='dummy_classifier' if classification else 'dummy')
    session.propose([p]);assert session.select()['id']=='root';seal(session,'root',provider);session.execute('root')


def test_reward_feedback_estimand_cannot_silently_reverse():
    table={'row_ids':list('abcde'),'groups':list('abcde'),'targets':list(range(5)),'seeds':[3,7],
        'fold_ids':[['0','0']]*5,'evidence_phase':'development'}
    mean=MetricSpec('spearman','maximize','mean_seed','row','group')
    ensemble=MetricSpec('spearman','maximize','ensemble','row','group')
    reference={**table,'predictions':np.column_stack([np.arange(5)*100,np.arange(4,-1,-1)]).tolist(),'metric_id':mean.identity}
    candidate={**table,'predictions':np.tile(np.array([0,2,1,4,3])[:,None],(1,2)).tolist(),'metric_id':mean.identity}
    evidence=paired_evidence(mean,candidate,reference,draws=20)
    assert evidence['paired_delta']==pytest.approx(mean.score(candidate)-mean.score(reference))
    assert evidence['paired_delta']>0 and ensemble.score(candidate)-ensemble.score(reference)<0
    with pytest.raises(ValueError):paired_evidence(ensemble,candidate,reference)


def test_macro_f1_uses_fixed_probability_vocabulary():
    m=MetricSpec('macro_f1','maximize','ensemble','row','group',labels=(0,1,2))
    table={'row_ids':['a','b'],'groups':['a','b'],'targets':[0,1],'seeds':[3,7],
        'predictions':[[[.9,.1,0],[.8,.2,0]],[[.1,.9,0],[.2,.8,0]]]}
    assert m.score(table)==pytest.approx(2/3)
    table['predictions']=[[0,0],[1,1]]
    with pytest.raises(ValueError):m.score(table)


def test_custom_task_metric_is_content_addressed_not_location_addressed(tmp_path):
    code='from sklearn.metrics import r2_score\ndef score(y,p): return r2_score(y,p)\n'
    a=tmp_path/'a.py';a.write_text(code);b=tmp_path/'b.py';b.write_text(code)
    args={'name':'task_r2','direction':'maximize','aggregation':'mean_seed','prediction_unit':'row','group_key':'group',
          'scorer_path':str(a),'scorer_sha256':file_digest(a)}
    ma=MetricSpec(**args);mb=MetricSpec(**dict(args,scorer_path=str(b)))
    assert ma.identity==mb.identity
    table={'row_ids':['a','b'],'groups':['a','b'],'targets':[0.,1.],'seeds':[3],'predictions':[[0.],[1.]]}
    assert ma.score(table)==1
    a.write_text(code+'# actual source changed\n')
    with pytest.raises(ValueError):ma.score(table)


def test_custom_metric_accepts_structured_multioutput_without_regression_fallback(tmp_path):
    source=tmp_path/'multioutput_score.py'
    source.write_text('from sklearn.metrics import mean_squared_error\ndef score(y,p): return mean_squared_error(y,p)\n')
    metric=MetricSpec('structured_mse','minimize','mean_seed','subject','subject',
        scorer_path=str(source),scorer_sha256=file_digest(source),prediction_kind='structured')
    table={'row_ids':['a','b'],'groups':['a','b'],'targets':[[0.,1.],[2.,3.]],'seeds':[3],
        'predictions':[[[0.,1.]],[[2.,3.]]]}
    assert metric.score(table)==0


def test_coverage_does_not_exhaust_or_backpropagate_into_strong_root():
    nodes={'root':{'status':'trained','phase':'benchmark','score':.9,'children':list(range(26))}}
    for i in range(26):
        nodes[str(i)]={'status':'trained','phase':'coverage','reference_id':'root','parent_id':None,'score':.1}
    assert 'root' in eligible_parents(nodes,20)
    with pytest.raises(ValueError):backpropagate(nodes,'0',.1)
    assert nodes['root'].get('optimization_visits',0)==0
    nodes['opt']={'status':'trained','phase':'optimization','parent_id':'root','relation':'replace','score':.95}
    assert backpropagate(nodes,'opt',.95)==['opt','root']
    assert nodes['root']['score']==.9 and nodes['root']['optimization_visits']==1
    with pytest.raises(ValueError):backpropagate(nodes,'opt',.95)
    assert nodes['root']['optimization_visits']==1


@pytest.mark.parametrize('gain',[-.5,0.,.5])
def test_cost_cannot_invert_priority_for_negative_gain(gain):
    estimate={'expected_gain':gain,'uncertainty':.01,'basis':'hypothesis','rationale':'explicit assumption',
        'cost_seconds':dict(acquisition=0,cache_miss=0,fit=1,evaluation=0)}
    policy={'uncertainty_weight':1,'cost_penalty_per_hour':1}
    cheap=priority(estimate,policy)['scientific_priority']
    estimate['cost_seconds']['fit']=100
    assert priority(estimate,policy)['scientific_priority']<cheap
    same=priority(estimate,policy)
    estimate['artifact_present']=True
    assert priority(estimate,policy)==same


def test_semantic_identity_changes_for_training_not_runtime_location():
    r={'parameters':{'width':8},'training':{'epochs':3},'code_sha256':{'model':'abc'},
       'input_sha256':{'table':'def'},'artifact_sha256':{},'environment':{'numpy':'version'}}
    first=semantic_identity(r,'metric')
    other=copy.deepcopy(r);other['training']['epochs']=4
    assert semantic_identity(other,'metric')!=first
    other=copy.deepcopy(r);other['parameters']['output_dir']='another-node'
    with pytest.raises(ValueError):semantic_identity(other,'metric')


def test_same_name_weakened_benchmark_cannot_replace_registered_recipe(tmp_path):
    session,spec,provider=setup(tmp_path)
    p=proposal(session,'root',phase='benchmark',kind='ridge')
    session.propose([p]);session.select()
    with pytest.raises(ValueError,match='Exact benchmark recipe changed'):seal(session,'root',provider)


@pytest.mark.parametrize('classification',[False,True])
def test_real_provider_full_cycle_replenishment_confirmation_and_exactly_once(tmp_path,classification):
    session,spec,provider=setup(tmp_path,optimization=2,classification=classification)
    train_root(session,provider,classification)
    for index in range(2):
        name=f'child{index}'
        session.propose([proposal(session,name,kind='logistic' if classification else 'ridge',alpha=index+1)])
        assert session.select()['id']==name
        seal(session,name,provider);receipt=session.execute(name)
        _,state=session._load();assert state['budget_used']['optimization']==index+1
        counter=session.run/'nodes'/name/'fit_counter.txt';before=counter.read_text()
        session.execute(name)
        assert counter.read_text()==before
        assert state['nodes'][name]['optimization_visits']==1
        if index==0:
            assert session.context()['next_action']=='research_and_submit_new_proposals_now'
            with pytest.raises(ValueError,match='Replenish'):session.select()
    before={p:str(p.read_text()) for p in (session.run/'nodes').glob('*/fit_counter.txt')}
    session.freeze(['root','child1'])
    with pytest.raises(ValueError):session.propose([proposal(session,'closed')])
    result=session.confirm('child1')
    assert result['model_refits']==result['calibration_refits']==0
    assert before=={p:str(p.read_text()) for p in (session.run/'nodes').glob('*/fit_counter.txt')}
    assert session.confirm('child1')==result
    assert session.verdict()['execution_complete']


def test_real_coverage_is_separate_from_optimizer_credit(tmp_path):
    session,spec,provider=setup(tmp_path,coverage=3)
    train_root(session,provider)
    for i in range(3):
        session.propose([proposal(session,f'coverage{i}',phase='coverage',alpha=i+1)])
        session.select();seal(session,f'coverage{i}',provider);session.execute(f'coverage{i}')
    context=session.context()
    assert 'root' in {r['node'] for r in context['parent_ranking']}
    _,state=session._load()
    assert state['nodes']['root']['optimization_visits']==0
    assert state['budget_used']==dict(coverage=3,optimization=0,confirmation=0)


def test_duplicate_execution_locations_reuse_evidence_without_new_reward(tmp_path):
    session,spec,provider=setup(tmp_path)
    train_root(session,provider)
    session.propose([proposal(session,'same_model_elsewhere',kind='dummy')]);session.select()
    copy_path=tmp_path/'same_content.py';copy_path.write_bytes(provider.read_bytes())
    assert seal(session,'same_model_elsewhere',copy_path)=={'duplicate_of':'root'}
    _,state=session._load()
    assert state['budget_used']['optimization']==0 and state['nodes']['root']['optimization_visits']==0
    assert not (session.run/'nodes'/'same_model_elsewhere').exists()


def test_explicit_replicate_is_not_a_new_semantic_architecture(tmp_path):
    session,spec,provider=setup(tmp_path)
    train_root(session,provider)
    p=proposal(session,'registered_repeat',kind='dummy')
    p['replicate']={'id':'numeric_repeat','purpose':'determinism engineering check, not new data','training_seed':11}
    session.propose([p]);session.select();seal(session,'registered_repeat',provider);session.execute('registered_repeat')
    verdict=session.verdict()
    assert verdict['trained_measurements']==2 and verdict['unique_semantic_candidates']==1


def test_bad_provider_repairs_or_skips_and_continues_queue(tmp_path):
    session,spec,provider=setup(tmp_path)
    train_root(session,provider)
    a=proposal(session,'a_bad',bad=True);b=proposal(session,'b_good')
    session.propose([a,b]);assert session.select()['id']=='a_bad';seal(session,'a_bad',provider)
    with pytest.raises(ValueError,match='Repair'):session.execute('a_bad')
    assert session.context()['next_action']=='implement_repair_acquire_or_execute_selected_now'
    with pytest.raises(ValueError):session.skip('a_bad','no attempt',[])
    session.skip('a_bad','Metric contract violation after actual evaluation',[
        {'action':'compiled and executed the provider; inspected returned metric ID','evidence':'recorded repair error and node fit counter'}])
    assert session.select()['id']=='b_good';seal(session,'b_good',provider);session.execute('b_good')
    _,state=session._load();assert state['budget_used']['optimization']==1
    assert not state['nodes']['a_bad'].get('reward_applied')


def test_test_poisoning_cannot_change_development_context(tmp_path):
    session,spec,provider=setup(tmp_path)
    train_root(session,provider)
    before=session.context()
    path=Path(spec['confirmation_contract']['path']);value=json.loads(path.read_text());value['targets']=[1e9,-1e9];write_record(path,value)
    assert session.context()==before
    assert before['prior_test_exposure'] is False
    p=proposal(session,'forbidden_feedback');p['hypothesis']['test_metrics']={'score':99}
    with pytest.raises(ValueError,match='Heldout'):session.propose([p])


def test_stale_hypothesis_snapshot_and_unproven_measured_gain_are_rejected(tmp_path):
    session,spec,provider=setup(tmp_path);train_root(session,provider)
    a=proposal(session,'a');b=proposal(session,'b')
    session.propose([a])
    with pytest.raises(ValueError,match='current immutable'):session.propose([b])
    b=proposal(session,'b');b['estimate']['basis']='measured';b['estimate']['evidence_node']='root'
    with pytest.raises(ValueError,match='actual matching'):session.propose([b])


def test_pruned_proposals_and_insufficient_budgets_cannot_be_trained_or_frozen(tmp_path):
    session,spec,provider=setup(tmp_path)
    train_root(session,provider)
    session.propose([proposal(session,f'c{i}',alpha=i+1) for i in range(10)])
    _,state=session._load();pruned=[n for n in state['nodes'].values() if n['status']=='pruned_not_selected']
    assert len(pruned)==2
    with pytest.raises(ValueError):seal(session,pruned[0]['id'],provider)
    with pytest.raises(ValueError):session.execute(pruned[0]['id'])
    with pytest.raises(ValueError,match='allocations remain'):session.freeze(['root'])


def test_no_incremental_signal_retains_exact_baseline(tmp_path):
    session,spec,provider=setup(tmp_path,constant=True);train_root(session,provider)
    session.propose([proposal(session,'unhelpful_complexity')]);session.select();seal(session,'unhelpful_complexity',provider);session.execute('unhelpful_complexity')
    verdict=session.verdict()
    assert verdict['retained_baseline']=='root' and not verdict['development_promotion_supported']


def test_unchanged_unused_ablation_is_not_artifact_validation():
    assert control_verdict(removed_roles=['pathway'],consumed_roles=['graph'],
        changed_dependency_identity=False,removed_roles_still_consumed=[])['applicability']=='not_applicable'
    result=control_verdict(removed_roles=['graph'],consumed_roles=['graph'],
        changed_dependency_identity=False,removed_roles_still_consumed=['graph'])
    assert not result['control_applied']


def test_controls_are_reachable_through_shared_session_and_report(tmp_path):
    session,spec,provider=setup(tmp_path);train_root(session,provider)
    unused=session.record_control('unused_pathway','root',['pathway'],rationale='The actual baseline does not consume pathways.')
    assert unused['applicability']=='not_applicable'
    session.propose([proposal(session,'linear')]);session.select();seal(session,'linear',provider);session.execute('linear')
    applied=session.record_control('remove_linear','linear',['module:ridge'],intervention='root',
        rationale='Compare the actually trained feature model with the fixed feature-ignoring baseline.')
    assert applied['control_applied']
    assert 'paired_development_evidence' in applied
    assert session.verdict()['control_results']['unused_pathway']['applicability']=='not_applicable'


def test_missing_coverage_does_not_block_unrelated_optimization(tmp_path):
    session,spec,provider=setup(tmp_path,coverage=1)
    train_root(session,provider)
    session.propose([proposal(session,'unavailable_coverage',phase='coverage')]);session.select()
    session.skip('unavailable_coverage','Primary files genuinely unavailable after research',[
        {'action':'searched authoritative sources and inspected downloads','evidence':'verified source/content reports'}])
    assert session.context()['next_action']=='research_and_submit_new_proposals_now'
    session.propose([proposal(session,'feasible')]);session.select();seal(session,'feasible',provider);session.execute('feasible')
    result=session.verdict()
    assert result['execution_complete'] and result['coverage']==0
    assert result['coverage_inventory_handled']==1 and result['coverage_gaps']==['unavailable_coverage']


def test_required_checkpoint_cannot_be_omitted_or_replaced_by_a_graph(tmp_path):
    session,spec,provider=setup(tmp_path);train_root(session,provider)
    p=proposal(session,'authentic_encoder')
    p['required_artifacts']={'encoder':{'kind':'pretrained_checkpoint','allowed_statuses':['original_public'],
        'required_files':['config.json','model.safetensors']}}
    session.propose([p]);session.select()
    with pytest.raises(ValueError,match='required artifacts'):seal(session,'authentic_encoder',provider)
    graph=tmp_path/'graph.tsv';graph.write_text('a\tb\n')
    artifact={'encoder':{'path':str(graph),'source':'explicit unit-test fixture, not an authentic model',
        'status':'original_public','alignment':'unit-test-only','kind':'graph'}}
    with pytest.raises(ValueError,match='not the required module'):seal(session,'authentic_encoder',provider,artifact_files=artifact)


def test_artifact_directories_must_have_real_contents_and_can_use_cache_links(tmp_path):
    directory=tmp_path/'model';directory.mkdir();(directory/'.gitattributes').write_text('metadata only')
    with pytest.raises(ValueError,match='model-card-only'):artifact_identity(directory)
    blob=tmp_path/'blob';blob.write_bytes(b'engineering fixture, never a scientific checkpoint')
    (directory/'weights').symlink_to(blob)
    first=artifact_identity(directory)
    blob.write_bytes(b'changed fixture bytes')
    assert artifact_identity(directory)!=first


def test_actual_shared_cli_initializes_and_reads_same_core_state(tmp_path):
    session,spec,provider=setup(tmp_path/'old')
    spec_path=tmp_path/'spec.json';write_record(spec_path,spec)
    run=tmp_path/'cli_run'
    base=[sys.executable,'scripts/run_research_harness.py','--run-dir',str(run)]
    init=subprocess.run(base+['init','--spec',str(spec_path)],text=True,capture_output=True,check=True)
    context=json.loads(init.stdout)
    assert context['next_action']=='submit_or_execute_required_benchmarks'
    assert 'confirmation_contract' not in context
    assert json.loads(subprocess.check_output(base+['context'],text=True))==context
    report=json.loads(subprocess.check_output(base+['report'],text=True))
    assert not report['execution_complete'] and report['trained_measurements']==0


@pytest.mark.parametrize('kind,composition',[('stack','crossfit_stack'),('residual','crossfit_residual')])
def test_open_composition_reaches_real_grouped_inner_training(tmp_path,kind,composition):
    session,spec,provider=setup(tmp_path);train_root(session,provider)
    session.propose([proposal(session,'combined',kind=kind,composition=composition)])
    session.select();seal(session,'combined',provider)
    result=session.execute('combined')
    assert len(result['composition_audit'])==6
    assert result['diagnostics']['total_solver_fit_count']>result['diagnostics']['outer_fit_count']
    assert session.verdict()['combination_fits_with_validated_inner_group_audits']==1
    session.freeze(['root','combined']);assert session.confirm('combined')['model_refits']==0


def test_invalid_inner_combination_audit_rejects_validation_group_leakage():
    contract={'folds':[{'seed':3,'fold_id':'0','train_groups':['a','b'],'validation_groups':['outside']}]}
    bad=[{'seed':3,'fold_id':'0','weight_training':'grouped_oof','weight_fit_groups':['a','b'],
        'inner_folds':[{'train_groups':['a','outside'],'validation_groups':['b']}]}]
    with pytest.raises(ValueError,match='leaks'):Session._composition_audit(bad,contract)


def test_queued_estimates_revise_only_against_immutable_current_evidence(tmp_path):
    session,spec,provider=setup(tmp_path);train_root(session,provider)
    a=proposal(session,'a');b=proposal(session,'b',alpha=2)
    session.propose([a,b]);context=session.context()
    estimate=copy.deepcopy(b['estimate']);estimate['expected_gain']=.5
    session.rerank({'b':estimate},context['evidence_id'])
    assert session.select()['id']=='b'
    with pytest.raises(ValueError):session.rerank({'a':estimate},context['evidence_id'])


def test_exhaustion_requires_registered_policy_and_still_drains_queue(tmp_path):
    session,spec,provider=setup(tmp_path/'not_allowed')
    with pytest.raises(ValueError,match='not registered'):
        session.declare_exhaustion('No further feasible design',[{'action':'investigated','evidence':'research records'}])
    spec['policy']['allow_documented_exhaustion']=True
    session=Session.initialize(tmp_path/'allowed',spec);train_root(session,provider)
    session.propose([proposal(session,'last')])
    session.declare_exhaustion('All additional registered hypotheses require unavailable inputs',
        [{'action':'searched primary sources and attempted actual implementation','evidence':'source-backed attempt logs'}])
    assert session.context()['next_action']=='rerank_global_queue_and_select'
    session.select();seal(session,'last',provider);session.execute('last')
    session.freeze(['root','last'])


def test_legacy_frontdoor_cannot_silently_launch_fresh_v1_research(tmp_path):
    import importlib.util
    from types import SimpleNamespace
    path=Path('scripts/run_generic_cellline_transfer_test.py')
    spec=importlib.util.spec_from_file_location('legacy_classification_guard',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    args=SimpleNamespace(execute=True,legacy_protocol=False,resume=False,run_dir=tmp_path)
    with pytest.raises(SystemExit,match='research_v2'):module.validate_legacy_execution(args)
    args.legacy_protocol=True;args.resume=True
    with pytest.raises(SystemExit,match='existing run state'):module.validate_legacy_execution(args)
    write_record(tmp_path/'tree.json',{'nodes':{'old':{'status':'trained'}}})
    module.validate_legacy_execution(args)
    write_record(tmp_path/'confirmation_lock.json',{'further_search_allowed':False})
    with pytest.raises(SystemExit,match='closed'):module.validate_legacy_execution(args)


def test_shared_cli_really_executes_select_seal_train_freeze_and_predict(tmp_path):
    session,spec,provider=setup(tmp_path/'source')
    spec_path=tmp_path/'spec.json';write_record(spec_path,spec)
    run=tmp_path/'cli'
    base=[sys.executable,'scripts/run_research_harness.py','--run-dir',str(run)]
    def cli(*args):
        return json.loads(subprocess.check_output(base+list(args),text=True))
    cli('init','--spec',str(spec_path));mirror=Session(run)
    for name,phase,kind in [('root','benchmark','dummy'),('child','optimization','ridge')]:
        p=proposal(mirror,name,phase=phase,kind=kind)
        proposal_path=tmp_path/(name+'.json');write_record(proposal_path,[p])
        cli('propose','--file',str(proposal_path));assert cli('select')['id']==name
        recipe={**p['proposed_recipe'],'code_sha256':{'provider':file_digest(provider)},
            'input_sha256':{k:v['sha256'] for k,v in spec['inputs'].items()},'artifact_sha256':{},'environment':{}}
        seal_path=tmp_path/(name+'_seal.json')
        write_record(seal_path,{'execution':{'code_files':{'provider':str(provider)}},'recipe':recipe})
        cli('seal','--node',name,'--file',str(seal_path))
        assert cli('execute','--node',name)['evidence_phase']=='development'
    cli('freeze','--nodes','root','child')
    assert cli('confirm','--node','child')['model_refits']==0
    assert cli('report')['execution_complete']
