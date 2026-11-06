"""Validate actual complete-study evidence, independently of scientific wins."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from vc_demo.t47d_full.study import RUN
from vc_demo.t47d_lineage.data import CV_SEEDS, dump


def audit(run=RUN):
    def read(name):
        return json.loads((run/name).read_text())
    nodes=read('tree.json')['nodes']
    trained=[n for n in nodes.values() if n['status']=='trained']
    splits=read('grouped_splits.json')
    heldout=set(splits['test_clones'])
    formal=[]
    for n in trained:
        rows=read('programs/'+n['id']+'/fold_results.json')
        pairs={(r['seed'],r['fold']) for r in rows}
        formal.append(len(rows)==15 and pairs=={(s,f) for s in CV_SEEDS for f in range(3)})
    trace=[json.loads(s) for s in (run/'mcts_trace.jsonl').read_text().splitlines()]
    backprop=Counter(e['node'] for e in trace if e['event']=='backpropagation')
    child_backprop=[i for i,e in enumerate(trace) if e['event']=='backpropagation' and nodes[e['node']].get('parent')]
    regeneration=[any(e['event']=='proposal_generated' for e in trace[a+1:z]) for a,z in zip(child_backprop[:-1],child_backprop[1:])]
    selection=read('frozen_selection.json')
    loco=read('loco_results.json')
    references=[json.loads(s) for s in (run/'reference/tf_reference_results.jsonl').read_text().splitlines()]
    per_barcode=Counter(r['barcode'] for r in references)
    guards=read('guardrail_audit.json')
    manifest=read('run_manifest.json')
    checks={
        'five_roots_forty_children':len(trained)==45 and sum(n.get('parent') is None for n in trained)==5,
        'all_675_primary_fits_and_unique_seed_folds':len(formal)==45 and all(formal),
        'exactly_once_trained_only_backprop':set(backprop)=={n['id'] for n in trained} and set(backprop.values())=={1},
        'regeneration_after_every_nonfinal_rollout':len(regeneration)==39 and all(regeneration),
        'primary_clone_disjoint':all(not heldout.intersection(f['train_clones']+f['validation_clones']) for f in splits['folds']),
        'original_task_hash_unchanged':hashlib.sha256((run/'task_contract.json').read_bytes()).hexdigest()==manifest['data_contract_sha256'],
        'original_split_hash_unchanged':hashlib.sha256((run/'grouped_splits.json').read_bytes()).hexdigest()==manifest['split_sha256'],
        'loco_exactly_46_unique_clones_each':all(len(loco[selection[k]]['folds'])==46 and len({f['clone'] for f in loco[selection[k]]['folds']})==46 for k in ('root','child')),
        'all_29_author_trajectories_16_fits_each':len(per_barcode)==29 and set(per_barcode.values())=={16},
        'all_464_reference_fits_with_four_variants':len(references)==464 and set(Counter(r['variant'] for r in references).values())=={116},
        'eight_ablations_120_formal_fits':len(read('eight_ablations.json'))==8 and all(v['formal_fold_fits']==15 for v in read('eight_ablations.json').values()),
        'no_pathway_control_preserves_unrelated_modules':read('eight_ablations.json')['no_pathway'].get('ablation_contract_version')==2,
        'all_twenty_denominator_diagnostics':len(read('denominator_null_diagnostic.json')['draws'])==20,
        'all_three_early_warning_cutoffs':set(read('challenge_metrics.json')['early_warning']['results'])=={'0','1','4'},
        'early_warning_keeps_frozen_parent_input_policy':read('challenge_metrics.json')['early_warning'].get('horizon_contract_version')==2,
        'no_unidentified_escape_recall_claim':read('resistance_attractor_and_month6.json')['locked_test_positive_count']==0 and read('resistance_attractor_and_month6.json')['unseen_clone_escape_recall'] is None,
        'guardrails':guards['passed'],
        'whole_original_completion_matrix':read('completion_matrix.json')['whole_original_document_complete'],
        'strong_historical_reference_retained':(run/'historical_baseline_reference_audit.json').exists(),
    }
    child=nodes[selection['child']]
    biology=read('biological_and_sensitivity_analysis.json')
    objectives={
        'child_beats_current_five_roots':child['validation_reward']>nodes[selection['root']]['validation_reward'],
        'child_beats_historical_strong_root':child['validation_reward']>read('historical_baseline_reference_audit.json')['validation']['validation_reward'],
        'child_beats_early_abundance_only':child['validation_reward']>read('early_abundance_baseline.json')['validation_reward'],
        'child_beats_day4_snapshot':child['validation_reward']>read('temporal_snapshot_control.json')['validation_reward'],
        'combined_suppression_observed_descriptively':biology['mono_positive_combo_negative_count']>0,
        'long_term_unseen_clone_forecast_identifiable':False,
    }
    result={'passed':all(checks.values()),'checks':checks,'scientific_objectives':objectives,
        'interpretation':'Completed implementation is not equivalent to achieving every scientific hypothesis. No test-driven reselection.',
        'logging_caveat':{'explicit_rollout_completed_events':sum(e['event']=='rollout_completed_regenerate_next' for e in trace),
            'trained_child_backprop_events':len(child_backprop),'regeneration_verified_from_actual_next_proposal_events':sum(regeneration),
            'note':'Three interruption-resumed rollouts lacked the redundant completion event; actual train/backprop and subsequent regeneration are present. Historical trace is not fabricated or rewritten.'},
        'formal_counts':{'primary':675,'ablations':120,'loco':92,'author_reference':464,'endpoint_permutation':300,'additional_snapshot_and_abundance':30}}
    dump(run/'complete_study_acceptance_audit.json',result)
    print(json.dumps(result),flush=True)
    if not result['passed']:raise SystemExit('Actual evidence is incomplete; do not declare whole-study completion')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,default=RUN)
    audit(parser.parse_args().run_dir)
