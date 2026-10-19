"""Origin-destination migrant shares for every country pair, balanced to WPP net migration.

Gravity prior: flow(o -> d) proportional to distance^-gamma x (1 + b_adj if land neighbours)
x (1 + b_cont if same continent). Arrivals per destination (positive WPP net) and departures per
origin (negative net) are then matched exactly by Sinkhorn balancing, so the matrix is consistent
with WPP totals. The result is a MODELLED matrix: it reflects geography, not observed bilateral flows.
Replace it with a real bilateral table whenever one is available.
"""
from __future__ import annotations

import numpy as np


def gravity_kernel(dist_km, adj, same_continent, gamma=1.0, b_adj=1.0, b_cont=0.5, min_km=100.0):
    """Positive kernel [dest, origin] with zero diagonal."""
    d = np.maximum(np.asarray(dist_km, float), min_km)
    K = d ** (-gamma) * (1.0 + b_adj * np.asarray(adj, float)) * (1.0 + b_cont * np.asarray(same_continent, float))
    np.fill_diagonal(K, 0.0)
    return K


def balanced_od(net_persons, K, iters=2000, tol=1e-10):
    """Sinkhorn balancing of the kernel to arrivals (positive nets) and departures (negative nets).

    Departures are scaled so their total equals total arrivals (WPP nets do not sum to zero).
    Returns (flows [dest, origin], share [dest, origin] rows summing to 1 where a destination has
    arrivals, and the balanced arrivals per destination)."""
    net = np.asarray(net_persons, float)
    A = np.maximum(net, 0.0)
    D = np.maximum(-net, 0.0)
    n = len(net)
    if A.sum() <= 0 or D.sum() <= 0:
        return np.zeros((n, n)), np.zeros((n, n)), A * 0
    D = D * (A.sum() / D.sum())
    Kd = K * (A > 0)[:, None] * (D > 0)[None, :]
    u = np.ones(n)
    v = np.ones(n)
    for _ in range(iters):
        Kv = Kd @ v
        u = np.where(Kv > 0, A / np.maximum(Kv, 1e-300), 0.0)
        Ku = Kd.T @ u
        v_new = np.where(Ku > 0, D / np.maximum(Ku, 1e-300), 0.0)
        change = np.max(np.abs(v_new - v) / np.maximum(v, 1e-300))
        v = v_new
        if change < tol:
            break
    flows = u[:, None] * Kd * v[None, :]
    arrivals = flows.sum(axis=1)
    share = flows / np.maximum(arrivals[:, None], 1e-300)
    return flows, share, arrivals
