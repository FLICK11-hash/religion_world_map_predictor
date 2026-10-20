"""Step 7 tests. Run:  .\\.venv\\Scripts\\python.exe test_step7.py   (or: python -m pytest test_step7.py)

Unit tests use synthetic data (no files). Integration tests use the real inputs and are skipped when
data/raw/WPP2024_Demographic_Indicators_Medium.csv.gz or the start state is missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

import step7_engine as E
import step7_migration as MG
import step7_residual as RL
import step7_switching as SW

ROOT = Path(__file__).resolve().parent


def _inputs(n, rng, switching=True):
    s, so, sb = E.life_tables(np.full(n, 72.0), np.full(n, 0.03))
    inp = dict(tfr=rng.uniform(1.3, 4.5, n), shape=E.asfr_shapes(rng.uniform(25, 32, n)),
               rel=rng.uniform(0.6, 1.6, size=(n, E.K, E.G)), female_share=rng.uniform(0.3, 0.55, size=(n, 7)),
               s=s, s_open=so, s_birth=sb, intensity=np.array([1.0, 0.4, 0.7]), T=None)
    if switching:
        sh = rng.dirichlet(np.ones(E.K), size=n)
        L = SW.lifetime_matrix(rng.uniform(0, .3, (n, 7)), rng.uniform(0, .05, (n, 7)), rng.uniform(0, .2, n), sh)
        inp['T'] = SW.five_year_matrices(L)
    return inp


def _migration_fn(n, rng):
    lat, lon = rng.uniform(-50, 70, n), rng.uniform(-170, 170, n)
    d = np.hypot(lat[:, None] - lat[None, :], lon[:, None] - lon[None, :]) * 111
    Kg = MG.gravity_kernel(d, (d < 900).astype(float), np.zeros((n, n)))

    def fn(Q):
        pop = Q.sum((1, 2, 3))
        net = rng.normal(0, 0.01, n) * pop
        E_o, I_d, _ = MG.margins_from_net(net, pop, 0.001)
        F, *_ = MG.sinkhorn(MG.mixed_kernel(Kg), E_o, I_d)
        emig, immig, _, _ = MG.realise(F, Q, MG.minority_selectivity(E.shares(Q), 0.2), cap=0.5)
        return emig, immig
    return fn


def test_life_table_matches_e0():
    for e0, q5 in ((50, .12), (70, .03), (90, .002)):
        assert abs(E.life_expectancy_of(e0, q5) - e0) < 0.05
        s, so, sb = E.life_tables(np.array([e0]), np.array([q5]))
        assert np.all((s > 0) & (s <= 1)) and 0 < so[0] < 1 and 0 < sb[0] <= 1


def test_asfr_shape_mean():
    for mac in (24.0, 29.0, 33.0):
        sh = E.asfr_shapes(np.array([mac]))[0]
        assert abs(sh.sum() - 1) < 1e-9 and abs((sh * E.AGE_MID[E.F0:E.F1]).sum() - mac) < 0.02


def test_births_reproduce_national_tfr():
    rng = np.random.default_rng(1)
    n = 6
    P = rng.uniform(1e3, 1e5, size=(n, E.K, E.G, E.A))
    inp = _inputs(n, rng, switching=False)
    aged, _ = E.survive(P, inp['s'], inp['s_open'])
    _, born, _, _ = E.births(P, aged, inp['tfr'], inp['shape'], inp['rel'], inp['female_share'], inp['s_birth'])
    W = 0.5 * (P[..., E.F0:E.F1] + aged[..., E.F0:E.F1]).sum((1, 2)) * inp['female_share']
    assert np.allclose(born.sum((1, 2)), inp['tfr'] * (W * inp['shape']).sum(1))


def test_step_accounting_is_exact():
    rng = np.random.default_rng(2)
    n = 8
    P = rng.uniform(1e3, 1e5, size=(n, E.K, E.G, E.A))
    inp = _inputs(n, rng)
    rho = rng.normal(0, 0.002, size=(n, E.K))
    rho -= rho.mean(1, keepdims=True)
    Q, rec = E.step(P, inp, migration_fn=_migration_fn(n, rng), rho=rho, natural_growth=rng.uniform(0.95, 1.1, n))
    dP = Q.sum((2, 3)) - P.sum((2, 3))
    assert np.abs(rec.persons.sum(2) - dP).max() <= 1e-9 * P.sum()
    assert np.abs(rec.share.sum(2) - (E.shares(Q) - E.shares(P))).max() < 1e-12
    w = lambda X: X.sum((0, 2, 3)) / X.sum()
    assert np.abs(rec.world_share.sum(1) - (w(Q) - w(P))).max() < 1e-12
    assert abs(rec.persons[:, :, 4].sum() + rec.persons[:, :, 5].sum()) <= 1e-6 * P.sum()   # migration conserved
    assert (Q >= 0).all() and np.allclose(E.shares(Q).sum(1), 1)


def test_migration_margins_conservation_and_cap():
    rng = np.random.default_rng(3)
    n = 40
    pop = rng.lognormal(15, 1.2, n)
    Kg = MG.gravity_kernel(rng.uniform(100, 15000, (n, n)), np.zeros((n, n)), np.zeros((n, n)))
    E_o, I_d, _ = MG.margins_from_net(rng.normal(0, .02, n) * pop, pop, 0.001)
    F, _, _, err = MG.sinkhorn(MG.mixed_kernel(Kg), E_o, I_d)
    assert err < 1e-8 and np.allclose(F.sum(1) - F.sum(0), E_o - I_d)
    P = rng.uniform(0, 1, (n, E.K, E.G, E.A)) * pop[:, None, None, None] / 200
    F2 = F.copy()
    F2[0] *= 1e5
    emig, immig, _, short = MG.realise(F2, P, None, cap=0.5)
    assert np.abs(emig.sum((0, 2)) - immig.sum(0)).max() <= 1e-9 * emig.sum()
    assert (emig <= 0.5 * P + 1e-9).all() and short > 0


def test_margins_feasible_when_one_country_dominates():
    rng = np.random.default_rng(4)
    n = 12
    pop = rng.uniform(1e5, 1e6, n)
    pop[1] = 50 * pop.sum()                                   # one country is almost the whole world
    net = rng.normal(0, 0.002, n) * pop
    net[1] = 0.02 * pop[1]
    E_o, I_d, info = MG.margins_from_net(net, pop, 0.001)
    assert info['feasibility_cut'] > 0
    assert (E_o + I_d <= E_o.sum() + 1e-6).all()              # nobody needs more arrivals than others send
    pos, neg = np.maximum(net, 0), np.maximum(-net, 0)
    scale = min(pos.sum(), neg.sum()) / max(pos.sum(), neg.sum())
    want = np.where(net > 0, pos * (scale if pos.sum() > neg.sum() else 1), -neg * (scale if neg.sum() > pos.sum() else 1))
    assert np.allclose(I_d - E_o, want)                       # net migration is unchanged by the cut
    Kg = MG.gravity_kernel(rng.uniform(100, 15000, (n, n)), np.zeros((n, n)), np.zeros((n, n)))
    F, _, _, err = MG.sinkhorn(MG.mixed_kernel(Kg), E_o, I_d)
    assert np.isfinite(F).all() and err < 1e-6


def test_soft_margins_follow_network():
    # origin 0 sends almost only to destination 2, which takes few immigrants; destination 3 takes many
    K = np.array([[0, 0, .9, .1], [0, 0, .1, .9], [.5, .5, 0, 0], [.5, .5, 0, 0]], float)
    row = np.array([10.0, 2.0, 1.0, 1.0])
    col = np.array([1.0, 1.0, 2.0, 10.0])
    share = []
    for rho in (1.0, 0.75, 0.5):
        F, _, _, err = MG.sinkhorn(MG.mixed_kernel(K), row, col, rho=rho, rho_col=rho)
        assert (F >= 0).all() and np.isfinite(F).all() and np.isclose(F.sum(1).sum(), F.sum(0).sum())
        if rho == 1.0:
            assert err < 1e-8 and np.allclose(F.sum(1), row) and np.allclose(F.sum(0), col)
        share.append(F[0, 3] / F[:, 3].sum())               # origin 0's share of destination 3's arrivals
    assert share[0] > share[1] > share[2]                   # softer margins: less forced routing


def test_corridor_affinity_conserves():
    rng = np.random.default_rng(9)
    n = 30
    pop = rng.lognormal(15, 1.0, n)
    P = rng.uniform(0, 1, (n, E.K, E.G, E.A)) * pop[:, None, None, None] / 200
    Kg = MG.gravity_kernel(rng.uniform(100, 15000, (n, n)), np.zeros((n, n)), np.zeros((n, n)))
    E_o, I_d, _ = MG.margins_from_net(rng.normal(0, .02, n) * pop, pop, 0.001)
    F, *_ = MG.sinkhorn(MG.mixed_kernel(Kg), E_o, I_d)
    F[0] *= 1e4                                                          # force the cap to bind
    emig, immig, Fu, short = MG.realise_affinity(F, P, lam=0.6, kappa=0.5, cap=0.5)
    assert np.abs(emig.sum((0, 2)) - immig.sum(0)).max() <= 1e-8 * emig.sum()
    assert (emig <= 0.5 * P + 1e-9).all() and short > 0
    assert np.allclose(Fu.sum(1), emig.sum((1, 2, 3)))
    m = MG.corridor_mix(E.shares(P), 0.6, 0.5)
    assert np.allclose(m.sum(2), 1)


def test_switching_matrices():
    rng = np.random.default_rng(4)
    n = 50
    sh = rng.dirichlet(np.ones(E.K), size=n)
    L = SW.lifetime_matrix(rng.uniform(0, .2, (n, 7)), rng.uniform(0, .03, (n, 7)), rng.uniform(0, .15, n), sh)
    assert np.allclose(L.sum(2), 1) and (L >= 0).all()
    T = SW.five_year_matrices(L)
    assert np.allclose(T.sum(3), 1) and (T >= 0).all()
    M = SW.lifetime_from_five_year(T)
    assert np.abs(M[:, :, E.U] - L[:, :, E.U]).max() < 0.01           # disaffiliation reproduced
    assert np.abs(M - L).mean() < 5e-4


def test_linear_effect_matches_simulation():
    rng = np.random.default_rng(5)
    n = 10
    sh = rng.dirichlet(np.ones(E.K) * .7, size=n)
    P = rng.uniform(1e3, 1e5, (n, E.K, E.G, E.A)) * sh[:, :, None, None]
    d, v, a = rng.uniform(0, .1, (n, 7)), rng.uniform(0, .01, (n, 7)), rng.uniform(0, .08, n)
    Tg = E.generation_matrices(SW.five_year_matrices(SW.lifetime_matrix(d, v, a, sh)), [1, .5, .8])
    Q, _, _ = E.switch(P, Tg)
    aged = np.zeros_like(Q)
    aged[..., 1:] = Q[..., :-1]
    aged[..., -1] += Q[..., -1]
    Q, _, _ = E.switch(aged, Tg)
    exact = E.shares(Q) - E.shares(P)
    Bd, Bv, Ba = SW.effect_basis(SW.exposure(P, [1, .5, .8], 2), E.shares(P))
    lin = np.einsum('nj,njk->nk', d, Bd) + np.einsum('nj,njk->nk', v, Bv) + a[:, None] * Ba
    assert np.abs(exact - lin).max() < 5e-4


def test_hierarchy_recovers_truth():
    prior = dict(mu_d={c: .08 for c in E.CATS if c != 'Unaffiliated'}, mu_v={c: .01 for c in E.CATS if c != 'Unaffiliated'},
                 mu_a=.12, beta_a=-.3, tau_e=.4, tau_a=.6, tau_v=.5,
                 grid=dict(delta=[-0.5, 0.5], beta_d=[0.0, 1.2], tau_u=[0.8]))
    rng = np.random.default_rng(6)
    n, D, truth = 120, 5, (0.5, 1.2, 0.8)
    gen = SW.Hierarchy(n, prior, M=1, seed=1)
    net = dict(z=rng.normal(0, 1, (n, D)), Bd=np.zeros((n, D, 7, E.K)), Bv=np.zeros((n, D, 7, E.K)),
               Ba=np.zeros((n, D, E.K)), y=np.zeros((n, D, E.K)), mask=np.ones((n, D), bool), weight=np.ones((n, D)),
               scale=np.full(E.K, 0.004))
    sh = rng.dirichlet(np.ones(E.K), size=n)
    for t in range(D):
        P = rng.uniform(1e4, 1e5, (n, E.K, E.G, E.A)) * sh[:, :, None, None]
        Bd, Bv, Ba = SW.effect_basis(SW.exposure(P), sh)
        net['Bd'][:, t], net['Bv'][:, t], net['Ba'][:, t] = Bd, Bv, Ba
        d, v, a = gen.rates(net['z'][:, t], truth)
        net['y'][:, t] = (np.einsum('nj,njk->nk', d[:, 0], Bd) + np.einsum('nj,njk->nk', v[:, 0], Bv)
                          + a[:, 0, None] * Ba + rng.normal(0, .004, (n, E.K)))
    h = SW.Hierarchy(n, prior, M=128, seed=2).fit(net=net)
    assert h.H == truth


def test_residual_ridge_is_zero_sum():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(200, 6))
    Y = rng.normal(size=(200, E.K))
    Y -= Y.mean(1, keepdims=True)
    pred = RL.Ridge(10).fit(X, Y).predict(rng.normal(size=(30, 6)))
    assert np.abs(pred.sum(1)).max() < 1e-10


def test_long_horizon_stability():
    rng = np.random.default_rng(8)
    n = 12
    P = rng.uniform(1e3, 1e6, (n, E.K, E.G, E.A))
    inp = _inputs(n, rng)
    inp['rel'] = rng.uniform(0.4, 2.5, (n, E.K, E.G))                # extreme fertility gaps
    mig = _migration_fn(n, rng)
    for _ in range(202):                                             # 2020 -> 3030
        P, rec = E.step(P, inp, migration_fn=mig)
        assert np.isfinite(P).all() and (P >= 0).all()
    assert np.allclose(E.shares(P).sum(1), 1)


def _have_data():
    return (ROOT / 'data' / 'raw' / 'WPP2024_Demographic_Indicators_Medium.csv.gz').exists() and (
        (ROOT / 'data' / 'processed' / 'pew_harmonized.csv').exists() or (ROOT / 'results_step5' / 'headline_country_shares.csv').exists())


def test_integration_reproducible_and_exact():
    if not _have_data():
        print('  (skipped: real inputs not present)')
        return
    import step7_estimate as ES
    import step7_model as SM
    ctx = SM.Context(need_wrp=False)
    ctx.selectivity = ES.calibrate_affinity(ctx)
    prior = dict(ctx.a['switching'], grid=dict(delta=[0.0], beta_d=[1.0], tau_u=[0.8]))
    hier = SW.Hierarchy(ctx.n, prior, M=16, seed=3).fit()
    cfg = ctx.a['scenarios']['rising_migration']
    out = []
    for _ in range(2):
        rng = np.random.default_rng(42)
        p = SM.draw_run(ctx, rng, 'rising_migration')
        idx = hier.sample_indices(rng, 1)[:, 0]
        out.append(SM.simulate(ctx, p, cfg, hier, idx, end_year=2050, keep_years=[2020, 2050]))
    a, b = out
    assert np.array_equal(a['shares'][2050], b['shares'][2050]), 'same seed must give the same result'
    sh = a['shares'][2050]
    assert np.allclose(sh.sum(1), 1) and (sh >= 0).all()
    rec = a['components'][(2020, 2050)]
    assert np.abs(rec.share.sum(2) - (a['shares'][2050] - a['shares'][2020])).max() < 1e-10
    assert abs(rec.persons[:, :, 4].sum() + rec.persons[:, :, 5].sum()) < 1e-6 * a['pop'][2020].sum()


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    bad = 0
    for t in tests:
        try:
            t()
            print('PASS', t.__name__)
        except Exception as exc:                                   # report and continue
            bad += 1
            print('FAIL', t.__name__, repr(exc))
    print(f'{len(tests) - bad}/{len(tests)} passed')
    sys.exit(1 if bad else 0)
