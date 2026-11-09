"""Portable train-only scVI, diffusion pseudotime, CellRank and transport representations."""
from __future__ import annotations

import copy
from pathlib import Path
import uuid

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsRegressor, NearestNeighbors

from vc_demo.harness.research_contract import digest, file_digest
from vc_demo.t47d_lineage.data import TREATMENTS
from .cell_sources import read_cells, verified_file


HEAVY = {'scvi', 'pseudotime', 'distance', 'cellrank'}
DEFAULTS = {'hvg': 2000, 'min_gene_cells': 3, 'pca_components': 20, 'n_neighbors': 15,
    'diffmap_components': 15, 'dpt_components': 10, 'graph_neighbors': 30,
    'scvi': {'n_hidden': 128, 'n_latent': 16, 'n_layers': 2, 'gene_likelihood': 'nb', 'dropout_rate': .1},
    'scvi_train': {'max_epochs': 50, 'batch_size': 256, 'train_size': .9,
        'accelerator': 'gpu', 'devices': 1, 'early_stopping': True, 'early_stopping_patience': 10},
    'unknown_batch': 'error', 'ot_regularization': .1, 'ot_iterations': 1000,
    'ot_tolerance': 1e-6, 'transport_backend': 'torch_cuda', 'connectivity_weight': .05,
    'distance_epsilon_factor': .05, 'mmd_gamma': .05, 'sliced_projections': 128}


def parameters(config):
    result = copy.deepcopy(DEFAULTS)
    for key, value in config.get('representation_parameters', {}).items():
        if key not in result:
            raise ValueError('Unknown representation parameter; implement/version its actual algorithm: ' + key)
        if isinstance(value, dict):
            result[key].update(value)
        else:
            result[key] = value
    return result


def aggregate(bundle, obs, values, treatment=None):
    out = np.zeros((len(bundle['meta']), 3, values.shape[1]), dtype=np.float32)
    lookup = obs.groupby(['clone_id', 'treatment', 'time_day'], observed=True).indices
    for i, row in bundle['meta'].iterrows():
        if treatment is not None and row.treatment != treatment:
            continue
        for j, day in enumerate((0, 1, 4)):
            loc = lookup.get((row.clone_id, 'baseline' if day == 0 else row.treatment, day))
            if loc is not None:
                out[i, j] = values[loc].mean(0)
    return out


def normalized(cells):
    x = sparse.csr_matrix(cells.X, dtype=np.float32)
    x = sparse.diags(1e4 / np.maximum(np.asarray(x.sum(1)).ravel(), 1)).dot(x).tocsr()
    x.data = np.log1p(x.data)
    return x.toarray()


