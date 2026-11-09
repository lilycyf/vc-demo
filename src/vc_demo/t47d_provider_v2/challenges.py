"""Registered T47D diagnostics and challenges, isolated from scientific selection."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import anndata as ad
import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr, wilcoxon
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, ndcg_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from vc_demo.harness.research_contract import file_digest, digest
from vc_demo.harness.research_v2.metrics import MetricSpec, paired_evidence
from vc_demo.harness.research_v2.session import Session
from vc_demo.harness.research_v2.verdicts import control_verdict
from vc_demo.t47d_lineage.data import TREATMENTS
from . import provider
from .cell_sources import attach_development, attach_query, info, verified_file
from .heavy_models import tf_call


def alter(config, **changes):
    c = copy.deepcopy(config)
    c.update(changes)
    if 'hazard_max_fit_day' in changes and c.get('training_event_policy'):
        c['training_event_policy']['max_day'] = min(c['training_event_policy']['max_day'], changes['hazard_max_fit_day'])
    if changes.get('remove_pathway'):
        if c.get('representation', 'pathway') in {'pathway', 'both'}:
            c['representation'] = 'expression'
    if c.get('parent_config'):
        c['parent_config'] = alter(c['parent_config'], **changes)
    return c


class Evaluation:
    def __init__(self, request):
        self.r = request
        self.contract = request['analysis_contract']
        self.settings = self.contract['settings']
        self.out = Path(request['output_dir'])
        self.out.mkdir(parents=True, exist_ok=True)
        self.config = provider.configurations(request['recipe']['parameters'], request['recipe']['training'])
        self.metric = MetricSpec.from_dict(request['metric'])
        self.dc = request['development_contract']
        self.dev, self.dev_rows = provider.read_inputs(request['development_inputs']['early_observations'])
        self.dev = attach_development(self.dev, request['development_inputs'])
        self.dev['meta']['label'] = self.dc['targets']
        self.cc, self.query = None, None
        if request['plan']['data_scope'] != 'development':
            self.cc = json.loads(verified_file(self.contract['inputs']['confirmation_contract']).read_text())
            self.query, self.query_rows = provider.read_inputs(self.cc['early_observations'])
            self.query = attach_query(self.query, self.cc)
            self.query['meta']['label'] = self.cc['targets']
        self.seeds = self.settings.get('seeds', self.dc['seeds'])
        if not self.seeds or not set(self.seeds).issubset(set(self.dc['seeds'])):
            raise ValueError('Preregister an available nonempty training/prediction seed set')
        self.fits, self.calibrations, self.audit, self.outputs, self.records = 0, 0, [], [], []
        self.builder = provider._builder({**request, 'output_dir': str(self.out)})

    def source(self, name):
        return verified_file(self.contract['inputs']['source:' + name])

    def calibrate(self, function):
        if self.calibrations >= self.r['plan']['fit_budget']['calibration']:
            raise ValueError('Registered analysis calibration allocation exhausted')
        self.calibrations += 1
        return function()

    def count_table(self):
        return pd.read_csv(self.source('clone_condition_counts.csv'))

    def counts(self, bundle, day=26, epsilon=1e-5):
        if self.r['plan']['data_scope'] == 'development':
            metadata = json.loads(self.source('development_label_metadata.json').read_text())
            table = pd.DataFrame(metadata['counts'])
            total = {(r['treatment'], r['time_day']): r['cell_count'] for r in metadata['population_totals']}
        else:
            table = self.count_table()
            total = table.groupby(['treatment', 'time_day']).cell_count.sum().to_dict()
        n = table.set_index(['clone_id', 'treatment', 'time_day']).cell_count.to_dict()
        values, f0, fy = [], [], []
        for row in bundle['meta'].itertuples():
            base = n[(row.clone_id, 'baseline', 0)] / total[('baseline', 0)]
            endpoint = n.get((row.clone_id, row.treatment, day), 0) / total[(row.treatment, day)]
            values.append(np.log2((endpoint + epsilon) / (base + epsilon)))
            f0.append(base)
            fy.append(endpoint)
        return np.asarray(values), np.asarray(f0), np.asarray(fy)

    def all_bundle(self):
        if self.query is None:
            raise ValueError('Development-only analysis may not open confirmation observations or outcomes')
        b = {key: np.concatenate([self.dev[key], self.query[key]]) for key in ('expression', 'pathway', 'pseudobulk', 'aux')}
        b['meta'] = pd.concat([self.dev['meta'], self.query['meta']], ignore_index=True)
        b['gene_order_info'] = self.dev.get('gene_order_info')
        if 'cell_source' in self.dev:
            a = ad.read_h5ad(verified_file(self.dev['cell_source']))
            q = ad.read_h5ad(verified_file(self.query['cell_source']))
            if a.var_names.tolist() != q.var_names.tolist():
                raise ValueError('Development/query cell vocabulary differs')
            merged = ad.concat([a, q], join='inner', merge='same')
            path = self.out / 'all_exposed_early_cells.h5ad'
            merged.write_h5ad(path)
            b['cell_source'] = info(path)
            self.outputs.append(str(path))
        events = self.count_table()
        b['training_events'] = events.loc[events.time_day.isin([1, 4, 8, 26]) & events.clone_id.isin(b['meta'].clone_id),
                                        ['clone_id', 'treatment', 'time_day', 'cell_count']]
        return b

    def fit(self, config, bundle, train, valid, seed, tag, target=None):
        if self.fits >= self.r['plan']['fit_budget']['model']:
            raise ValueError('Registered analysis task-pipeline fitting allocation exhausted')
        self.fits += 1
        y = bundle['meta'].iloc[train].label.to_numpy() if target is None else np.asarray(target)
        safe = provider._safe_bundle(bundle, train, y)
        model = provider._fit(config, safe, np.asarray(train), seed, self.builder, self.records)
        if config.get('composition') in {'crossfit_stack', 'crossfit_residual'}:
            f = {'seed': seed, 'fold_id': tag, 'train_groups': sorted(set(bundle['meta'].iloc[train].clone_id)),
                 'validation_groups': sorted(set(bundle['meta'].iloc[valid].clone_id))}
            Session._composition_audit([provider._composition_record(model, f)], {'folds': [f]})
        self.audit.append({'seed': seed, 'tag': tag, 'train_groups': sorted(set(bundle['meta'].iloc[train].clone_id)),
            'validation_groups': sorted(set(bundle['meta'].iloc[valid].clone_id)),
            'training_conditions': sorted(set(bundle['meta'].iloc[train].treatment)),
            'training_row_ids_sha256': digest([str(r.clone_id)+'::'+str(r.treatment) for r in bundle['meta'].iloc[train].itertuples()]),
            'max_predictor_input_day': 0 if config.get('baseline_only', config.get('historical_recipe', {}).get('baseline_only', False)) else config.get('input_cutoff_day', 4),
            'max_auxiliary_outcome_day': config.get('hazard_max_fit_day', 26) if config.get('model') == 'hazard' else None})
        provider._rebind(model, bundle)
        path = self.out / ('fitted_pipeline_' + str(self.fits) + '.joblib')
        joblib.dump(model, path, compress=3)
        self.outputs.append(str(path))
        self.outputs.extend(path for record in self.records for path in record.get('fitted_sidecars', []))
        return model

    def save(self, name, **arrays):
        path = self.out / (name + '.npz')
        np.savez_compressed(path, **arrays)
        self.outputs.append(str(path))

    def score(self, y, predictions, groups=None):
        p = np.asarray(predictions)
        if groups is None:
            if len(y) == len(self.dev['meta']):
                groups = self.dev['meta'].clone_id.tolist()
            elif self.query is not None and len(y) == len(self.query['meta']):
                groups = self.query['meta'].clone_id.tolist()
            else:
                raise ValueError('Supply the actual scoring group alignment')
        table = {'targets': np.asarray(y).tolist(), 'predictions': p.tolist(), 'seeds': self.seeds,
            'row_ids': ['analysis_row_' + str(i) for i in range(len(y))], 'groups': list(groups)}
        try:
            primary = self.metric.score(table)
        except ValueError:
            primary = None
        ensemble_metric = MetricSpec.from_dict({**self.r['metric'], 'aggregation': 'ensemble'})
        try:
            secondary = ensemble_metric.score(table)
        except ValueError:
            secondary = None
        return {'mean_seed_score': primary, 'ensemble_secondary_score': secondary,
            'metric_id': self.metric.identity, 'ensemble_metric_id': ensemble_metric.identity,
            'seeds': self.seeds, 'prediction_rows': len(y), 'evidence': 'descriptive postselection, never search reward'}

    def frozen(self, bundle):
        provider._builder(self.r)
        saved = [joblib.load(path) for path in self.r['checkpoint_files'] if path.endswith('.joblib')]
        pred = []
        for seed in self.seeds:
            record = next(x for x in saved if x['seed'] == seed)
            model = record['model']
            provider._rebind(model, bundle)
            pred.append(model.predict(np.arange(len(bundle['meta'])).reshape(-1, 1)))
        return np.stack(pred, axis=1)

    def oof(self, config, bundle, tag):
        groups = bundle['meta'].clone_id.to_numpy()
        predictions = np.full((len(bundle['meta']), len(self.seeds)), np.nan)
        for f in self.dc['folds']:
            if f['seed'] not in self.seeds:
                continue
            train = np.flatnonzero(np.isin(groups, f['train_groups']))
            valid = np.flatnonzero(np.isin(groups, f['validation_groups']))
            m = self.fit(config, bundle, train, valid, f['seed'], tag + '_' + f['fold_id'])
            predictions[valid, self.seeds.index(f['seed'])] = m.predict(valid.reshape(-1, 1))
        self.save(tag, predictions=predictions)
        return predictions

    def refit_query(self, config, tag, target=None):
        b = self.all_bundle()
        train = np.arange(len(self.dev['meta']))
        valid = np.arange(len(train), len(b['meta']))
        if config.get('heldout_treatment'):
            train = train[b['meta'].iloc[train].treatment.ne(config['heldout_treatment']).to_numpy()]
        predictions = []
        for seed in self.seeds:
            actual_target = None if target is None else target[train]
            model = self.fit(config, b, train, valid, seed, tag, actual_target)
            predictions.append(model.predict(valid.reshape(-1, 1)))
        predictions = np.stack(predictions, axis=1)
        self.save(tag, predictions=predictions)
        return predictions

    def paired(self, prediction, reference=None):
        positions = [self.dc['seeds'].index(seed) for seed in self.seeds]
        ref = copy.deepcopy(self.r['development_receipt']['prediction_table'])
        ref['predictions'] = np.asarray(ref['predictions'])[:, positions].tolist()
        ref['seeds'] = self.seeds
        ref['fold_ids'] = np.asarray(ref['fold_ids'])[:, positions].tolist()
        after = dict(ref, predictions=np.asarray(prediction).tolist())
        try:
            return paired_evidence(self.metric, after, ref, draws=self.settings.get('bootstrap_draws', 500))
        except ValueError as e:
            return {'defined': False, 'reason': str(e)}

    def simple_challenge(self, kind):
        if kind == 'loco':
            if self.r['plan']['data_scope'] != 'all_exposed_secondary':
                raise ValueError('Original full-cohort LOCO requires explicit all-exposed secondary scope')
            b = self.all_bundle()
            groups = b['meta'].clone_id.to_numpy()
            p = np.full((len(groups), len(self.seeds)), np.nan)
            for clone in sorted(set(groups)):
                train, valid = np.flatnonzero(groups != clone), np.flatnonzero(groups == clone)
                for j, seed in enumerate(self.seeds):
                    model = self.fit(self.config, b, train, valid, seed, 'loco')
                    p[valid, j] = model.predict(valid.reshape(-1, 1))
            self.save('loco', predictions=p)
            return {'scope': 'postselection full-exposed-cohort LOCO, not primary locked-test evidence',
                    **self.score(b['meta'].label.to_numpy(), p, b['meta'].clone_id)}
        if kind == 'monotherapy_to_combination':
            config = alter(self.config, heldout_treatment='combination')
            def batch_policy(c):
                if c.get('representation') == 'scvi':
                    value = self.settings['unseen_batch_policy']
                    if value not in {'reference_baseline', 'error'}:
                        raise ValueError('Register a real fixed-encoder batch policy')
                    c.setdefault('representation_parameters', {})['unknown_batch'] = value
                if c.get('parent_config'):
                    batch_policy(c['parent_config'])
            batch_policy(config)
            p = self.refit_query(config, 'monotherapy_to_combination')
            use = self.query['meta'].treatment.eq('combination').to_numpy()
            return {'training_combination_labels': 0, 'representation_training_combination_cells': 0,
                'query_combination_early_observations_allowed': True,
                **self.score(self.query['meta'].label.to_numpy()[use], p[use], self.query['meta'].loc[use, 'clone_id'])}
        if kind == 'late_interval':
            b = self.all_bundle()
            target, _, _ = self.counts(b, 8)
            config = alter(self.config, hazard_max_fit_day=8)
            p = self.refit_query(config, 'late_interval', target)
            return {'training_response_day': 8, 'query_response_day': 26, 'training_day26_outcomes_used': 0,
                'interpretation': 'day8 response transport, not calibrated horizon extrapolation',
                **self.score(self.query['meta'].label.to_numpy(), p)}
        days = self.settings['cutoffs']
        out = {}
        for day in days:
            if day not in {0, 1, 4}:
                raise ValueError('Unsupported predictor observation horizon')
            config = alter(self.config, input_cutoff_day=day)
            p = self.refit_query(config, 'early_warning_' + str(day))
            out[str(day)] = {'lead_days': 26 - day, **self.score(self.query['meta'].label.to_numpy(), p)}
        positive = [int(day) for day, value in out.items() if value['mean_seed_score'] is not None and value['mean_seed_score'] > 0]
        return {'horizons': out, 'parent_baseline_only_flags_preserved': True,
                'descriptive_first_positive_cutoff': min(positive) if positive else None,
                'clinical_warning_threshold_established': False}

    def shuffle_pathways(self, bundle):
        genes = pd.read_csv(self.source('gene_order.csv')).gene_symbol.fillna('').to_numpy()
        permutation = np.random.default_rng(self.settings['permutation_seed']).permutation(len(genes))
        ids = []
        for line in Path(self.contract['assets']['hallmark']['path']).read_text().splitlines():
            terms = line.split('\t')
            found = np.flatnonzero(np.isin(genes, terms[2:]))
            if len(found) >= 5:
                ids.append(permutation[found])
        if len(ids) != bundle['pathway'].shape[-1]:
            raise ValueError('Shuffled memberships must preserve original pathway vocabulary/width')
        b = dict(bundle, pathway=np.stack([bundle['expression'][:, :, members].mean(2) for members in ids], axis=-1))
        return b

    def ablations(self):
        roles, modules = provider.native_roles(self.config)
        consumed = set(roles) | set(modules)
        inventory = {
            'no_barcode_informed_inputs': ({'input:barcode_state', 'input:early_abundance'}, {'no_barcode_inputs': True, 'no_clone_abundance': True}),
            'baseline_only': ({'input:temporal_order'}, {'baseline_only': True}),
            'no_temporal_order': ({'input:temporal_order'}, {'no_temporal_order': True}),
            'no_pathway': ({'hallmark'}, {'remove_pathway': True, 'no_pathway_supervision': True}),
            'shuffled_gene_memberships': ({'hallmark'}, {}),
            'matched_capacity_no_artifact': ({'hallmark', 'representation:' + self.config.get('representation', 'pathway')},
                {'representation': 'matched_no_artifact', 'auxiliary_no_artifact': True}),
            'no_treatment_interaction': ({'input:treatment_interaction'}, {'no_treatment_interaction': True}),
            'no_dense_parent_branch': ({'branch:dense', 'branch:parent'}, {'no_dense_parent': True})}
        result = {}
        for name, (removed, changes) in inventory.items():
            if not (removed & consumed):
                result[name] = {'applicability': 'not_applicable', 'control_applied': False, 'reason': 'Target component was not consumed'}
                continue
            config = alter(self.config, **changes)
            if name == 'matched_capacity_no_artifact':
                def matched(original):
                    c = copy.deepcopy(original)
                    base = original.get('historical_recipe', original)
                    genes = min(base.get('genes', 128), self.dev['expression'].shape[-1])
                    width = {'pathway': self.dev['pathway'].shape[-1],
                        'scvi': original.get('representation_parameters', {}).get('scvi', {}).get('n_latent', 16),
                        'pca': 8 if 'historical_recipe' in original else 16,
                        'distance': 4, 'pseudotime': 2, 'cellrank': 4,
                        'expression': genes, 'pseudobulk': genes, 'both': genes + self.dev['pathway'].shape[-1]}[base.get('representation', 'pathway')]
                    c.update(representation='matched_no_artifact', auxiliary_no_artifact=True, matched_width=width)
                    if original.get('parent_config'):
                        c['parent_config'] = matched(original['parent_config'])
                    return c
                config = matched(self.config)
            if name == 'no_dense_parent_branch':
                config.pop('parent_config', None)
                config['composition'] = 'replace'
            bundle = self.shuffle_pathways(self.dev) if name == 'shuffled_gene_memberships' else self.dev
            p = self.oof(config, bundle, name)
            actual_roles, actual_modules = provider.native_roles(config)
            verdict = control_verdict(removed_roles=removed, consumed_roles=consumed,
                changed_dependency_identity=digest(config) != digest(self.config),
                removed_roles_still_consumed=set(actual_roles) | set(actual_modules))
            if name == 'shuffled_gene_memberships':
                verdict = {'applicability': 'applied', 'control_applied': True,
                    'intervention': 'fixed global gene permutation preserves pathway sizes and overlap, not column shuffling'}
            result[name] = {**verdict, 'paired_development': self.paired(p)}
        return result

    def denominator(self):
        _, f0, f26 = self.counts(self.dev)
        out = []
        for seed in self.settings['permutation_seeds']:
            rng = np.random.default_rng(seed)
            permuted = f26.copy()
            for treatment in TREATMENTS:
                use = np.flatnonzero(self.dev['meta'].treatment.eq(treatment))
                permuted[use] = rng.permutation(f26[use])
            b = dict(self.dev)
            b['meta'] = self.dev['meta'].copy()
            b['meta']['label'] = np.log2((permuted + 1e-5) / (f0 + 1e-5))
            p = self.oof(self.config, b, 'denominator_' + str(seed))
            out.append(self.score(b['meta'].label.to_numpy(), p))
        return {'draws': out, 'test_labels_used': False, 'not_a_confirmatory_selection_corrected_p_value': True}

    def biology(self):
        genes = pd.read_csv(self.source('gene_order.csv')).gene_symbol.fillna('').to_numpy()
        rows = pd.read_csv(self.source('clone_expression_rows.csv'))
        matrix = sparse.load_npz(self.source('clone_mean_log_expression.npz'))
        lookup = {(r.clone_id, r.treatment, int(r.time_day)): i for i, r in rows.iterrows()}
        sets = {}
        for line in Path(self.contract['assets']['hallmark']['path']).read_text().splitlines():
            terms = line.split('\t')
            if any(name in terms[0] for name in ('ESTROGEN_RESPONSE', 'E2F_TARGETS', 'EPITHELIAL_MESENCHYMAL')):
                loc = np.flatnonzero(np.isin(genes, terms[2:]))
                if len(loc):
                    sets[terms[0]] = loc
        records = []
        all_groups = sorted(set(self.dc['groups']) | set(self.cc['groups']))
        for clone in all_groups:
            for treatment in TREATMENTS:
                for day in self.settings['expression_days']:
                    key = (clone, treatment, day)
                    if key not in lookup or (clone, 'baseline', 0) not in lookup:
                        continue
                    record = {'clone_id': clone, 'treatment': treatment, 'day': day}
                    for name, loc in sets.items():
                        record[name] = float(matrix[lookup[key], loc].mean() - matrix[lookup[(clone, 'baseline', 0)], loc].mean())
                    records.append(record)
        frame = pd.DataFrame(records)
        path = self.out / 'paired_program_observations.csv'
        frame.to_csv(path, index=False)
        self.outputs.append(str(path))
        comparisons = {}
        rng = np.random.default_rng(self.settings['bootstrap_seed'])
        for day in self.settings['expression_days']:
            for name in sets:
                table = frame.loc[frame.day.eq(day)].pivot(index='clone_id', columns='treatment', values=name)
                for mono in TREATMENTS[:2]:
                    if not {'combination', mono} <= set(table):
                        continue
                    pair = table[['combination', mono]].dropna()
                    d = (pair.combination - pair[mono]).to_numpy()
                    if not len(d):
                        continue
                    samples = rng.choice(d, (self.settings['bootstrap_draws'], len(d)), replace=True).mean(1)
                    comparisons[name + '_' + str(day) + '_' + mono] = {'n_clones': len(d), 'mean': float(d.mean()),
                        'ci95': np.quantile(samples, [.025, .975]).tolist(),
                        'nominal_uncorrected_wilcoxon': float(wilcoxon(d).pvalue) if np.any(d) else 1.}
        b = self.all_bundle()
        sensitivity = {}
        for epsilon in self.settings['epsilons']:
            y, _, _ = self.counts(b, 26, epsilon)
            sensitivity[str(epsilon)] = {'positive_count': int((y > 0).sum()), 'median': float(np.median(y)),
                'correlation_with_registered_label': float(spearmanr(y, b['meta'].label).statistic)}
        return {'program_comparisons': comparisons, 'epsilon_sensitivity': sensitivity,
            'interpretation': 'descriptive clone-paired observed-cell comparison; survivorship and shared-denominator caveats; no causal reversal or clinical efficacy'}

    def resistance(self):
        b = self.all_bundle()
        ndev = len(self.dev['meta'])
        dev = np.arange(ndev)
        pred = self.frozen(b)
        positions = [self.dc['seeds'].index(seed) for seed in self.seeds]
        pred[dev] = np.asarray(self.r['development_receipt']['prediction_table']['predictions'])[:, positions]
        genes = pd.read_csv(self.source('gene_order.csv')).gene_symbol.fillna('').to_numpy()
        signatures = []
        for line in Path(self.contract['assets']['hallmark']['path']).read_text().splitlines():
            terms = line.split('\t')
            if any(k in terms[0] for k in ('ESTROGEN_RESPONSE', 'E2F_TARGETS', 'EPITHELIAL_MESENCHYMAL')):
                loc = np.flatnonzero(np.isin(genes, terms[2:]))
                if len(loc):
                    signatures.append(loc)
        if not signatures:
            raise ValueError('No source-backed biological signature coverage')
        adaptive = np.stack([(b['expression'][:, 2, loc].mean(1) - b['expression'][:, 0, loc].mean(1)) for loc in signatures], axis=1).mean(1)
        scaler = self.calibrate(lambda: StandardScaler().fit(b['pathway'][dev, 0]))
        negative = dev[b['meta'].iloc[dev].label.to_numpy() < 0]
        if not len(negative):
            return {'defined': False, 'reason': 'No negative development reference; do not invent a sensitivity prototype'}
        distance = cdist(scaler.transform(b['pathway'][:, 2]), scaler.transform(b['pathway'][negative, 2])).min(1)
        cfg = self.settings['hazard_config']
        hazard = self.fit(cfg, b, dev, np.arange(ndev, len(b['meta'])), self.seeds[0], 'persistence_auxiliary')
        if not isinstance(hazard, provider.IndexEstimator) or not hasattr(hazard.model.model, 'predict_survival'):
            raise ValueError('Persistence analysis needs an actual standalone interval AFT model')
        survival = hazard.model.model.predict_survival(b, np.arange(len(b['meta'])), [180])[:, 0]
        terms = np.column_stack([pred.mean(1), adaptive, distance, survival])
        scale = self.calibrate(lambda: MinMaxScaler().fit(terms[dev]))
        calibrators = self.out / 'resistance_calibrators.joblib'
        joblib.dump({'pathway_scaler': scaler, 'term_scaler': scale}, calibrators)
        self.outputs.append(str(calibrators))
        weights = np.asarray(self.settings['weights'])
        if weights.shape != (4,) or not np.allclose(weights.sum(), 1):
            raise ValueError('Predeclare the actual four exploratory score weights')
        ras = scale.transform(terms).clip(0, 1) @ weights
        table = self.count_table()
        positives = set(table.loc[table.time_day.eq(180) & table.cell_count.ge(3), 'clone_id'])
        use = b['meta'].treatment.eq('combination').to_numpy()
        ranked = b['meta'].loc[use, 'clone_id'].to_numpy()[np.argsort(-ras[use])]
        all_groups, heldout = set(ranked), set(self.cc['groups'])
        top = set(ranked[:self.settings['top_k']])
        observed, unseen = positives & all_groups, positives & heldout
        self.save('resistance_terms', terms=terms, score=ras)
        return {'weights': weights.tolist(), 'in_sample_predictions_not_used_for_development_primary_term': True,
            'eligible_observed_positive_count': len(observed), 'heldout_positive_count': len(unseen),
            'noneligible_observed_positive_count': len(positives - all_groups),
            'descriptive_recall_at_k': len(top & observed) / len(observed) if observed else None,
            'unseen_clone_escape_recall': len(top & unseen) / len(unseen) if unseen else None,
            'undefined_unseen_recall_reason': None if unseen else 'No heldout eligible positive clone',
            'interpretation': 'registered descriptive score; day180 survival extrapolation unvalidated; no causal/clinical reversal claim'}

    def secondary(self):
        p = self.frozen(self.query)
        positions = [self.dc['seeds'].index(s) for s in self.seeds]
        dev_oof = np.asarray(self.r['development_receipt']['prediction_table']['predictions'])[:, positions].mean(1)
        y = np.asarray(self.dc['targets']) > 0
        if len(set(y)) < 2:
            return {'defined': False, 'reason': 'Only one development sign class; cannot fit genuine calibrator'}
        calibrator = self.calibrate(lambda: LogisticRegression(C=self.settings['calibrator_C'], random_state=self.settings['calibrator_seed']).fit(dev_oof.reshape(-1, 1), y))
        path = self.out / 'development_oof_calibrator.joblib'
        joblib.dump(calibrator, path)
        self.outputs.append(str(path))
        probability = calibrator.predict_proba(p.mean(1).reshape(-1, 1))[:, 1]
        truth = np.asarray(self.cc['targets'])
        positive = truth > 0
        result = {'regression': self.score(truth, p), 'calibration_fit': 'development OOF only',
            'brier': float(np.mean((probability - positive) ** 2)),
            'auroc': float(roc_auc_score(positive, probability)) if len(set(positive)) > 1 else None,
            'auprc': float(average_precision_score(positive, probability)) if positive.any() else None}
        observed = self.query['meta'].assign(pred=p.mean(1)).pivot(index='clone_id', columns='treatment', values='label')
        estimate = self.query['meta'].assign(pred=p.mean(1)).pivot(index='clone_id', columns='treatment', values='pred')
        delta = observed[list(TREATMENTS[:2])].max(1) - observed.combination
        d_pred = estimate[list(TREATMENTS[:2])].max(1) - estimate.combination
        result['log_suppression_rho'] = float(spearmanr(delta, d_pred).statistic) if np.ptp(d_pred) else None
        _, f0, f26 = self.counts(self.query)
        raw = self.query['meta'].assign(raw=f26 / f0).pivot(index='clone_id', columns='treatment', values='raw')
        inv = (np.exp2(np.clip(p.mean(1), -20, 20)) * (f0 + 1e-5) - 1e-5).clip(0, 1) / f0
        raw_pred = self.query['meta'].assign(raw=inv).pivot(index='clone_id', columns='treatment', values='raw')
        raw_delta = raw[list(TREATMENTS[:2])].max(1) - raw.combination
        estimate_delta = raw_pred[list(TREATMENTS[:2])].max(1) - raw_pred.combination
        result['raw_ratio_suppression_rho'] = float(spearmanr(raw_delta, estimate_delta).statistic) if np.ptp(estimate_delta) else None
        clone_truth, clone_pred = observed.max(1).to_numpy(), estimate.max(1).to_numpy()
        for k in (5, 10):
            result['clonewise_ndcg_at' + str(k)] = float(ndcg_score([clone_truth - clone_truth.min()], [clone_pred], k=min(k, len(clone_truth))))
        sensitive = ((observed[list(TREATMENTS[:2])].max(1) > 0) & (observed.combination < 0)).to_numpy()
        result['mono_resistant_combo_sensitive'] = {'auroc': float(roc_auc_score(sensitive, d_pred)) if len(set(sensitive)) > 1 else None,
            'auprc': float(average_precision_score(sensitive, d_pred)) if sensitive.any() else None,
            'score_kind': 'predicted monotherapy-minus-combination margin, not a calibrated joint probability'}
        result['suppression_sign_accuracy'] = float(((d_pred > 0) == (delta > 0)).mean())
        result['positive_selection_accuracy'] = float(((p.mean(1) > 0) == positive).mean())
        result['within_treatment'] = {t: {'mae': float(np.mean(np.abs(truth[self.query['meta'].treatment.eq(t)] - p.mean(1)[self.query['meta'].treatment.eq(t)])))} for t in TREATMENTS}
        self.save('secondary_predictions', predictions=p, probability=probability)
        return result

    def reference(self):
        directory = self.out / 'author_reference'
        directory.mkdir(exist_ok=True)
        source = verified_file(self.contract['inputs']['reference_data'])
        config = self.settings['tracsed_config']
        result_path = directory / 'results.json'
        tf_call('reference', directory, config, self.contract['assets'], reference_data=source,
                intervals=self.settings['intervals'], result=result_path,
                model_fit_budget=self.r['plan']['fit_budget']['model'])
        value = json.loads(result_path.read_text())
        for item in value['results']:
            if item.get('status') == 'insufficient_source_windows':
                continue
            self.fits += 1
            self.audit.append({'train_groups': [item['barcode']], 'validation_groups': [item['barcode']],
                'tag': 'author_prefix_windows_' + item['variant'], 'not_unseen_clone_evaluation': True})
        self.outputs.extend(str(p) for p in directory.rglob('*') if p.is_file())
        return {'evaluated_windows_variants': len(value['results']), 'model_refits': self.fits,
                'source_function_sha256': value['source_function_sha256'], 'protocol': value['protocol']}


def evaluate(request):
    e = Evaluation(request)
    kind = e.contract['kind']
    if kind in {'loco', 'monotherapy_to_combination', 'late_interval', 'early_warning'}:
        metrics = e.simple_challenge(kind)
    elif kind == 'ablations':
        metrics = e.ablations()
    elif kind in {'last_snapshot', 'early_abundance'}:
        config = alter(e.config, last_snapshot_only=True, baseline_only=False) if kind == 'last_snapshot' else {
            'model': 'frequency', 'representation': 'pathway', 'baseline_only': False, 'alpha': e.settings['alpha']}
        p = e.oof(config, e.dev, kind)
        metrics = {'paired_development': e.paired(p)}
    elif kind == 'denominator_null':
        metrics = e.denominator()
    elif kind == 'biology_sensitivity':
        metrics = e.biology()
    elif kind == 'resistance_month6':
        metrics = e.resistance()
    elif kind == 'secondary_metrics':
        metrics = e.secondary()
    elif kind == 'author_reference':
        metrics = e.reference()
    else:
        raise ValueError('Implement the registered analysis; no empty success placeholder')
    if e.calibrations > request['plan']['fit_budget']['calibration']:
        raise ValueError('Actual analysis calibration fits exceed the preregistered allocation')
    return {'metrics': metrics, 'model_refits': e.fits, 'calibration_refits': e.calibrations,
        'fit_audit': e.audit, 'component_fit_count': len(e.records), 'output_files': sorted(set(e.outputs)),
        'scope': 'report-only; no promotion, optimizer credit or additional selection',
        'diagnostics': {'registered_kind': kind, 'fitted_component_records': e.records}}
