"""A single executable estimand for rewards, paired evidence and promotion."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import f1_score

from vc_demo.harness.research_contract import digest, file_digest


@dataclass(frozen=True)
class MetricSpec:
    name: str
    direction: str
    aggregation: str
    prediction_unit: str
    group_key: str
    labels: tuple = ()
    scorer_path: str | None = None
    scorer_sha256: str | None = None
    scorer_function: str = 'score'
    prediction_kind: str = 'regression'

    def __post_init__(self):
        if self.scorer_path and self.name in {'spearman','mae','macro_f1'}:
            raise ValueError('Do not shadow a built-in metric; register a distinct custom scorer identity')
        if self.name not in {'spearman', 'mae', 'macro_f1'} and not (self.scorer_path and self.scorer_sha256):
            raise ValueError('Custom task metrics require an immutable, tested scorer provider')
        if self.name in {'spearman','mae','macro_f1'} and self.direction != ('minimize' if self.name == 'mae' else 'maximize'):
            raise ValueError('Metric direction differs from the registered scorer')
        if self.direction not in {'minimize','maximize'}:raise ValueError('Metric direction must be explicit')
        if self.name=='macro_f1':object.__setattr__(self,'prediction_kind','class_probabilities')
        if self.name in {'spearman','mae'} and (self.prediction_kind!='regression' or self.labels):
            raise ValueError('Continuous built-in metrics do not consume class probabilities/vocabularies')
        if self.prediction_kind not in {'regression','class_probabilities','structured'}:raise ValueError('Declare the prediction contract')
        if self.prediction_kind=='structured' and not self.scorer_path:raise ValueError('Structured task outputs require a tested custom scorer')
        if self.aggregation not in {'mean_seed', 'ensemble'}:
            raise ValueError('Aggregation order must be explicit')
        if not self.prediction_unit or not self.group_key:
            raise ValueError('Prediction and independent sampling units are required')
        if self.classification and (len(self.labels)<2 or len(set(self.labels))!=len(self.labels)):
            raise ValueError('Classification requires a fixed class vocabulary')
        if self.scorer_path and file_digest(Path(self.scorer_path))!=self.scorer_sha256:raise ValueError('Scorer source differs from the metric contract')

    @classmethod
    def from_dict(cls, value):
        return cls(**{**value, 'labels':tuple(value.get('labels', ()))})

    @property
    def identity(self):
        value=asdict(self);value.pop('scorer_path')
        return digest(value)

    @property
    def classification(self):
        return self.name=='macro_f1' or self.prediction_kind=='class_probabilities'

    @property
    def sign(self):
        return -1 if self.direction == 'minimize' else 1

    def arrays(self, table):
        y, p = np.asarray(table['targets']), np.asarray(table['predictions'], dtype=float)
        n, s = len(y), len(table['seeds'])
        if (self.prediction_kind!='structured' and y.ndim!=1) or not n or not s or len(set(table['row_ids']))!=n or len(set(table['seeds']))!=s:
            raise ValueError('Prediction rows and evaluation seeds must be nonempty and unique')
        if len(table['groups'])!=n or len(table['row_ids'])!=n or not np.isfinite(p).all():
            raise ValueError('Invalid prediction alignment or nonfinite predictions')
        if self.classification:
            if p.shape!=(n,s,len(self.labels)) or not set(y).issubset(self.labels):
                raise ValueError('Classification predictions must be [row, seed, fixed class] probabilities')
            if (p<0).any() or (p>1).any() or not np.allclose(p.sum(-1),1,atol=1e-5):
                raise ValueError('Invalid class probabilities; class IDs cannot be averaged')
        elif self.prediction_kind=='structured':
            if p.ndim<2 or p.shape[:2]!=(n,s):raise ValueError('Structured predictions preserve the row/seed axes; task scorer validates the remaining structure')
        elif p.shape!=(n,s) or not np.isfinite(y.astype(float)).all():
            raise ValueError('Regression predictions must be [row, seed]')
        return y, p

    def score(self, table, indices=None):
        y, p = self.arrays(table)
        if indices is not None:
            y, p = y[indices], p[indices]
        def single(pred):
            if self.scorer_path:
                if file_digest(Path(self.scorer_path))!=self.scorer_sha256:raise ValueError('Frozen metric implementation changed')
                spec=importlib.util.spec_from_file_location('metric_'+self.scorer_sha256[:16],self.scorer_path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                return float(getattr(module,self.scorer_function)(y,pred))
            if self.name == 'macro_f1':
                return float(f1_score(y,np.asarray(self.labels)[pred.argmax(-1)],labels=self.labels,
                                      average='macro',zero_division=0))
            if self.name == 'mae':
                return float(np.abs(y-pred).mean())
            if np.ptp(y)==0 or np.ptp(pred)==0:
                raise ValueError('Undefined rank metric')
            return float(spearmanr(y,pred).statistic)
        value = single(p.mean(1)) if self.aggregation=='ensemble' else float(np.mean([single(p[:,j]) for j in range(p.shape[1])]))
        if not np.isfinite(value):
            raise ValueError('Undefined metric')
        return value


def paired_evidence(spec, candidate, reference, *, draws=500, seed=0, minimum_effect=0.):
    if draws<1 or minimum_effect<0:
        raise ValueError('Invalid uncertainty or minimum-effect policy')
    for table in (candidate, reference):
        if table.get('evidence_phase')!='development' or table.get('metric_id')!=spec.identity:
            raise ValueError('Only matching development evidence can enter search feedback')
        spec.arrays(table)
    for key in ('row_ids','groups','targets','seeds','fold_ids'):
        if candidate.get(key)!=reference.get(key):
            raise ValueError('Paired rows, groups, targets, folds and seeds must match: '+key)
    delta = lambda ids:spec.sign*(spec.score(candidate,ids)-spec.score(reference,ids))
    groups = np.asarray(candidate['groups']); unique = np.unique(groups)
    rng = np.random.default_rng(seed); boot = []
    for _ in range(draws):
        rows = np.concatenate([np.flatnonzero(groups==g) for g in rng.choice(unique,len(unique),replace=True)])
        try:
            boot.append(delta(rows))
        except ValueError:
            continue
    ci = np.quantile(boot,[.025,.975]).tolist() if boot else None
    enough = len(unique)>=2 and len(boot)>=max(1,int(.8*draws))
    return {'metric_id':spec.identity,'evidence_phase':'development','candidate_score':spec.score(candidate),
        'reference_score':spec.score(reference),'paired_delta':delta(np.arange(len(groups))),
        'delta_ci95':ci,'independent_groups':len(unique),'valid_draws':len(boot),'requested_draws':draws,
        'minimum_effect':minimum_effect,'promotion_supported':bool(enough and ci[0]>minimum_effect),
        'uncertainty_type':'conditional whole-group bootstrap of fixed OOF predictions',
        'caveat':'Not independent confirmation or correction for adaptive candidate selection.'}