class Representation:
    def __init__(self, config, directory):
        self.config, self.directory = copy.deepcopy(config), Path(directory)
        self.p = parameters(config)
        self.kind = config['representation']
        self.cutoff = 0 if config.get('baseline_only') else config.get('input_cutoff_day', 4)
        self._scvi = None

    def fit(self, bundle, idx, seed):
        import scanpy as sc
        self.seed = int(seed)
        self.directory.mkdir(parents=True, exist_ok=True)
        groups = sorted(set(bundle['meta'].iloc[idx].clone_id))
        self.conditions = sorted(set(bundle['meta'].iloc[idx].treatment))
        cells = read_cells(bundle['cell_source'], groups=groups, cutoff=self.cutoff, treatments=self.conditions)
        if bundle.get('gene_order_info'):
            order = pd.read_csv(verified_file(bundle['gene_order_info'])).gene_id.astype(str).tolist()
            if cells.var_names.tolist() != order:
                raise ValueError('Cell source and clone-level gene vocabulary/order differ')
        self.gene_vocabulary = cells.var_names.tolist()
        expressed = np.asarray((cells.X > 0).sum(0)).ravel() >= self.p['min_gene_cells']
        training = cells[:, expressed].copy()
        sc.pp.highly_variable_genes(training, flavor='seurat_v3', n_top_genes=min(self.p['hvg'], training.n_vars), span=.5)
        self.genes = training.var_names[training.var.highly_variable].tolist()
        if not self.genes:
            raise ValueError('No training-only HVGs')
        training = cells[:, self.genes].copy()
        self.audit = {'algorithm': self.kind, 'parameters': self.p, 'source_sha256': bundle['cell_source']['sha256'],
            'fit_seed': self.seed,
            'train_groups': groups, 'training_conditions': self.conditions, 'fit_cells': training.n_obs,
            'fit_cell_ids_sha256': digest(training.obs_names.tolist()), 'gene_order_sha256': digest(self.genes),
            'fit_max_time_day': int(training.obs.time_day.max()), 'supervised_labels_used': False,
            'query_optimization_steps': 0, 'source_vocabulary_sha256': digest(self.gene_vocabulary)}
        if self.kind == 'scvi':
            import scvi
            training.obs['library_id'] = training.obs.library_id.astype('category').cat.remove_unused_categories()
            self.batches = training.obs.library_id.cat.categories.tolist()
            self.reference_batch = str(training.obs.loc[training.obs.time_day.eq(0), 'library_id'].mode().iloc[0])
            scvi.settings.seed = self.seed
            scvi.model.SCVI.setup_anndata(training, batch_key='library_id')
            model = scvi.model.SCVI(training, **self.p['scvi'])
            model.train(**self.p['scvi_train'], enable_progress_bar=False, enable_model_summary=False,
                logger=False, enable_checkpointing=False, check_val_every_n_epoch=1)
            self.audit['epochs'] = int(model.trainer.current_epoch)
            self.audit['parameters_count'] = sum(x.numel() for x in model.module.parameters())
            self.scvi_dir = self.directory / 'scvi_model'
            model.save(self.scvi_dir, save_anndata=True, overwrite=True)
            model.to_device('cpu')
            self._scvi = model
        else:
            dense = normalized(training)
            self.pca = PCA(n_components=self.p['pca_components'], svd_solver='randomized', random_state=self.seed).fit(dense)
            z = self.pca.transform(dense).astype(np.float32)
            self.scale = np.maximum(z.std(0), .01)
            z /= self.scale
            obs = training.obs.copy()
            if self.kind == 'pseudotime':
                graph = ad.AnnData(z)
                graph.obsm['X_pca'] = z
                sc.pp.neighbors(graph, n_neighbors=self.p['graph_neighbors'], use_rep='X_pca', random_state=self.seed)
                sc.tl.diffmap(graph, n_comps=self.p['diffmap_components'], random_state=self.seed)
                base = np.flatnonzero(obs.time_day.eq(0))
                graph.uns['iroot'] = int(base[np.argmin(((z[base] - z[base].mean(0)) ** 2).sum(1))])
                sc.tl.dpt(graph, n_dcs=self.p['dpt_components'])
                pt = graph.obs.dpt_pseudotime.to_numpy()
                finite = np.isfinite(pt)
                if finite.sum() < self.p['n_neighbors']:
                    raise ValueError('Insufficient finite training DPT values; no sentinel projection')
                self.mapper = KNeighborsRegressor(n_neighbors=self.p['n_neighbors'], weights='distance').fit(z[finite], pt[finite])
                self.distance_model = NearestNeighbors(n_neighbors=1).fit(z[finite])
                self.audit['disconnected_training_cells'] = int((~finite).sum())
            elif self.kind == 'distance':
                self.reference = z[obs.time_day.eq(0)]
                if len(self.reference) < 2:
                    raise ValueError('Transport reference needs real training baseline cells')
            elif self.kind == 'cellrank':
                self._fit_cellrank(z, obs, sc)
            else:
                raise ValueError('Unknown actual heavy representation')
        self.saved_files = {str(p): file_digest(p) for p in self.directory.rglob('*') if p.is_file()}
        return self

    def _fit_cellrank(self, z, obs, sc):
        import cellrank as cr
        import ot
        self.projections = {}
        self.transitions = {}
        self.audit['kernel_training_conditions'] = {}
        self.audit['kernel_cell_order_sha256'] = {}
        self.audit['coupling_errors'] = {}
        days = [d for d in (0, 1, 4) if d <= self.cutoff]
        stationary = bool(self.config.get('no_temporal_order') or self.config.get('last_snapshot_only') or len(days) == 1)
        self.audit['stationary_kernel'] = stationary
        for treatment in TREATMENTS:
            fit_conditions = [treatment] if treatment in self.conditions else self.conditions
            self.audit['kernel_training_conditions'][treatment] = fit_conditions
            use = obs.treatment.isin(fit_conditions) | obs.time_day.eq(0)
            o, x = obs.loc[use].copy(), z[use]
            coupling = {}
            for src, tgt in ([] if stationary else zip(days[:-1], days[1:])):
                a, b = np.flatnonzero(o.time_day.eq(src)), np.flatnonzero(o.time_day.eq(tgt))
                if not len(a) or not len(b):
                    raise ValueError('Missing training time point for real temporal coupling')
                cost = cdist(x[a], x[b], metric='sqeuclidean')
                cost /= max(float(np.median(cost)), 1e-6)
                if self.p['transport_backend'] == 'numpy':
                    transport, log = ot.sinkhorn(np.full(len(a), 1 / len(a)), np.full(len(b), 1 / len(b)), cost,
                        reg=self.p['ot_regularization'], numItermax=self.p['ot_iterations'], stopThr=self.p['ot_tolerance'], method='sinkhorn_stabilized', log=True)
                elif self.p['transport_backend'] == 'torch_cuda':
                    import torch
                    if not torch.cuda.is_available():
                        raise ValueError('Registered Torch CUDA transport backend unavailable; no silent CPU substitution')
                    transport, log = ot.sinkhorn(torch.full((len(a),), 1 / len(a), dtype=torch.float64, device='cuda'),
                        torch.full((len(b),), 1 / len(b), dtype=torch.float64, device='cuda'), torch.as_tensor(cost, device='cuda'),
                        reg=self.p['ot_regularization'], numItermax=self.p['ot_iterations'], stopThr=self.p['ot_tolerance'], method='sinkhorn_stabilized', log=True)
                    transport = transport.detach().cpu().numpy()
                else:
                    raise ValueError('Unknown declared transport backend')
                errors = log.get('err', [])
                error = float(errors[-1]) if errors else float('inf')
                self.audit['coupling_errors'][treatment + '_' + str(src) + '_' + str(tgt)] = error
                if not np.isfinite(error) or error > self.p['ot_tolerance']:
                    raise ValueError('Real Sinkhorn coupling did not meet the declared convergence tolerance')
                if not np.isfinite(transport).all() or not np.allclose(transport.sum(1), 1 / len(a), atol=1e-4) or not np.allclose(transport.sum(0), 1 / len(b), atol=1e-4):
                    raise ValueError('OT coupling is invalid or unconverged')
                coupling[(src, tgt)] = transport.astype(np.float32)
            graph = ad.AnnData(x, obs=o)
            graph.obs['time_category'] = pd.Categorical(o.time_day, categories=days, ordered=True)
            graph.obsm['X_pca'] = x
            if stationary:
                sc.pp.neighbors(graph, n_neighbors=self.p['n_neighbors'], use_rep='X_pca', random_state=self.seed)
                kernel = cr.kernels.ConnectivityKernel(graph).compute_transition_matrix()
            else:
                kernel = cr.kernels.RealTimeKernel(graph, time_key='time_category', couplings=coupling)
                kernel.compute_transition_matrix(threshold='auto', self_transitions='all', conn_weight=self.p['connectivity_weight'],
                    conn_kwargs={'n_neighbors': self.p['n_neighbors'], 'use_rep': 'X_pca'})
            matrix = sparse.csr_matrix(kernel.transition_matrix)
            source_order = pd.Index(kernel.adata.obs_names)
            order = source_order.get_indexer(o.index)
            if (order < 0).any() or len(source_order) != len(o) or not source_order.is_unique:
                raise ValueError('CellRank kernel cell identity differs from the training cells')
            matrix = matrix[order][:, order]
            self.audit['kernel_cell_order_sha256'][treatment] = digest(o.index.tolist())
            if not np.allclose(np.asarray(matrix.sum(1)).ravel(), 1., atol=1e-4):
                raise ValueError('CellRank transition matrix is not row-stochastic')
            self.transitions[treatment] = matrix
            sparse.save_npz(self.directory / ('cellrank_' + treatment + '.npz'), matrix)
            shift = matrix @ x - x
            entropy = matrix.copy()
            entropy.data = -entropy.data * np.log(np.maximum(entropy.data, 1e-30))
            dt = np.zeros(len(o)) if stationary else matrix @ o.time_day.to_numpy(dtype=float) - o.time_day.to_numpy(dtype=float)
            descriptor = np.column_stack([shift[:, :2], dt, np.asarray(entropy.sum(1)).ravel()])
            for day in ([None] if stationary else days):
                ids = np.arange(len(o)) if day is None else np.flatnonzero(o.time_day.eq(day))
                mapper = KNeighborsRegressor(n_neighbors=min(self.p['n_neighbors'], len(ids)), weights='distance').fit(x[ids], descriptor[ids])
                self.projections[(treatment, day)] = mapper

    def _latent(self, query):
        if query.var_names.tolist() != self.gene_vocabulary:
            raise ValueError('Query source gene vocabulary/order changed')
        query = query[:, self.genes].copy()
        if self.kind != 'scvi':
            return self.pca.transform(normalized(query)).astype(np.float32) / self.scale
        import scvi
        if self._scvi is None:
            self._scvi = scvi.model.SCVI.load(self.scvi_dir, accelerator='cpu', device='auto')
        query.obs['library_id'] = query.obs.library_id.astype(str)
        unknown = ~query.obs.library_id.isin(self.batches)
        if unknown.any():
            if self.p['unknown_batch'] != 'reference_baseline':
                raise ValueError('Unseen scVI query batch; register an explicit fixed reference mapping')
            query.obs.loc[unknown, 'library_id'] = self.reference_batch
        query.obs['library_id'] = pd.Categorical(query.obs.library_id, categories=self.batches)
        self._scvi.module.eval()
        latent = self._scvi.get_latent_representation(adata=query, give_mean=True)
        if latent.shape[0] != query.n_obs or not np.isfinite(latent).all():
            raise ValueError('Frozen scVI query row/finite-output contract failed')
        return latent

    def transform(self, bundle, *, training=False):
        for path, expected in self.saved_files.items():
            if file_digest(Path(path)) != expected:
                raise ValueError('Fitted representation artifact changed')
        conditions = self.conditions if training else None
        groups = self.audit['train_groups'] if training else set(bundle['meta'].clone_id)
        query = read_cells(bundle['cell_source'], groups=groups, cutoff=self.cutoff, treatments=conditions)
        z = self._latent(query)
        if self.kind == 'scvi':
            return aggregate(bundle, query.obs, z)
        if self.kind == 'pseudotime':
            values = np.column_stack([self.mapper.predict(z), self.distance_model.kneighbors(z)[0][:, 0]])
            return aggregate(bundle, query.obs, values)
        if self.kind == 'cellrank':
            result = np.zeros((len(bundle['meta']), 3, 4), dtype=np.float32)
            for treatment in TREATMENTS:
                values = np.zeros((len(query), 4))
                for day in ([None] if self.audit['stationary_kernel'] else [d for d in (0, 1, 4) if d <= self.cutoff]):
                    mask = (query.obs.treatment.eq(treatment) | query.obs.time_day.eq(0)).to_numpy()
                    if day is not None:
                        mask &= query.obs.time_day.eq(day).to_numpy()
                    if mask.any():
                        values[mask] = self.projections[(treatment, day)].predict(z[mask])
                result += aggregate(bundle, query.obs, values, treatment)
            return result
        return self._distances(bundle, query, z)

    def _distances(self, bundle, query, z):
        import pertpy as pt
        import ot
        import jax.numpy as jnp
        from ott.geometry.pointcloud import PointCloud
        from ott.problems.linear.linear_problem import LinearProblem
        from pertpy.tools._distances._distances import _sqeuclidean_std, _padded_uniform_weights
        from vc_demo.t47d_full.features import _wasserstein_solver
        energy, mmd = pt.tl.Distance('edistance').metric_fct, pt.tl.Distance('mmd').metric_fct
        reference = self.reference
        result = np.zeros((len(query), 4))
        for ids in query.obs.groupby(['clone_id', 'treatment', 'time_day'], observed=True).indices.values():
            x = z[ids]
            eps = self.p['distance_epsilon_factor'] * _sqeuclidean_std(x, reference)
            wa, wb = _padded_uniform_weights(len(x)), _padded_uniform_weights(len(reference))
            geometry = PointCloud(jnp.asarray(np.pad(x, ((0, len(wa)-len(x)), (0, 0)))),
                jnp.asarray(np.pad(reference, ((0, len(wb)-len(reference)), (0, 0)))), epsilon=eps)
            solved = _wasserstein_solver()(LinearProblem(geometry, a=jnp.asarray(wa), b=jnp.asarray(wb)))
            cost = float(solved.reg_ot_cost)
            if not np.isfinite(cost) or not bool(solved.converged):
                raise ValueError('Real pertpy/OTT transport did not converge; no sentinel/fallback')
            values = [energy(x, reference), mmd(x, reference, kernel='rbf', gamma=self.p['mmd_gamma']), cost,
                ot.sliced_wasserstein_distance(x, reference, n_projections=self.p['sliced_projections'], seed=self.seed)]
            result[ids] = values
        if not np.isfinite(result).all():
            raise ValueError('Nonfinite true distance representation')
        return aggregate(bundle, query.obs, result)

    def close(self):
        if self._scvi is not None:
            self._scvi.to_device('cpu')
        self._scvi = None

    def __getstate__(self):
        state = dict(self.__dict__)
        state['_scvi'] = None
        return state
