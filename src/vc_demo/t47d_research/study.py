"""Fresh, development-only T47D research search using shared protocol boundaries."""
from __future__ import annotations

import copy
import importlib.util
import json
import math
import subprocess
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from vc_demo.harness.mcts import backpropagate, select_parent
from vc_demo.harness.research_contract import (
    assert_search_open, assert_recipe_files, digest, executable_recipe, file_digest,
    freeze_record, register_benchmark, register_protocol, verify_benchmarks,
    verify_protocol, write_record,
)
from vc_demo.harness.research_feedback import paired_feedback, rank_hypotheses
from vc_demo.t47d_full import study as legacy
from vc_demo.t47d_lineage.data import CV_SEEDS
from vc_demo.t47d_research import runtime
from vc_demo.t47d_research.models import NEURAL
from vc_demo.t47d_full.models import effective_objective

_fold_evaluate = legacy.evaluate
RUN = Path('experiments/t47d_research_protocol_formal_v3')


def event(run, kind, **fields):
    legacy.event(run, kind, **fields)


def normalize(config):
    c = copy.deepcopy(config)
    c.setdefault('composition', 'replace')
    if c['model'] in NEURAL:
        for key, value in {'epochs':80, 'hidden':32, 'lr':.001, 'weight_decay':.02,
                           'optimizer':'adamw', 'dropout':.15, 'gradient_clip':1,
                           'auxiliary_weight':.2, 'ranking_weight':.1, 'pathway_weight':.1}.items():
            c.setdefault(key, value)
    elif c['model'] == 'tracsed':
        c['epochs'] = 20
        c['batch_size'] = 32
        c['optimizer'] = 'author_Adam_0.001_MSE'
        c['author_seed'] = 42
    else:
        c.pop('epochs', None)
    if c.get('parent_config'):
        c['parent_config'] = normalize(c['parent_config'])
    return c


def materialize(run, node):
    directory = run/'programs'/node['id']
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/'model.py'
    if not path.exists():
        path.write_text('from vc_demo.t47d_research.models import ResearchCandidate\n\ndef build_model(config):\n    return ResearchCandidate(config)\n')
    subprocess.run([sys.executable, '-m', 'py_compile', str(path)], check=True)
    write_record(directory/'pipeline.json', {'config':node['config'], 'parent':node.get('parent'),
        'composition':node['config'].get('composition', 'replace'), 'backend':'t47d_research_v3',
        'effective_training_objective':('squared error + L2; exact historical scaling and categorical encoding'
            if node['config']['model']=='historical_ridge' else effective_objective(node['config'])),
        'fallback':False, 'proxy':False, 'test_evaluation':'withheld_until_frozen_confirmation',
        'training_policy':'native direct-target model; OOF-only learned combination when explicitly selected'})
    module_name = 'research_node_'+digest({'path':str(path), 'sha256':file_digest(path)})[:16]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.build_model


def input_files():
    prepared = Path('data/t47d_lineage/prepared')
    names = ['dataset_manifest.json', 'clone_condition_counts.csv', 'clone_expression_rows.csv',
             'clone_mean_log_expression.npz', 'clone_pseudobulk_counts.npz', 'gene_order.csv', 'qc_counts.h5ad']
    return [prepared/name for name in names]+[legacy.PATHWAYS]


def recipe(run, node):
    materialize(run, node)
    code = [p for base in ('src/vc_demo/t47d_research', 'src/vc_demo/t47d_full', 'src/vc_demo/t47d_lineage')
            for p in Path(base).glob('*.py')]
    code += [Path('src/vc_demo/harness')/name for name in
             ('composition.py', 'research_contract.py', 'research_feedback.py', 'mcts.py')]
    code += [run/'programs'/node['id']/'model.py']
    code += [Path('scripts/t47d')/name for name in ('research_demo.py','full_prepare.py','full_demo.py',
        'full_tf_worker.py','full_reference.R')]
    code += [Path('/workspace/_external/TraCSED/model_scripts/TraCSED_final_model.ipynb')]
    environment = dict(runtime.source_identity()['packages'])
    external = run/'requirements_tensorflow.lock.txt'
    if external.is_file():
        environment['external_tensorflow_environment_sha256'] = file_digest(external)
    value = executable_recipe({'node_name':node['id'], 'task':'T47D_v3', 'model':node['config'],
        'metric':{'name':'spearman', 'direction':'maximize'}, 'cv_seeds':list(CV_SEEDS),
        'split_sha256':file_digest(run/'grouped_splits.json')}, code_files=code, data_files=input_files(),
        environment=environment)
    freeze_record(run/'execution_recipes'/(node['id']+'.json'), value)
    return value


