"""Complete registered T47D experiment; primary confirmation never refits models."""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ndcg_score

from vc_demo.harness.research_contract import (assert_recipe_files, file_digest, freeze_record,
    freeze_selection, verify_protocol, write_record)
from vc_demo.t47d_full import evaluation as diagnostic
from vc_demo.t47d_full import study as legacy
from vc_demo.t47d_lineage.data import CV_SEEDS, TREATMENTS
from vc_demo.t47d_research import study, runtime


def save_model(path, model):
    temporary = path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    joblib.dump(model, temporary)
    joblib.load(temporary)
    os.replace(temporary, path)


def budget_check():
    path = Path('/workspace/t47d_formal_budget_guard_state.json')
    if not path.is_file():
        raise RuntimeError('Formal execution requires an armed independently verified Pod deadline')
    record = json.loads(path.read_text())
    if record['mode'] != 'armed' or datetime.now(timezone.utc) >= datetime.fromisoformat(record['deadline_utc']):
        raise RuntimeError('Approved compute deadline reached or watchdog is not armed')
    process = Path('/proc')/str(record['pid'])/'cmdline'
    if not process.is_file() or b'budget_guard.py' not in process.read_bytes():
        raise RuntimeError('Recorded budget watchdog is not running')
    pairs = [p.split(b'=',1) for p in Path('/proc/1/environ').read_bytes().split(b'\0') if b'=' in p]
    if dict(pairs).get(b'RUNPOD_POD_ID',b'').decode() != record['pod_id']:
        raise RuntimeError('Budget watchdog belongs to another Pod')


def development_preparation(run):
    source = Path('data/t47d_lineage/prepared/dataset_manifest.json')
    if not source.is_file():
        raise RuntimeError('Complete source-backed preparation must be restored before formal execution')
    guard=json.loads(Path('/workspace/t47d_formal_budget_guard_state.json').read_text())
    resources=run/'execution_resources.json'
    if not resources.exists():
        write_record(resources,{'start_utc':datetime.now(timezone.utc).isoformat(),
            'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total','--format=csv,noheader'],text=True).strip(),
            'pod_id':guard['pod_id'],'stop_deadline_utc':guard['deadline_utc'],
            'gpu_rate_usd_per_hour':.24,'container_disk_rate_usd_per_hour_approx':.007,
            'new_network_volume_monthly_usd':7,'approved_incremental_total_limit_usd':20,
            'maximum_allocation_hours':24,'old_copy_compute_stopped':True})
    from scripts.t47d import full_demo
    full_demo.RUN = run
    full_demo.author_source()
    subprocess.run([sys.executable, 'scripts/t47d/full_prepare.py', '--run-dir', str(run)], check=True)
    write_record(run/'artifact_registry.json', {'task':'T47D', 'source':'GSE260703 / Hallmark / pinned public TraCSED',
        'inputs':{str(p):{'status':'derived' if '/prepared/' in str(p) else 'original_public',
                        'sha256':file_digest(p), 'size_bytes':p.stat().st_size} for p in study.input_files()},
        'foundation_checkpoints_required':False, 'fallback':False,
        'representation_policy':'fresh content-addressed train-fold-only scVI, distance, pseudotime and CellRank artifacts'})
    (run/'requirements.lock.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    (run/'requirements_tensorflow.lock.txt').write_text(subprocess.check_output(
        ['/workspace/t47d_tf_venv/bin/python','-m','pip','freeze'],text=True))


