"""Step 7 estimation: the evidence that switching rates are fitted to.

For each historical window (WRP decades 1950-2010; Pew 2010-2020 when data/processed has Pew 2010)
a hindcast WITHOUT switching runs from the observed start shares with WPP estimates of fertility,
mortality and net migration. What it leaves unexplained,
    residual = observed end shares - hindcast end shares,
is the net-change evidence for switching (religion_forecast.switching.Hierarchy). The hindcast already contains
births, deaths, ageing and migration, so those are not counted again; only the unexplained part can
be attributed to switching, and the hierarchical model decides how much of it is switching versus
noise (definition changes between sources, measurement error).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from religion_forecast import engine as E
from religion_forecast import model as SM
from religion_forecast import switching as SW

CATS, K, U = E.CATS, E.K, E.U
SHARE_COLS = [f'share_{c}' for c in CATS]


def central_params(ctx, scenario='stabilising'):
    """Deterministic parameter set at the middle of every range (no country noise)."""
    rng = np.random.default_rng(0)
    p = SM.draw_run(ctx, rng, scenario)
    a = ctx.a
    mid = lambda r: 0.5 * (r[0] + r[1])
    f, sw, mg, lr = a['fertility'], a['switching'], a['migration'], a['long_run_demography']
    p.update(phi=mid(f['phi']['range']), w_add=mid(f['w_add']['range']), Hf=mid(f['gap_half_life_years']['range']),
             m_g1=mid(f['first_generation_multiplier']['range']), m_g2=mid(f['second_generation_multiplier']['range']),
             psi=mid(a['age_structure']['psi']['range']), h1=mid(sw['generation_intensity']['first']),
             h2=mid(sw['generation_intensity']['second']),
             g2_ratio=mid(a['generations']['second_generation_initial_ratio']['range']),
             turnover=mid(mg['turnover_per_year']['range']), omega=mid(mg['omega_gravity_weight']['range']),
             margin_rho=mid(mg.get('margin_rho', {}).get('range', [1.0, 1.0])),
             lam_sel=0.0, theta=1.0, tfr_lr=mid(lr['tfr_long_run']), tfr_hl=mid(lr['tfr_half_life_years']),
             e0_gain=mid(lr['e0_gain_per_year']), e0_cap=mid(lr['e0_cap']))
    p['eps'] = np.zeros((ctx.n, K))
    p['tfr_dev'] = np.zeros(ctx.n)
    return p


def wrp_shares(ctx, year):
    """[n, K] WRP shares for usable country-years (NaN rows elsewhere)."""
    w = ctx.wrp
    w = w[w.use & w.year.eq(year) & w.country_id.isin(ctx.idx)]
    out = np.full((ctx.n, K), np.nan)
    for _, r in w.iterrows():
        out[ctx.idx[r.country_id]] = r[SHARE_COLS].to_numpy(float)
    return out


def fill_missing(ctx, shares, year):
    """Countries without an observation keep a stand-in composition so they can still send and
    receive migrants: their nearest usable WRP year, else the 2020 start state. They are masked
    out of every score and of the switching evidence."""
    out = shares.copy()
    miss = ~np.isfinite(out).all(1)
    if not miss.any():
        return out
    w = ctx.wrp[ctx.wrp.use & ctx.wrp.country_id.isin(ctx.idx)]
    for i in np.flatnonzero(miss):
        rows = w[w.country_id.eq(ctx.ids[i])]
        if len(rows):
            r = rows.iloc[int(np.argmin(np.abs(rows.year.to_numpy() - year)))]
            out[i] = r[SHARE_COLS].to_numpy(float)
        else:
            out[i] = ctx.s2020[i]
    return out


def windows(ctx, starts=(1950, 1960, 1970, 1980, 1990, 2000), include_pew=True):
    """List of dicts: source, start, end, s0 [n, K] (filled), s1 [n, K] (NaN where unobserved), mask."""
    out = []
    for t in starts:
        s0, s1 = wrp_shares(ctx, t), wrp_shares(ctx, t + 10)
        mask = np.isfinite(s0).all(1) & np.isfinite(s1).all(1)
        out.append(dict(source='WRP', start=t, end=t + 10, s0=fill_missing(ctx, s0, t), s1=s1, mask=mask))
    if include_pew and ctx.s2010 is not None:
        s0 = ctx.s2010
        mask = np.isfinite(s0).all(1) & np.isfinite(ctx.s2020).all(1)
        out.append(dict(source='Pew', start=2010, end=2020, s0=fill_missing(ctx, s0, 2010), s1=ctx.s2020.copy(),
                        mask=mask))
    return out


def no_switching_hindcasts(ctx, p, wins, migration=True):
    """Adds pred (no switching), resid, P0, exposure basis and z to every window."""
    for w in wins:
        pred, P0 = SM.hindcast(ctx, p, w['start'], w['s0'], years=w['end'] - w['start'], migration=migration)
        w['pred'] = pred
        w['resid'] = np.where(w['mask'][:, None], np.nan_to_num(w['s1']) - pred, 0.0)
        w['P0'] = P0
        ex = SW.exposure(P0, SM.default_intensity(p), steps=(w['end'] - w['start']) // 5)
        w['Bd'], w['Bv'], w['Ba'] = SW.effect_basis(ex, w['s0'])
        w['z'] = SW.development_index(ctx.wpp_at('e0', w['start']), ctx.wpp_at('tfr', w['start']), ctx.a)
    return wins


def net_arrays(ctx, wins, weight):
    D = len(wins)
    n = ctx.n
    net = dict(z=np.zeros((n, D)), Bd=np.zeros((n, D, K - 1, K)), Bv=np.zeros((n, D, K - 1, K)),
               Ba=np.zeros((n, D, K)), y=np.zeros((n, D, K)), mask=np.zeros((n, D), bool),
               weight=np.full((n, D), float(weight)))
    for t, w in enumerate(wins):
        net['z'][:, t], net['Bd'][:, t], net['Bv'][:, t], net['Ba'][:, t] = w['z'], w['Bd'], w['Bv'], w['Ba']
        net['y'][:, t] = w['resid']
        net['mask'][:, t] = w['mask']
    net['scale'] = SW.robust_scale(net['y'], net['mask'])
    return net


def survey_arrays(ctx):
    s = ctx.switch_obs
    if s is None or not len(s):
        return None
    z = SW.development_index(ctx.wpp_mean('e0', 2015, 2020), ctx.wpp_mean('tfr', 2015, 2020), ctx.a)
    return dict(country=s.country.to_numpy(int), raised=s.raised.to_numpy(int), current=s.current.to_numpy(int),
                p=s.p.to_numpy(float), neff=np.minimum(s.neff.to_numpy(float), 500.0),
                z=z[s.country.to_numpy(int)])


def fit_switching(ctx, wins, use_survey=True, seed=7):
    """Empirical Bayes fit on the given windows (and verified survey cells). Returns Hierarchy."""
    sw = ctx.a['switching']
    hier = SW.Hierarchy(ctx.n, sw, M=sw['latent_draws'], seed=seed)
    net = net_arrays(ctx, wins, sw['net_evidence_weight']['value']) if wins else None
    survey = survey_arrays(ctx) if use_survey else None
    hier.fit(net=net, survey=survey)
    hier.net_scale = None if net is None else net['scale']
    return hier


def expected_switch_effect(hier, w):
    """Posterior-mean first-order switching effect on shares over a window [n, K]."""
    d, v, a = hier.rates(w['z'], hier.H)
    wt = hier.posterior_weights()
    eff = (np.einsum('nmj,njk->nmk', d, w['Bd']) + np.einsum('nmj,njk->nmk', v, w['Bv'])
           + a[:, :, None] * w['Ba'][:, None, :])
    return np.einsum('nm,nmk->nk', wt, eff)


MENA = {'DZA', 'BHR', 'EGY', 'IRN', 'IRQ', 'ISR', 'JOR', 'KWT', 'LBN', 'LBY', 'MAR', 'OMN', 'PSE', 'QAT', 'SAU',
        'SYR', 'TUN', 'ARE', 'YEM', 'ESH'}
PEW7 = {'Christianity': [0], 'Islam': [1], 'Unaffiliated': [7], 'Hinduism': [2], 'Buddhism': [3], 'other': [5, 6],
        'Judaism': [4]}


def selectivity_targets(ctx):
    """Targets from inputs/migrant_religion_published.csv usable with bilateral stocks."""
    from religion_forecast import datasets as D
    p = D.TRACKED / 'migrant_religion_published.csv'
    if not p.exists():
        return []
    df = pd.read_csv(p, comment='#')
    df = df[~df.evidence_type.astype(str).str.contains('secondary')]
    eu = np.array([c == 'Europe' for c in ctx.continent])
    mena = np.array([c in MENA for c in ctx.ids])
    where = {'world_migrants_2020': ('world', None), 'migrants_living_in_Europe_2020': ('dest', eu),
             'migrants_living_in_MENA_2020': ('dest', mena),
             'india_born_migrants_2020': ('origin', ctx.idx.get('IND')),
             'us_foreign_born_adults_2023': ('destc', ctx.idx.get('USA'))}
    out = []
    for _, r in df.iterrows():
        kind, mask = where.get(r.scope, (None, None))
        if kind is None or (mask is None and kind != 'world'):
            continue
        for cat in PEW7:
            if cat in r and pd.notna(r[cat]):
                out.append((kind, mask, cat, float(r[cat]), r.scope))
    return out



def calibrate_affinity(ctx, S=None, kappas=np.arange(0.0, 2.01, 0.1), lams=np.arange(0.0, 1.01, 0.05)):
    """Who migrates where, by religion: grid fit of destination affinity kappa (migrants go where their
    religion is common) and minority effect lambda, so that UN bilateral stocks (2020) reproduce Pew's
    published religious composition of migrants. Two parameters; replaces global religion propensities
    (which fit worse and push every country's composition in the same direction over time)."""
    S = ctx.stock2020 if S is None else S
    T = selectivity_targets(ctx)
    if S is None or len(T) < 6:
        return None
    from religion_forecast import migration as MG
    sh = ctx.s2020

    def resid(kappa, lam):
        X = S[:, :, None] * MG.corridor_mix(sh, lam, kappa)
        out = []
        for kind, mask, cat, target, _ in T:
            if kind == 'world':
                v = X.sum((0, 1))
            elif kind == 'dest':
                v = X[:, mask].sum((0, 1))
            elif kind == 'destc':
                v = X[:, mask].sum(0)
            else:
                v = X[mask].sum(0)
            out.append(100 * (v / max(v.sum(), 1e-300))[PEW7[cat]].sum() - target)
        return np.array(out)

    grid = [(float(np.sqrt(np.mean(resid(k, l) ** 2))), float(k), float(l)) for k in kappas for l in lams]
    best = min(grid)
    mirror = float(np.sqrt(np.mean(resid(0.0, 0.0) ** 2)))
    return dict(kind='affinity', kappa=best[1], lam=best[2], rmse_pp=best[0], rmse_mirror_pp=mirror,
                residuals=[(T[i][4], T[i][2], float(v)) for i, v in enumerate(resid(best[1], best[2]))],
                propensity=np.ones(K))


def switching_table(ctx, hier, year=2020):
    """Posterior lifetime switching rates per country at `year` development (for the report)."""
    z = SW.development_index(ctx.wpp_mean('e0', year - 5, year), ctx.wpp_mean('tfr', year - 5, year), ctx.a)
    s = hier.posterior_summary(z)
    rows = []
    surveyed = set() if ctx.switch_obs is None else set(ctx.switch_obs.country_id)
    ess = hier.effective_sample_size()
    for i, c in enumerate(ctx.ids):
        for j, r in enumerate(SW.REL):
            rows.append({'country_id': c, 'religion': CATS[r], 'rate': 'disaffiliation (raised r -> unaffiliated)',
                         'mean': s['d_mean'][i, j], 'q05': s['d_q05'][i, j], 'q95': s['d_q95'][i, j],
                         'evidence': 'survey + net change' if c in surveyed else 'net change + hierarchical prior',
                         'posterior_ess': ess[i]})
            rows.append({'country_id': c, 'religion': CATS[r], 'rate': 'conversion (raised r -> other religion)',
                         'mean': s['v_mean'][i, j], 'q05': s['v_q05'][i, j], 'q95': s['v_q95'][i, j],
                         'evidence': 'survey + prior' if c in surveyed else 'prior (not identified by net change)',
                         'posterior_ess': ess[i]})
        rows.append({'country_id': c, 'religion': 'Unaffiliated', 'rate': 'affiliation (raised unaffiliated -> any religion)',
                     'mean': s['a_mean'][i], 'q05': s['a_q05'][i], 'q95': s['a_q95'][i],
                     'evidence': 'survey + net change' if c in surveyed else 'net change + hierarchical prior',
                     'posterior_ess': ess[i]})
    return pd.DataFrame(rows)


# ------------------------------------------------------------ survey-level calibration
def _completion_weights(ctx):
    """Share of lifetime switching completed by adults 18-54 in each country (model age weights x the
    country's 2020 age structure) and the 18-54 population."""
    age = ctx.age_dist(2020)
    cumw = np.cumsum(np.concatenate([np.zeros(SW.SWITCH_AGES[0]), SW.SWITCH_AGE_WEIGHTS,
                                     np.zeros(E.A - SW.SWITCH_AGES[-1] - 1)]))
    wt = age[:, 3:11].copy()
    wt[:, 0] *= 0.4                       # 18-19 of the 15-19 group
    frac = (wt * cumw[None, 3:11]).sum(1) / np.maximum(wt.sum(1), 1e-300)
    return frac, ctx.wpp_at('pop', 2020) * wt.sum(1)


def global_left_per_100(ctx, hier, shift_d=None, shift_a=0.0):
    """Model 'left per 100 raised' among adults 18-54, population-weighted over countries, by religion
    (Pew's 117-country measure). Uses posterior-weighted rates at 2015-2020 development, with the
    survey-maximum caps of config/assumptions.json."""
    z = SW.development_index(ctx.wpp_mean('e0', 2015, 2020), ctx.wpp_mean('tfr', 2015, 2020), ctx.a)
    d, v, a = hier.rates(z, hier.H, shift_d=shift_d, shift_a=shift_a)
    d, v, a = SW.apply_caps(d, v, a, ctx.a['switching'].get('lifetime_outflow_cap', {}).get('by_group'))
    w = hier.posterior_weights()
    out_rel = np.einsum('nm,nmj->nj', w, d + v)
    out_u = (w * a).sum(1)
    frac, pop = _completion_weights(ctx)
    res = {}
    for r in SW.REL + [U]:
        base = pop * ctx.s2020[:, r]
        out = out_rel[:, SW.REL.index(r)] if r != U else out_u
        res[CATS[r]] = 100 * float((base * frac * out).sum() / max(base.sum(), 1e-300))
    return res


def survey_targets():
    from religion_forecast import datasets as D
    p = D.TRACKED / 'switching_global_targets.csv'
    if not p.exists():
        return {}
    df = pd.read_csv(p, comment='#')
    df = df[df.scope.eq('world_18_54') & df.measure.eq('left_per_100_raised')]
    return dict(zip(df.religion, df.value.astype(float)))


def calibrate_survey_level(ctx, hier, masked=False):
    """Logit shifts that make the fitted rates reproduce Pew's 117-country survey figures (adults
    18-54, left per 100 raised) for every religion with a published figure. Religions without a
    figure (here Judaism, Folk/Traditional, Other) get no shift.

    Default (masked=False): one shift per religion for every country. Interpretation: the country
    survey cells describe ALL adults, the global figure describes adults 18-54, and Pew finds younger
    adults switch more in many countries, so the survey level stands for recent cohorts' rates.
    masked=True: only countries without their own survey cells for that religion are shifted (a
    sensitivity option; it pushes the whole gap onto unsurveyed countries). Caps always apply.
    Returns dict or None."""
    tg = survey_targets()
    if not tg:
        return None
    n = ctx.n
    observed = np.zeros((n, K), bool)            # (country, raised religion) with its own survey cells
    if ctx.switch_obs is not None:
        observed[ctx.switch_obs.country.to_numpy(int), ctx.switch_obs.raised.to_numpy(int)] = True
    surveyed = observed.copy()
    if not masked:
        observed[:] = False
    shift_d = np.zeros((n, K - 1))
    shift_a = np.zeros(n)
    for r in SW.REL + [U]:
        g = CATS[r]
        if g not in tg:
            continue
        free = ~observed[:, r]                    # surveyed countries keep their own evidence
        lo, hi = -4.0, 4.0
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if r == U:
                sa = np.where(free, mid, 0.0)
                val = global_left_per_100(ctx, hier, shift_d, sa)[g]
            else:
                sd = shift_d.copy()
                sd[:, SW.REL.index(r)] = np.where(free, mid, 0.0)
                val = global_left_per_100(ctx, hier, sd, shift_a)[g]
            if val > tg[g]:
                hi = mid
            else:
                lo = mid
        best = 0.5 * (lo + hi)
        if r == U:
            shift_a = np.where(free, best, 0.0)
        else:
            shift_d[:, SW.REL.index(r)] = np.where(free, best, 0.0)
    before = global_left_per_100(ctx, hier)
    after = global_left_per_100(ctx, hier, shift_d, shift_a)
    def shown(g):
        x = shift_a if g == 'Unaffiliated' else shift_d[:, SW.REL.index(CATS.index(g))]
        nz = x[x != 0]
        return float(nz[0]) if len(nz) else 0.0
    table = pd.DataFrame([{'religion': g, 'pew_left_per_100_raised_18_54': tg.get(g, np.nan),
                           'history_level_model': before[g], 'survey_level_model': after[g],
                           'logit_shift': shown(g),
                           'countries_with_own_survey_cells': int(surveyed[:, CATS.index(g)].sum())}
                          for g in CATS])
    return dict(shift_d=shift_d, shift_a=shift_a, table=table)
