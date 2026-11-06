"""Frozen-model evaluation, all eight ablations, and longitudinal challenges."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import joblib

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,roc_auc_score,ndcg_score,brier_score_loss
from sklearn.preprocessing import StandardScaler,MinMaxScaler

from vc_demo.t47d_full.study import RUN,bundle,score,evaluate,materialize
from vc_demo.t47d_full.models import FullCandidate
from vc_demo.t47d_lineage.data import dump,TREATMENTS,CV_SEEDS


def block_bootstrap(meta,pred,draws=2000):
    rng=np.random.default_rng(20261106);clones=meta.clone_id.unique();values=[]
    for _ in range(draws):
        idx=np.concatenate([np.flatnonzero(meta.clone_id.eq(c)) for c in rng.choice(clones,len(clones),replace=True)])
        v=score(meta.iloc[idx].label.to_numpy(),pred[idx])['spearman']
        if v is not None and np.isfinite(v):values.append(v)
    return {'unit':'clone block, all treatments kept together','draws':draws,'valid_draws':len(values),
            'spearman_ci95':np.percentile(values,[2.5,97.5]).tolist() if values else None}


def classification_metrics(y,p,probability=None):
    y=np.asarray(y).astype(int);p=np.asarray(p)
    ece=None
    if probability is not None:
        bins=np.minimum((np.asarray(probability)*10).astype(int),9)
        ece=float(sum(np.mean(bins==k)*abs(np.asarray(probability)[bins==k].mean()-y[bins==k].mean()) for k in range(10) if np.any(bins==k)))
    return {'positive_count':int(y.sum()),'n':len(y),
        'auroc':float(roc_auc_score(y,p)) if len(set(y))==2 else None,
        'auprc':float(average_precision_score(y,p)) if y.sum() else None,
        'brier_score':float(brier_score_loss(y,probability)) if probability is not None else None,
        'ece_fixed_10_bins':ece,
        'undefined_reason':None if len(set(y))==2 else 'only one class in evaluated clone set'}


def secondary(meta,p,train_meta,train_oof):
    calibrator=LogisticRegression(C=1,random_state=42).fit(np.asarray(train_oof).reshape(-1,1),(train_meta.label.to_numpy()>0).astype(int))
    prob=calibrator.predict_proba(p.reshape(-1,1))[:,1]
    result={'positive_selection':classification_metrics(meta.label.to_numpy()>0,p,prob),
            'calibration_fit':'development OOF predictions and development labels only; never test',
            'ndcg':float(ndcg_score([meta.label.to_numpy()-meta.label.min()],[p],k=min(10,len(p))))}
    truth=meta.assign(prediction=p).pivot(index='clone_id',columns='treatment',values='label')
    predicted=meta.assign(prediction=p).pivot(index='clone_id',columns='treatment',values='prediction')
    if all(t in truth for t in TREATMENTS):
        mono=truth[list(TREATMENTS[:2])].max(axis=1);combo=truth.combination
        pmono=predicted[list(TREATMENTS[:2])].max(axis=1);pcombo=predicted.combination
        y=(mono>0)&(combo<0);pp=pmono-pcombo
        result['mono_resistant_combo_sensitive']=classification_metrics(y,pp)
        result['mono_resistant_combo_sensitive']['score_definition']='maximum predicted monotherapy log2 selection minus predicted combination log2 selection; margin ranking, not calibrated joint probability'
        result['mono_positive_combo_negative_accuracy']=float((((pmono>0)&(pcombo<0))==y).mean())
        result['suppression_sign_accuracy']=float(((pp>0)==((mono-combo)>0)).mean())
        result['log2_suppression']=score(mono-combo,pp)
        raw=meta.assign(raw_ratio=meta.fraction_day26/meta.fraction_baseline).pivot(index='clone_id',columns='treatment',values='raw_ratio')
        f0=meta.fraction_baseline.to_numpy()
        inverted=(np.exp2(np.clip(p,-20,20))*(f0+1e-5)-1e-5).clip(0,1)/f0
        rawp=meta.assign(raw_ratio=inverted).pivot(index='clone_id',columns='treatment',values='raw_ratio')
        result['raw_ratio_suppression']=score(raw[list(TREATMENTS[:2])].max(axis=1)-raw.combination,
                                             rawp[list(TREATMENTS[:2])].max(axis=1)-rawp.combination)
        result['suppression_scale_note']='Observed raw ratio is f26/f0, NOT exp2(smoothed log label). Predictions invert the registered eps transform and clip predicted fractions to [0,1]. Raw and log2 differences are separate.'
        clone_y=truth.max(axis=1).to_numpy();clone_p=predicted.max(axis=1).to_numpy()
        result['clonewise_ndcg_at5']=float(ndcg_score([clone_y-clone_y.min()],[clone_p],k=min(5,len(clone_y))))
        result['clonewise_ndcg_at10']=float(ndcg_score([clone_y-clone_y.min()],[clone_p],k=min(10,len(clone_y))))
    return result,prob


def altered(config,changes):
    c=copy.deepcopy(config);c.update(changes)
    if changes.get('remove_pathway') and config.get('representation') in {'pathway','both'}:
        c['representation']='expression'
    if changes.get('representation')=='matched_no_artifact':
        c['matched_width']={'pathway':50,'scvi':16,'pca':16,'distance':4,'pseudotime':2,'cellrank':4,
            'expression':config.get('genes',128),'pseudobulk':config.get('genes',128),'both':config.get('genes',128)+50}[config.get('representation','pathway')]
    if c.get('parent_config'):c['parent_config']=altered(c['parent_config'],changes)
    return c


def restricted_horizon(config,day):
    # Restrict the observation window without expanding baseline-only parents.
    return altered(config,{'input_cutoff_day':day})


def ablate(run,b,chosen):
    path=run/'eight_ablations.json';results=json.loads(path.read_text()) if path.exists() else {}
    controls={
        'no_barcode_informed_inputs':{'no_barcode_inputs':True,'no_clone_abundance':True},
        'baseline_only':{'baseline_only':True},
        'no_temporal_order':{'no_temporal_order':True},
        'no_pathway':{'remove_pathway':True,'no_pathway_supervision':True},
        'shuffled_gene_memberships':{},
        'matched_capacity_no_artifact':{'representation':'matched_no_artifact','auxiliary_no_artifact':True},
        'no_treatment_interaction':{'no_treatment_interaction':True},
        'no_dense_parent_branch':{'no_dense_parent':True}}
    for name,changes in controls.items():
        if name in results:
            if name!='no_pathway' or results[name].get('ablation_contract_version')==2:continue
            archive=run/'ablation_protocol_diagnostics';archive.mkdir(exist_ok=True)
            dump(archive/'no_pathway_legacy.json',results[name])
        modified=b
        if name=='shuffled_gene_memberships':
            modified=dict(b)
            genes=pd.read_csv('data/t47d_lineage/prepared/gene_order.csv').gene_symbol.fillna('').to_numpy()
            perm=np.random.default_rng(20261106).permutation(len(genes))
            membership=[]
            for line in Path('data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt').read_text().splitlines():
                terms=line.split('\t');ids=np.flatnonzero(np.isin(genes,terms[2:]))
                if len(ids)>=5:membership.append(perm[ids])
            modified['ablation_pathway']=np.stack([b['expression'][:,:,ids].mean(2) for ids in membership],axis=-1)
        config=altered(chosen,changes)
        n={'id':'ablation_'+name+('_v2' if name=='no_pathway' else ''),'config':config,'parent':None}
        results[name]=evaluate(run,n,modified)
        if name=='no_pathway':results[name]['ablation_contract_version']=2
        results[name]['interpretation']={
            'no_barcode_informed_inputs':'True barcode kept for endpoint labels/group splitting only; predictive state pooled across TRAIN clones per condition; abundance removed',
            'no_pathway':'Only pathway/both views and curated pathway supervision removed; independent scVI/CellRank/PCA components preserved',
            'shuffled_gene_memberships':'One fixed global gene permutation preserves all pathway sizes and overlaps; NOT pathway-column permutation',
            'matched_capacity_no_artifact':'Each pipeline level retains original representation width using fixed random gene projection; gene selection/scalers training-only',
            'no_dense_parent_branch':'Removes inherited prediction branch AND neural internal dense branch; readout itself remains necessary',
            'no_treatment_interaction':'Removes drug covariates at every inherited level; cross-attention/bilinear condition interaction disabled'}.get(name,name)
        dump(path,results)
    snapshot=run/'temporal_snapshot_control.json'
    if not snapshot.exists():
        config=altered(chosen,{'last_snapshot_only':True,'baseline_only':False})
        result=evaluate(run,{'id':'ablation_last_day4_snapshot','config':config,'parent':None},b)
        result['interpretation']='Additional endpoint-snapshot control: day4 state and abundance only, no explicit temporal order; CellRank uses a stationary graph. Day26 inputs remain forbidden.'
        dump(snapshot,result)
    abundance=run/'early_abundance_baseline.json'
    if not abundance.exists():
        config={'model':'frequency','representation':'pathway','baseline_only':False,'alpha':10}
        result=evaluate(run,{'id':'diagnostic_early_abundance_only','config':config,'parent':None},b)
        result['predictive_inputs']='Only day0/1/4 abundance, observation flags and chemical indicators; pathway columns are not passed to the estimator'
        dump(abundance,result)
    return results


def frozen_test(run,b,selection):
    path=run/'frozen_test_metrics.json';results=json.loads(path.read_text()) if path.exists() else {}
    dev=np.flatnonzero(b['meta'].split.eq('development'));test=np.flatnonzero(b['meta'].split.eq('test'))
    for kind in ('root','child'):
        name=selection[kind]
        if name in results:
            saved=pd.read_csv(run/(name+'_heldout_predictions.csv'))
            oof=pd.read_csv(run/'programs'/name/'oof_predictions.csv').groupby('row').prediction.mean().reindex(dev).to_numpy()
            results[name]['secondary_metrics']=secondary(b['meta'].iloc[test],saved.prediction.to_numpy(),b['meta'].iloc[dev],oof)[0]
            dump(path,results)
            continue
        config=selection['configurations'][name];build=materialize(run,{'id':name,'config':config})
        predictions=[];byseed=[]
        for seed in CV_SEEDS:
            model=build(config).fit(b,dev,seed);p=model.predict(b,test)
            predictions.append(p);byseed.append(dict(seed=seed,**score(b['meta'].iloc[test].label,p)));model.close()
            dest=run/'nodes'/name;dest.mkdir(parents=True,exist_ok=True)
            joblib.dump(model,dest/('seed'+str(seed)+'_frozen_model.joblib'))
        p=np.mean(predictions,axis=0)
        oof=pd.read_csv(run/'programs'/name/'oof_predictions.csv').groupby('row').prediction.mean().reindex(dev).to_numpy()
        extra,prob=secondary(b['meta'].iloc[test],p,b['meta'].iloc[dev],oof)
        frame=b['meta'].iloc[test].copy();frame['prediction']=p;frame['positive_probability']=prob
        frame.to_csv(run/(name+'_heldout_predictions.csv'),index=False)
        results[name]={'kind':kind,'seed_metrics':byseed,'ensemble':score(frame.label,p),'bootstrap':block_bootstrap(frame,p),
            'secondary_metrics':extra,'within_treatment':{t:score(frame.loc[frame.treatment.eq(t),'label'],p[frame.treatment.eq(t)]) for t in TREATMENTS},
            'caveat':'These heldout clone IDs were exposed in earlier pilot. This is a frozen new-run comparison, not fresh blind external confirmation.'}
        dump(path,results)
    return results


def loco(run,b,selection):
    path=run/'loco_results.json';results=json.loads(path.read_text()) if path.exists() else {}
    for kind in ('root','child'):
        name=selection[kind];record=results.setdefault(name,{'folds':[],'protocol':'46 complete-data leave-one-clone-out fits, frozen model choice; secondary post-selection evaluation, NOT primary locked-test statistic'})
        done={r['clone'] for r in record['folds']}
        build=materialize(run,{'id':name,'config':selection['configurations'][name]})
        for clone in b['meta'].clone_id.unique():
            if clone in done:continue
            train=np.flatnonzero(b['meta'].clone_id.ne(clone));valid=np.flatnonzero(b['meta'].clone_id.eq(clone))
            model=build(selection['configurations'][name]).fit(b,train,3);p=model.predict(b,valid);model.close()
            record['folds'].append({'clone':clone,'indices':valid.tolist(),'prediction':p.tolist(),**score(b['meta'].iloc[valid].label,p)})
            dump(path,results)
        pred=np.empty(len(b['meta']))
        for f in record['folds']:pred[f['indices']]=f['prediction']
        record['pooled']=score(b['meta'].label,pred);record['bootstrap']=block_bootstrap(b['meta'],pred)
        dump(path,results)
    return results


def challenges(run,b,selection):
    path=run/'challenge_metrics.json';out=json.loads(path.read_text()) if path.exists() else {}
    dev=np.flatnonzero(b['meta'].split.eq('development'));test=np.flatnonzero(b['meta'].split.eq('test'))
    name=selection['child'];config=selection['configurations'][name]
    if 'monotherapy_to_combination' not in out:
        ti=np.array([i for i in dev if b['meta'].iloc[i].treatment!='combination']);vi=np.array([i for i in test if b['meta'].iloc[i].treatment=='combination'])
        mono_config=altered(config,{'heldout_treatment':'combination'})
        build=materialize(run,{'id':'challenge_mono_to_combo','config':mono_config});pred=[]
        for seed in CV_SEEDS:
            model=build(mono_config).fit(b,ti,seed);pred.append(model.predict(b,vi));model.close()
        p=np.mean(pred,0);out['monotherapy_to_combination']={'training_combo_labels':0,'test_unseen_clone_groups':True,
            'combo_early_expression_allowed_at_query_only':True,'combo_cells_in_representation_training':0,
            'scvi_unseen_batch_policy':'fixed-encoder reference-baseline-batch mapping, no query adaptation',
            'cross_treatment_training_policy':'withheld combination K/V token masked; never read combination state during training',
            'drug_encoding':'two chemical-presence indicators; combination=[1,1]',**score(b['meta'].iloc[vi].label,p)}
        dump(path,out)
    counts=pd.read_csv('data/t47d_lineage/prepared/clone_condition_counts.csv')
    n=counts.set_index(['clone_id','treatment','time_day']).cell_count.to_dict();tot=counts.groupby(['treatment','time_day']).cell_count.sum().to_dict()
    if 'late_interval_holdout' not in out:
        early=dict(b);early['meta']=b['meta'].copy()
        early['meta']['label']=[np.log2((n.get((r.clone_id,r.treatment,8),0)/tot[(r.treatment,8)]+1e-5)/(r.fraction_baseline+1e-5)) for r in b['meta'].itertuples()]
        cfg=altered(config,{'hazard_max_fit_day':8})
        build=materialize(run,{'id':'challenge_day8_to_day26','config':cfg});pred=[]
        for seed in CV_SEEDS:
            model=build(cfg).fit(early,dev,seed);pred.append(model.predict(early,test));model.close()
        p=np.mean(pred,0);out['late_interval_holdout']={'training_endpoint':8,'unseen_endpoint':26,'max_input_day':4,
            'training_day26_labels':0,'hazard_event_censoring_cutoff':8,
            'interpretation':'Direct day8-to-day26 response transport; not calibrated horizon-conditioned survival extrapolation',**score(b['meta'].iloc[test].label,p)}
        dump(path,out)
    if 'early_warning' not in out or out['early_warning'].get('horizon_contract_version')!=2:
        if 'early_warning' in out:
            archive=run/'evaluation_protocol_diagnostics';archive.mkdir(exist_ok=True)
            dump(archive/'early_warning_expanded_parent_legacy.json',out['early_warning'])
        byday={}
        for day in (0,1,4):
            cfg=restricted_horizon(config,day)
            build=materialize(run,{'id':'early_warning_day'+str(day),'config':cfg});pred=[]
            for seed in CV_SEEDS:
                model=build(cfg).fit(b,dev,seed);pred.append(model.predict(b,test));model.close()
            p=np.mean(pred,0);byday[str(day)]={'lead_days':26-day,**score(b['meta'].iloc[test].label,p),
                'classification':classification_metrics(b['meta'].iloc[test].label.to_numpy()>0,p)}
        out['early_warning']={'frozen_architecture_refit_per_horizon':True,'horizon_contract_version':2,
            'parent_policy':'Preserve every original baseline_only flag; restrict cutoff only. No expanded-parent feature access.', 'results':byday,
            'criterion':'Descriptive earliest observed cutoff with positive heldout Spearman; not clinical decision threshold'}
        dump(path,out)
    return out


def resistance_scores(run,b,selection):
    path=run/'resistance_attractor_and_month6.json'
    if path.exists():return json.loads(path.read_text())
    dev=np.flatnonzero(b['meta'].split.eq('development'));allrows=np.arange(len(b['meta']))
    config=selection['configurations'][selection['child']]
    build=materialize(run,{'id':'frozen_attractor_predictor','config':config});model=build(config).fit(b,dev,3)
    prediction=model.predict(b,allrows);model.close()
    names=b['contract']['pathways']['names'];ix=[i for i,s in enumerate(names) if any(x in s for x in ('ESTROGEN_RESPONSE','E2F_TARGETS','EPITHELIAL_MESENCHYMAL'))]
    adaptive=(b['pathway'][:,2,ix]-b['pathway'][:,0,ix]).mean(1)
    scaler=StandardScaler().fit(b['pathway'][dev,0]);z=scaler.transform(b['pathway'][:,2]);neg=dev[b['meta'].iloc[dev].label.to_numpy()<0]
    prototype=scaler.transform(b['pathway'][neg,2]);distance=cdist(z,prototype).min(1)
    hazard=FullCandidate({'model':'hazard','representation':'pca'}).fit(b,dev,3)
    _,x,_=hazard.view.transform(b,allrows)
    frame=pd.DataFrame(hazard.hazard_pca.transform(x),columns=['z'+str(i) for i in range(hazard.hazard_pca.n_components_)])
    persistence=hazard.hazard.predict_survival_function(frame,times=[180]).to_numpy().ravel()
    terms=np.column_stack([prediction,adaptive,distance,persistence])
    scaled=MinMaxScaler().fit(terms[dev]).transform(terms).clip(0,1)
    ras=scaled@np.array([.4,.25,.2,.15])
    rows=b['meta'].copy();rows['frozen_prediction']=prediction;rows['adaptive_program']=adaptive;rows['negative_reference_distance']=distance
    rows['predicted_persistence_day180']=persistence;rows['exploratory_ras']=ras
    rows.to_csv(run/'resistance_attractor_scores.csv',index=False)
    counts=pd.read_csv('data/t47d_lineage/prepared/clone_condition_counts.csv');month=counts.loc[counts.time_day.eq(180)]
    combo=rows.loc[rows.treatment.eq('combination')].sort_values('exploratory_ras',ascending=False)
    positives=set(month.loc[month.cell_count.ge(3),'clone_id'])
    eligible=set(combo.clone_id);tested=set(b['splits']['test_clones'])
    rankings={c:int(i+1) for i,c in enumerate(combo.clone_id)}
    available=positives&eligible;test_positive=available&tested
    result={'weights':[.4,.25,.2,.15],'weights_predeclared':True,'all_scalers_fit_on_development_only':True,
        'prediction_inputs':'days0/1/4 only; no observed late values enter query predictors',
        'persistence_model':'Actual interval-censored lognormal AFT trained on development endpoint counts; extrapolated survival to180 is exploratory and unvalidated',
        'month6_all_observed_clones':month[['clone_id','cell_count']].to_dict('records'),
        'eligible_positive_clones':sorted(available),'eligible_positive_ranks':{c:rankings[c] for c in available},
        'descriptive_recall_at5':len(available&set(combo.head(5).clone_id))/len(available) if available else None,
        'locked_test_positive_count':len(test_positive),
        'unseen_clone_escape_recall':None if not test_positive else len(test_positive&set(combo.head(5).clone_id))/len(test_positive),
        'month6_claim':'No positive heldout eligible clone => unseen-escape recall undefined; do not report in-sample dominant-clone rank as prospective validation',
        'noneligible_month6_clones':sorted(set(month.clone_id)-eligible),
        'clinical_claim':'No causal reversal, restored drug sensitivity, absolute cell killing, or clinical efficacy established'}
    dump(path,result);return result


def denominator_null(run,b,selection):
    path=run/'denominator_null_diagnostic.json'
    out=json.loads(path.read_text()) if path.exists() else {'draws':[]}
    dev=np.flatnonzero(b['meta'].split.eq('development'))
    config=selection['configurations'][selection['root']]
    for draw in range(len(out['draws']),20):
        changed=dict(b);changed['meta']=b['meta'].copy();rng=np.random.default_rng(12000+draw)
        f26=changed['meta'].fraction_day26.to_numpy().copy()
        for trt in TREATMENTS:
            idx=np.array([i for i in dev if b['meta'].iloc[i].treatment==trt])
            f26[idx]=rng.permutation(f26[idx])
        changed['meta']['label']=np.log2((f26+1e-5)/(changed['meta'].fraction_baseline+1e-5))
        result=evaluate(run,{'id':'diagnostic_endpoint_permutation_'+str(draw),'config':config,'parent':None},changed)
        out['draws'].append({'draw':draw,'reward':result['validation_reward'],'formal_fold_fits':result['formal_fold_fits']})
        dump(path,out)
    observed=json.loads((run/'tree.json').read_text())['nodes'][selection['root']]['validation_reward']
    values=np.array([d['reward'] for d in out['draws']])
    out.update(observed_root_reward=observed,null_mean=float(values.mean()),null_quantiles=np.quantile(values,[.025,.5,.975]).tolist(),
        mechanism='Permute day26 fractions within treatment among development clones, retain each clone baseline fraction, then recompute log-ratio target; refit fixed root on grouped CV',
        purpose='Diagnose denominator coupling/regression-to-the-mean. Not a new search or confirmatory permutation p value; root was already selected.',
        test_labels_used=False)
    dump(path,out);return out


def run_all(run=RUN):
    b=bundle(run);selection=json.loads((run/'frozen_selection.json').read_text())
    frozen_test(run,b,selection)
    ablate(run,b,selection['configurations'][selection['child']])
    loco(run,b,selection)
    challenges(run,b,selection)
    resistance_scores(run,b,selection)
    denominator_null(run,b,selection)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,default=RUN)
    run_all(parser.parse_args().run_dir)
