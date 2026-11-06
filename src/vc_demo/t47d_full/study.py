"""Formal repeated clone-heldout MCTS study; resumable at completed fits."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import time
import traceback
import warnings
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from vc_demo.harness.mcts import backpropagate,select_parent
from vc_demo.t47d_lineage.data import dump,load_bundle,CV_SEEDS
from vc_demo.t47d_full.models import ComposedCandidate

RUN=Path('experiments/t47d_lineage_resistance_full_v2')
PREPARED=Path('data/t47d_lineage/prepared')
PATHWAYS=Path('data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt')


def bundle(run=RUN):
    run.mkdir(parents=True,exist_ok=True)
    return load_bundle(PREPARED,PATHWAYS,run)


def score(y,p):
    y,p=np.asarray(y),np.asarray(p)
    if not np.isfinite(p).all():raise ValueError('Nonfinite prediction')
    rho=float(spearmanr(y,p).statistic) if np.ptp(p)>0 and np.ptp(y)>0 else None
    return dict(spearman=rho,mae=float(np.abs(y-p).mean()))


def event(run,kind,**kwargs):
    with (run/'mcts_trace.jsonl').open('a') as f:
        f.write(json.dumps(dict(time=datetime.now(timezone.utc).isoformat(),event=kind,**kwargs))+'\n')


def manifest():
    entries=[]
    for rep in ('pseudobulk','pca','scvi','pathway','distance','pseudotime'):
        for model in ('early_elastic','gru','temporal_transformer'):
            for loss in ('huber','weighted_bce','focal','pairwise','multitask'):
                if model=='early_elastic' and loss!='huber':continue
                entries.append(dict(model=model,representation=rep,loss=loss,head='ranking' if loss=='pairwise' else 'regression',epochs=80))
    for model in ('additive_null','bilinear','gated_pathway','cross_attention','moe','hazard','tracsed'):
        for rep in ('pathway','scvi','pca'):
            entries.append(dict(model=model,representation=rep,loss='huber',head='regression',epochs=80))
    for model in ('gru','gated_pathway','early_elastic'):
        entries.append(dict(model=model,representation='cellrank',loss='huber',head='regression',epochs=80))
    for head in ('positive_selected','mono_resistant_combo_sensitive'):
        for model in ('gated_pathway','moe'):
            for loss in ('weighted_bce','focal'):
                entries.append(dict(model=model,representation='pathway',loss=loss,head=head,epochs=80))
    for alpha in (1,10,100):
        for rep in ('pseudobulk','pathway','pca'):
            entries.append(dict(model='ridge',representation=rep,alpha=alpha,head='regression',loss='huber'))
    return entries


def roots():
    return [dict(model='frequency',representation='pathway',baseline_only=True),
            dict(model='ridge',representation='pathway',baseline_only=True,alpha=100),
            dict(model='early_elastic',representation='pseudobulk',baseline_only=True),
            dict(model='pls',representation='pathway',baseline_only=True,components=3),
            dict(model='xgboost',representation='pca')]


def materialize(run,node):
    dest=run/'programs'/node['id'];dest.mkdir(parents=True,exist_ok=True)
    dump(dest/'pipeline.json',{'config':node['config'],'parent':node.get('parent'),'fallback':False,'proxy':False,
        'backend':'full_t47d_native_or_author_tf','train_contract':'5 seeds x 3 clone folds; labels confined to training clones'})
    path=dest/'model.py'
    if not path.exists():
        path.write_text('from vc_demo.t47d_full.models import ComposedCandidate\n\ndef build_model(config):\n    return ComposedCandidate(config)\n')
    subprocess.run([sys.executable,'-m','py_compile',str(path)],check=True)
    name='full_'+hashlib.sha256(str(path).encode()+path.read_bytes()).hexdigest()[:12]
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    if not callable(getattr(module,'build_model',None)):raise ValueError('Missing authoritative node-local build_model')
    return module.build_model


def evaluate(run,node,b,only_splits=None):
    build=materialize(run,node)
    dest=run/'programs'/node['id'];progress=dest/'fold_results.json'
    folds=json.loads(progress.read_text()) if progress.exists() else []
    completed={(r['seed'],r['fold']) for r in folds}
    for split in only_splits or b['splits']['folds']:
        if (split['seed'],split['fold']) in completed:continue
        ti=np.flatnonzero(b['meta'].clone_id.isin(split['train_clones']))
        vi=np.flatnonzero(b['meta'].clone_id.isin(split['validation_clones']))
        assert not set(b['meta'].iloc[ti].clone_id)&set(b['meta'].iloc[vi].clone_id)
        assert not b['meta'].iloc[ti].split.eq('test').any()
        start=time.monotonic()
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always');model=build(node['config']).fit(b,ti,split['seed'])
            p=model.predict(b,vi)
        if p.shape!=(len(vi),) or not np.isfinite(p).all():raise ValueError('Native prediction contract failed')
        model.close()
        r=dict(seed=split['seed'],fold=split['fold'],validation_indices=vi.tolist(),predictions=p.tolist(),
            seconds=time.monotonic()-start,warnings=[str(w.message) for w in captured],**score(b['meta'].iloc[vi].label,p))
        folds.append(r);dump(progress,folds)
        dump(dest/'smoke.json',{'passed':True,'compile':True,'fit_forward_backward':True,'prediction_shape':[len(vi)],
            'scientific_smoke_score_used_as_reward':False,'validation_fold_complete':True})
        print(json.dumps({'node':node['id'],'seed':split['seed'],'fold':split['fold'],'rho':r['spearman'],'seconds':r['seconds']}),flush=True)
    dev=np.flatnonzero(b['meta'].split.eq('development'))
    seed_records=[];oof=[]
    for seed in CV_SEEDS:
        per={i:p for r in folds if r['seed']==seed for i,p in zip(r['validation_indices'],r['predictions'])}
        if set(per)!=set(dev):raise ValueError('Incomplete repeated OOF; no backprop allowed')
        pp=np.array([per[int(i)] for i in dev]);m=score(b['meta'].iloc[dev].label,pp)
        if m['spearman'] is None:raise ValueError('Undefined repeated OOF reward')
        seed_records.append(dict(seed=seed,**m))
        for i,p in zip(dev,pp):oof.append({'row':int(i),'seed':seed,'prediction':float(p)})
    pd.DataFrame(oof).to_csv(dest/'oof_predictions.csv',index=False)
    return {'validation_reward':float(np.mean([r['spearman'] for r in seed_records])),
            'validation_std':float(np.std([r['spearman'] for r in seed_records],ddof=1)),
            'validation_mae':float(np.mean([r['mae'] for r in seed_records])),
            'seed_metrics':seed_records,'formal_fold_fits':len(folds),'status':'trained',
            'duration_seconds':sum(r['seconds'] for r in folds)}


def required_choices(space):
    needs=[('early_elastic','pseudobulk','huber'),('early_elastic','scvi','huber'),
           ('early_elastic','distance','huber'),('early_elastic','pseudotime','huber'),
           ('gated_pathway','cellrank','huber'),('gru','pathway','huber'),
           ('temporal_transformer','pathway','huber'),('tracsed','pathway','huber'),
           ('hazard','pca','huber'),('additive_null','pathway','huber'),('bilinear','pathway','huber'),
           ('gated_pathway','pathway','huber'),('cross_attention','pathway','huber'),('moe','pathway','huber'),
           ('gated_pathway','pathway','weighted_bce'),('gated_pathway','pathway','focal'),
           ('gru','pathway','pairwise'),('gru','pathway','multitask')]
    choices=[]
    for model,rep,loss in needs:
        choices.append(next(c for c in space if c['model']==model and c['representation']==rep and c['loss']==loss))
    choices.extend(c for c in space if c['head'] in {'positive_selected','mono_resistant_combo_sensitive'})
    return choices


def checkpoint(run,tree):
    dump(run/'tree.json',tree)
    status=Counter(n['status'] for n in tree['nodes'].values())
    dump(run/'run_status.json',{'counts':dict(status),'trained_rollouts':sum(n['status']=='trained' and n.get('parent') is not None for n in tree['nodes'].values()),
        'prior_test_exposure':'Same clone split was reported in pilot; no claim of new blind confirmation',
        'budget_trained_rollouts':40,'reward':'5 seed repeated 3-fold clone OOF Spearman'})


def run_search(run=RUN,budget=40):
    b=bundle(run);space=manifest();dump(run/'search_space.json',{'candidates':space,'count':len(space),'all_implemented':True,
        'task_specific_claim':'public-data functional reconstruction; no private orchestrator equivalence claim'})
    if not (run/'run_manifest.json').exists():
        dump(run/'run_manifest.json',{'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'recorded_utc':datetime.now(timezone.utc).isoformat(),'selected_rollout_budget':budget,
            'cv_seeds':list(CV_SEEDS),'cv_folds_per_seed':3,'reward':'mean seed-level clone OOF Spearman',
            'proposal_pool':4,'global_queue_capacity':48,'parent_selection':'UCT','exploration':math.sqrt(2),
            'max_parent_depth':1,'max_proposals_per_parent':20,'no_improvement_stop':'disabled until complete predeclared module coverage; formal budget 40',
            'data_contract_sha256':hashlib.sha256((run/'task_contract.json').read_bytes()).hexdigest(),
            'split_sha256':hashlib.sha256((run/'grouped_splits.json').read_bytes()).hexdigest(),
            'test_exposure':'Prior pilot exposed the same test clones and Month6 observations; no new-blind claim',
            'implementation_repairs':'API/dependency corrections and mathematically equivalent reference-statistic caching are retained in logs; no test-driven architecture changes',
            'node_entrypoint':'node-local build_model(config), used for all 15 fold fits',
            'authorized_initial_limits':{'hours':24,'usd':20,'no_automatic_extension':True},
            'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],text=True).strip()})
    path=run/'tree.json'
    if (run/'frozen_selection.json').exists():return
    tree=json.loads(path.read_text()) if path.exists() else {'nodes':{},'roots':[],'root_nodes':[],'events':[],'mcts':{}}
    for i,c in enumerate(roots()):
        name='root_'+str(i)+'_'+c['model'];tree['nodes'].setdefault(name,{'id':name,'name':name,'parent':None,'config':c,'status':'candidate_queued','children':[],'visits':0,'value':0.,'depth':0})
        if name not in tree['roots']:tree['roots'].append(name)
        if name not in tree.setdefault('root_nodes',[]):tree['root_nodes'].append(name)
        node=tree['nodes'][name]
        if node['status']!='trained':
            node.update(evaluate(run,node,b));backpropagate(tree,name,node['validation_reward']);event(run,'backpropagation',node=name,status='trained',reward=node['validation_reward']);checkpoint(run,tree)
    required=required_choices(space)
    while sum(n['status']=='trained' and n.get('parent') is not None for n in tree['nodes'].values())<budget:
        interrupted=[n for n in tree['nodes'].values() if n['status']=='selected']
        for node in interrupted:
            node.update(evaluate(run,node,b));backpropagate(tree,node['id'],node['validation_reward'])
            event(run,'backpropagation',node=node['id'],status='trained',reward=node['validation_reward'],resumed_selected=True)
            checkpoint(run,tree)
        if sum(n['status']=='trained' and n.get('parent') is not None for n in tree['nodes'].values())>=budget:break
        trained=[n for n in tree['nodes'].values() if n['status']=='trained']
        completed={json.dumps(n.get('mutation_config'),sort_keys=True) for n in trained if n.get('parent')}
        mandatory=next((c for c in required if json.dumps(c,sort_keys=True) not in completed),None)
        parent,components=select_parent(tree,math.sqrt(2),20,policy='uct')
        for c in components:c.pop('best_val_macro_f1',None)
        eligible=[n for n in trained if n['depth']<2 and len(n['children'])<20]
        if not eligible:raise RuntimeError('No eligible trained parent under declared depth/children limits')
        if parent not in {n['id'] for n in eligible}:
            total=max(2,sum(n['visits'] for n in eligible))
            parent=max(eligible,key=lambda n:n['value']/max(n['visits'],1)+math.sqrt(2)*math.sqrt(math.log(total)/max(n['visits'],1)))['id']
        event(run,'parent_selection',parent=parent,components=components)
        existing={json.dumps(n.get('mutation_config'),sort_keys=True) for n in tree['nodes'].values() if n.get('parent')==parent}
        options=[c for c in space if json.dumps(c,sort_keys=True) not in existing]
        np.random.default_rng(len(tree['nodes'])+43).shuffle(options)
        if mandatory is not None:
            options=[mandatory]+[c for c in options if c!=mandatory]
        for mutation in options[:4]:
            cfg=dict(mutation,parent_config=tree['nodes'][parent]['config'],composition='parent prediction + .25 train-residual mutation')
            name='n'+str(len(tree['nodes']))+'_'+mutation['model']+'_'+hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:8]
            if any(n.get('parent')==parent and n.get('mutation_config')==mutation for n in tree['nodes'].values()):continue
            tree['nodes'][name]={'id':name,'name':name,'parent':parent,'config':cfg,'mutation_config':mutation,'children':[],
                'status':'candidate_queued','visits':0,'value':0.,'depth':tree['nodes'][parent]['depth']+1}
            tree['nodes'][parent]['children'].append(name);event(run,'proposal_generated',node=name,parent=parent,mutation=mutation)
        queue=[n for n in tree['nodes'].values() if n['status']=='candidate_queued' and n.get('parent')]
        counts=Counter(n['config']['model'] for n in trained if n.get('parent'))
        for n in queue:
            p=tree['nodes'][n['parent']]
            n['scientific_priority']=p['validation_reward']-.25*p.get('validation_std',0)+.15/(1+counts[n['config']['model']])
            if mandatory is not None and n['mutation_config']==mandatory:n['scientific_priority']+=10
        if not queue:raise RuntimeError('Global queue unexpectedly exhausted before mandatory coverage')
        selected=max(queue,key=lambda n:n['scientific_priority'])
        for n in sorted(queue,key=lambda n:n['scientific_priority'],reverse=True)[48:]:
            n['status']='pruned_not_selected';event(run,'global_prune',node=n['id'],reason='global queue capacity 48')
        event(run,'global_queue_selected',node=selected['id'],candidates=len(queue),priority=selected['scientific_priority'],
              priority_basis='validation reward, uncertainty, scientific family coverage; no artifact-presence bonus')
        selected['status']='selected';checkpoint(run,tree)
        success=False
        for attempt in range(1,4):
            try:
                selected.update(evaluate(run,selected,b));success=True;break
            except Exception:
                error=traceback.format_exc();print(error,flush=True)
                event(run,'implementation_or_training_error',node=selected['id'],attempt=attempt,error=error)
                selected['last_error']=error
                checkpoint(run,tree)
                raise
        if not success:raise RuntimeError('Real-time implementation repair required; cannot fabricate trained reward')
        backpropagate(tree,selected['id'],selected['validation_reward'])
        event(run,'backpropagation',node=selected['id'],status='trained',reward=selected['validation_reward'],
              path=tree['mcts']['last_backpropagation']['path'])
        event(run,'rollout_completed_regenerate_next',node=selected['id'],trained_rollout_count=sum(n['status']=='trained' and n.get('parent') is not None for n in tree['nodes'].values()))
        checkpoint(run,tree)
    trained=[n for n in tree['nodes'].values() if n['status']=='trained']
    root=max((n for n in trained if n.get('parent') is None),key=lambda n:n['validation_reward'])
    child=max((n for n in trained if n.get('parent') is not None),key=lambda n:n['validation_reward'])
    for n in tree['nodes'].values():
        if n['status']=='candidate_queued':n['status']='pruned_budget_exhausted'
    dump(run/'frozen_selection.json',{'root':root['id'],'child':child['id'],'selected_by':'repeated development OOF Spearman only',
        'configurations':{n['id']:n['config'] for n in (root,child)},'prior_test_exposure':True,
        'stop_reason':'40 selected formal rollout budget exhausted after mandatory module coverage'})
    checkpoint(run,tree)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,default=RUN);parser.add_argument('--budget-rollouts',type=int,default=40)
    args=parser.parse_args();run_search(args.run_dir,args.budget_rollouts)
