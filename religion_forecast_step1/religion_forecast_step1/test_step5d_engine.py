"""Unit tests for step5d_engine on synthetic data (numpy only): python test_step5d_engine.py"""
import numpy as np
import step5d_engine as E

rng = np.random.default_rng(1)
K = 8
CATS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 'Folk_Traditional', 'Other', 'Unaffiliated']


def synthetic(n=12):
    shares = rng.dirichlet(np.ones(K) * 0.7, n)
    med = rng.uniform(18, 45, n)
    pop = rng.uniform(1e6, 1e8, n)
    return shares, med, pop


def dem(pop, tfr=2.1, mig=None):
    n = len(pop)
    return dict(tfr=np.full(n, tfr) if np.isscalar(tfr) else tfr, wpp_population=pop.copy(),
                net_migrations=np.zeros(n) if mig is None else mig)


def engine(**kw):
    p = dict(phi=0.5, psi=0.5, Hf=50.0, e0=72.0, lam=0.4, eps=None)
    p.update(kw)
    return E.Engine(np.ones(K), np.zeros(K), np.full(12, -1), p)


# 1. life table: e0 recovered, survival ratios in (0,1)
for e0 in (60, 72, 80):
    s, sl, sb, S = E.life_table(e0)
    assert abs((S * 0.25).sum() - e0) < 0.2, e0
    assert (s > 0).all() and (s < 1).all() and 0 < sl < 1 and 0 < sb < 1

# 2. pyramid hits requested median
for m in (16, 22, 30, 38, 46):
    got = E.median_age_of(E.pyramid_for_median(np.array([m])))[0]
    assert abs(got - m) < 0.4, (m, got)

# 3. initial population: totals, shares and national median reproduced
shares, med, pop = synthetic()
off = np.array([0, -6, -2, 6, 8, 0, 2, 6.0])
P = E.initial_population(pop, shares, med, off)
assert np.allclose(P.sum((1, 2)), pop) and np.allclose(E.shares_of(P), shares, atol=1e-9)
assert np.abs(E.median_age_of(P.sum(1)) - med).max() < 0.6

# 4. identical groups, no migration: shares are exactly preserved for any TFR
same = np.tile(rng.dirichlet(np.ones(K)), (12, 1))
P0 = E.initial_population(pop, same, med, np.zeros(K))
e = engine()
d0 = dem(pop, 1.6)
P1, _ = e.step(P0, d0, dem(pop * 1.01, 1.6), 0.0)
assert np.allclose(E.shares_of(P1), same, atol=1e-9)

# 5. population always rescaled to the target
target = pop * 1.07
P2, lg = e.step(P0, d0, dem(target, 1.6), 0.0)
assert np.allclose(P2.sum((1, 2)), target)

# 6. higher-fertility group gains share, with same age structure and no migration
rel = np.ones(K); rel[1] = 1.5
e2 = E.Engine(rel, np.zeros(K), np.full(12, -1), dict(phi=1.0, psi=0.0, Hf=1e9, e0=72.0, lam=0.4, eps=None))
share_a = np.tile(np.array([.5, .3, .05, .05, .02, .03, .02, .03]), (12, 1))
Pa = E.initial_population(pop, share_a, np.full(12, 28.0), np.zeros(K))
Pn, _ = e2.step(Pa, dem(pop, 2.5), dem(pop, 2.5), 0.0)
assert (E.shares_of(Pn)[:, 1] > share_a[:, 1]).all() and (E.shares_of(Pn)[:, 0] < share_a[:, 0]).all()
# ... and the national aggregate births equal the equal-gap case (TFR identity)
e3 = E.Engine(np.ones(K), np.zeros(K), np.full(12, -1), dict(phi=1.0, psi=0.0, Hf=1e9, e0=72.0, lam=0.4, eps=None))
b2 = e2.project(Pa, dem(pop, 2.5)['tfr'], e2.rel_tfr(0, 12))[:, :, 0].sum(1)
b3 = e3.project(Pa, dem(pop, 2.5)['tfr'], e3.rel_tfr(0, 12))[:, :, 0].sum(1)
assert np.allclose(b2, b3, rtol=1e-9)

# 7. fertility gaps converge: gap at t=300 much smaller than at t=0
e4 = engine(Hf=40.0)
e4.rel_within = np.linspace(.7, 1.4, K)
g0 = np.abs(e4.rel_tfr(0, 12) - 1).max(); g300 = np.abs(e4.rel_tfr(300, 12) - 1).max()
assert g300 < 0.01 * g0 + 1e-3 and g0 > .3

# 7b. additive gaps: bigger ratio where national TFR is low, smaller where high; TFR identity holds
e5 = engine(w_add=1.0, world_tfr=2.5, phi=1.0)
e5.rel_within = np.full(K, 1.0); e5.rel_within[1] = 1.24
lo = e5.rel_tfr(0, 12, np.full(12, 1.4))[0, 1]; hi = e5.rel_tfr(0, 12, np.full(12, 5.0))[0, 1]
assert lo > 1.24 > hi > 1.0, (lo, hi)
em = engine(w_add=0.0); em.rel_within = e5.rel_within.copy()
assert np.allclose(em.rel_tfr(0, 12, np.full(12, 1.4)), em.rel_tfr(0, 12))
bb = e5.project(P0, np.full(12, 1.4), e5.rel_tfr(0, 12, np.full(12, 1.4)))[:, :, 0].sum(1)
b0 = em.project(P0, np.full(12, 1.4), np.ones((12, K)))[:, :, 0].sum(1)
assert np.allclose(bb, b0, rtol=1e-9)      # national births still equal the WPP-implied births

