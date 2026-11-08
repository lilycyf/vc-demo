"""T47D research adapter: standalone models or explicit grouped OOF composition."""
from __future__ import annotations

import copy
from functools import partial
import numpy as np
import torch
from torch import nn
from sklearn.linear_model import Ridge

from vc_demo.harness.composition import CrossFittedResidualRegressor, CrossFittedStackingRegressor
from vc_demo.t47d_full.models import FullCandidate, FullView, Network, secondary_labels
from vc_demo.t47d_lineage.composition import build_candidate as build_historical
from vc_demo.t47d_lineage.models import View as HistoricalView

NEURAL = {'gru', 'temporal_transformer', 'gated_pathway', 'cross_attention', 'bilinear', 'moe'}


class HistoricalControlView(HistoricalView):
    """Apply registered controls without changing the unmodified historical root."""
    def controlled(self, bundle):
        b = dict(bundle)
        b['expression'] = bundle['expression'].copy()
        b['pathway'] = bundle.get('ablation_pathway', bundle['pathway']).copy()
        b['aux'] = bundle['aux'].copy()
        c = self.controls
        if c.get('no_barcode_inputs'):
            for treatment, means in self.training_means.items():
                rows = bundle['meta'].treatment.eq(treatment).to_numpy()
                for name in ('expression','pathway'):
                    b[name][rows] = means[name]
            b['aux'][:,:6] = 0
        steps = 1 if self.config.get('baseline_only') else sum(d<=c.get('input_cutoff_day',4) for d in (0,1,4))
        for name in ('expression','pathway'):
            values = b[name]
            if steps<3:
                values[:,steps:] = values[:,steps-1:steps]
            if c.get('no_temporal_order'):
                values[:] = values[:,:steps].mean(1,keepdims=True)
            if c.get('last_snapshot_only'):
                values[:] = values[:,2:3]
        for j in range(steps,3):
            b['aux'][:,[j,j+3]] = 0
        if c.get('last_snapshot_only'):
            b['aux'][:,[0,1,3,4]] = 0
        if c.get('no_temporal_order'):
            for start in (0,3):
                b['aux'][:,start:start+steps] = b['aux'][:,start:start+steps].mean(1,keepdims=True)
        if self.projection is not None:
            b['expression'] = b['expression'][:,:,self.projection_genes]@self.projection
        return b

    def fit(self, bundle, idx):
        self.training_means = {}
        for treatment in bundle['meta'].treatment.unique():
            rows = [i for i in idx if bundle['meta'].iloc[i].treatment==treatment]
            self.training_means[treatment] = {name:bundle.get('ablation_pathway',bundle[name])[rows].mean(0)
                if name=='pathway' else bundle[name][rows].mean(0) for name in ('expression','pathway')}
        self.projection = None
        if self.controls.get('representation')=='matched_no_artifact':
            expression = bundle['expression'][idx]
            self.projection_genes = np.argsort(expression.reshape(-1,expression.shape[-1]).var(0))[-self.config.get('genes',128):]
            width = self.controls.get('matched_width',50)
            self.projection = np.random.default_rng(3).normal(size=(len(self.projection_genes),width))/np.sqrt(len(self.projection_genes))
        return super().fit(self.controlled(bundle),idx)

    def transform(self, bundle, idx):
        return super().transform(self.controlled(bundle),idx)


