"""Checks on real WRP/WPP/Natural Earth data and on the origin-destination and hindcast code.
Run: python test_step5e.py   (about 30 seconds; needs data/raw)"""
from pathlib import Path

import numpy as np

import migration_od as mod
import step5d_engine as eng
import step5e_wrp_hindcast as S
import wrp_history as H

RAW = Path("data/raw")
wrp, wpp, geo, nbrs = H.load_all(RAW, RAW / "ne_50m_admin_0_countries.zip")

# 1. population check: WRP and WPP agree closely in 2010 for most countries
r2010 = wrp[wrp.year.eq(2010) & wrp.country_id.notna()].pop_ratio
assert 0.95 <= r2010.median() <= 1.05, r2010.median()
assert wrp.use.sum() > 1500

# 2. shares: every used country-year sums to one and is non-negative
cols = [c for c in wrp.columns if c.startswith("share_")]
u = wrp[wrp.use]
assert np.allclose(u[cols].sum(axis=1), 1, atol=1e-9) and (u[cols] >= 0).all().all()

# 3. geography: centroids in the right place; known land borders detected
assert abs(geo.loc["USA", "lat"] - 39) < 8 and abs(geo.loc["USA", "lon"] + 98) < 15
assert "MEX" in nbrs["USA"] and "DEU" in nbrs["FRA"] and "PAK" not in nbrs["USA"]

# 4. gravity matrix: exact WPP marginals, and a land neighbour gets more than a distant country
rng = np.random.default_rng(0)
n = 10
dist = rng.uniform(300, 9000, (n, n))
dist = (dist + dist.T) / 2
adj = np.zeros((n, n))
adj[0, 1] = adj[1, 0] = 1.0
same = np.ones((n, n))
net = np.array([3e5, -2e5, -1e5, 2e5, -4e5, 1e5, 0.0, -1e5, 2e5, -1e5])
flows, share, arrivals = mod.balanced_od(net, mod.gravity_kernel(dist, adj, same))
assert np.allclose(arrivals, np.maximum(net, 0), rtol=1e-6, atol=1e-3)
assert np.allclose(flows.sum(0), np.maximum(-net, 0) * (np.maximum(net, 0).sum() / np.maximum(-net, 0).sum()), rtol=1e-6)
no_border = mod.balanced_od(net, mod.gravity_kernel(dist, adj * 0, same))[1]
assert share[0, 1] > no_border[0, 1] > 0   # a land border raises the neighbour's share of arrivals

# 5. hindcast: with no within-country gap, no age offset and no migration, the model equals persistence
inp = S.decade_inputs(1990, wrp, wpp, geo, nbrs)
rel, off = S.load_prior()
flat = dict(phi=0.0, psi=0.0, w_add=0.0, Hf=50.0, gamma=1.0, b_adj=1.0)
assert np.allclose(S.run(inp, flat, "demo", rel, off), inp["sh0"], atol=1e-9)

# 6. hindcast scores: persistence has a popw error that is positive and finite
score = S.score(inp["sh0"], inp)
assert 0 < score["popw_tv_pp"] < 50 and np.isfinite(score["popw_tv_pp"])

# 7. group TFR: share-weighted average equals the national TFR where shares exist
gt = S.group_tfr_table(wpp, rel, {"central": 0.5}, 0.0,
                       {r.country_id: np.array([getattr(r, f"share_{c}") for c in S.CATS])
                        for r in wrp[wrp.use & wrp.year.eq(2010)].itertuples()})
sample = gt[gt.normalised].drop_duplicates("country_id").country_id.head(20)
for cid in sample:
    shares = {r.country_id: np.array([getattr(r, f"share_{c}") for c in S.CATS])
              for r in wrp[wrp.use & wrp.year.eq(2010) & wrp.country_id.eq(cid)].itertuples()}[cid]
    d = gt[(gt.country_id == cid)].sort_values("religion")
    order = [S.CATS.index(c) for c in sorted(S.CATS)]
    weighted = np.sum(shares[order] * d.group_tfr.to_numpy())
    assert abs(weighted - d.tfr_national.iloc[0]) < 1e-6, (cid, weighted)
print("PASS: step5e checks (population match, shares, geography, gravity, hindcast identity, group TFR)")
