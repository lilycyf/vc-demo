from __future__ import annotations

import numpy as np
import pandas as pd
import runpy
from scipy import sparse

from vc_demo.t47d_lineage.data import make_split
from vc_demo.t47d_lineage.models import Candidate, View
from vc_demo.t47d_lineage.composition import build_candidate, inherit_mutation


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


def test_parent_preservation_and_no_label_mutation():
    data = bundle()
    original_labels = data["meta"].label.copy()
    parent = {"model": "ridge", "representation": "pathway", "baseline_only": True, "alpha": 100.}
    config = inherit_mutation(parent, {"model": "gru", "representation": "expression", "genes": 8, "epochs": 2})
    assert config["parent_config"] == parent
    assert config["baseline_only"] is False
    config["residual_weight"] = 0.
    fitted = build_candidate(config).fit(data, np.arange(16), seed=3)
    np.testing.assert_allclose(fitted.predict(data, np.arange(16,24)), fitted.parent.predict(data, np.arange(16,24)))
    pd.testing.assert_series_equal(original_labels, data["meta"].label)


def test_node_local_program_is_the_execution_authority(tmp_path):
    namespace = runpy.run_path("scripts/t47d/run.py")
    path = tmp_path / "model.py"
    path.write_text("class NodeLocal: pass\ndef build_model(config): return NodeLocal()\n")
    factory = namespace["load_program"](path)
    assert factory({}).__class__.__name__ == "NodeLocal"


def test_cv_calls_selected_node_factory_for_every_fold():
    namespace = runpy.run_path("scripts/t47d/run.py")
    data = bundle()
    data["meta"]["clone_id"] = np.repeat([f"c{i}" for i in range(8)],3)
    data["splits"] = make_split(data["meta"].clone_id.unique())
    data["meta"]["split"] = np.where(data["meta"].clone_id.isin(data["splits"]["test_clones"]),"test","development")
    calls = []
    def factory(config):
        calls.append(dict(config))
        return Candidate(config)
    result = namespace["cross_validate"](data,{"model":"ridge","representation":"expression","genes":8},build_model=factory)
    assert len(calls)==15
    assert result["formal_fold_fits"]==15
