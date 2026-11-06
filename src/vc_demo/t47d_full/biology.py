"""Clone-paired descriptive biology and sampling/label sensitivity analyses."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import wilcoxon,spearmanr
from vc_demo.t47d_full.study import RUN,bundle
from vc_demo.t47d_lineage.data import dump,TREATMENTS


def paired_ci(x):
    x=np.asarray(x);rng=np.random.default_rng(20261106)
    means=np.mean(rng.choice(x,(2000,len(x)),replace=True),axis=1)
    return {'n_clones':len(x),'mean':float(x.mean()),'median':float(np.median(x)),
        'clone_bootstrap_mean_ci95':np.quantile(means,[.025,.975]).tolist(),
        'wilcoxon_descriptive_p':float(wilcoxon(x).pvalue) if np.any(x) else 1.}


def analyze(run=RUN):
    b=bundle(run);root=Path('data/t47d_lineage/prepared')
    rows=pd.read_csv(root/'clone_expression_rows.csv');expr=sparse.load_npz(root/'clone_mean_log_expression.npz')
    symbols=pd.read_csv(root/'gene_order.csv').gene_symbol.fillna('').to_numpy()
    sets={}
    for line in Path('data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt').read_text().splitlines():
        t=line.split('\t')
        if any(k in t[0] for k in ('ESTROGEN_RESPONSE','E2F_TARGETS','EPITHELIAL_MESENCHYMAL')):
            ids=np.flatnonzero(np.isin(symbols,t[2:]));sets[t[0]]=ids
    lookup={(r.clone_id,r.treatment,int(r.time_day)):i for i,r in rows.iterrows()}
    records=[]
    for clone in b['meta'].clone_id.unique():
        base=lookup[(clone,'baseline',0)]
        for trt in TREATMENTS:
            for day in (1,4,8,26):
                key=(clone,trt,day)
                if key not in lookup:continue
                row={'clone_id':clone,'treatment':trt,'time_day':day,
                     'split':'test' if clone in b['splits']['test_clones'] else 'development'}
                for name,ids in sets.items():
                    row[name]=float(expr[lookup[key],ids].mean()-expr[base,ids].mean())
                records.append(row)
    frame=pd.DataFrame(records);frame.to_csv(run/'clone_pathway_adaptation.csv',index=False)
    comparisons={}
    for day in (1,4,8,26):
        for name in sets:
            table=frame.loc[frame.time_day.eq(day)].pivot(index='clone_id',columns='treatment',values=name)
            for mono in TREATMENTS[:2]:
                paired=table[['combination',mono]].dropna()
                comparisons[name+'__day'+str(day)+'__combo_minus_'+mono]=paired_ci(paired.combination-paired[mono])
    counts=pd.read_csv(root/'clone_condition_counts.csv')
    n=counts.set_index(['clone_id','treatment','time_day']).cell_count.to_dict();tot=counts.groupby(['treatment','time_day']).cell_count.sum().to_dict()
    eps={}
    for e in (1e-6,1e-5,1e-4):
        labels=np.array([np.log2((n.get((r.clone_id,r.treatment,26),0)/tot[(r.treatment,26)]+e)/(r.fraction_baseline+e)) for r in b['meta'].itertuples()])
        eps[str(e)]={'selection_median':float(np.median(labels)),'positive_count':int((labels>0).sum()),
            'correlation_with_registered_label':float(spearmanr(labels,b['meta'].label).statistic)}
    table=b['meta'].pivot(index='clone_id',columns='treatment',values='label')
    raw=b['meta'].assign(raw_ratio=b['meta'].fraction_day26/b['meta'].fraction_baseline).pivot(index='clone_id',columns='treatment',values='raw_ratio')
    suppression=pd.DataFrame({'clone_id':table.index,'log2_difference':table[list(TREATMENTS[:2])].max(axis=1)-table.combination,
        'raw_ratio_difference':raw[list(TREATMENTS[:2])].max(axis=1)-raw.combination,
        'mono_positive_combo_negative':((table[list(TREATMENTS[:2])].max(axis=1)>0)&(table.combination<0)).astype(int)})
    suppression.to_csv(run/'observed_combination_suppression.csv',index=False)
    report={'pathway_pairs':comparisons,'epsilon_sensitivity':eps,
        'selection_by_treatment':{t:{'positive_clones':int((table[t]>0).sum()),'median_log2_selection':float(table[t].median()),
            'endpoint_nondetected':int(b['meta'].loc[b['meta'].treatment.eq(t),'endpoint_sampling_zero'].sum())} for t in TREATMENTS},
        'mono_positive_combo_negative_count':int(suppression.mono_positive_combo_negative.sum()),
        'mono_positive_count':int((table[list(TREATMENTS[:2])].max(axis=1)>0).sum()),
        'caveats':['Pathway comparisons condition on observed cells, so survivorship/attrition can change cohort composition',
            'No absolute cell numbers or reculturing/rechallenge => cannot prove restored sensitivity or state reversal',
            'Libraries are not independently verified biological replicates; clone bootstrap is not donor-level inference',
            'Many descriptive pathway comparisons; nominal p values uncorrected and not confirmatory evidence'],
        'paper_alignment':'Hallmark ER/E2F/EMT signatures reconstructed from public memberships, not unavailable private custom ER signature'}
    dump(run/'biological_and_sensitivity_analysis.json',report)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,default=RUN)
    analyze(parser.parse_args().run_dir)