def evaluate(run, node, bundle, only_splits=None):
    assert_search_open(run)
    node['config'] = normalize(node['config'])
    value = recipe(run, node)
    node['executable_recipe_fingerprint'] = value['fingerprint']
    # Reuse the tested fold evaluator, not its legacy fixed-composition materializer.
    legacy.materialize = materialize
    result = _fold_evaluate(run, node, bundle, only_splits)
    result.update(evidence_phase='search', executable_recipe_fingerprint=value['fingerprint'])
    write_record(run/'programs'/node['id']/'development_metrics.json', result)
    return result


def root_nodes():
    result = []
    for i, c in enumerate(legacy.roots()):
        name = 'root_'+str(i)+'_'+c['model']
        result.append({'id':name, 'name':name, 'parent':None, 'config':normalize(c),
                       'status':'candidate_queued', 'children':[], 'visits':0, 'value':0., 'depth':0})
    old = json.loads(Path('experiments/t47d_lineage_resistance_demo/tree.json').read_text())
    historical = old['nodes']['root_2_ridge']['config']
    result.append({'id':'root_historical_exact_ridge', 'name':'root_historical_exact_ridge', 'parent':None,
        'config':{'model':'historical_ridge', 'historical_recipe':historical, 'composition':'replace',
                  'representation':historical.get('representation', 'pathway')},
        'status':'candidate_queued', 'children':[], 'visits':0, 'value':0., 'depth':0})
    return result


def checkpoint(run, tree, plan):
    write_record(run/'tree.json', tree)
    counts = Counter(n['status'] for n in tree['nodes'].values())
    usage = {phase:sum(n.get('parent') is not None and n['status']=='trained' and n.get('budget_phase')==phase
                      for n in tree['nodes'].values()) for phase in ('coverage', 'optimization')}
    write_record(run/'research_budget.json', {**plan, 'used':usage})
    write_record(run/'run_status.json', {'counts':dict(counts), 'trained_rollouts':sum(usage.values()),
        'budget_trained_rollouts':plan['coverage_limit']+plan['optimization_limit'],
        'budget_by_phase':usage, 'reward':'5 seeds x 3 clone-fold OOF Spearman', 'prior_test_exposure':True})


def feedback(run, tree, bundle, node):
    if node['id']=='root_historical_exact_ridge':
        return
    reference = run/'programs'/'root_historical_exact_ridge'/'oof_predictions.csv'
    current = run/'programs'/node['id']/'oof_predictions.csv'
    if not reference.exists():
        return
    a = pd.read_csv(current).groupby('row').prediction.mean().sort_index()
    b = pd.read_csv(reference).groupby('row').prediction.mean().reindex(a.index)
    meta = bundle['meta'].iloc[a.index]
    details = paired_feedback(meta.label.to_numpy(), a.to_numpy(), b.to_numpy(), meta.clone_id.to_numpy(),
        lambda y,p:legacy.score(y,p)['spearman'], strata=meta.treatment.to_numpy(), draws=500, seed=43)
    write_record(run/'programs'/node['id']/'paired_development_feedback.json', details)
    node['paired_delta_vs_historical'] = details['paired_delta']
    node['paired_delta_ci95'] = details['delta_ci95']
    write_record(run/'development_feedback.json', {'evidence_phase':'development',
        'reference':'root_historical_exact_ridge', 'latest_node':node['id'], 'paired':details,
        'independent_development_clones':int(meta.clone_id.nunique()),
        'note':'Adaptive development evidence is not independent confirmation'})


def priority(tree, node):
    family = node['config']['model']
    prior = [n for n in tree['nodes'].values() if n['status']=='trained' and n.get('parent')
             and n['config']['model']==family]
    gains = [n['paired_delta_vs_historical'] for n in prior if n.get('paired_delta_vs_historical') is not None]
    gain = float(np.mean(gains))*len(gains)/(len(gains)+3) if gains else 0.
    uncertainty = max(float(np.std(gains, ddof=1)) if len(gains)>1 else .06, .01)/math.sqrt(len(gains)+1)
    if prior:
        cost = max(float(np.median([n['duration_seconds'] for n in prior]))/60, .1)
    else:
        cost = 1. if family in {'ridge','early_elastic','pls','xgboost','frequency'} else 3.
        if node['config'].get('representation') in {'scvi','cellrank','distance','pseudotime'}:
            cost *= 3
        if node['config'].get('composition') in {'crossfit_residual','crossfit_stack'}:
            cost *= 4
    ranked = rank_hypotheses([{'id':node['id'], 'expected_gain':gain, 'uncertainty':uncertainty,
                               'estimated_cost':cost}])[0]
    return ranked['scientific_priority'], ranked


