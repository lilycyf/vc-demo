"""Replay the previously frozen pilot root without changing formal selection."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from vc_demo.t47d_full.study import RUN,bundle,score
from vc_demo.t47d_lineage.composition import build_candidate,move_to_cpu
from vc_demo.t47d_lineage.data import CV_SEEDS,dump


def main():
    if not (RUN/'frozen_selection.json').exists():raise RuntimeError('Reference replay is post-freeze only')
    b=bundle()
    old=Path('experiments/t47d_lineage_resistance_demo')
    config=json.loads((old/'tree.json').read_text())['nodes']['root_2_ridge']['config']
    spec=importlib.util.spec_from_file_location('t47d_registered_pilot','scripts/t47d/run.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    validation=module.cross_validate(b,config)
    dev=np.flatnonzero(b['meta'].split.eq('development'));test=np.flatnonzero(b['meta'].split.eq('test'))
    predictions=[]
    for seed in CV_SEEDS:
        model=build_candidate(config).fit(b,dev,seed)
        predictions.append(model.predict(b,test));move_to_cpu(model)
    pred=np.mean(predictions,axis=0)
    result={'purpose':'Replay stronger previously frozen reference; never eligible for post-test reselection of formal winner',
        'config':config,'validation':validation,'heldout':score(b['meta'].iloc[test].label,pred),
        'previously_exposed_test':True,
        'preprocessing_difference':'Pilot baseline uses standardized 3-category treatment covariates; new full-study plugin uses 2 chemical-presence indicators. Regularized baselines are not preprocessing-equivalent.',
        'interpretation':'Beating only the current 5 roots does not establish improvement over the previously validated stronger root. Preserve this comparison rather than tune the test.',
        'recommendation':'Future framework revisions must freeze baseline input encoding/scaling as well as split/labels; retain strong historical roots as fixed benchmarks.'}
    dump(RUN/'historical_baseline_reference_audit.json',result)
    b['meta'].iloc[test].assign(prediction=pred).to_csv(RUN/'historical_baseline_reference_predictions.csv',index=False)
    print(json.dumps({'validation':validation['validation_reward'],'heldout':result['heldout']}),flush=True)


if __name__=='__main__':main()