def fit_confirmation_models(run, bundle, selected):
    dev = np.flatnonzero(bundle['meta'].split.eq('development'))
    checkpoint_files = {}
    for kind in ('root','child'):
        name = selected[kind]
        directory = run/'nodes'/name
        directory.mkdir(parents=True, exist_ok=True)
        build = study.materialize(run, {'id':name, 'config':selected['configurations'][name]})
        for seed in CV_SEEDS:
            path = directory/('seed'+str(seed)+'_frozen_model.joblib')
            if not path.is_file():
                model = build(selected['configurations'][name]).fit(bundle, dev, seed)
                model.close()
                save_model(path, model)
            else:
                joblib.load(path)
            checkpoint_files[str(path.resolve())] = file_digest(path)
        oof = pd.read_csv(run/'programs'/name/'oof_predictions.csv').groupby('row').prediction.mean().reindex(dev).to_numpy()
        calibrator_path = directory/'development_calibrator.joblib'
        if not calibrator_path.is_file():
            calibrator = LogisticRegression(C=1,random_state=42).fit(oof.reshape(-1,1),
                (bundle['meta'].iloc[dev].label.to_numpy()>0).astype(int))
            save_model(calibrator_path, calibrator)
        checkpoint_files[str(calibrator_path.resolve())] = file_digest(calibrator_path)
    # Public TensorFlow candidates keep their real fitted weight files outside joblib.
    for name in (selected['root'], selected['child']):
        for seed in CV_SEEDS:
            model = joblib.load(run/'nodes'/name/('seed'+str(seed)+'_frozen_model.joblib'))
            def inspect(value, visited):
                if id(value) in visited:
                    return
                visited.add(id(value))
                if hasattr(value,'tf_dir'):
                    for name in ('model.keras','provenance.json','train.npz'):
                        p=value.tf_dir/name
                        if p.is_file():
                            checkpoint_files[str(p.resolve())] = file_digest(p)
                for attr in ('model','core_','parent_','mutation_'):
                    if hasattr(value,attr):
                        inspect(getattr(value,attr),visited)
                for child in getattr(value,'models_',[]):
                    inspect(child,visited)
            inspect(model,set())
    return checkpoint_files