# 8. migration: totals added match inflow, removal matches outflow, groups non-negative
net = np.zeros(12); net[:3] = -2e5; net[3:6] = 1e5
Pm = e.migrate(P0, net)
assert (Pm >= -1e-9).all()
assert abs((Pm.sum() - P0.sum()) - (5 * 1e5 * 3 - 5 * 2e5 * 3)) < 1e-3 * P0.sum() * 0 + 1.0
# arrivals use the origin religious mix: emigrants are all one group -> immigrants too
one = np.zeros((12, K)); one[:, 0] = 1.0; one[3:6, :] = 0; one[3:6, 0] = 1
mix_in = np.zeros((12, K)); mix_in[:3, 1] = 1.0; mix_in[3:, 0] = 1.0   # origins Muslim, others Christian
Pone = E.initial_population(pop, mix_in, np.full(12, 28.0), np.zeros(K))
Pm2 = e.migrate(Pone, net)
gain = E.shares_of(Pm2)[3:6, 1]
expected = 5e5 / (pop[3:6] + 5e5)      # all 5-year arrivals are Muslim, none lived there before
assert np.allclose(gain, expected, rtol=1e-6), (gain, expected)

# 8b. neighbour pool: with lam=0, lam_nb=1 arrivals mirror the emigrants of land neighbours
adj = np.zeros((12, 12)); adj[3, 0] = adj[0, 3] = 1; adj[4, 1] = adj[1, 4] = 1
mix2 = np.zeros((12, K)); mix2[:, 0] = 1; mix2[0, 0] = 0; mix2[0, 1] = 1      # country 0: Muslim; country 1: Hindu below
mix2[1, 0] = 0; mix2[1, 2] = 1
Pnb = E.initial_population(pop, mix2, np.full(12, 28.0), np.zeros(K))
net2 = np.zeros(12); net2[0] = net2[1] = -1e5; net2[3] = net2[4] = 5e4
enb = E.Engine(np.ones(K), np.zeros(K), np.full(12, 0), dict(phi=0, psi=0, Hf=50., e0=72., lam=0.0, lam_nb=1.0, eps=None), adj)
Pm3 = enb.migrate(Pnb, net2)
arr3 = (Pm3 - Pnb).sum(2)
assert arr3[3, 1] > 0 and abs(arr3[3, 0]) < 1e-6 and arr3[4, 2] > 0 and abs(arr3[4, 1]) < 1e-6   # 3 gets Muslims, 4 gets Hindus
# conservation of arrivals: total added to a receiver equals its 5-year net inflow
assert abs(arr3[3].sum() - 5 * 5e4) < 1e-3 and abs(arr3[4].sum() - 5 * 5e4) < 1e-3
# no neighbours with emigrants -> falls back to the other pools (still adds the full inflow)
net3 = np.zeros(12); net3[0] = -1e5; net3[7] = 5e4
Pm4 = enb.migrate(Pnb, net3)
assert abs((Pm4 - Pnb).sum(2)[7].sum() - 5 * 5e4) < 1e-3

# 9. switching conserves persons and moves the requested share
rho = np.zeros((12, K)); rho[:, 0] = -0.02; rho[:, 7] = 0.02
Ps = e.switch(P0, rho, 1.0)
assert np.allclose(Ps.sum((1, 2)), P0.sum((1, 2)))
assert (Ps >= -1e-9).all()
d = E.shares_of(Ps) - E.shares_of(P0)
ok = (E.shares_of(P0)[:, 0] > 0.1)
assert np.allclose(d[ok, 7], 0.02, atol=1e-6) and np.allclose(d[ok, 0], -0.02, atol=1e-6)

# 10. a stationary-ish population stays near stationary at TFR 2.1, e0 72
Pst = E.initial_population(np.full(12, 1e7), same, np.full(12, 38.0), np.zeros(K))
growth = []
Pt = Pst
for _ in range(10):
    Q = e.project(Pt, np.full(12, 2.1), e.rel_tfr(0, 12))
    growth.append(Q.sum() / Pt.sum()); Pt = Q
assert 0.9 < np.mean(growth) < 1.1, growth

# 11. calibrate_switching: zero-sum, capped, Folk/Other combined, invalid rows zero
obs = rng.dirichlet(np.ones(K), 12); pred = rng.dirichlet(np.ones(K), 12)
r = E.calibrate_switching(obs, pred, CATS, valid=np.arange(12) % 2 == 0)
assert np.allclose(r.sum(1), 0, atol=1e-12) and (0.5 * np.abs(r).sum(1) <= 0.10 + 1e-12).all()
assert (r[1::2] == 0).all()
print('PASS: step5d_engine unit tests (11 groups of checks)')