class StandaloneNeural(FullCandidate):
    """Train the declared architecture directly, without an in-sample Ridge residual."""
    def fit(self, bundle, idx, seed=3):
        c = self.config
        self.view = FullView(c).fit(bundle, idx, seed)
        s, x, cross = self.view.transform(bundle, idx)
        y = bundle['meta'].iloc[idx].label.to_numpy(dtype=float)
        self.mean, self.std = float(y.mean()), max(float(y.std()), .1)
        torch.manual_seed(seed)
        np.random.seed(seed)
        torch.set_num_threads(2)
        self.device = torch.device(c.get('device', 'cuda'))
        self.network = Network(s.shape[-1], x.shape[-1], c['model'], c.get('hidden', 32), c).to(self.device)
        self.network.drop.p = float(c.get('dropout', .15))
        self.base = None
        sx, xx, cx = [torch.tensor(v, device=self.device) for v in (s, x, cross)]
        target = torch.tensor((y-self.mean)/self.std, dtype=torch.float32, device=self.device)
        labels, mask = secondary_labels(bundle, idx)
        classes = torch.tensor(labels, dtype=torch.float32, device=self.device)
        active = torch.tensor(mask, dtype=torch.float32, device=self.device)
        if c.get('head') == 'positive_selected':
            active[:, 1] = 0
        if c.get('head') == 'mono_resistant_combo_sensitive':
            active[:, 0] = 0
        positive = (classes*active).sum(0).clamp(min=1)
        weight = (active.sum(0)-positive).clamp(min=1)/positive
        auxiliary = bundle.get('ablation_pathway', bundle['pathway'])[idx].mean(1)
        if c.get('auxiliary_no_artifact'):
            genes = self.view.genes
            projection = np.random.default_rng(seed+19).normal(size=(len(genes), 50))/np.sqrt(len(genes))
            auxiliary = bundle['expression'][idx][:, :, genes].mean(1)@projection
        auxiliary = torch.tensor(auxiliary, dtype=torch.float32, device=self.device)
        auxiliary = (auxiliary-auxiliary.mean(0))/auxiliary.std(0).clamp(min=.1)
        optimizers = {'adamw': torch.optim.AdamW, 'adam': torch.optim.Adam}
        optimizer = optimizers[c.get('optimizer', 'adamw')](self.network.parameters(),
            lr=float(c.get('lr', .001)), weight_decay=float(c.get('weight_decay', .02)))
        self.losses = []
        self.network.train()
        for _ in range(int(c.get('epochs', 80))):
            optimizer.zero_grad()
            prediction, logits, reconstruction = self.network(sx, xx, cx)
            loss = nn.functional.huber_loss(prediction, target)
            kind = c.get('loss', 'huber')
            if kind in {'weighted_bce', 'focal'}:
                term = nn.functional.binary_cross_entropy_with_logits(logits, classes, pos_weight=weight, reduction='none')
                if kind == 'focal':
                    term = term*(1-torch.exp(-term)).pow(float(c.get('focal_gamma', 2)))
                loss = loss+float(c.get('auxiliary_weight', .2))*(term*active).sum()/active.sum().clamp(min=1)
            if kind == 'pairwise' or c.get('head') == 'ranking':
                difference = target[:, None]-target[None, :]
                pairs = difference.abs()>1e-6
                if pairs.any():
                    margin = prediction[:, None]-prediction[None, :]
                    loss = loss+float(c.get('ranking_weight', .1))*nn.functional.softplus(-margin[pairs]*difference[pairs].sign()).mean()
            if kind == 'multitask' and not c.get('no_pathway_supervision'):
                loss = loss+float(c.get('pathway_weight', .1))*nn.functional.mse_loss(reconstruction, auxiliary)
            if not torch.isfinite(loss):
                raise ValueError('Nonfinite research model loss')
            loss.backward()
            nn.utils.clip_grad_norm_(self.network.parameters(), float(c.get('gradient_clip', 1)))
            optimizer.step()
            self.losses.append(float(loss.detach().cpu()))
        self.network.eval()
        return self