def confirm(run, bundle, selected):
    lock = json.loads((run/'confirmation_lock.json').read_text())
    frozen = Path(lock['selection_path'])
    if file_digest(frozen) != lock['selection_sha256']:
        raise RuntimeError('Frozen selection changed')
    for value in lock['recipes'].values():
        assert_recipe_files(value)
    for path, expected in selected['checkpoint_files'].items():
        if file_digest(Path(path)) != expected:
            raise RuntimeError('Frozen checkpoint or calibration artifact changed: '+path)
    test = np.flatnonzero(bundle['meta'].split.eq('test'))
    meta = bundle['meta'].iloc[test]
    results = {}
    for kind in ('root','child'):
        name = selected[kind]
        predictions = []
        seeds = []
        for seed in CV_SEEDS:
            model = joblib.load(run/'nodes'/name/('seed'+str(seed)+'_frozen_model.joblib'))
            pred = model.predict(bundle,test)
            predictions.append(pred)
            seeds.append({'seed':seed, **legacy.score(meta.label,pred)})
            model.close()
        prediction = np.mean(predictions,axis=0)
        calibrator = joblib.load(run/'nodes'/name/'development_calibrator.joblib')
        probability = calibrator.predict_proba(prediction.reshape(-1,1))[:,1]
        frame = meta.copy()
        frame['prediction'],frame['positive_probability'] = prediction,probability
        frame.to_csv(run/(name+'_heldout_predictions.csv'),index=False)
        secondary = {'positive_selection':diagnostic.classification_metrics(meta.label.to_numpy()>0,prediction,probability),
            'calibration_fit':'frozen development OOF calibrator; zero confirmation fitting steps'}
        secondary['ndcg_at10'] = float(ndcg_score([meta.label.to_numpy()-meta.label.min()],
                                                 [prediction], k=min(10,len(meta))))
        truth = frame.pivot(index='clone_id',columns='treatment',values='label')
        estimate = frame.pivot(index='clone_id',columns='treatment',values='prediction')
        delta = truth[list(TREATMENTS[:2])].max(axis=1)-truth['combination']
        delta_pred = estimate[list(TREATMENTS[:2])].max(axis=1)-estimate['combination']
        secondary['log2_suppression'] = legacy.score(delta,delta_pred)
        secondary['suppression_sign_accuracy'] = float(((delta>0)==(delta_pred>0)).mean())
        mono_truth = truth[list(TREATMENTS[:2])].max(axis=1)
        mono_pred = estimate[list(TREATMENTS[:2])].max(axis=1)
        secondary['mono_resistant_combo_sensitive'] = diagnostic.classification_metrics(
            ((mono_truth>0)&(truth['combination']<0)).to_numpy(), delta_pred.to_numpy())
        secondary['mono_positive_combo_negative_accuracy'] = float(
            (((mono_pred>0)&(estimate['combination']<0))==((mono_truth>0)&(truth['combination']<0))).mean())
        clone_y,clone_p = truth.max(axis=1).to_numpy(),estimate.max(axis=1).to_numpy()
        for k in (5,10):
            secondary['clonewise_ndcg_at'+str(k)] = float(ndcg_score([clone_y-clone_y.min()],[clone_p],k=min(k,len(clone_y))))
        raw = frame.assign(raw_ratio=frame.fraction_day26/frame.fraction_baseline).pivot(
            index='clone_id',columns='treatment',values='raw_ratio')
        f0 = frame.fraction_baseline.to_numpy()
        inverted = (np.exp2(np.clip(prediction,-20,20))*(f0+1e-5)-1e-5).clip(0,1)/f0
        raw_p = frame.assign(raw_ratio=inverted).pivot(index='clone_id',columns='treatment',values='raw_ratio')
        secondary['raw_ratio_suppression'] = legacy.score(
            raw[list(TREATMENTS[:2])].max(axis=1)-raw['combination'],
            raw_p[list(TREATMENTS[:2])].max(axis=1)-raw_p['combination'])
        results[name] = {'kind':kind, 'seed_metrics':seeds, 'ensemble':legacy.score(meta.label,prediction),
            'bootstrap':diagnostic.block_bootstrap(meta,prediction), 'secondary_metrics':secondary,
            'within_treatment':{t:legacy.score(meta.loc[meta.treatment.eq(t),'label'],prediction[meta.treatment.eq(t)]) for t in TREATMENTS},
            'evidence_phase':'confirmation', 'model_refits':0, 'calibration_refits':0,
            'caveat':'Historically exposed test clone IDs; retrospective frozen comparison, not a fresh blind test.'}
    write_record(run/'frozen_test_metrics.json',results)
    write_record(run/'confirmation_complete.json',{'complete':True,'model_refits':0,'calibration_refits':0,
        'further_search_allowed':False,'historical_test_exposure':True})


