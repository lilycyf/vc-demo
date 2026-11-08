"""Development-only paired evidence and explicit research-budget scheduling."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable, Any
import numpy as np


def paired_feedback(y, candidate, reference, groups, scorer: Callable, *, strata=None,
                    direction="maximize", draws=500, seed=0, evidence_phase="development"):
    if evidence_phase != "development":
        raise ValueError("Only development evidence may enter scientific feedback")
    if direction not in {"maximize", "minimize"}:
        raise ValueError("Metric direction must be explicit")
    y, candidate, reference, groups = map(np.asarray, (y, candidate, reference, groups))
    if not (len(y) == len(candidate) == len(reference) == len(groups)) or not len(y):
        raise ValueError("Paired predictions and clone/sample groups must align")
    if not all(np.isfinite(a).all() for a in (y, candidate, reference)):
        raise ValueError("Nonfinite paired evidence")
    sign = 1 if direction == "maximize" else -1
    delta = lambda ids: sign * (float(scorer(y[ids], candidate[ids])) - float(scorer(y[ids], reference[ids])))
    ids = np.arange(len(y));observed = delta(ids)
    if not np.isfinite(observed):
        raise ValueError("Undefined primary metric")
    unique = np.unique(groups);rng = np.random.default_rng(seed);boot = []
    for _ in range(draws):
        sampled = np.concatenate([np.flatnonzero(groups == g) for g in rng.choice(unique, len(unique), replace=True)])
        value = delta(sampled)
        if np.isfinite(value):boot.append(value)
    split = {}
    if strata is not None:
        strata = np.asarray(strata)
        if len(strata) != len(y):raise ValueError("Strata do not align")
        for value in np.unique(strata):
            loc = np.flatnonzero(strata == value);score = delta(loc)
            split[str(value)] = {"n": len(loc), "groups": len(np.unique(groups[loc])),
                "delta": float(score) if np.isfinite(score) else None}
    ci = np.quantile(boot, [.025, .975]).tolist() if boot else None
    return {"format":"vc_demo_paired_development_feedback.v1", "evidence_phase":evidence_phase,
        "paired_delta":observed,"delta_ci95":ci,"independent_groups":len(unique),
        "rows":len(y),"bootstrap_unit":"whole group blocks","valid_bootstrap_draws":len(boot),
        "strata":split,"residual_summary":{"candidate_mae":float(np.abs(y-candidate).mean()),
        "reference_mae":float(np.abs(y-reference).mean())},
        "promotion_supported":bool(len(unique)>=2 and ci and ci[0]>0),
        "selection_optimism_caveat":"Development winner and adaptive reuse are not independent confirmation"}


@dataclass
class ResearchBudget:
    coverage_limit: int = 0
    optimization_limit: int = 40
    confirmation_limit: int = 2
    coverage_used: int = 0
    optimization_used: int = 0
    confirmation_used: int = 0
    confirmation_open: bool = False

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name != "confirmation_open" and (not isinstance(value, int) or value < 0):
                raise ValueError("Budgets must be nonnegative integer counts")

    def consume(self, phase):
        if phase not in {"coverage", "optimization", "confirmation"}:raise ValueError("Unknown research phase")
        if self.confirmation_open and phase != "confirmation":raise ValueError("Search closed after confirmation")
        used, limit = phase+"_used", phase+"_limit"
        if getattr(self, used)>=getattr(self, limit):raise ValueError(phase+" budget exhausted")
        if phase=="confirmation":self.confirmation_open=True
        setattr(self, used,getattr(self,used)+1)

    def to_dict(self):return asdict(self)


def rank_hypotheses(proposals: list[dict[str, Any]], *, phase="optimization"):
    if phase not in {"coverage", "optimization"}:raise ValueError("Confirmation is not a proposal search phase")
    scored=[]
    for proposal in proposals:
        if any(k in proposal for k in ("test_score", "test_metrics", "test_delta")):
            raise ValueError("Test evidence cannot rank proposals")
        evidence=proposal.get("development_evidence",{})
        if evidence and evidence.get("evidence_phase")!="development":raise ValueError("Untrusted evidence phase")
        gain=float(evidence.get("paired_delta",proposal.get("expected_gain",0.0)))
        ci=evidence.get("delta_ci95")
        uncertainty=(ci[1]-ci[0])/2 if ci else float(proposal.get("uncertainty",1.0))
        cost=float(proposal.get("estimated_cost",1.0))
        if cost<=0 or not np.isfinite([gain,uncertainty,cost]).all() or uncertainty<0:
            raise ValueError("Invalid scientific priority inputs")
        score=(gain+uncertainty)/np.sqrt(cost)
        if phase=="coverage":score=float(proposal.get("coverage_priority",0.0))
        scored.append({**proposal,"scientific_priority":float(score),"budget_phase":phase,
            "priority_basis":"development gain/uncertainty/cost; artifact presence is a later acquisition gate"})
    return sorted(scored,key=lambda p:(-p["scientific_priority"],str(p.get("id",""))))
