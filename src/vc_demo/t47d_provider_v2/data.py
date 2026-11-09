"""Source-backed T47D export; preparation is separate from research execution."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
from scipy import sparse

from vc_demo.harness.research_contract import digest, file_digest, freeze_record
from vc_demo.t47d_lineage.data import load_bundle, TREATMENTS


def save_inputs(path, bundle, indices):
    """Store early observations only, never endpoint counts or response labels."""
    path = Path(path)
    meta = bundle['meta'].iloc[indices]
    arrays = {key: np.asarray(bundle[key])[indices] for key in
              ('expression', 'pathway', 'aux', 'pseudobulk')}
    arrays.update(row_ids=np.asarray([f'{r.clone_id}::{r.treatment}' for r in meta.itertuples()]),
                  groups=np.asarray(meta.clone_id, dtype=str),
                  treatments=np.asarray(meta.treatment, dtype=str))
    np.savez_compressed(path, **arrays)
    return {'path': str(path.resolve()), 'sha256': file_digest(path)}


def read_inputs(info):
    path = Path(info['path'])
    if file_digest(path) != info['sha256']:
        raise ValueError('Early-observation input content changed')
    with np.load(path, allow_pickle=False) as stored:
        data = {key: stored[key] for key in stored.files}
    expected = {'expression', 'pathway', 'aux', 'pseudobulk', 'row_ids', 'groups', 'treatments'}
    if set(data) != expected:
        raise ValueError('Early inputs contain unexpected fields, possibly endpoint/label leakage')
    n = len(data['row_ids'])
    for key in ('expression', 'pathway', 'pseudobulk'):
        x = data[key]
        if x.ndim != 3 or x.shape[:2] != (n, 3) or not np.isfinite(x).all():
            raise ValueError('Invalid early sequence shape/content: ' + key)
    if data['pseudobulk'].shape != data['expression'].shape:
        raise ValueError('Pseudobulk gene order/width differs from expression')
    if data['aux'].shape != (n, 9) or not np.isfinite(data['aux']).all():
        raise ValueError('Invalid early abundance/observation/treatment encoding')
    if len(set(data['row_ids'])) != n or len(data['groups']) != n or len(data['treatments']) != n:
        raise ValueError('Invalid row/group identity')
    groups, treatments = data.pop('groups'), data.pop('treatments')
    rows = data.pop('row_ids').tolist()
    if not set(treatments) <= set(TREATMENTS):
        raise ValueError('Unknown treatment vocabulary')
    for group in set(groups):
        if sorted(treatments[groups == group]) != sorted(TREATMENTS):
            raise ValueError('Each clone must retain all three treatment rows')
    if rows != [f'{g}::{t}' for g, t in zip(groups, treatments)]:
        raise ValueError('Row identity differs from clone/treatment order')
    data['meta'] = pd.DataFrame({'clone_id': groups, 'treatment': treatments,
                                 'label': np.full(n, np.nan)})
    return data, rows


def development_contract(bundle, indices):
    meta = bundle['meta'].iloc[indices]
    folds = [{'seed': int(f['seed']), 'fold_id': str(f['fold']),
              'train_groups': list(f['train_clones']),
              'validation_groups': list(f['validation_clones'])} for f in bundle['splits']['folds']]
    seeds = list(dict.fromkeys(f['seed'] for f in folds))
    groups = meta.clone_id.astype(str).tolist()
    return {'row_ids': [f'{r.clone_id}::{r.treatment}' for r in meta.itertuples()],
            'groups': groups, 'targets': meta.label.astype(float).tolist(), 'seeds': seeds,
            'folds': folds, 'fold_ids': [[next(f['fold_id'] for f in folds
                if f['seed'] == seed and group in f['validation_groups']) for seed in seeds] for group in groups]}


def prepare(prepared, pathways, historical_run, baseline_tree, output_dir, *, heavy_sources=False,
            tracsed_notebook=None, tensorflow_python=None):
    """Export the exact existing task/split, without fitting or initializing a run."""
    prepared, pathways, historical_run, baseline_tree, out = map(Path,
        (prepared, pathways, historical_run, baseline_tree, output_dir))
    if out.exists() and any(out.iterdir()):
        raise ValueError('Use a fresh preparation directory; never overwrite data contracts')
    required = ['dataset_manifest.json', 'clone_condition_counts.csv', 'clone_expression_rows.csv',
                'clone_mean_log_expression.npz', 'clone_pseudobulk_counts.npz', 'gene_order.csv', 'qc_counts.h5ad']
    files = [prepared / name for name in required] + [pathways,
        historical_run / 'task_contract.json', historical_run / 'grouped_splits.json', baseline_tree]
    provenance = {str(p.resolve()): {'sha256': file_digest(p), 'size_bytes': p.stat().st_size} for p in files}
    with tempfile.TemporaryDirectory(prefix='t47d_v2_prepare_') as temp:
        b = load_bundle(prepared, pathways, Path(temp))
    if b['contract'] != json.loads((historical_run / 'task_contract.json').read_text()):
        raise ValueError('Source-backed task differs from historical contract')
    if b['splits'] != json.loads((historical_run / 'grouped_splits.json').read_text()):
        raise ValueError('Do not redraw clone partitions during adapter migration')
    tree = json.loads(baseline_tree.read_text())
    root = tree['nodes']['root_2_ridge']['config']
    if root.get('model') != 'ridge' or root.get('parent_config'):
        raise ValueError('Historical strong benchmark must be the exact standalone Ridge recipe')
    # Select only early cell-count rows before aggregating the separate pseudobulk input.
    table = pd.read_csv(prepared / 'clone_expression_rows.csv')
    counts = sparse.load_npz(prepared / 'clone_pseudobulk_counts.npz').astype(float)
    counts = sparse.diags(1e4 / np.maximum(np.asarray(counts.sum(1)).ravel(), 1)).dot(counts).tocsr()
    counts.data = np.log1p(counts.data)
    lookup = {(r.clone_id, r.treatment, int(r.time_day)): i for i, r in table.iterrows()}
    early = np.zeros_like(b['expression'])
    for i, r in b['meta'].iterrows():
        for j, day in enumerate((0, 1, 4)):
            key = (r.clone_id, 'baseline' if day == 0 else r.treatment, day)
            if key in lookup:
                early[i, j] = counts[lookup[key]].toarray()[0]
    b['pseudobulk'] = early
    dev = np.flatnonzero(b['meta'].split.eq('development'))
    heldout = np.flatnonzero(b['meta'].split.eq('test'))
    out.mkdir(parents=True, exist_ok=True)
    dev_input = save_inputs(out / 'development_early.npz', b, dev)
    heldout_input = save_inputs(out / 'confirmation_early.npz', b, heldout)
    dc = development_contract(b, dev)
    freeze_record(out / 'development_contract.json', dc)
    schema = {'early_days': [0, 1, 4], 'treatments': list(TREATMENTS),
              'gene_order_sha256': file_digest(prepared / 'gene_order.csv'),
              'hallmark_sha256': file_digest(pathways),
              'normalization': 'original clone mean log expression; separate log1p library-normalized pseudobulk',
              'forbidden_model_metadata': ['n_day26', 'fraction_day26', 'endpoint_sampling_zero', 'label']}
    freeze_record(out / 'feature_schema.json', schema)
    meta = b['meta'].iloc[heldout]
    cc = {'row_ids': [f'{r.clone_id}::{r.treatment}' for r in meta.itertuples()],
          'groups': meta.clone_id.astype(str).tolist(), 'targets': meta.label.astype(float).tolist(),
          'seeds': dc['seeds'], 'early_observations': heldout_input,
          'prior_test_exposure': True}
    extra = None
    if heavy_sources:
        from .cell_sources import export
        extra = export(prepared, out, set(dc['groups']), set(cc['groups']))
        cc.update(early_cells=extra['confirmation'], gene_order=extra['gene_order'])
    freeze_record(out / 'confirmation_contract.json', cc)
    manifest = {'schema_version': 't47d_provider_v2', 'accession': 'GSE260703',
        'dataset_sha256': digest(provenance), 'split_sha256': file_digest(historical_run / 'grouped_splits.json'),
        'source_files': provenance, 'task_contract': b['contract'], 'historical_ridge_config': root,
        'development_inputs': {'early_observations': dict(dev_input, scope='development'),
            'feature_schema': {'path': str((out / 'feature_schema.json').resolve()),
                               'sha256': file_digest(out / 'feature_schema.json'), 'scope': 'public'}},
        'development_contract': str((out / 'development_contract.json').resolve()),
        'confirmation_contract': {'path': str((out / 'confirmation_contract.json').resolve()),
                                  'sha256': file_digest(out / 'confirmation_contract.json')},
        'hallmark': {'path': str(pathways.resolve()), 'sha256': file_digest(pathways),
                    'source': 'MSigDB Hallmark v2025.1.Hs GMT; source-backed existing task contract',
                    'status': 'original_public', 'kind': 'gene_set_membership',
                    'alignment': 'Exact gene_order.csv -> mean log1p expression, fixed early days 0/1/4'},
        'counts': {'development_rows': len(dev), 'development_clones': len(set(dc['groups'])),
                   'confirmation_rows': len(heldout), 'confirmation_clones': len(set(cc['groups'])),
                   'seeds': len(dc['seeds']), 'outer_folds': len(dc['folds'])},
        'prior_test_exposure': True, 'models_fitted': 0, 'scientific_run_started': False}
    if extra:
        from .cell_sources import info
        manifest['development_inputs'].update(early_cells=extra['development'],
            training_events=extra['training_events'], gene_order=extra['gene_order'])
        manifest['heavy_source_counts'] = {phase: extra[phase + '_cells'] for phase in ('development', 'confirmation')}
        manifest['postselection_sources'] = {name: info(prepared / name) for name in
            ('clone_condition_counts.csv', 'clone_expression_rows.csv', 'clone_mean_log_expression.npz', 'gene_order.csv')}
        manifest['postselection_sources']['development_label_metadata.json'] = extra['development_label_metadata']
        manifest['preparation_capabilities'] = ['portable_early_cells', 'training_only_event_counts', 'postselection_analysis_sources']
        manifest['scope_groups'] = {'development': sorted(set(dc['groups'])), 'confirmation': sorted(set(cc['groups']))}
    if tracsed_notebook is not None or tensorflow_python is not None:
        if tracsed_notebook is None or tensorflow_python is None:
            raise ValueError('Both pinned author notebook and isolated TensorFlow runtime are required')
        import subprocess
        from .cell_sources import info
        code = 'import sys,json,importlib.metadata as m;print(json.dumps({"python_version":sys.version.split()[0],"packages":{p:m.version(p) for p in ["tensorflow","keras","numpy","pandas","scikit-learn","scipy"]}}))'
        env = dict(__import__('os').environ, CUDA_VISIBLE_DEVICES='')
        identity = json.loads(subprocess.check_output([str(tensorflow_python), '-c', code], env=env, text=True))
        runtime_path = out / 'tensorflow_runtime_identity.json'
        freeze_record(runtime_path, identity)
        manifest['tracsed_notebook'] = dict(info(tracsed_notebook), source='https://github.com/Genentech/TraCSED; pinned author notebook',
            status='original_public', kind='author_source', alignment='source-extracted architecture; early forecast and retrospective tasks distinguished')
        manifest['tensorflow_runtime'] = dict(info(runtime_path), python=str(Path(tensorflow_python).absolute()),
            source='installed isolated TensorFlow runtime, exact version identity checked per invocation',
            status='derived', kind='environment_lock', alignment='author NumPy/Keras/scikit-learn runtime isolated from metric stack')
    freeze_record(out / 'preparation_manifest.json', manifest)
    return manifest
