"""Tests of the projection model.  Run:  python run.py test   (or: python -m pytest tests)

Unit tests use synthetic data and read no files. Integration tests use the real inputs and are
skipped when data/raw/WPP2024_Demographic_Indicators_Medium.csv.gz or the start state is missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from religion_forecast import engine as E
from religion_forecast import migration as MG
from religion_forecast import switching as SW
from religion_forecast import config




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
    Q, rec = E.step(P, inp, migration_fn=_migration_fn(n, rng), natural_growth=rng.uniform(0.95, 1.1, n))
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
    assert abs(h.H[0] - truth[0]) < 0.3 and abs(h.H[1] - truth[1]) < 0.3 and abs(h.H[2] - truth[2]) < 0.35, h.H


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


def test_shift_share_parts_sum_to_the_total():
    """The within-country, population-weighting and interaction parts must reconstruct the change."""
    from religion_forecast import tables as T
    rng = np.random.default_rng(11)
    n = 25
    rows = []
    for year, scale in ((2020, 1.0), (2100, 1.0)):
        sh = rng.dirichlet(np.ones(E.K), size=n)
        pop = rng.lognormal(15, 1.0, n)
        for i in range(n):
            rows.append({'scenario': 'x', 'country_id': f'C{i:03d}', 'year': year, 'mean_population': pop[i],
                         **{f'mean_{c}': sh[i, k] for k, c in enumerate(E.CATS)}})
    ct = pd.DataFrame(rows)
    out = T.shift_share(ct, 'x', years=(2100,))
    parts = out.within_country_pp + out.population_weighting_pp + out.interaction_pp
    assert np.allclose(parts, out.change_pp, atol=1e-9), 'parts must add up to the change'
    assert np.allclose(out.world_share_pp - out.world_share_2020_pp, out.change_pp, atol=1e-9)


def test_sensitivity_recovers_a_known_driver():
    """A planted linear relationship must come out as the largest coefficient."""
    from religion_forecast import experiments as XP
    rng = np.random.default_rng(5)
    n = 300
    df = pd.DataFrame({'a': rng.uniform(0, 1, n), 'b': rng.uniform(0, 1, n), 'c': rng.uniform(0, 1, n)})
    df['world_Islam'] = 3.0 * df.a - 0.5 * df.b + rng.normal(0, 0.05, n)
    out = XP.sensitivity(df, ['a', 'b', 'c'], ['world_Islam'])
    rank = out[out.basis.eq('rank')].set_index('parameter').coefficient
    assert rank.abs().idxmax() == 'a' and rank['a'] > 0 and rank['b'] < 0
    assert out[out.basis.eq('value')].model_r2.iloc[0] > 0.95


def _have_data():
    return (config.DATA / 'raw' / 'WPP2024_Demographic_Indicators_Medium.csv.gz').exists() and (
        (config.DATA / 'processed' / 'pew_harmonized.csv').exists() or config.FALLBACK_START_STATE.exists())


def test_integration_reproducible_and_exact():
    if not _have_data():
        print('  (skipped: real inputs not present)')
        return
    from religion_forecast import calibration as ES
    from religion_forecast import model as SM
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


def test_life_table_open_group_is_stationary():
    """A stationary population (persons by age = person-years lived, 80+ = T80) must reproduce
    itself under survival, including the open age group."""
    for e0 in (55.0, 72.0, 86.0):
        b, c = E._hazard_params(e0, 0.01)
        py = E._survival_fine(b, c) * 0.25
        F = E._FINE
        L = np.array([py[(F >= 5 * i) & (F < 5 * i + 5)].sum() for i in range(E.A - 1)])
        T80 = py[F >= 80].sum()
        P = np.concatenate([L, [T80]])[None, None, None, :] * np.ones((1, 1, 1, 1))
        s, so, _ = E.life_table(e0, 0.01)
        aged, _ = E.survive(P, s[None, :], np.array([so]))
        assert np.allclose(aged[0, 0, 0, 1:], P[0, 0, 0, 1:], rtol=1e-9), e0


def test_lgamma_matches_math():
    import math
    x = np.array([1e-4, 0.03, 0.5, 1.0, 3.7, 25.0, 480.5, 1e5])
    ref = np.array([math.lgamma(v) for v in x])
    assert np.max(np.abs(SW.lgamma(x) - ref) / np.maximum(np.abs(ref), 1.0)) < 1e-12


def _survey_row(cells, n, alpha):
    """A one-country survey dict: cells = [(raised, current, p, dest_frac)]."""
    return dict(group=np.zeros(len(cells), int), raised=np.array([c[0] for c in cells]),
                current=np.array([c[1] for c in cells]), p=np.array([c[2] for c in cells]),
                dest_frac=np.array([c[3] for c in cells]), group_country=np.array([0]), group_n=np.array([float(n)]),
                group_z=np.array([0.0]), alpha=alpha)


def test_survey_row_is_one_multinomial():
    """One reported cell is a binomial; a row reporting stay + unaffiliated + one conversion cell
    is a single multinomial with the unreported conversions pooled, not three binomials."""
    prior = dict(mu_d={c: .1 for c in E.CATS if c != 'Unaffiliated'}, mu_v={c: .02 for c in E.CATS if c != 'Unaffiliated'},
                 mu_a=.12, beta_a=0.0, tau_e=.4, tau_a=.6, tau_v=.5, grid=dict(delta=[0.0], beta_d=[0.0], tau_u=[1.0]))
    h = SW.Hierarchy(1, prior, M=5, seed=1)
    H = (0.0, 0.0, 1.0)
    d, v, _ = h.rates(np.array([0.0]), H)
    j = SW.REL.index(0)
    one = h.loglik(H, survey=_survey_row([(0, E.U, 0.2, 0.0)], 100, np.inf))[0]
    pd_ = d[0, :, j]
    assert np.allclose(one, 100 * (0.2 * np.log(pd_) + 0.8 * np.log1p(-pd_)))
    row = h.loglik(H, survey=_survey_row([(0, 0, 0.7, 0.0), (0, E.U, 0.2, 0.0), (0, 1, 0.06, 0.6)], 100, np.inf))[0]
    pc = v[0, :, j] * 0.6
    expect = 100 * (0.7 * np.log(1 - pd_ - v[0, :, j]) + 0.2 * np.log(pd_) + 0.06 * np.log(pc)
                    + 0.04 * np.log(1 - (1 - pd_ - v[0, :, j]) - pd_ - pc))
    assert np.allclose(row, expect)
    # Dirichlet-multinomial: tends to the multinomial as alpha grows, and a larger survey adds
    # little once n is well above alpha
    big = h.loglik(H, survey=_survey_row([(0, E.U, 0.2, 0.0)], 100, 1e9))[0]
    assert np.allclose(big - big.mean(), one - one.mean(), atol=1e-4)
    curv = lambda n: np.ptp(h.loglik(H, survey=_survey_row([(0, E.U, 0.2, 0.0)], n, 50.0))[0])
    assert curv(5000) < 1.2 * curv(500)


def test_nelder_mead_finds_a_quadratic_minimum():
    f = lambda x: (x[0] - 1.3) ** 2 + 3 * (x[1] + 0.4) ** 2 + 0.5 * (x[2] - 2.0) ** 2
    x = SW.nelder_mead(f, np.zeros(3), np.array([0.5, 0.5, 0.5]), max_eval=400, xtol=1e-6, ftol=1e-10)
    assert np.allclose(x, [1.3, -0.4, 2.0], atol=1e-3)


def test_error_model_recovers_scale_and_calibrates():
    """Errors planted as e = (h/10)^beta (s(1-s))^b u must be recovered, and the predictive
    intervals of a held-out origin must cover close to their nominal level."""
    from religion_forecast import errors as ER
    rng = np.random.default_rng(11)
    n, b_true, beta_true = 400, 0.8, 0.4
    rec = []
    for t0, horizons in ((1970, (10, 20, 30)), (1980, (10, 20)), (1990, (10, 20)), (2000, (10,))):
        s = rng.dirichlet(np.full(E.K, 1.5), size=n)
        for h in horizons:
            u = rng.standard_t(6, size=(n, E.K)) * 0.6
            obs = np.clip(s + (h / 10) ** beta_true * (s * (1 - s) + ER.EPS) ** b_true * u, 1e-6, None)
            obs = obs / obs.sum(1, keepdims=True)
            samples = np.repeat(s[None], 4, axis=0) * (1 + rng.normal(0, 1e-4, (4, n, E.K)))
            rec.append(dict(source='WRP', origin=t0, horizon=h, target=t0 + h, samples=samples, obs=obs,
                            mask=np.ones(n, bool), pop=np.ones(n), train_windows=2))
    m = ER.fit(rec)
    assert abs(m['b'] - b_true) < 0.15 and abs(m['beta'] - beta_true) < 0.2, (m['b'], m['beta'])
    cal, _ = ER.validate(rec, draws=20, log=lambda *a: None)
    c = cal[cal.method.eq('error-calibrated')].groupby('nominal').coverage.mean()
    assert abs(c[0.8] - 0.8) < 0.08 and abs(c[0.9] - 0.9) < 0.06, c.to_dict()


def test_corridor_cap_keeps_emigrants_and_limits_shares():
    rng = np.random.default_rng(12)
    n = 15
    F = rng.gamma(0.5, 1.0, (n, n))
    np.fill_diagonal(F, 0.0)
    S = rng.gamma(0.5, 1.0, (n, n))
    np.fill_diagonal(S, 0.0)
    G = MG.cap_corridors(F, S, cap=2.0)
    assert (G >= 0).all() and np.allclose(G.sum(1), F.sum(1), rtol=1e-6)        # every origin keeps its emigrants
    share = S / S.sum(0, keepdims=True)
    excess = lambda X: np.maximum(X / X.sum(0, keepdims=True) - 2.0 * np.maximum(share, 0.01), 0.0).sum()
    assert excess(G) < 0.5 * excess(F)                                          # concentration beyond the cap falls


def test_inference_detects_a_planted_improvement():
    from religion_forecast import backtest as BT
    assert abs(BT.sign_flip_p([1.0, 2.0, 0.5, 1.5]) - 0.125) < 1e-12
    assert BT.sign_flip_p([1.0, -1.0, 1.0, -1.0]) == 1.0
    rng = np.random.default_rng(13)
    rows = []
    for w in ('WRP 1970-1980', 'WRP 1980-1990', 'WRP 1990-2000', 'WRP 2000-2010'):
        for c in range(150):
            base = rng.gamma(2.0, 0.02)
            for m in BT.MODELS:
                gain = 0.004 if m == 'demography' else 0.0
                rows.append(dict(window=w, source='WRP', country_id=f'C{c}', population=rng.uniform(1, 10),
                                 model=m, tv=max(base - gain + rng.normal(0, 0.002), 0.0)))
    inf = BT.inference(pd.DataFrame(rows), B=1000)
    r = inf[inf.model.eq('demography')].iloc[0]
    assert r.ci95_high_pp < 0 and r.p_bootstrap < 0.01
    t = inf[inf.model.eq('trend')].iloc[0]
    assert t.ci95_low_pp < 0 < t.ci95_high_pp


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
