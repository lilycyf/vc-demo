"""Separate early cell inputs, training-only event outcomes and postselection sources."""
from pathlib import Path
import json

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from vc_demo.harness.research_contract import file_digest


OBS = ['clone_id', 'treatment', 'time_day', 'library_id']


def info(path, scope=None):
    path = Path(path).resolve()
    value = {'path': str(path), 'sha256': file_digest(path)}
    if scope:
        value['scope'] = scope
    return value


def verified_file(value):
    path = Path(value['path'])
    if file_digest(path) != value['sha256']:
        raise ValueError('Registered input changed: ' + path.name)
    return path


def export(prepared, out, development_groups, confirmation_groups):
    prepared, out = Path(prepared), Path(out)
    raw = ad.read_h5ad(prepared / 'qc_counts.h5ad')
    if not raw.var_names.is_unique or not raw.obs_names.is_unique:
        raise ValueError('Source cell and gene IDs must be unique; do not invent vocabulary suffixes')
    genes = pd.read_csv(prepared / 'gene_order.csv')
    if raw.var_names.tolist() != genes.gene_id.astype(str).tolist():
        raise ValueError('Raw-cell gene vocabulary/order differs from clone-level inputs')
    result = {}
    for phase, groups in [('development', development_groups), ('confirmation', confirmation_groups)]:
        use = raw.obs.clone_id.isin(groups) & raw.obs.time_day.isin([0, 1, 4])
        obs = raw.obs.loc[use, OBS].copy()
        obs.index = pd.Index(obs.index.to_numpy(dtype=object), dtype=object, name='cell_id')
        for key in ('clone_id', 'treatment', 'library_id'):
            obs[key] = obs[key].astype(str).astype(object)
        # Export identity only, not nullable source annotations or old fitted metadata.
        var = pd.DataFrame(index=pd.Index(raw.var_names.to_numpy(dtype=object), dtype=object, name='gene_id'))
        cells = ad.AnnData(X=raw.X[use.to_numpy()].copy(), obs=obs, var=var)
        # No precomputed graph/latent state or late metadata is transferred.
        path = out / (phase + '_cells.h5ad')
        cells.write_h5ad(path, compression='gzip')
        result[phase] = info(path, 'development' if phase == 'development' else None)
        result[phase + '_cells'] = cells.n_obs
    counts = pd.read_csv(prepared / 'clone_condition_counts.csv')
    selected = counts.loc[counts.clone_id.isin(development_groups) & counts.time_day.isin([1, 4, 8, 26]),
                          ['clone_id', 'treatment', 'time_day', 'cell_count']]
    path = out / 'development_training_events.csv'
    selected.to_csv(path, index=False)
    result['training_events'] = info(path, 'development')
    result['gene_order'] = info(prepared / 'gene_order.csv', 'public')
    metadata = {'counts': counts.loc[counts.clone_id.isin(development_groups) & counts.time_day.isin([0, 1, 4, 8, 26]),
        ['clone_id', 'treatment', 'time_day', 'cell_count']].to_dict('records'),
        'population_totals': counts.loc[counts.time_day.isin([0, 1, 4, 8, 26])].groupby(
            ['treatment', 'time_day'], as_index=False).cell_count.sum().to_dict('records')}
    path = out / 'development_label_metadata.json'
    path.write_text(json.dumps(metadata))
    result['development_label_metadata'] = info(path)
    return result


def read_cells(value, *, groups, cutoff=4, treatments=None):
    cells = ad.read_h5ad(verified_file(value))
    if set(cells.obs) != set(OBS) or cells.obsm or cells.obsp:
        raise ValueError('Cell source must contain only raw early counts and allowed metadata')
    if not cells.obs_names.is_unique or not cells.var_names.is_unique:
        raise ValueError('Cell/gene identity changed')
    if not set(cells.obs.time_day).issubset({0, 1, 4}):
        raise ValueError('Late observations are forbidden in representation inputs')
    from vc_demo.t47d_lineage.data import TREATMENTS
    if not set(cells.obs.treatment).issubset({'baseline', *TREATMENTS}):
        raise ValueError('Unknown treatment vocabulary in early cells')
    if not cells.obs.loc[cells.obs.time_day.eq(0), 'treatment'].eq('baseline').all():
        raise ValueError('Day0 cell provenance is not baseline')
    use = cells.obs.clone_id.isin(groups) & cells.obs.time_day.le(cutoff)
    if treatments is not None:
        use &= cells.obs.treatment.isin(treatments) | cells.obs.time_day.eq(0)
    cells = cells[use].copy()
    values = cells.X.data if sparse.issparse(cells.X) else cells.X
    if not cells.n_obs or not np.isfinite(values).all() or (values < 0).any() or not np.allclose(values, np.round(values)):
        raise ValueError('Real nonnegative integer cell counts are required')
    return cells


def attach_development(bundle, inputs):
    result = dict(bundle)
    if 'early_cells' in inputs:
        result['cell_source'] = inputs['early_cells']
    if 'training_events' in inputs:
        table = pd.read_csv(verified_file(inputs['training_events']))
        if set(table) != {'clone_id', 'treatment', 'time_day', 'cell_count'} or not set(table.time_day).issubset({1, 4, 8, 26}):
            raise ValueError('Invalid training-only event outcome schema')
        if not set(table.clone_id).issubset(set(bundle['meta'].clone_id)):
            raise ValueError('Confirmation outcomes must not enter development requests')
        result['training_events'] = table
    if 'gene_order' in inputs:
        result['gene_order_info'] = inputs['gene_order']
    return result


def attach_query(bundle, contract):
    result = dict(bundle)
    if 'early_cells' in contract:
        result['cell_source'] = contract['early_cells']
    if 'gene_order' in contract:
        result['gene_order_info'] = contract['gene_order']
    return result


def fitting_resources(bundle, config):
    result = dict(bundle)
    if 'training_events' in result:
        policy = config.get('training_event_policy')
        if config.get('model') == 'hazard':
            cutoff = config.get('hazard_max_fit_day', 26)
        elif policy and policy.get('purpose') and type(policy.get('max_day')) is int:
            cutoff = policy['max_day']
        else:
            result.pop('training_events')
            return result
        if cutoff not in {1, 4, 8, 26}:
            raise ValueError('Training auxiliary outcome horizon is outside this registered task')
        result['training_events'] = result['training_events'].loc[result['training_events'].time_day.le(cutoff)].copy()
    return result
