"""Portable task heads, genuine isolated TraCSED and training-only interval AFT."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler

from vc_demo.harness.research_contract import file_digest, digest
from vc_demo.t47d_full.models import FullView, Network, secondary_labels
from vc_demo.t47d_research.models import NEURAL
from .representations import Representation, HEAVY


class PortableView(FullView):
    def __init__(self, config, directory):
        super().__init__(config)
        self.directory = Path(directory)

    def fit(self, bundle, idx, seed):
        c = self.c
        if c.get('representation', 'pathway') not in HEAVY:
            self.c = dict(c, no_barcode_inputs=False) if c.get('no_barcode_inputs') else c
            super().fit(bundle, idx, seed)
            self.c = c
            if c.get('no_barcode_inputs'):
                self.means = {t: self.source[[i for i in idx if bundle['meta'].iloc[i].treatment == t]].mean(0)
                              for t in bundle['meta'].iloc[idx].treatment.unique()}
                self.pooled_mean = np.mean(list(self.means.values()), axis=0)
                self.source = np.asarray([self.means.get(t, self.pooled_mean) for t in bundle['meta'].treatment])
                self.scaler = StandardScaler().fit(self.source[idx, :self.time_steps].reshape(-1, self.source.shape[-1]))
            return self
        self.time_steps = sum(day <= (0 if c.get('baseline_only') else c.get('input_cutoff_day', 4)) for day in (0, 1, 4))
        self.encoder = Representation(c, self.directory).fit(bundle, idx, seed)
        self.source = self.encoder.transform(bundle, training=True)
        self.means = {t: self.source[[i for i in idx if bundle['meta'].iloc[i].treatment == t]].mean(0)
                      for t in self.encoder.conditions}
        self.pooled_mean = np.mean(list(self.means.values()), axis=0)
        if c.get('no_barcode_inputs'):
            self.source = np.asarray([self.means.get(t, self.pooled_mean) for t in bundle['meta'].treatment])
        fit = self.source[idx, :self.time_steps]
        self.scaler = StandardScaler().fit(fit.reshape(-1, self.source.shape[-1]))
        self.aux_scaler = StandardScaler().fit(bundle['aux'][idx, :6])
        self.artifact = {'method': c['representation'], 'train_only': True, 'portable_query': True}
        return self

    def refresh_query(self, bundle):
        if hasattr(self, 'encoder'):
            self.source = self.encoder.transform(bundle)
            if self.c.get('no_barcode_inputs'):
                self.source = np.asarray([self.means.get(t, self.pooled_mean) for t in bundle['meta'].treatment])
        else:
            # Reuse the already-tested light query transform, never fit a new view.
            from .provider import _query_view
            class Core:
                pass
            core = Core()
            core.view = self
            if self.c.get('no_barcode_inputs'):
                core.query_treatment_means = {t: self.means.get(t, self.pooled_mean) for t in bundle['meta'].treatment.unique()}
            _query_view(core, bundle, skip_portable=True)


def tf_call(action, directory, config, artifacts, **paths):
    notebook = artifacts['tracsed_notebook']
    runtime = artifacts['tensorflow_runtime']
    request = {'directory': str(directory), 'config': config, 'notebook': notebook['path'],
        'notebook_sha256': file_digest(Path(notebook['path'])),
        'runtime_identity': json.loads(Path(runtime['path']).read_text()),
        **{k: str(v) if isinstance(v, (Path, str)) else v for k, v in paths.items()}}
    request_path = Path(directory) / (action + '_' + uuid.uuid4().hex + '.json')
    request_path.write_text(json.dumps(request))
    env = {k: v for k, v in os.environ.items() if k in {'PATH', 'HOME', 'LANG', 'LC_ALL', 'LD_LIBRARY_PATH'}}
    env.update(TF_NUM_INTRAOP_THREADS='2', TF_NUM_INTEROP_THREADS='2', OMP_NUM_THREADS='2', TF_CPP_MIN_LOG_LEVEL='2')
    libraries = Path(runtime['python']).parent.parent.glob('lib/python*/site-packages/nvidia/*/lib')
    env['LD_LIBRARY_PATH'] = ':'.join([*(str(p) for p in libraries), env.get('LD_LIBRARY_PATH', '')])
    env['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
    if config.get('device') == 'cpu':
        env['CUDA_VISIBLE_DEVICES'] = ''
    elif 'CUDA_VISIBLE_DEVICES' in os.environ:
        env['CUDA_VISIBLE_DEVICES'] = os.environ['CUDA_VISIBLE_DEVICES']
    result = subprocess.run([runtime['python'], str(Path(__file__).with_name('tensorflow_worker.py')),
        '--action', action, '--request', str(request_path)], env=env, text=True, capture_output=True)
    (Path(directory) / (request_path.stem + '.log')).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Actual isolated TraCSED execution failed: ' + result.stderr[-2000:])


class HeavyCandidate:
    def __init__(self, config, *, artifacts, directory):
        self.config, self.artifacts, self.directory = copy.deepcopy(config), copy.deepcopy(artifacts), Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def fit(self, bundle, idx, seed):
        c = self.config
        from .cell_sources import fitting_resources
        bundle = fitting_resources(bundle, c)
        self.view = PortableView(c, self.directory / 'representation').fit(bundle, idx, seed)
        s, x, cross = self.view.transform(bundle, idx)
        y = bundle['meta'].iloc[idx].label.to_numpy(dtype=float)
        self.mean, self.std = float(y.mean()), max(float(y.std()), .1)
        target = (y - self.mean) / self.std
        family = c['model']
        self.losses = []
        if family in {'ridge', 'frequency', 'early_elastic', 'pls', 'xgboost'}:
            if family == 'frequency':
                x = x[:, -8:]
            if family in {'ridge', 'frequency'}:
                self.estimator = Ridge(alpha=c.get('alpha', 10)).fit(x, target)
            elif family == 'early_elastic':
                self.estimator = ElasticNet(alpha=c.get('alpha', .01), l1_ratio=c.get('l1_ratio', .5), max_iter=c.get('max_iter', 10000)).fit(x, target)
            elif family == 'pls':
                self.estimator = PLSRegression(n_components=c.get('components', 3), scale=False).fit(x, target)
            else:
                from xgboost import XGBRegressor
                self.estimator = XGBRegressor(n_estimators=c.get('n_estimators', 160), max_depth=c.get('depth', 2),
                    learning_rate=c.get('learning_rate', .035), reg_lambda=c.get('reg_lambda', 10),
                    subsample=.9, colsample_bytree=.8, n_jobs=2, random_state=seed).fit(x, target)
        elif family == 'additive_null':
            mono = bundle['meta'].iloc[idx].treatment.ne('combination').to_numpy()
            self.additive = Ridge(alpha=c.get('alpha', 10)).fit(x[mono], target[mono])
        elif family == 'hazard':
            self._fit_hazard(bundle, idx, x, target, seed)
        elif family == 'tracsed':
            training = self.directory / 'training.npz'
            np.savez(training, s=s, y=target)
            self.tf_config = dict(c, author_seed=c.get('author_seed', seed))
            self.actual_model_seed = self.tf_config['author_seed']
            tf_call('fit', self.directory, self.tf_config, self.artifacts, training=training)
            self.losses = json.loads((self.directory / 'fit_provenance.json').read_text())['losses']
        elif family in NEURAL:
            self._fit_neural(bundle, idx, s, x, cross, target, seed)
        else:
            raise ValueError('Implement a real task head; no generic fallback for ' + family)
        self.checkpoint_files = [str(p) for p in self.directory.rglob('*') if p.is_file() and
            (p.name in {'model.keras', 'fit_provenance.json', 'model.pt', 'adata.h5ad', 'attr.pkl', 'var_names.csv', 'registry.json'} or p.name.startswith('cellrank_'))]
        if hasattr(self.view, 'encoder') and hasattr(self.view.encoder, 'scvi_dir'):
            self.checkpoint_files = sorted(set(self.checkpoint_files) | {str(p) for p in self.view.encoder.scvi_dir.rglob('*') if p.is_file()})
        self.representation_audit = getattr(getattr(self.view, 'encoder', None), 'audit', None)
        return self

    def _fit_hazard(self, bundle, idx, x, target, seed):
        from .interval_aft import IntervalLogNormalAFT
        if 'training_events' not in bundle:
            raise ValueError('Prepare real train-only event outcomes; never read a global endpoint table inside a model')
        c = self.config
        self.hazard_pca = PCA(n_components=c.get('hazard_components', min(5, len(idx)-2)), random_state=seed).fit(x)
        frame = pd.DataFrame(self.hazard_pca.transform(x), columns=['z' + str(i) for i in range(self.hazard_pca.n_components_)])
        events = bundle['training_events']
        groups = set(bundle['meta'].iloc[idx].clone_id)
        conditions = set(bundle['meta'].iloc[idx].treatment)
        if not set(events.clone_id).issubset(groups) or not set(events.treatment).issubset(conditions):
            raise ValueError('AFT received outcomes outside current fitting rows')
        counts = events.set_index(['clone_id', 'treatment', 'time_day']).cell_count.to_dict()
        self.event_days = [d for d in (1, 4, 8, 26) if d <= c.get('hazard_max_fit_day', 26)]
        if not self.event_days:
            raise ValueError('AFT needs a declared nonempty training outcome horizon')
        lower, upper = [], []
        for row in bundle['meta'].iloc[idx].itertuples():
            observed = [counts.get((row.clone_id, row.treatment, day), 0) >= 3 for day in self.event_days]
            first = next((k for k in range(len(observed)) if not any(observed[k:])), None)
            lower.append(float(self.event_days[-1]) if first is None else float(([0] + self.event_days)[first]))
            upper.append(np.inf if first is None else float(self.event_days[first]))
        frame['lower'], frame['upper'] = lower, upper
        self.hazard = IntervalLogNormalAFT(penalizer=c.get('hazard_penalizer', 1.)).fit_interval_censoring(frame, 'lower', 'upper')
        survival = self.hazard.predict_survival_function(frame, times=[26]).to_numpy().ravel()
        self.estimator = Ridge(alpha=c.get('alpha', 10)).fit(np.column_stack([x, survival]), target)
        self.hazard_audit = {'training_groups_sha256': digest(sorted(groups)), 'training_conditions': sorted(conditions),
            'max_outcome_day': max(self.event_days), 'definition': 'persistent sampled-count non-detection, not extinction',
            'interval_rows': len(idx), 'non_detection_intervals': int(np.isfinite(upper).sum()),
            'training_day26_counts_used': 26 in self.event_days,
            'boundary_policy': 'exact H(0)=0, positive-time lifelines log-normal likelihood unchanged'}

    def _fit_neural(self, bundle, idx, s, x, cross, target, seed):
        import torch
        from torch import nn
        c = self.config
        torch.manual_seed(seed)
        np.random.seed(seed)
        torch.set_num_threads(2)
        self.device = torch.device(c.get('device', 'cuda'))
        self.network = Network(s.shape[-1], x.shape[-1], c['model'], c.get('hidden', 32), c).to(self.device)
        self.network.drop.p = c.get('dropout', .15)
        sx, xx, cx = [torch.tensor(v, device=self.device) for v in (s, x, cross)]
        target = torch.tensor(target, dtype=torch.float32, device=self.device)
        labels, active = secondary_labels(bundle, idx)
        if c.get('head') == 'positive_selected':
            active[:, 1] = 0
        if c.get('head') == 'mono_resistant_combo_sensitive':
            active[:, 0] = 0
        classes = torch.tensor(labels, dtype=torch.float32, device=self.device)
        active = torch.tensor(active, dtype=torch.float32, device=self.device)
        positive = (classes * active).sum(0).clamp(min=1)
        weight = (active.sum(0) - positive).clamp(min=1) / positive
        auxiliary = bundle['pathway'][idx].mean(1)
        if c.get('auxiliary_no_artifact'):
            raw = bundle['expression'][idx]
            genes = np.argsort(raw.reshape(-1, raw.shape[-1]).var(0))[-c.get('genes', 128):]
            projection = np.random.default_rng(seed + 19).normal(size=(len(genes), 50)) / np.sqrt(len(genes))
            auxiliary = raw[:, :, genes].mean(1) @ projection
        auxiliary = torch.tensor(auxiliary, dtype=torch.float32, device=self.device)
        auxiliary = (auxiliary - auxiliary.mean(0)) / auxiliary.std(0).clamp(min=.1)
        auxiliary = (auxiliary - auxiliary.mean(0)) / auxiliary.std(0).clamp(min=.1)
        optimizer = {'adamw': torch.optim.AdamW, 'adam': torch.optim.Adam}[c.get('optimizer', 'adamw')](
            self.network.parameters(), lr=c.get('lr', .001), weight_decay=c.get('weight_decay', .02))
        self.network.train()
        for _ in range(c.get('epochs', 80)):
            optimizer.zero_grad()
            prediction, logits, reconstruction = self.network(sx, xx, cx)
            loss = nn.functional.huber_loss(prediction, target)
            kind = c.get('loss', 'huber')
            if kind in {'weighted_bce', 'focal'}:
                term = nn.functional.binary_cross_entropy_with_logits(logits, classes, pos_weight=weight, reduction='none')
                if kind == 'focal':
                    term *= (1 - torch.exp(-term)).pow(c.get('focal_gamma', 2))
                loss += c.get('auxiliary_weight', .2) * (term * active).sum() / active.sum().clamp(min=1)
            if kind == 'pairwise' or c.get('head') == 'ranking':
                delta = target[:, None] - target[None, :]
                mask = delta.abs() > 1e-6
                if mask.any():
                    margin = prediction[:, None] - prediction[None, :]
                    loss += c.get('ranking_weight', .1) * nn.functional.softplus(-margin[mask] * delta[mask].sign()).mean()
            if kind == 'multitask' and not c.get('no_pathway_supervision'):
                loss += c.get('pathway_weight', .1) * nn.functional.mse_loss(reconstruction, auxiliary)
            if not torch.isfinite(loss):
                raise ValueError('Nonfinite genuine task-head loss')
            loss.backward()
            nn.utils.clip_grad_norm_(self.network.parameters(), c.get('gradient_clip', 1))
            optimizer.step()
            self.losses.append(float(loss.detach().cpu()))
        self.network.eval()

    def predict_survival(self, bundle, idx, times):
        self.view.refresh_query(bundle)
        _, x, _ = self.view.transform(bundle, idx)
        frame = pd.DataFrame(self.hazard_pca.transform(x), columns=['z' + str(i) for i in range(self.hazard_pca.n_components_)])
        return self.hazard.predict_survival_function(frame, times=times).to_numpy().T

    def predict(self, bundle, idx):
        self.view.refresh_query(bundle)
        s, x, cross = self.view.transform(bundle, idx)
        family = self.config['model']
        if family == 'tracsed':
            provenance = json.loads((self.directory / 'fit_provenance.json').read_text())
            if provenance['author_notebook_sha256'] != file_digest(Path(self.artifacts['tracsed_notebook']['path'])):
                raise ValueError('Frozen TraCSED source identity changed')
            with tempfile.TemporaryDirectory(prefix='tracsed_query_') as temp:
                temp = Path(temp)
                query, prediction, metadata = temp / 'query.npz', temp / 'prediction.npy', temp / 'metadata.json'
                np.savez(query, s=s)
                tf_call('predict', self.directory, self.tf_config, self.artifacts, query=query, prediction=prediction, prediction_metadata=metadata)
                value = json.loads(metadata.read_text())
                if value['model_refits'] or value['calibration_refits']:
                    raise ValueError('Frozen TraCSED prediction refitted a model')
                p = np.load(prediction)
        elif family == 'hazard':
            survival = self.predict_survival(bundle, idx, [26])[:, 0]
            p = self.estimator.predict(np.column_stack([x, survival]))
        elif hasattr(self, 'network'):
            import torch
            with torch.no_grad():
                p = self.network(*[torch.tensor(v, device=self.device) for v in (s, x, cross)])[0].cpu().numpy()
        elif family == 'additive_null':
            lookup = {(r.clone_id, r.treatment): i for i, r in bundle['meta'].iterrows()}
            p = []
            for i in idx:
                r = bundle['meta'].iloc[i]
                if r.treatment == 'combination':
                    rows = [lookup[(r.clone_id, t)] for t in ('giredestrant', 'palbociclib')]
                    values = self.additive.predict(self.view.transform(bundle, rows)[1])
                    p.append(values.sum() + self.mean / self.std)
                else:
                    p.append(self.additive.predict(self.view.transform(bundle, [i])[1])[0])
            p = np.asarray(p)
        else:
            p = np.asarray(self.estimator.predict(x[:, -8:] if family == 'frequency' else x)).ravel()
        return np.asarray(p) * self.std + self.mean

    def close(self):
        if hasattr(self.view, 'encoder'):
            self.view.encoder.close()
        if hasattr(self, 'network'):
            import torch
            self.network.to('cpu')
            self.device = torch.device('cpu')
