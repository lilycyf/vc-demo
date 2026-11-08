"""Optional grouped out-of-fold composition, not a mandatory model topology."""
from __future__ import annotations

import inspect
from typing import Callable, Any
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold


def fit_estimator(model, x, y, groups):
    if "groups" in inspect.signature(model.fit).parameters:
        model.fit(x, y, groups=groups)
    else:
        model.fit(x, y)
    return model


def _arrays(x, y, groups, splits):
    x, y, groups = np.asarray(x), np.asarray(y), np.asarray(groups)
    if y.ndim != 1 or len(x) != len(y) or len(groups) != len(y):
        raise ValueError("Regression composition requires aligned X, one-dimensional y, and groups")
    if splits < 2 or len(np.unique(groups)) < splits:
        raise ValueError("Insufficient independent groups for declared cross-fitting; do not silently use in-sample residuals")
    if not np.isfinite(y).all():
        raise ValueError("Targets must be finite")
    return x, y, groups


def crossfit_predictions(factory: Callable, x, y, groups, splits=3):
    x, y, groups = _arrays(x, y, groups, splits)
    predictions = np.full(len(y), np.nan)
    records = []
    retained = []
    for train, valid in GroupKFold(splits).split(x, y, groups):
        model = factory()
        if any(model is prior for prior in retained):
            raise ValueError("Estimator factory reused fitted state across folds")
        retained.append(model)
        fit_estimator(model, x[train], y[train], groups[train])
        values = np.asarray(model.predict(x[valid]))
        if values.shape != (len(valid),) or not np.isfinite(values).all():
            raise ValueError("Invalid cross-fitted predictions")
        predictions[valid] = values
        records.append({"train_groups": sorted(map(str, np.unique(groups[train]))),
                        "validation_groups": sorted(map(str, np.unique(groups[valid]))),
                        "validation_indices": valid.tolist()})
    if not np.isfinite(predictions).all():
        raise ValueError("Incomplete OOF predictions")
    return predictions, records


class ResidualCore:
    """Fit the mutation on parent OOF errors within the supplied training set."""
    def __init__(self, parent_factory: Callable, mutation_factory: Callable, splits=3):
        self.parent_factory = parent_factory
        self.mutation_factory = mutation_factory
        self.splits = splits

    def fit(self, x, y, groups):
        x, y, groups = _arrays(x, y, groups, self.splits)
        parent_oof, self.fold_audit_ = crossfit_predictions(self.parent_factory, x, y, groups, self.splits)
        self.parent_ = fit_estimator(self.parent_factory(), x, y, groups)
        self.mutation_ = fit_estimator(self.mutation_factory(), x, y - parent_oof, groups)
        self.training_groups_ = sorted(map(str, np.unique(groups)))
        return self

    def predict_parts(self, x):
        return np.column_stack([self.parent_.predict(x), self.mutation_.predict(x)])

    def predict(self, x):
        return self.predict_parts(x).sum(axis=1)


class CrossFittedResidualRegressor:
    """Nested grouped cross-fitting learns the combination, never a fixed .25."""
    def __init__(self, parent_factory: Callable, mutation_factory: Callable, splits=3,
                 weight_factory: Callable | None = None):
        self.parent_factory = parent_factory
        self.mutation_factory = mutation_factory
        self.splits = splits
        self.weight_factory = weight_factory or (lambda: Ridge(alpha=1.0))

    def fit(self, x, y, groups):
        x, y, groups = _arrays(x, y, groups, self.splits)
        design = np.full((len(y), 2), np.nan)
        self.meta_fold_audit_ = []
        for train, valid in GroupKFold(self.splits).split(x, y, groups):
            if len(np.unique(groups[train])) < self.splits:
                raise ValueError("Nested residual composition needs more training groups; change the declared policy or choose replacement")
            core = ResidualCore(self.parent_factory, self.mutation_factory, self.splits)
            core.fit(x[train], y[train], groups[train])
            design[valid] = core.predict_parts(x[valid])
            self.meta_fold_audit_.append({"train_groups": core.training_groups_,
                "validation_groups": sorted(map(str, np.unique(groups[valid]))), "inner_folds": core.fold_audit_})
        self.combiner_ = fit_estimator(self.weight_factory(), design, y, groups)
        self.core_ = ResidualCore(self.parent_factory, self.mutation_factory, self.splits).fit(x, y, groups)
        self.oof_design_ = design
        self.training_groups_ = sorted(map(str, np.unique(groups)))
        return self

    def predict(self, x):
        return self.combiner_.predict(self.core_.predict_parts(np.asarray(x)))


class CrossFittedStackingRegressor:
    def __init__(self, factories: list[Callable], splits=3, meta_factory: Callable | None = None):
        if not factories:
            raise ValueError("At least one estimator is required")
        self.factories = factories
        self.splits = splits
        self.meta_factory = meta_factory or (lambda: Ridge(alpha=1.0))

    def fit(self, x, y, groups):
        x, y, groups = _arrays(x, y, groups, self.splits)
        columns, self.fold_audit_ = [], []
        for factory in self.factories:
            column, record = crossfit_predictions(factory, x, y, groups, self.splits)
            columns.append(column)
            self.fold_audit_.append(record)
        self.oof_design_ = np.column_stack(columns)
        self.meta_ = fit_estimator(self.meta_factory(), self.oof_design_, y, groups)
        self.models_ = [fit_estimator(factory(), x, y, groups) for factory in self.factories]
        self.training_groups_ = sorted(map(str, np.unique(groups)))
        return self

    def predict(self, x):
        return self.meta_.predict(np.column_stack([model.predict(x) for model in self.models_]))
