"""Explicit parent-plus-mutation composition for future registered searches."""
from __future__ import annotations

import copy

import numpy as np

from vc_demo.t47d_lineage.models import Candidate


class ParentResidualCandidate:
    def __init__(self, config):
        self.config = copy.deepcopy(config)
        self.parent = build_candidate(config["parent_config"])
        mutation = {k: v for k, v in config.items() if k not in {"parent_config", "composition", "residual_weight"}}
        self.mutation = Candidate(mutation)
        self.weight = float(config.get("residual_weight", .25))

    def fit(self, bundle, idx, seed=3):
        self.parent.fit(bundle, idx, seed)
        target = bundle["meta"].iloc[idx].label.to_numpy()
        parent_prediction = self.parent.predict(bundle, idx)
        residual_bundle = dict(bundle)
        residual_bundle["meta"] = bundle["meta"].copy(deep=True)
        column = residual_bundle["meta"].columns.get_loc("label")
        residual_bundle["meta"].iloc[idx, column] = target - parent_prediction
        self.mutation.fit(residual_bundle, idx, seed)
        return self

    def predict(self, bundle, idx):
        return self.parent.predict(bundle, idx) + self.weight * self.mutation.predict(bundle, idx)


def build_candidate(config):
    if "parent_config" in config:
        if config.get("composition") != "parent_plus_residual":
            raise ValueError("Parent-bearing config must explicitly declare residual composition")
        return ParentResidualCandidate(config)
    return Candidate(config)


def move_to_cpu(model):
    if isinstance(model, ParentResidualCandidate):
        move_to_cpu(model.parent)
        move_to_cpu(model.mutation)
    elif hasattr(model, "network"):
        import torch
        model.network = model.network.cpu()
        model.device = torch.device("cpu")
    return model


def inherit_mutation(parent, mutation):
    base = {k: v for k, v in parent.items() if k not in {"parent_config", "composition", "residual_weight"}}
    child = {**base, **copy.deepcopy(mutation)}
    # A temporal mutation may consume early observations, but never deletes the
    # preserved parent's own baseline-only or artifact-backed representation.
    if mutation["model"] in {"gru", "transformer", "gated_residual"}:
        child["baseline_only"] = False
    child.update(parent_config=copy.deepcopy(parent), composition="parent_plus_residual", residual_weight=.25)
    return child