def generate(run, tree, space, iteration):
    parent, components = select_parent(tree, math.sqrt(2), 20, policy='uct')
    event(run, 'parent_selection', parent=parent, components=components)
    rng = np.random.default_rng(43+iteration)
    options = list(space)
    rng.shuffle(options)
    created = 0
    for mutation in options:
        c = normalize(mutation)
        if c['model'] in NEURAL:
            c['hidden'] = int(rng.choice([32, 64]))
            c['epochs'] = int(rng.choice([80, 160]))
            c['lr'] = float(rng.choice([.0003, .001]))
        cheap = {'ridge','early_elastic','pls','frequency','xgboost','historical_ridge'}
        if (c['model'] in cheap and tree['nodes'][parent]['config']['model'] in cheap
                and tree['nodes'][parent]['config'].get('composition','replace')=='replace' and iteration%3==0):
            c['composition'] = 'crossfit_residual' if iteration%2 else 'crossfit_stack'
            c['parent_config'] = tree['nodes'][parent]['config']
        signature = digest(c)
        name = 'n_'+signature[:16]
        if name in tree['nodes']:
            continue
        n = {'id':name, 'name':name, 'parent':parent, 'config':c, 'mutation_config':mutation,
             'status':'candidate_queued', 'children':[], 'visits':0, 'value':0.,
             'depth':tree['nodes'][parent].get('depth',0)+1, 'budget_phase':'optimization'}
        tree['nodes'][name] = n
        tree['nodes'][parent]['children'].append(name)
        directory = run/'programs'/name
        directory.mkdir(parents=True, exist_ok=True)
        write_record(directory/'research_hypothesis.json', {'hypothesis':'Test '+str(c),
            'evidence_refs':[str(run/'development_feedback.json')],
            'expected_change':'Improve clone-grouped development prediction versus the unchanged exact historical recipe',
            'falsification':'No positive paired gain, or matched control explains the apparent gain',
            'composition':c['composition'], 'training_policy':c,
            'selection_evidence':'Development only; family estimates are descriptive, not confirmed effects'})
        event(run, 'proposal_generated', node=name, parent=parent, config=c)
        created += 1
        if created==4:
            break
    return created


