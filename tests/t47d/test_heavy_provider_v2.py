"""Actual-library CPU fixtures; never a formal T47D fit or paper-level score."""
import copy
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import anndata as ad
import joblib
import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from vc_demo.harness.research_contract import file_digest, write_record
from vc_demo.t47d_provider_v2.cell_sources import info, attach_development, attach_query
from vc_demo.t47d_provider_v2.data import save_inputs
from vc_demo.t47d_provider_v2 import provider
from vc_demo.t47d_provider_v2.representations import Representation
from vc_demo.t47d_lineage.data import TREATMENTS


spec = importlib.util.spec_from_file_location('t47d_adapter_engineering_fixtures', Path(__file__).with_name('test_provider_v2.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def raw_fixture(tmp_path):
    p, c, cc, light = base.fixture(tmp_path)
    rng = np.random.default_rng(120)
    cells, rows = [], []
    for group in sorted(set(light['meta'].clone_id)):
        for day in (0, 1, 4):
            for treatment in (['baseline'] if day == 0 else TREATMENTS):
                for k in range(4):
                    rate = 3 + .3 * day + .4 * np.sin(np.arange(64) + k)
                    cells.append(rng.poisson(rate).astype('float32'))
                    rows.append({'clone_id': group, 'treatment': treatment, 'time_day': day,
                                 'library_id': treatment + '_' + str(day)})
    obs = pd.DataFrame(rows, index=[f'fixture_cell_{i}' for i in range(len(rows))])
    raw = ad.AnnData(sparse.csr_matrix(cells), obs=obs, var=pd.DataFrame(index=[f'g{i}' for i in range(64)]))
    expression = np.zeros((len(light['meta']), 3, 64), dtype='float32')
    pseudobulk = np.zeros_like(expression)
    for i, row in light['meta'].iterrows():
        for j, day in enumerate((0, 1, 4)):
            treatment = 'baseline' if day == 0 else row.treatment
            use = (obs.clone_id.eq(row.clone_id) & obs.treatment.eq(treatment) & obs.time_day.eq(day)).to_numpy()
            x = raw.X[use].toarray()
            expression[i, j] = np.log1p(x * 1e4 / np.maximum(x.sum(1, keepdims=True), 1)).mean(0)
            sums = x.sum(0)
            pseudobulk[i, j] = np.log1p(sums * 1e4 / max(sums.sum(), 1))
    light['expression'], light['pseudobulk'] = expression, pseudobulk
    p['development_inputs']['early_observations'] = dict(save_inputs(tmp_path / 'early.npz', light, np.arange(36)), scope='development')
    cc['early_observations'] = save_inputs(tmp_path / 'confirm_early.npz', light, np.arange(36, 42))
    genes = tmp_path / 'gene_order.csv'
    pd.DataFrame({'gene_id': raw.var_names, 'gene_symbol': [f'GENE{i}' for i in range(64)]}).to_csv(genes, index=False)
    p['development_inputs']['gene_order'] = info(genes, 'public')
    cc['gene_order'] = info(genes)
    for name, groups in [('development', set(c['groups'])), ('confirmation', set(cc['groups']))]:
        selected = raw[raw.obs.clone_id.isin(groups)].copy()
        selected.write_h5ad(tmp_path / (name + '_cells.h5ad'))
    p['development_inputs']['early_cells'] = info(tmp_path / 'development_cells.h5ad', 'development')
    cc['early_cells'] = info(tmp_path / 'confirmation_cells.h5ad')
    events = []
    for i, group in enumerate(sorted(set(c['groups']))):
        for j, treatment in enumerate(TREATMENTS):
            cutoff = [1, 4, 8, 99][(i + j) % 4]
            for day in (1, 4, 8, 26):
                events.append({'clone_id': group, 'treatment': treatment, 'time_day': day,
                               'cell_count': 0 if day >= cutoff else 8 + j})
    path = tmp_path / 'events.csv'
    pd.DataFrame(events).to_csv(path, index=False)
    p['development_inputs']['training_events'] = info(path, 'development')
    b, _ = provider.read_inputs(p['development_inputs']['early_observations'])
    b = attach_development(b, p['development_inputs'])
    q, _ = provider.read_inputs(cc['early_observations'])
    q = attach_query(q, cc)
    return p, c, cc, b, q


def representation_config(kind):
    return {'model': 'ridge', 'representation': kind, 'alpha': 10.,
        'representation_parameters': {'hvg': 32, 'pca_components': 4, 'graph_neighbors': 8,
            'n_neighbors': 3, 'diffmap_components': 4, 'dpt_components': 3,
            'transport_backend': 'numpy', 'ot_iterations': 3000, 'ot_regularization': .5,
            'scvi': {'n_hidden': 16, 'n_latent': 4, 'n_layers': 2},
            'scvi_train': {'max_epochs': 1, 'batch_size': 64, 'train_size': 1.,
                'accelerator': 'cpu', 'early_stopping': False, 'limit_val_batches': 0, 'num_sanity_val_steps': 0}}}


@pytest.mark.parametrize('kind,width', [('scvi', 4), ('pseudotime', 2), ('cellrank', 4), ('distance', 4)])
def test_actual_portable_representation_fit_save_load_query_without_refitting(tmp_path, monkeypatch, kind, width):
    p, c, cc, b, q = raw_fixture(tmp_path)
    train = np.arange(24)
    rep = Representation(representation_config(kind), tmp_path / 'fitted').fit(b, train, 3)
    assert set(rep.audit['train_groups']) == set(b['meta'].iloc[train].clone_id)
    assert set(rep.audit['train_groups']).isdisjoint(q['meta'].clone_id)
    assert rep.audit['fit_max_time_day'] == 4 and rep.audit['supervised_labels_used'] is False
    first = rep.transform(q)
    assert first.shape == (6, 3, width) and np.isfinite(first).all()
    path = tmp_path / 'representation.joblib'
    rep.close()
    joblib.dump(rep, path)
    del rep
    loaded = joblib.load(path)
    def forbidden(*args, **kwargs):
        raise AssertionError('Frozen query attempted training')
    from sklearn.decomposition import PCA
    from sklearn.neighbors import KNeighborsRegressor
    import scanpy as sc
    monkeypatch.setattr(PCA, 'fit', forbidden)
    monkeypatch.setattr(KNeighborsRegressor, 'fit', forbidden)
    monkeypatch.setattr(sc.pp, 'highly_variable_genes', forbidden)
    if kind == 'scvi':
        import scvi
        monkeypatch.setattr(scvi.model.SCVI, 'train', forbidden)
    if kind == 'cellrank':
        import cellrank as cr
        monkeypatch.setattr(cr.kernels.RealTimeKernel, 'compute_transition_matrix', forbidden)
    second = loaded.transform(q)
    np.testing.assert_allclose(first, second, rtol=1e-5, atol=1e-5)
    if kind == 'cellrank':
        assert all(np.allclose(np.asarray(t.sum(1)).ravel(), 1.) for t in loaded.transitions.values())


def test_representation_never_fits_validation_cells_and_rejects_changed_vocab(tmp_path):
    p, c, cc, b, q = raw_fixture(tmp_path)
    cfg = representation_config('pseudotime')
    idx = np.arange(24)
    a = Representation(cfg, tmp_path / 'a').fit(b, idx, 3)
    cells = ad.read_h5ad(b['cell_source']['path'])
    outside = (~cells.obs.clone_id.isin(b['meta'].iloc[idx].clone_id)).to_numpy()
    cells.X[outside] = cells.X[outside] * 1000
    path = tmp_path / 'validation_poisoned.h5ad'
    cells.write_h5ad(path)
    changed = dict(b, cell_source=info(path))
    z = Representation(cfg, tmp_path / 'z').fit(changed, idx, 3)
    assert a.genes == z.genes
    np.testing.assert_array_equal(a.pca.components_, z.pca.components_)
    query = ad.read_h5ad(q['cell_source']['path'])[:, ::-1].copy()
    path = tmp_path / 'wrong_vocabulary.h5ad'
    query.write_h5ad(path)
    with pytest.raises(ValueError, match='vocabulary'):
        a.transform(dict(q, cell_source=info(path)))


def test_scvi_unknown_query_batch_has_explicit_nonadaptive_reference_policy(tmp_path):
    p, c, cc, b, q = raw_fixture(tmp_path)
    cfg = representation_config('scvi')
    cfg['representation_parameters']['unknown_batch'] = 'reference_baseline'
    rep = Representation(cfg, tmp_path / 'fitted').fit(b, np.arange(24), 3)
    query = ad.read_h5ad(q['cell_source']['path'])
    query.obs['library_id'] = 'new_fixture_batch'
    path = tmp_path / 'unknown_batch.h5ad'
    query.write_h5ad(path)
    changed = dict(q, cell_source=info(path))
    assert np.isfinite(rep.transform(changed)).all()
    assert rep.audit['query_optimization_steps'] == 0
    rep.p['unknown_batch'] = 'error'
    with pytest.raises(ValueError, match='Unseen scVI'):
        rep.transform(changed)


def test_hazard_uses_actual_train_only_intervals_and_frozen_survival(tmp_path, monkeypatch):
    p, c, cc, b, q = raw_fixture(tmp_path)
    cfg = {'model': 'hazard', 'representation': 'pca', 'hazard_components': 2,
           'hazard_max_fit_day': 8, 'hazard_penalizer': 2.}
    train = np.arange(24)
    safe = provider._safe_bundle(b, train, np.asarray(c['targets'])[train])
    assert set(safe['training_events'].clone_id) == set(b['meta'].iloc[train].clone_id)
    model = provider.PortableNative(cfg, output_root=tmp_path / 'node').fit(safe, train, 3)
    assert model.hazard_audit['max_outcome_day'] == 8
    assert model.hazard_audit['training_day26_counts_used'] is False
    assert model.hazard_audit['non_detection_intervals'] > 0
    from lifelines import LogNormalAFTFitter
    from sklearn.linear_model import Ridge
    def forbidden(*args, **kwargs):
        raise AssertionError('Frozen AFT query refitted')
    monkeypatch.setattr(LogNormalAFTFitter, 'fit_interval_censoring', forbidden)
    monkeypatch.setattr(Ridge, 'fit', forbidden)
    a = model.predict(q, np.arange(6))
    query = dict(q, training_events=pd.DataFrame({'nonsense': [999999]}))
    np.testing.assert_array_equal(a, model.predict(query, np.arange(6)))
    survival = model.model.predict_survival(q, np.arange(6), [26, 180])
    assert survival.shape == (6, 2) and ((survival >= 0) & (survival <= 1)).all()


def tf_artifacts(tmp_path):
    notebook = Path(os.environ.get('T47D_TRACSED_NOTEBOOK', '/workspace/_external/TraCSED/model_scripts/TraCSED_final_model.ipynb'))
    python = Path(os.environ.get('T47D_TENSORFLOW_PYTHON', '/workspace/t47d_tf_venv/bin/python'))
    if not notebook.is_file() or not python.is_file():
        pytest.skip('Real pinned author source/isolated TensorFlow runtime absent; this is not a capability pass')
    code = 'import json,sys,importlib.metadata as m;print(json.dumps({"python_version":sys.version.split()[0],"packages":{p:m.version(p) for p in ["tensorflow","keras","numpy","pandas","scikit-learn","scipy"]}}))'
    identity = json.loads(subprocess.check_output([str(python), '-c', code], text=True))
    path = tmp_path / 'tf_runtime.json'
    write_record(path, identity)
    return {'tracsed_notebook': dict(info(notebook), source='https://github.com/Genentech/TraCSED',
                status='original_public', kind='author_source', alignment='pinned source-extracted architecture'),
            'tensorflow_runtime': dict(info(path), python=str(python), source='installed exact isolated environment',
                status='derived', kind='environment_lock', alignment='version-checked per worker invocation')}


@pytest.mark.parametrize('seed_override', [None, 101])
def test_full_author_tracsed_architecture_cpu_fit_save_reload_prediction_only(tmp_path, seed_override):
    p, c, cc, b, q = raw_fixture(tmp_path)
    artifacts = tf_artifacts(tmp_path)
    cfg = {'model': 'tracsed', 'representation': 'pathway', 'device': 'cpu', 'epochs': 1,
           'batch_size': 32, 'head_size': 5, 'num_heads': 40, 'attention_blocks': 10, 'transformer_blocks': 10, 'author_seed': 42}
    train = np.arange(24)
    safe = provider._safe_bundle(b, train, np.asarray(c['targets'])[train])
    model = provider.PortableNative(cfg, artifact_files=artifacts, output_root=tmp_path / 'node',
                                    training_seed_override=seed_override).fit(safe, train, 3)
    provenance_path = next(Path(x) for x in model.checkpoint_files if x.endswith('fit_provenance.json'))
    provenance = json.loads(provenance_path.read_text())
    assert provenance['author_notebook_sha256'] == file_digest(Path(artifacts['tracsed_notebook']['path']))
    assert provenance['actual_parameters'] > 10000 and len(provenance['losses']) == 1
    assert provenance['effective_config']['num_heads'] == 40
    expected = 42 if seed_override is None else seed_override
    assert provenance['effective_config']['author_seed'] == expected and model.actual_model_seed == expected
    path = tmp_path / 'frozen_tracsed.joblib'
    joblib.dump(model, path)
    fitted = {f: file_digest(Path(f)) for f in model.checkpoint_files}
    result = joblib.load(path).predict(q, np.arange(6))
    assert result.shape == (6,) and np.isfinite(result).all()
    assert fitted == {f: file_digest(Path(f)) for f in model.checkpoint_files}