class BundleEstimator:
    def __init__(self, config, bundle, seed):
        self.config, self.bundle, self.seed = config, bundle, seed

    def fit(self, x, y, groups=None):
        idx = np.asarray(x, dtype=int).ravel()
        b = dict(self.bundle)
        b['truth_meta'] = self.bundle.get('truth_meta', self.bundle['meta']).copy()
        b['meta'] = self.bundle['meta'].copy()
        b['truth_meta'].loc[~b['truth_meta'].index.isin(idx), 'label'] = np.nan
        b['meta'].loc[~b['meta'].index.isin(idx), 'label'] = np.nan
        b['meta'].loc[idx, 'label'] = np.asarray(y)
        self.model = ResearchCandidate(self.config).fit(b, idx, self.seed)
        self.bundle = b
        return self

    def predict(self, x):
        return self.model.predict(self.bundle, np.asarray(x, dtype=int).ravel())


class ResearchCandidate:
    def __init__(self, config):
        self.config = copy.deepcopy(config)

    def fit(self, bundle, idx, seed=3):
        c = copy.deepcopy(self.config)
        if 'ablation_pathway' in bundle:
            bundle = dict(bundle, pathway=bundle['ablation_pathway'])
        composition = c.pop('composition', 'replace')
        parent = c.pop('parent_config', None)
        if parent and composition in {'crossfit_residual', 'crossfit_stack'} and not c.get('no_dense_parent'):
            training_bundle = dict(bundle)
            for key in ('meta','truth_meta'):
                if key in bundle:
                    training_bundle[key] = bundle[key].copy()
                    training_bundle[key].loc[~training_bundle[key].index.isin(idx),'label'] = np.nan
            parent_factory = partial(BundleEstimator, parent, training_bundle, seed)
            child_factory = partial(BundleEstimator, dict(c, composition='replace'), training_bundle, seed)
            self.model = (CrossFittedResidualRegressor(parent_factory, child_factory, splits=3, weight_factory=partial(Ridge,alpha=1.))
                          if composition == 'crossfit_residual' else
                          CrossFittedStackingRegressor([parent_factory, child_factory], splits=3, meta_factory=partial(Ridge,alpha=1.)))
            self.model.fit(np.asarray(idx).reshape(-1, 1), bundle['meta'].iloc[idx].label.to_numpy(),
                           bundle['meta'].iloc[idx].clone_id.to_numpy())
            self.index_model = True
        elif c.get('historical_recipe') is not None:
            recipe = copy.deepcopy(c['historical_recipe'])
            for key in ('baseline_only', 'input_cutoff_day', 'no_temporal_order', 'no_clone_abundance'):
                if key in c:
                    recipe[key] = c[key]
            controls = any(c.get(key) for key in ('input_cutoff_day','no_temporal_order','no_clone_abundance',
                'no_barcode_inputs','no_treatment_interaction','last_snapshot_only','remove_pathway'))
            controls = controls or 'input_cutoff_day' in c or c.get('representation')=='matched_no_artifact' or 'ablation_pathway' in bundle
            if c.get('remove_pathway'):
                recipe['representation'] = 'expression'
            if c.get('representation')=='matched_no_artifact':
                recipe['representation'] = 'expression'
            if c.get('no_treatment_interaction'):
                recipe['no_treatment'] = True
            self.model = build_historical(recipe)
            if controls:
                view = HistoricalControlView(recipe)
                view.controls = c
                self.model.view = view
            self.model.fit(bundle, idx, seed)
            self.index_model = False
        else:
            cls = StandaloneNeural if c['model'] in NEURAL else FullCandidate
            self.model = cls(c).fit(bundle, idx, seed)
            self.index_model = False
        return self

    def predict(self, bundle, idx):
        if self.index_model:
            return self.model.predict(np.asarray(idx).reshape(-1, 1))
        return self.model.predict(bundle, idx)

    def close(self):
        visited = set()
        def close(value):
            if id(value) in visited:
                return
            visited.add(id(value))
            if isinstance(value, FullCandidate):
                value.close()
            elif hasattr(value, 'model'):
                close(value.model)
            for name in ('core_', 'parent_', 'mutation_'):
                if hasattr(value, name):
                    close(getattr(value, name))
            for child in getattr(value, 'models_', []):
                close(child)
        close(self.model)