def search(run=RUN, optimization_budget=40):
    assert_search_open(run)
    runtime.configure()
    run.mkdir(parents=True, exist_ok=True)
    bundle = legacy.bundle(run)
    space = legacy.manifest()
    required = [normalize(c) for c in legacy.required_choices(space)]
    plan = {'coverage_limit':len(required), 'optimization_limit':optimization_budget, 'confirmation_limit':2,
            'attribution_policy':'all original eight ablations, LOCO, horizon/combination/long-term challenges',
            'no_automatic_budget_extension':True}
    freeze_record(run/'research_budget_plan.json', plan)
    write_record(run/'search_space.json', {'candidates':space, 'count':len(space), 'open_compositions':
        ['replace','joint architecture','crossfit_residual','crossfit_stack'], 'all_implemented':True})
    path = run/'tree.json'
    if path.exists():
        verify_protocol(run)
        verify_benchmarks(run)
        tree = json.loads(path.read_text())
        for node in tree['nodes'].values():
            if node['status'] == 'selected':
                node['status'] = 'candidate_queued'
    else:
        roots = root_nodes()
        tree = {'nodes':{n['id']:n for n in roots}, 'roots':[n['id'] for n in roots],
                'root_nodes':[n['id'] for n in roots], 'events':[], 'mcts':{}}
        receipts = {}
        for root in roots:
            value = recipe(run, root)
            register_benchmark(run, root['id'], value)
            receipts[root['id']] = value['fingerprint']
        register_protocol(run, {'task_id':'T47D_lineage_research_v3',
            'dataset_sha256':digest({str(p):file_digest(p) for p in input_files()}),
            'split_sha256':file_digest(run/'grouped_splits.json'), 'label_semantics':bundle['contract']['label'],
            'metric':{'name':'spearman', 'direction':'maximize'}, 'group_key':'clone_id',
            'input_policy':'days0/1/4 only; every representation and combiner fitted within training clones',
            'required_benchmarks':receipts, 'prior_test_exposure':True,
            'interpretation':'Retrospective rerun, never fresh blind confirmation'})
        checkpoint(run, tree, plan)
    for name in tree['roots']:
        node = tree['nodes'][name]
        if node['status'] != 'trained':
            node.update(evaluate(run, node, bundle))
            backpropagate(tree, name, node['validation_reward'])
            event(run, 'backpropagation', node=name, reward=node['validation_reward'], status='trained')
            checkpoint(run, tree, plan)
    for root in (tree['nodes'][name] for name in tree['roots']):
        feedback(run, tree, bundle, root)
    for index, c in enumerate(required):
        name = 'coverage_'+str(index)+'_'+digest(c)[:10]
        if name not in tree['nodes']:
            parent = 'root_historical_exact_ridge'
            tree['nodes'][name] = {'id':name, 'name':name, 'parent':parent, 'config':c,
                'mutation_config':c, 'status':'candidate_queued', 'children':[], 'visits':0, 'value':0.,
                'budget_phase':'coverage', 'depth':1}
            tree['nodes'][parent]['children'].append(name)
        node = tree['nodes'][name]
        if node['status']!='trained':
            try:
                node.update(evaluate(run, node, bundle))
            except Exception:
                node.update(status='failed', error=traceback.format_exc())
                event(run, 'coverage_failure_continued', node=name, error=node['error'])
                checkpoint(run, tree, plan)
                continue
            backpropagate(tree, name, node['validation_reward'])
            feedback(run, tree, bundle, node)
            event(run, 'coverage_completed', node=name, reward=node['validation_reward'], status='trained')
            checkpoint(run, tree, plan)
    iteration = sum(n.get('budget_phase')=='optimization' and n['status']=='trained' for n in tree['nodes'].values())
    while iteration < optimization_budget:
        assert_search_open(run)
        generate(run, tree, space, iteration+len(tree['nodes']))
        queue = [n for n in tree['nodes'].values() if n['status']=='candidate_queued' and n.get('budget_phase')=='optimization']
        if not queue:
            raise RuntimeError('No feasible global candidate; formal budget not completed')
        ranked = sorted(((priority(tree,n)[0], n['id']) for n in queue), reverse=True)
        for _, name in ranked[48:]:
            tree['nodes'][name]['status'] = 'pruned_not_selected'
            event(run, 'global_prune', node=name, reason='global capacity 48 after development re-ranking')
        node = tree['nodes'][ranked[0][1]]
        node['status'] = 'selected'
        node['scientific_selection'] = priority(tree,node)[1]
        event(run, 'global_queue_selected', node=node['id'], priority=node['scientific_selection'])
        checkpoint(run, tree, plan)
        try:
            node.update(evaluate(run, node, bundle))
        except Exception:
            node.update(status='failed', error=traceback.format_exc())
            event(run, 'training_failure', node=node['id'], error=node['error'])
            checkpoint(run, tree, plan)
            if sum(n['status']=='failed' for n in tree['nodes'].values()) >= 8:
                raise RuntimeError('Repeated real training failures require active Codex repair')
            continue
        backpropagate(tree, node['id'], node['validation_reward'])
        feedback(run, tree, bundle, node)
        iteration += 1
        event(run, 'rollout_completed_regenerate_next', node=node['id'], completed_optimization_rollouts=iteration,
              reward=node['validation_reward'], backprop_path=tree['mcts']['last_backpropagation']['path'])
        checkpoint(run, tree, plan)
    roots = [n for n in tree['nodes'].values() if n['status']=='trained' and not n.get('parent')]
    children = [n for n in tree['nodes'].values() if n['status']=='trained' and n.get('parent')]
    root, child = max(roots,key=lambda n:n['validation_reward']), max(children,key=lambda n:n['validation_reward'])
    optimized = [n for n in children if n.get('budget_phase')=='optimization']
    selected = {'root':root['id'], 'child':child['id'], 'configurations':{n['id']:n['config'] for n in (root,child)},
                'prior_test_exposure':True, 'selected_by':'development OOF only',
                'selected_child_phase':child['budget_phase'],
                'best_optimization_child':max(optimized,key=lambda n:n['validation_reward'])['id'],
                'stop_reason':'separate registered coverage and optimization budgets exhausted'}
    write_record(run/'development_selection.json', selected)
    return selected
