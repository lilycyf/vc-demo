"""Exact log-normal boundary at t=0, avoiding autograd's 0 * infinity derivative."""
from autograd import numpy as anp
from lifelines import LogNormalAFTFitter


class IntervalLogNormalAFT(LogNormalAFTFitter):
    def _cumulative_hazard(self, params, time, covariates):
        # Left-censored (0, first observation] is real, not an epsilon-duration event.
        positive = time > 0
        safe_time = anp.where(positive, time, 1.)
        value = super()._cumulative_hazard(params, safe_time, covariates)
        return anp.where(positive, value, 0.)