def report(run):
    tree = json.loads((run/'tree.json').read_text())
    selected = json.loads((run/'frozen_selection.json').read_text())
    metrics = json.loads((run/'frozen_test_metrics.json').read_text())
    nodes = list(tree['nodes'].values())
    counts = {s:sum(n['status']==s for n in nodes) for s in sorted({n['status'] for n in nodes})}
    lines = ['# T47D Shared-Protocol Formal Study v3','',
        'Retrospective public-data experiment. Previously exposed test groups are not new blind confirmation.','',
        '## Protocol','',
        '- Unit: clone x treatment; input days0/1/4; day26 smoothed log2 relative selection.',
        '- Selection: five seeds x three clone-grouped OOF folds; reward is mean seed-level Spearman.',
        '- Coverage and optimization have separate registered allocations. Neither is independent replication.',
        '- Exact historical Ridge is an unchanged required benchmark, including category encoding/scaling.',
        '- New neural candidates predict the response directly, without hidden in-sample Ridge residuals.',
        '- Explicit residual/stacking candidates learn weights on grouped OOF predictions.',
        '- Primary confirmation loads frozen weights/calibrators and performs zero refits.','',
        '## Results','', '| Kind | Node | Development rho | Confirmation rho | Confirmation MAE |',
        '|---|---|---:|---:|---:|']
    for kind in ('root','child'):
        name = selected[kind]
        values = metrics[name]['ensemble']
        lines.append(f"| {kind} | {name} | {tree['nodes'][name]['validation_reward']:.4f} | {values['spearman']} | {values['mae']:.4f} |")
    lines += ['', '## Counts','', '```json',json.dumps(counts,indent=2),'```','',
        '## Node Relationships','', '```mermaid','graph TD']
    for n in nodes:
        if n['status']=='trained':
            lines.append('  '+n['id']+'["'+n['id']+'"]')
            if n.get('parent'):
                lines.append('  '+n['parent']+' --> '+n['id'])
    lines += ['```','','## Interpretation','',
        'Selected child phase: '+selected.get('selected_child_phase','unknown')+'.',
        'Best optimization-only child: '+selected.get('best_optimization_child','not available')+'.',
        'Report the paired development confidence interval, not only a winner score. A null result is valid.',
        'Adaptive development evidence, fixed secondary analyses and historically exposed confirmation have different evidential strength.',
        'This run does not by itself establish that the general framework transfers to independent tasks.','']
    resources=json.loads((run/'execution_resources.json').read_text())
    hours=(datetime.now(timezone.utc)-datetime.fromisoformat(resources['start_utc'])).total_seconds()/3600
    lines += ['', '## Compute And Cost','',
        '- GPU: '+resources['gpu'],
        '- Experiment wall time: '+str(round(hours,3))+' hours.',
        '- One-GPU reserved experiment hours (not GPU-utilization hours): '+str(round(hours,3))+'.',
        '- Approximate experiment GPU plus container cost: $'+str(round(hours*.247,3))+'.',
        '- New persistent volume: $7/month recurring until deleted; setup/copy overhead is additional.',
        '- Allocation stops at '+resources['stop_deadline_utc']+'; this is not permission to extend compute.','',
        '## Complete-Scope Outputs','']
    needed = ['research_protocol.json','research_budget.json','eight_ablations.json','temporal_snapshot_control.json',
        'early_abundance_baseline.json','loco_results.json','challenge_metrics.json','reference/reference_data.json',
        'biological_and_sensitivity_analysis.json','resistance_attractor_and_month6.json','denominator_null_diagnostic.json']
    for name in needed:
        lines.append('- '+name+': '+('present' if (run/name).exists() else 'missing; scope not complete'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figures = run/'figures'
    figures.mkdir(exist_ok=True)
    fig,axes = plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for ax,kind in zip(axes,('root','child')):
        frame = pd.read_csv(run/(selected[kind]+'_heldout_predictions.csv'))
        for treatment in TREATMENTS:
            subset = frame.loc[frame.treatment.eq(treatment)]
            ax.scatter(subset.label,subset.prediction,s=22,label=treatment)
        ax.set(xlabel='Observed day26 log2 selection',ylabel='Frozen prediction',title=kind)
    axes[1].legend(fontsize=7)
    fig.savefig(figures/'frozen_root_child.png',dpi=160)
    plt.close(fig)
    trained = sorted([n for n in nodes if n['status']=='trained'],key=lambda n:n['validation_reward'])
    fig,ax = plt.subplots(figsize=(9,max(5,len(trained)*.15)),constrained_layout=True)
    ax.barh(range(len(trained)),[n['validation_reward'] for n in trained],
            color=['#4a7486' if not n.get('parent') else '#b18b4d' if n.get('budget_phase')=='coverage' else '#4c9464' for n in trained])
    ax.set_yticks(range(len(trained)),[n['id'] for n in trained],fontsize=5)
    ax.set_xlabel('Mean repeated clone-OOF Spearman (development only)')
    fig.savefig(figures/'development_search.png',dpi=160)
    plt.close(fig)
    lines += ['', '![Frozen root and child](figures/frozen_root_child.png)',
              '', '![Development search](figures/development_search.png)']
    (run/'final_report.md').write_text('\n'.join(lines)+'\n')
    plan = json.loads((run/'research_budget_plan.json').read_text())
    usage = json.loads((run/'research_budget.json').read_text())['used']
    missing = [p for p in needed if not (run/p).exists()]
    complete = not missing and usage['coverage']==plan['coverage_limit'] and usage['optimization']==plan['optimization_limit']
    pipelines=[json.loads(p.read_text()) for p in (run/'programs').glob('*/pipeline.json')]
    write_record(run/'completion_audit.json',{'complete_scope':complete,'counts':counts,'missing_outputs':missing,
        'fallback':sum(bool(p.get('fallback')) for p in pipelines),'proxy':sum(bool(p.get('proxy')) for p in pipelines),
        'nontrained_backprop':sum(n.get('rollout_backpropagated',False) and n['status']!='trained' for n in nodes),
        'primary_confirmation_refits':0,'scientific_superiority_not_assumed':True})
    if not complete:
        raise RuntimeError('Report written, but registered scope is incomplete; inspect completion_audit.json')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path,default=study.RUN)
    parser.add_argument('--optimization-rollouts',type=int,default=40)
    parser.add_argument('--phase',choices=['all','prepare','search','confirm','secondary','reference','biology','report'],default='all')
    args = parser.parse_args()
    run = args.run_dir
    run.mkdir(parents=True,exist_ok=True)
    runtime.configure()
    phases = ['prepare','search','confirm','secondary','reference','biology','report'] if args.phase=='all' else [args.phase]
    for phase in phases:
        budget_check()
        marker = run/(phase+'_complete.json')
        if marker.is_file():
            continue
        write_record(run/'active_phase.json',{'phase':phase,'utc':datetime.now(timezone.utc).isoformat()})
        if phase=='prepare':
            development_preparation(run)
        elif phase=='search':
            study.search(run,args.optimization_rollouts)
        else:
            bundle = legacy.bundle(run)
            development = run/'development_selection.json'
            selected = json.loads(development.read_text())
            diagnostic.materialize = study.materialize
            diagnostic.evaluate = study.evaluate
            if phase=='confirm':
                if not (run/'confirmation_lock.json').exists():
                    diagnostic.ablate(run,bundle,selected['configurations'][selected['child']])
                    diagnostic.denominator_null(run,bundle,selected)
                    selected['checkpoint_files'] = fit_confirmation_models(run,bundle,selected)
                    selected['recipe_fingerprints'] = {n:json.loads((run/'execution_recipes'/(n+'.json')).read_text())['fingerprint']
                        for n in (selected['root'],selected['child'])}
                    selected['secondary_analysis_plan'] = ['eight registered development ablations','LOCO',
                        'monotherapy to combination','day8 to day26','day0/1/4 warning','public R/TF reference','long-term biology']
                    freeze_record(run/'frozen_selection.json',selected)
                    freeze_selection(run,run/'frozen_selection.json')
                selected = json.loads((run/'frozen_selection.json').read_text())
                confirm(run,bundle,selected)
            elif phase=='secondary':
                selected = json.loads((run/'frozen_selection.json').read_text())
                diagnostic.loco(run,bundle,selected)
                diagnostic.challenges(run,bundle,selected)
                diagnostic.resistance_scores(run,bundle,selected)
            elif phase=='reference':
                from scripts.t47d import full_demo
                full_demo.RUN=run
                full_demo.reference()
            elif phase=='biology':
                subprocess.run([sys.executable,'-m','vc_demo.t47d_full.biology','--run-dir',str(run)],check=True)
            else:
                report(run)
        write_record(marker,{'complete':True,'utc':datetime.now(timezone.utc).isoformat()})


if __name__=='__main__':
    main()
