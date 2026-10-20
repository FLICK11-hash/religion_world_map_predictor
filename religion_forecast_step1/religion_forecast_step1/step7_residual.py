"""Step 7 residual learner: what the mechanisms (births, deaths, migration, switching) leave unexplained.

A ridge regression (numpy, closed form) predicts the residual share change over a decade from
conditions at the start of the decade. Targets are zero-sum across the eight religions, and a
linear model fitted to zero-sum targets gives zero-sum predictions, so adding it keeps every
country's shares summing to one (shares are then clipped at zero and renormalised).
It is trained only on windows that end before the window it predicts (forward chaining), and its
weight is chosen the same way; a weight of 0 means it is not used.
"""
from __future__ import annotations

import numpy as np

import step7_engine as E

K = E.K


def features(ctx, w, prev_resid=None):
    """Feature matrix [n, F] at the start of window w."""
    t = w['start']
    e0, tfr = ctx.wpp_at('e0', t), ctx.wpp_at('tfr', t)
    e0p = ctx.wpp_at('e0', max(t - 10, ctx.years_wpp[0]))
    tfrp = ctx.wpp_at('tfr', max(t - 10, ctx.years_wpp[0]))
    cont = np.array([[1.0 if c == k else 0.0 for k in ctx.continents] for c in ctx.continent])
    prev = np.zeros((ctx.n, K)) if prev_resid is None else np.nan_to_num(prev_resid)
    X = np.column_stack([w['s0'], (e0 - 70) / 10, np.log(tfr), (e0 - e0p) / 5, np.log(tfr / tfrp), cont, prev])
    return X


class Ridge:
    def __init__(self, alpha=10.0):
        self.alpha = alpha

    def fit(self, X, Y, wt=None):
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Z = (X - self.mu) / self.sd
        wt = np.ones(len(X)) if wt is None else wt
        Zw = Z * np.sqrt(wt)[:, None]
        Yw = (Y - (Y * wt[:, None]).sum(0) / wt.sum()) * np.sqrt(wt)[:, None]
        self.ybar = (Y * wt[:, None]).sum(0) / wt.sum()
        self.B = np.linalg.solve(Zw.T @ Zw + self.alpha * np.eye(Z.shape[1]), Zw.T @ Yw)
        return self

    def predict(self, X):
        return self.ybar + ((X - self.mu) / self.sd) @ self.B


def apply(pred, delta):
    """Add a zero-sum change to predicted shares, then project back to the simplex."""
    s = np.clip(pred + delta, 0.0, None)
    return s / np.maximum(s.sum(1, keepdims=True), 1e-300)
