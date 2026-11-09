"""Post-hoc diagnostic only: never refit models or feed results back to search."""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from vc_demo.harness.research_contract import digest, write_record
from vc_demo.t47d_lineage.data import load_bundle


def rho(y, p):
    return float(spearmanr(y, p).statistic)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--draws', type=int, default=2000)
    args = parser.parse_args()
    run = args.run_dir
    output = run/'retrospective'
    output.mkdir(exist_ok=True)
    nodes = json.loads((run/'tree.json').read_text())['nodes']
    selected = json.loads((run/'development_selection.json').read_text())
    root, child = selected['root'], selected['child']
    trace = [json.loads(line) for line in (run/'mcts_trace.jsonl').read_text().splitlines()]
    parents = collections.Counter(t['parent'] for t in trace if t['event']=='parent_selection')
    trained = [n for n in nodes.values() if n['status']=='trained']
    signatures = collections.defaultdict(list)
    for n in trained:
        signatures[digest(n['config'])].append(n['id'])
    summary = {
        'evidence_phase':'posthoc_retrospective', 'selection_feedback_allowed':False,
        'refitted_models':0, 'primary_run_and_original_feedback_modified':False,
        'root':root, 'child':child,
        'trained_nodes':len(trained), 'unique_declared_configurations':len(signatures),
        'duplicate_configuration_groups':[v for v in signatures.values() if len(v)>1],
        'parent_selection_counts':dict(parents),
        'strong_root_optimization_parent_selections':parents[root],
        'strong_root_children':len(nodes[root]['children']),
        'configured_parent_child_limit':20,
        'first_selection_strong_root_eligible':any(c['node']==root for c in next(t for t in trace if t['event']=='parent_selection')['components']),
        'proposal_compositions':dict(collections.Counter(t['config'].get('composition','replace') for t in trace if t['event']=='proposal_generated')),
        'optimization_representations_by_status':{},
        'negative_priority_selected_rollouts':sum(t['priority']['scientific_priority']<0 for t in trace if t['event']=='global_queue_selected'),
    }
    for status in ('trained','candidate_queued','pruned_not_selected'):
        summary['optimization_representations_by_status'][status] = dict(collections.Counter(
            n['config']['representation'] for n in nodes.values()
            if n['status']==status and n.get('budget_phase')=='optimization'))
    # A temporary metadata export avoids rewriting the frozen original task files.
    metadata = Path('/tmp/t47d_retrospective_metadata')
    metadata.mkdir(exist_ok=True)
    bundle = load_bundle(Path('data/t47d_lineage/prepared'),
        Path('data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt'), metadata)
    a = pd.read_csv(run/'programs'/child/'oof_predictions.csv').pivot(index='row',columns='seed',values='prediction')
    b = pd.read_csv(run/'programs'/root/'oof_predictions.csv').pivot(index='row',columns='seed',values='prediction').reindex(a.index)
    meta = bundle['meta'].iloc[a.index]
    y, groups, ap, bp = meta.label.to_numpy(), meta.clone_id.to_numpy(), a.to_numpy(), b.to_numpy()
    def primary_delta(ids):
        return float(np.mean([rho(y[ids],ap[ids,j])-rho(y[ids],bp[ids,j]) for j in range(ap.shape[1])]))
    rng = np.random.default_rng(43)
    unique = np.unique(groups)
    boot = [primary_delta(np.concatenate([np.flatnonzero(groups==g)
        for g in rng.choice(unique,len(unique),replace=True)])) for _ in range(args.draws)]
    summary['development_primary_metric'] = {
        'definition':'mean over seeds of complete OOF Spearman',
        'paired_delta':primary_delta(np.arange(len(y))),
        'conditional_cluster_bootstrap_ci95':np.quantile(boot,[.025,.975]).tolist(),
        'independent_clone_groups':len(unique), 'draws':args.draws,
        'per_seed':{str(seed):{'root':rho(y,bp[:,j]),'child':rho(y,ap[:,j]),
            'delta':rho(y,ap[:,j])-rho(y,bp[:,j])} for j,seed in enumerate(a.columns)},
    }
    summary['development_original_feedback_estimand'] = {
        'definition':'Spearman after averaging OOF predictions over seeds',
        'root':rho(y,bp.mean(1)), 'child':rho(y,ap.mean(1)),
        'paired_delta':rho(y,ap.mean(1))-rho(y,bp.mean(1)),
    }
    ar = pd.read_csv(run/(root+'_heldout_predictions.csv')).sort_values(['clone_id','treatment'])
    ac = pd.read_csv(run/(child+'_heldout_predictions.csv')).sort_values(['clone_id','treatment'])
    assert ar[['clone_id','treatment']].equals(ac[['clone_id','treatment']])
    np.testing.assert_allclose(ar.label, ac.label)
    ty, rp, cp, tg = ar.label.to_numpy(), ar.prediction.to_numpy(), ac.prediction.to_numpy(), ar.clone_id.to_numpy()
    unique = np.unique(tg)
    rng = np.random.default_rng(44)
    deltas = []
    for _ in range(args.draws):
        ids = np.concatenate([np.flatnonzero(tg==g) for g in rng.choice(unique,len(unique),replace=True)])
        delta = rho(ty[ids],cp[ids])-rho(ty[ids],rp[ids])
        if np.isfinite(delta):
            deltas.append(delta)
    summary['frozen_confirmation_descriptive_comparison'] = {
        'root':rho(ty,rp), 'child':rho(ty,cp), 'delta':rho(ty,cp)-rho(ty,rp),
        'conditional_paired_clone_bootstrap_ci95':np.quantile(deltas,[.025,.975]).tolist(),
        'independent_clone_groups':len(unique), 'historical_test_exposure':True,
    }
    summary['uncertainty_caveat'] = (
        'Bootstrap resamples whole clone blocks with predictions fixed. It does not refit the pipeline, '
        'correct adaptive model selection, create fresh heldout data, or establish significance of framework superiority.')
    write_record(output/'framework_audit_evidence.json', summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
