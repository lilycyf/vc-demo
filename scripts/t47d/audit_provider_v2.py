"""Engineering-only real-source audit. No Session initialization or model fitting."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from vc_demo.harness.research_contract import assert_recipe_files, file_digest
from vc_demo.harness.research_v2.metrics import MetricSpec
from vc_demo.harness.research_v2.session import Session
from vc_demo.t47d_provider_v2.data import read_inputs
from vc_demo.t47d_provider_v2.registration import make_task_spec


parser = argparse.ArgumentParser(description=__doc__)
if not __debug__:
    raise RuntimeError('Engineering audit requires normal assertion checks; do not run Python with -O')
parser.add_argument('--preparation-dir', type=Path, required=True)
parser.add_argument('--historical-run', type=Path, required=True)
parser.add_argument('--budget-guard', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.preparation_dir
p = json.loads((root / 'preparation_manifest.json').read_text())
c = json.loads(Path(p['development_contract']).read_text())
cc = json.loads(Path(p['confirmation_contract']['path']).read_text())
metric = MetricSpec('spearman', 'maximize', 'mean_seed', 'clone_x_treatment', 'clone_id')
Session._validate_contract(c, metric)
early, rows = read_inputs(p['development_inputs']['early_observations'])
query, qrows = read_inputs(cc['early_observations'])
assert rows == c['row_ids'] and qrows == cc['row_ids']
assert early['meta'].label.isna().all() and query['meta'].label.isna().all()
assert set(c['groups']).isdisjoint(cc['groups'])
assert c['seeds'] == p['task_contract']['cv_seeds']
assert p['counts'] == dict(development_rows=len(rows), development_clones=len(set(c['groups'])),
    confirmation_rows=len(qrows), confirmation_clones=len(set(cc['groups'])),
    seeds=len(c['seeds']), outer_folds=len(c['folds']))
original_splits = json.loads((args.historical_run / 'grouped_splits.json').read_text())
assert set(c['groups']) == set(original_splits['development_clones'])
assert set(cc['groups']) == set(original_splits['test_clones'])

# Independently check the response formula against the original count table.
count_paths = [path for path in p['source_files'] if Path(path).name == 'clone_condition_counts.csv']
assert len(count_paths) == 1
counts = pd.read_csv(count_paths[0])
totals = counts.groupby(['treatment', 'time_day']).cell_count.sum().to_dict()
lookup = counts.set_index(['clone_id', 'treatment', 'time_day']).cell_count.to_dict()
for contract in (c, cc):
    truth = []
    for row in contract['row_ids']:
        clone, treatment = row.split('::')
        f0 = lookup[(clone, 'baseline', 0)] / totals[('baseline', 0)]
        f26 = lookup.get((clone, treatment, 26), 0) / totals[(treatment, 26)]
        truth.append(np.log2((f26 + 1e-5) / (f0 + 1e-5)))
    np.testing.assert_allclose(truth, contract['targets'], rtol=0, atol=0)

guard = json.loads(args.budget_guard.read_text())
assert guard['mode'] == 'armed'
assert b'budget_guard.py' in (Path('/proc') / str(guard['pid']) / 'cmdline').read_bytes()
spec = make_task_spec(p, budget={'coverage': 0, 'optimization': 0, 'confirmation': 0},
    policy={'queue_capacity': 8, 'min_new_proposals': 1, 'parent_policy': 'global_queue',
            'exploration': 1., 'uncertainty_weight': 1., 'cost_penalty_per_hour': .01},
    resources={'authorization_id': 'Engineering preview only; does not authorize a scientific run',
               'deadline_utc': guard['deadline_utc']}, minimum_effect=0.)
Session._deadline(spec)
assert len(spec['benchmarks']) == 6 and spec['prior_test_exposure'] is True
assert spec['benchmark_recipes']['root_historical_exact_ridge']['parameters']['model_config']['historical_recipe'] == p['historical_ridge_config']
assert spec['metric']['aggregation'] == 'mean_seed'

historical = args.historical_run
lock = json.loads((historical / 'confirmation_lock.json').read_text())
assert file_digest(Path(lock['selection_path'])) == lock['selection_sha256']
for recipe in lock['recipes'].values():
    assert_recipe_files(recipe)
selected = json.loads((historical / 'frozen_selection.json').read_text())
for path, expected in selected['checkpoint_files'].items():
    assert file_digest(Path(path)) == expected

result = {'kind': 'real_source_adapter_preflight_not_scientific_experiment',
    'counts': p['counts'], 'metric_id': metric.identity, 'exact_baseline_count': len(spec['benchmarks']),
    'historical_exact_ridge_recipe_preserved': True, 'independent_label_formula_check': 'passed',
    'early_input_row_group_and_shape_checks': 'passed', 'development_confirmation_groups_disjoint': True,
    'endpoint_metadata_in_model_inputs': False, 'historical_test_exposure_preserved': True,
    'models_fitted_on_real_data': 0, 'real_data_session_initialized': False,
    'historical_selection_recipe_checkpoint_checksums': 'verified unchanged',
    'budget_guard_pid_preserved': guard['pid'], 'original_deadline_utc': guard['deadline_utc'],
    'scientific_search_started': False}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
