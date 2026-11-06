from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse

from vc_demo.t47d_lineage.data import make_split
from vc_demo.t47d_lineage.models import Candidate, View


def bundle():
    rng = np.random.default_rng(3)
    return {"expression": rng.normal(size=(24, 3, 20)).astype("float32"),
            "pathway": rng.normal(size=(24, 3, 6)).astype("float32"),
            "aux": rng.normal(size=(24, 9)).astype("float32"),
            "meta": pd.DataFrame({"label": rng.normal(size=24)})}


def test_clone_group_splits_never_overlap():
    split = make_split([f"clone_{i}" for i in range(46)])
    assert len(split["folds"]) == 15
    for fold in split["folds"]:
        assert not set(fold["train_clones"]) & set(fold["validation_clones"])
        assert not set(fold["train_clones"]) & set(split["test_clones"])
        assert not set(fold["validation_clones"]) & set(split["test_clones"])


def test_heldout_features_cannot_change_fitted_gene_selection():
    data = bundle()
    cfg = {"model": "ridge", "representation": "expression", "genes": 8}
    train = np.arange(16)
    first = View(cfg).fit(data, train)
    data["expression"][16:] *= 100000
    second = View(cfg).fit(data, train)
    np.testing.assert_array_equal(first.genes, second.genes)
    np.testing.assert_allclose(first.scaler.mean_, second.scaler.mean_)


def test_baseline_ablation_cannot_consume_early_timepoints():
    data = bundle()
    cfg = {"model": "ridge", "representation": "expression", "baseline_only": True, "genes": 8}
    view = View(cfg).fit(data, np.arange(16))
    one, aux = view.transform(data, np.arange(16, 24))
    data["expression"][16:, 1:] += 10000
    two, aux2 = view.transform(data, np.arange(16, 24))
    np.testing.assert_allclose(one, two)
    data["expression"][:16, 1:] += 10000
    refit = View(cfg).fit(data, np.arange(16))
    np.testing.assert_array_equal(view.genes, refit.genes)
    np.testing.assert_allclose(view.scaler.mean_, refit.scaler.mean_)


def test_real_temporal_model_forward_backward_fit_predict():
    data = bundle()
    for family in ("gru", "transformer", "gated_residual"):
        cfg = {"model": family, "representation": "both", "genes": 8, "epochs": 2}
        candidate = Candidate(cfg).fit(data, np.arange(16), seed=3)
        pred = candidate.predict(data, np.arange(16, 24))
        assert pred.shape == (8,)
        assert np.isfinite(pred).all()
        assert len(candidate.losses) == 2
