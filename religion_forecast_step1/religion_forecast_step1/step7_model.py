"""Step 7 model assembly: data + one run's parameters -> engine inputs for every 5-year step.

Used by step7_forecast.py (2020 -> 3030) and step7_validate.py (historical decades). The pieces:
  Context        aligned country list, WPP paths, geography, bilateral stocks, start shares
  draw_run       one Monte Carlo parameter set (fixed seed per run)
  Demography     WPP period inputs to 2100; long-run rules after 2100 (per run)
  Fertility      religion x generation multipliers relative to the national TFR
  SwitchPlan     age-specific transition matrices from the posterior switching draw, by scenario
  MigrationPlan  conserving origin-destination flows (Sinkhorn to WPP margins, rules after 2100)
  initial_population  persons by religion, generation and age in a start year
  simulate       the time loop, with exact component accounting
  hindcast       a no-switching (or posterior-switching) run over one historical decade
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import step5d_engine as e5
import step7_data as D
import step7_engine as E
import step7_migration as MG
import step7_switching as SW
import wrp_history as H

ROOT = Path(__file__).resolve().parent
CATS, K, G, A, U = E.CATS, E.K, E.G, E.A, E.U
GEO_PROXY = {'GLP': 'DMA', 'MTQ': 'LCA', 'GUF': 'SUR', 'MYT': 'COM', 'REU': 'MUS'}
G2_AGE = np.array([0.12, 0.12, 0.12, 0.12, 0.11, 0.10, 0.09, 0.07, 0.05, 0.04, 0.03, 0.02, 0.01,
                   0.0, 0.0, 0.0, 0.0])
G2_AGE = G2_AGE / G2_AGE.sum()
PERIODS = [(2020, 2050), (2050, 2100), (2100, 2200), (2200, 2500), (2500, 3030)]
KEEP_YEARS = [2020, 2025, 2030, 2040, 2050, 2060, 2075, 2100, 2125, 2150, 2200, 2300, 2400, 2500,
              2600, 2750, 2900, 3000, 3025, 3030]


def load_assumptions():
    return json.loads((ROOT / 'step7_assumptions.json').read_text(encoding='utf8'))


# ----------------------------------------------------------------------------- context
class Context:
    """options: bilateral (use UN bilateral stocks when present), age_data (use WPP age structure when
    present). Set to False to measure what each dataset adds (step7_validate --ablations)."""

    def __init__(self, assumptions=None, need_wrp=True, bilateral=True, age_data=True):
        self.a = assumptions or load_assumptions()
        self.options = dict(bilateral=bilateral, age_data=age_data)
        self.selectivity = None
        self.wpp = D.wpp_table()
        st = D.start_state()
        self.start_source = st['source']
        s20 = st['s2020']
        wpp_ids = set(self.wpp.country_id)
        self.dropped = sorted(set(s20.country_id) - wpp_ids)
        s20 = s20[s20.country_id.isin(wpp_ids)].sort_values('country_id').reset_index(drop=True)
        self.ids = s20.country_id.tolist()
        self.n = len(self.ids)
        self.idx = {c: i for i, c in enumerate(self.ids)}
        self.s2020 = s20[D.SHARE_COLS].to_numpy(float)
        self.s2010 = None
        if st['s2010'] is not None:
            m = st['s2010'].set_index('country_id').reindex(self.ids)
            self.s2010 = m[D.SHARE_COLS].to_numpy(float)
        self.folk_method = st['folk_method']
        fo = self.s2020[:, CATS.index('Folk_Traditional')]
        ot = self.s2020[:, CATS.index('Other')]
        self.folk_ratio = np.where(fo + ot > 0, fo / np.maximum(fo + ot, 1e-300), 0.0)
        self._wpp_arrays()
        if need_wrp:
            self.wrp, geo, nbrs = D.wrp_and_geography()
        else:
            geo, nbrs = H.load_geography(D.RAW / 'ne_50m_admin_0_countries.zip')
            self.wrp = None
        self._geography(geo, nbrs)
        cube = D.wpp_age_cube(self.ids) if age_data else None
        self.age_years, self.age_tot, self.age_fem = (None, None, None) if cube is None else cube
        self.stock_df = D.ims_bilateral(self.wpp) if bilateral else None
        self.stock2020, self.stock_year = D.stock_matrix(self.stock_df, self.ids, 2020)
        self.mobility = self.mobility_from(self.stock2020, self.stock_year)
        self.migrant_religion = D.pew_migrants(self.ids, self.folk_ratio)
        self.switch_obs = D.switching_observations(self.ids)
        self.fert_obs = D.fertility_observations(self.ids)
        self.unhcr = D.unhcr_population(self.ids)

    def _wpp_arrays(self):
        w = self.wpp[self.wpp.country_id.isin(self.idx)]
        self.years_wpp = sorted(w.year.unique())
        cols = ['tfr', 'e0', 'q5', 'mac', 'median_age', 'pop', 'female_share', 'net_migrations']
        cube = {c: np.full((len(self.years_wpp), self.n), np.nan) for c in cols}
        yi = {y: i for i, y in enumerate(self.years_wpp)}
        r = w.year.map(yi).to_numpy(int)
        c = w.country_id.map(self.idx).to_numpy(int)
        for col in cols:
            cube[col][r, c] = w[col].to_numpy(float)
        # fill gaps along time, then with world medians
        for col in cols:
            x = pd.DataFrame(cube[col]).ffill().bfill().to_numpy()
            med = np.nanmedian(x, axis=1, keepdims=True)
            cube[col] = np.where(np.isfinite(x), x, med)
        cube['net_migrations'] = np.nan_to_num(cube['net_migrations'])
        self.cube = cube
        self.yi = yi

    def mobility_from(self, S, year):
        """Relative two-way migration intensity per country [n]: (immigrant + emigrant stock) / population
        from a UN bilateral stock matrix S (the 2020 table for forecasts, the start-year table for history
        tests), normalised to a population-weighted mean of 1 and clipped to 0.05-10. Circulation (two-way
        flows beyond net migration) scales with it, so large countries with little migration (India,
        China) do not generate huge flows. 1 everywhere without the table."""
        if S is None:
            return np.ones(self.n)
        pop = self.wpp_at('pop', int(year))
        m = 0.5 * (S.sum(0) + S.sum(1)) / np.maximum(pop, 1.0)
        m = m / max(float((m * pop).sum() / pop.sum()), 1e-12)
        return np.clip(m, 0.05, 10.0)

    def wpp_at(self, col, year):
        return self.cube[col][self.yi[int(year)]]

    def age_dist(self, year):
        """National age shares [n, A] at `year`: WPP population by age where available, otherwise
        a stable-population pyramid matching the WPP median age."""
        approx = e5.pyramid_for_median(self.wpp_at('median_age', min(year, 2100)))
        if self.age_years is None:
            return approx
        y = int(min(max(year, self.age_years[0]), self.age_years[-1]))
        y = y - (y % 5)
        tot = self.age_tot[list(self.age_years).index(y)]
        ok = np.isfinite(tot).all(1) & (np.nan_to_num(tot).sum(1) > 0)
        real = np.nan_to_num(tot) / np.maximum(np.nan_to_num(tot).sum(1, keepdims=True), 1e-300)
        return np.where(ok[:, None], real, approx)

    def female_share_repro(self, y0, y1):
        """Female share of each reproductive age group [n, 7] over a step (mean of its end points);
        the national female share where age data are missing; held at 2100 after 2100."""
        nat = self.wpp_mean('female_share', min(y0, 2095), min(y1, 2100))
        if self.age_years is None:
            return nat
        vals = []
        for y in (y0, y1):
            yy = int(min(max(y, self.age_years[0]), self.age_years[-1]))
            yy = yy - (yy % 5)
            k = list(self.age_years).index(yy)
            vals.append(self.age_fem[k][:, E.F0:E.F1] / np.maximum(self.age_tot[k][:, E.F0:E.F1], 1e-300))
        fs = 0.5 * (vals[0] + vals[1])
        ok = np.isfinite(fs).all(1)
        return np.where(ok[:, None], np.nan_to_num(fs), nat[:, None])

    def wpp_mean(self, col, y0, y1):
        """Mean over calendar years y0 .. y1-1."""
        return self.cube[col][self.yi[int(y0)]:self.yi[int(y1)]].mean(0)

    def _geography(self, geo, nbrs):
        lat, lon, cont = np.zeros(self.n), np.zeros(self.n), np.empty(self.n, object)
        self.has_geometry = np.zeros(self.n, bool)
        for i, c in enumerate(self.ids):
            key = c if c in geo.index else GEO_PROXY.get(c)
            if key in geo.index:
                # the .dbf reader keeps NUL padding in text fields; strip it so names compare cleanly
                lat[i], lon[i] = geo.loc[key, 'lat'], geo.loc[key, 'lon']
                cont[i] = str(geo.loc[key, 'continent']).replace('\x00', '').strip()
                self.has_geometry[i] = c in geo.index
            else:
                lat[i], lon[i], cont[i] = 0.0, 0.0, 'Unknown'
        self.lat, self.lon, self.continent = lat, lon, cont
        dist = H.haversine_km(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
        adj = np.array([[1.0 if b in nbrs.get(a, set()) else 0.0 for b in self.ids] for a in self.ids])
        same = (cont[:, None] == cont[None, :]).astype(float)
        g = self.a['migration']['gravity']
        self.gravity = MG.gravity_kernel(dist, adj, same, g['gamma'], g['b_adj'], g['b_cont'])
        self.adjacency = adj
        self.continents = sorted(set(cont))


# ------------------------------------------------------------------------ run parameters
def _u(rng, rr):
    return float(rng.uniform(rr[0], rr[1]))


def draw_run(ctx, rng, scenario):
    a = ctx.a
    f, sw, mg, lr = a['fertility'], a['switching'], a['migration'], a['long_run_demography']
    p = dict(scenario=scenario,
             phi=_u(rng, f['phi']['range']), w_add=_u(rng, f['w_add']['range']),
             Hf=_u(rng, f['gap_half_life_years']['range']),
             m_g1=_u(rng, f['first_generation_multiplier']['range']),
             m_g2=_u(rng, f['second_generation_multiplier']['range']),
             psi=_u(rng, a['age_structure']['psi']['range']),
             h1=_u(rng, sw['generation_intensity']['first']), h2=_u(rng, sw['generation_intensity']['second']),
             g2_ratio=_u(rng, a['generations']['second_generation_initial_ratio']['range']),
             turnover=_u(rng, mg['turnover_per_year']['range']),
             omega=_u(rng, mg['omega_gravity_weight']['range']),
             lam_sel=_u(rng, mg['minority_selectivity_lambda']['range']),
             theta=_u(rng, mg['post2100_congestion_theta']['range']),
             tfr_lr=_u(rng, lr['tfr_long_run']), tfr_hl=_u(rng, lr['tfr_half_life_years']),
             e0_gain=_u(rng, lr['e0_gain_per_year']), e0_cap=_u(rng, lr['e0_cap']),
             tfr_country_sd=0.1,
             eps=rng.normal(0.0, 0.06, size=(ctx.n, K)),
             drift_seed=int(rng.integers(0, 2 ** 31 - 1)))
    p['tfr_dev'] = rng.normal(0.0, p['tfr_country_sd'], size=ctx.n)     # persistent country deviation after 2100
    p['switch_strength'] = _u(rng, sw.get('strength_range', {}).get('range', [1.0, 1.0]))
    p['survey_weight'] = _u(rng, sw.get('survey_level_weight', {}).get('range', [0.0, 1.0]))
    p['margin_rho'] = _u(rng, mg.get('margin_rho', {}).get('range', [1.0, 1.0]))     # drawn last: earlier draws unchanged
    return p


# --------------------------------------------------------------------------- demography
class Demography:
    """Period inputs for the step ENDING in `year` (5 years)."""

    def __init__(self, ctx, p):
        self.ctx, self.p = ctx, p
        self.last = 2100
        lr = {}
        for col in ('tfr', 'e0', 'q5', 'mac'):
            lr[col] = ctx.wpp_mean(col, 2095, 2100)
        lr['female_share'] = ctx.female_share_repro(2095, 2100)
        self.base2100 = lr

    def period(self, year):
        c, y0 = self.ctx, year - 5
        if year <= self.last:
            out = {col: c.wpp_mean(col, y0, year) for col in ('tfr', 'e0', 'q5', 'mac')}
            out['female_share'] = c.female_share_repro(y0, year)
            out['net5'] = c.cube['net_migrations'][c.yi[y0]:c.yi[year]].sum(0)
            pop0, pop1 = c.wpp_at('pop', y0), c.wpp_at('pop', year)
            out['natural_growth'] = (pop1 - out['net5']) / np.maximum(pop0, 1.0)
            out['wpp'] = True
            return out
        p, b = self.p, self.base2100
        t = year - 2.5 - 2100.0
        lvl = p['tfr_lr'] + p['tfr_dev']
        tfr = lvl + (b['tfr'] - lvl) * np.exp(-t / p['tfr_hl'])
        e0 = np.minimum(b['e0'] + p['e0_gain'] * t, p['e0_cap'])
        gain = np.maximum(e0 - b['e0'], 0.0)
        q5 = b['q5'] * np.exp(-0.08 * gain)
        return dict(tfr=np.clip(tfr, 0.8, 6.0), e0=e0, q5=q5, mac=b['mac'], female_share=b['female_share'],
                    net5=None, natural_growth=None, wpp=False)


# ----------------------------------------------------------------------------- fertility
class Fertility:
    """rel[c, r, g] = group TFR / national TFR before national normalisation (step7_engine.births)."""

    def __init__(self, ctx, p, scenario_cfg):
        a = ctx.a['fertility']
        g = a['pew_global_tfr_2010_15']
        rel_global = np.array([g['by_group'][c] for c in CATS]) / g['world']
        self.gap0 = (p['phi'] * (rel_global - 1.0))[None, :] + p['eps']        # [n, K]
        self.observed = np.zeros((ctx.n, K), bool)
        if ctx.fert_obs is not None:
            for _, r in ctx.fert_obs.iterrows():
                i, k = int(r.country), int(r.k)
                ratio = float(r.tfr) / max(float(ctx.wpp_mean('tfr', 2015, 2020)[i]), 0.5)
                self.gap0[i, k] = ratio - 1.0
                self.observed[i, k] = True
        hl = scenario_cfg.get('fertility', {}).get('gap_half_life') or p['Hf']
        self.Hf = float(hl)
        self.w_add, self.world = p['w_add'], g['world']
        self.gen = np.array([1.0, p['m_g1'], p['m_g2']])

    def rel(self, year, tfr):
        t = max(year - 2.5 - 2020.0, 0.0)
        gap = self.gap0 * np.exp(-t / self.Hf)
        rel = 1.0 + gap
        if self.w_add > 0:
            add = gap * self.world / np.maximum(tfr, 0.8)[:, None]
            rel = (1 - self.w_add) * rel + self.w_add * (1.0 + add)
        rel = np.clip(rel, 0.4, 2.5)
        return rel[:, :, None] * self.gen[None, None, :]


# ----------------------------------------------------------------------------- switching
class SwitchPlan:
    """Time path of lifetime switching rates for one run, then 5-year matrices."""

    def __init__(self, ctx, p, hier, draw_idx, scenario_cfg, every=2):
        self.ctx, self.p, self.h, self.idx = ctx, p, hier, draw_idx
        s = scenario_cfg['switching']
        self.s = s
        self.every = every
        self.cache = (None, None)
        rng = np.random.default_rng(p['drift_seed'])
        # long-run drift: logit random walk, sd per century
        steps = (3030 - 2100) // 5 + 1
        sd = s.get('drift_sd_per_century', 0.0) * np.sqrt(5.0 / 100.0)
        self.drift_d = np.cumsum(rng.normal(0, sd, size=(steps, ctx.n)), 0)
        self.drift_a = np.cumsum(rng.normal(0, sd, size=(steps, ctx.n)), 0)
        self.H = hier.H
        i = np.arange(ctx.n)
        self.xi_u = hier.xi_u[i, draw_idx]
        self.xi_e = hier.xi_e[i, draw_idx]
        self.xi_a = hier.xi_a[i, draw_idx]
        self.xi_v = hier.xi_v[i, draw_idx]

    def rates(self, year, z):
        h, s, (delta, beta, tau_u) = self.h, self.s, self.H
        pr = h.prior
        t = year - 2.5
        trend_end = s.get('trend_until', 3030)
        trend = s.get('trend_logit_per_century', 0.0) * (min(t, trend_end) - 2020.0) / 100.0 if t > 2020 else 0.0
        n = len(z)
        if year > 2100:
            k = min(int((year - 2100) // 5), len(self.drift_d) - 1)
            dd, da = self.drift_d[k], self.drift_a[k]
        else:
            dd, da = np.zeros(n), np.zeros(n)
        cal = getattr(h, 'survey_level', None)
        om = float(self.p.get('survey_weight', 0.0)) if cal is not None else 0.0
        sd = om * np.asarray(cal['shift_d']) if cal is not None else 0.0              # [n, K-1]
        sa = om * np.asarray(cal['shift_a']) if cal is not None else 0.0              # [n]
        ld = (h.mu_d[None, :] + delta + beta * z[:, None] + tau_u * self.xi_u[:, None] + pr['tau_e'] * self.xi_e
              + s.get('retention_shift', 0.0) + trend + dd[:, None] + sd)
        la = h.mu_a + pr['beta_a'] * z + pr['tau_a'] * self.xi_a + s.get('affiliation_shift', 0.0) + da + sa
        lv = h.mu_v[None, :] + pr['tau_v'] * self.xi_v[:, None] + sd
        k = float(self.p.get('switch_strength', 1.0))
        hl = s.get('post2100_half_life')
        if hl and year > 2100:              # 'trends gradually stabilise': switching fades toward a floor
            fl = float(s.get('post2100_floor', 0.0))
            k = k * (fl + (1.0 - fl) * 2.0 ** (-(year - 2.5 - 2100.0) / float(hl)))
        d, v, a = SW.apply_caps(SW.expit(ld), SW.expit(lv), SW.expit(la),
                                self.ctx.a['switching'].get('lifetime_outflow_cap', {}).get('by_group'))
        return k * d, k * v, k * a

    def matrices(self, year, z, shares):
        """5-year matrices [n, A, K, K], recomputed every `every` steps (rates move slowly)."""
        key = (year - 2020) // (5 * self.every)
        if self.cache[0] == key:
            return self.cache[1]
        d, v, a = self.rates(year, z)
        T = SW.five_year_matrices(SW.lifetime_matrix(d, v, a, shares), refine=4)
        self.cache = (key, T)
        self.last_rates = (d, v, a)
        return T

    def generation_matrices(self, T, intensity):
        if getattr(self, '_tg_src', None) is not T:
            self._tg = E.generation_matrices(T, intensity)
            self._tg_src = T
        return self._tg


def development(ctx, e0, tfr):
    return SW.development_index(e0, tfr, ctx.a)


# ----------------------------------------------------------------------------- migration
class MigrationPlan:
    def __init__(self, ctx, p, scenario_cfg):
        self.ctx, self.p = ctx, p
        m = scenario_cfg['migration']
        knots = np.array(m['multiplier_knots'], float)
        self.knot_t, self.knot_m = knots[:, 0], np.log(knots[:, 1])
        self.omega_by = m.get('omega_drift_to_gravity_by')
        self.pressure = bool(m.get('pressure_pull', False))
        self.network = ctx.stock2020
        self.mobility = ctx.mobility
        self.omega0 = 1.0 if self.network is None else p['omega']
        self.cap = ctx.a['migration']['cell_cap']['value']
        self.rho = float(p.get('margin_rho', 1.0))
        self.b2100 = None
        self.rate2100 = None
        self.pop2100 = None
        self.dep2100 = None
        self.shortfall = 0.0
        self.balance = []
        self.selectivity_fixed = None
        if ctx.migrant_religion is not None and 'emigrants' in ctx.migrant_religion:
            self.selectivity_fixed = MG.selectivity_from_migrant_composition(ctx.s2020, ctx.migrant_religion['emigrants'])

    def multiplier(self, year):
        return float(np.exp(np.interp(year - 2.5, self.knot_t, self.knot_m)))

    def kernel(self, year):
        om = self.omega0
        if self.omega_by and self.network is not None:
            om = float(np.interp(year, [2020, self.omega_by], [self.omega0, 1.0]))
        return MG.mixed_kernel(self.ctx.gravity, self.network, om)

    def selectivity(self, shares):
        if self.selectivity_fixed is not None:
            return self.selectivity_fixed
        return emigration_selectivity(self.ctx, shares, self.p)

    def flows(self, year, dem, P):
        """Flow matrix F[o, d] for the step ending in `year` given the current population P."""
        pop = P.sum((1, 2, 3))
        mult = self.multiplier(year)
        Km = self.kernel(year)
        if dem['wpp']:
            E_o, I_d, info = MG.margins_from_net(mult * dem['net5'], pop * self.mobility, mult * self.p['turnover'])
            F, a_, b_, err = MG.sinkhorn(Km, E_o, I_d, rho=self.rho, rho_col=self.rho)
            self.balance.append(info['balance_scale'])
            if year == 2100:
                self.b2100 = b_ / max(np.mean(b_[b_ > 0]), 1e-300)
                self.rate2100 = F.sum(1) / np.maximum(pop, 1.0) / mult
                self.pop2100 = pop.copy()
                self.dep2100 = old_age_dependency(P)
                self.mult2100 = mult
            return F
        if self.b2100 is None:
            raise RuntimeError('post-2100 migration needs a 2100 WPP step first')
        E_o = self.rate2100 * mult * pop
        att = MG.congestion_attraction(self.b2100, pop, self.pop2100, self.p['theta'])
        if self.pressure:
            att = att * np.clip(old_age_dependency(P) / np.maximum(self.dep2100, 1e-6), 0.25, 4.0)
        return MG.origin_constrained(Km, E_o, att)

    def realise(self, year, dem, P):
        F = self.flows(year, dem, P)
        sel = self.ctx.selectivity
        if sel is not None and sel.get('kind') == 'affinity' and self.selectivity_fixed is None:
            emig, immig, F_used, short = MG.realise_affinity(F, P, sel['lam'], sel['kappa'], self.cap)
        else:
            emig, immig, F_used, short = MG.realise(F, P, self.selectivity(E.shares(P)), self.cap)
        self.shortfall += short
        self.last_F = F_used
        return emig, immig


def emigration_selectivity(ctx, shares, p=None):
    """Relative chance of emigrating by religion [n, K]: the calibrated minority effect and religion
    propensities (step7_estimate.calibrate_selectivity) when available, else the assumption
    share^-lam_sel (lam_sel = 0: emigrants mirror their origin)."""
    if ctx.selectivity is not None and ctx.selectivity.get('kind') == 'affinity':
        return MG.minority_selectivity(shares, ctx.selectivity['lam'])
    if ctx.selectivity is not None:
        sel = MG.minority_selectivity(shares, ctx.selectivity['lam']) * ctx.selectivity['propensity'][None, :]
        return sel / np.maximum((sel * shares).sum(1, keepdims=True), 1e-300)
    lam = 0.0 if p is None else p.get('lam_sel', 0.0)
    return None if lam <= 0 else MG.minority_selectivity(shares, lam)


def old_age_dependency(P):
    tot = P.sum((1, 2))
    return tot[:, 13:].sum(1) / np.maximum(tot[:, 3:13].sum(1), 1.0)


# ------------------------------------------------------------------------ initial state
def foreign_born_proxy(ctx, year, attrition=45.0):
    """Foreign-born persons per country at `year` without UN stocks: positive WPP net migration
    in earlier years, decayed with mean residence time `attrition` (deaths, onward and return)."""
    y0 = ctx.years_wpp[0]
    if year <= y0:
        return np.zeros(ctx.n)
    rows = ctx.cube['net_migrations'][ctx.yi[y0]:ctx.yi[year]]
    ages = year - np.arange(y0, year)
    stock = (np.maximum(rows, 0.0) * np.exp(-ages / attrition)[:, None]).sum(0)
    return np.minimum(stock, 0.85 * ctx.wpp_at('pop', year))


def initial_population(ctx, p, year, shares, age_dist=None):
    """Persons [n, K, G, A] at `year` from religious shares [n, K]."""
    pop = ctx.wpp_at('pop', year)
    if age_dist is None:
        age_dist = ctx.age_dist(year)
    off = np.array([ctx.a['age_structure']['pew_global_median_age_2010']['by_group'][c] for c in CATS], float) \
        - ctx.a['age_structure']['pew_global_median_age_2010']['world']
    tilt = E.age_tilt_from_offsets(age_dist, np.broadcast_to(p['psi'] * off, (ctx.n, K)))
    if ctx.stock_df is not None and year >= 1990:
        S, _ = D.stock_matrix(ctx.stock_df, ctx.ids, year)
        g1 = np.minimum(S.sum(0), 0.85 * pop)
        w = S
    else:
        g1 = foreign_born_proxy(ctx, year, ctx.a['generations']['foreign_born_proxy_attrition_years']['value'])
        w = ctx.gravity * pop[:, None]                         # gravity-weighted origins
    if ctx.selectivity is not None and ctx.selectivity.get('kind') == 'affinity':
        mix = MG.corridor_mix(shares, ctx.selectivity['lam'], ctx.selectivity['kappa'])      # [o, d, r]
        comp = np.einsum('od,odr->dr', w, mix)
    else:
        sel = emigration_selectivity(ctx, shares, p)
        origin_mix = shares if sel is None else shares * sel
        origin_mix = origin_mix / np.maximum(origin_mix.sum(1, keepdims=True), 1e-300)
        comp = w.T @ origin_mix                                # [dest, K]
    if ctx.migrant_religion is not None and 'immigrants' in ctx.migrant_religion and year >= 2010:
        im = ctx.migrant_religion['immigrants']
        comp = np.where(np.isfinite(im).all(1, keepdims=True), im, comp)
    comp = comp / np.maximum(comp.sum(1, keepdims=True), 1e-300)
    s, _, _ = E.life_tables(np.full(1, 74.0))
    flow_age = MG.AGE_PROPENSITY / MG.AGE_PROPENSITY.sum()
    g1_age = E.stock_age_profile(flow_age, s[0])
    return E.initial_state(pop, shares, age_dist, tilt, g1, comp, g1_age,
                           np.full(ctx.n, p['g2_ratio']), G2_AGE)


# ---------------------------------------------------------------------------- simulate
def default_intensity(p):
    return np.array([1.0, p['h1'], p['h2']])


def simulate(ctx, p, scenario_cfg, hier, draw_idx, start_year=2020, end_year=3030, start_shares=None,
             switching=True, migration=True, keep_years=None, record=True, residual=None):
    """Run one parameter set. Returns dict with shares/pop at kept years, components by period,
    global shares at every step, and diagnostics."""
    keep = set(keep_years or KEEP_YEARS)
    shares0 = ctx.s2020 if start_shares is None else start_shares
    P = initial_population(ctx, p, start_year, shares0)
    dem = Demography(ctx, p)
    fert = Fertility(ctx, p, scenario_cfg)
    sw = SwitchPlan(ctx, p, hier, draw_idx, scenario_cfg) if (switching and hier is not None) else None
    mig = MigrationPlan(ctx, p, scenario_cfg) if migration else None
    inten = default_intensity(p)
    periods = [pr for pr in PERIODS if pr[0] >= start_year and pr[1] <= end_year] or [(start_year, end_year)]
    comp = {pr: E.StepRecord(ctx.n) for pr in periods}
    mig_out = {pr: np.zeros((ctx.n, K)) for pr in periods}
    mig_in = {pr: np.zeros((ctx.n, K)) for pr in periods}
    od = {pr: np.zeros((ctx.n, ctx.n)) for pr in periods[:2]}
    res = {'shares': {}, 'pop': {}, 'foreign_born': {}, 'second_gen': {}, 'world': {}, 'rescale': [],
           'group_tfr_2025': None, 'lifetime_rates': {}}

    def save(year, P):
        sh = E.shares(P)
        res['world'][year] = P.sum((0, 2, 3)) / P.sum()
        if year in keep:
            res['shares'][year] = sh
            res['pop'][year] = P.sum((1, 2, 3))
            res['foreign_born'][year] = P[:, :, 1].sum((1, 2)) / np.maximum(P.sum((1, 2, 3)), 1e-300)
            res['second_gen'][year] = P[:, :, 2].sum((1, 2)) / np.maximum(P.sum((1, 2, 3)), 1e-300)

    save(start_year, P)
    for year in range(start_year + 5, end_year + 1, 5):
        d = dem.period(year)
        s_, so, sb = E.life_tables(d['e0'], d['q5'])
        inp = dict(tfr=d['tfr'], shape=E.asfr_shapes(d['mac']), rel=fert.rel(year, d['tfr']),
                   female_share=d['female_share'], s=s_, s_open=so, s_birth=sb, intensity=inten, T=None)
        if sw is not None:
            if d['wpp'] or sw.s.get('dev_link_until', 2100) >= year:
                z = development(ctx, d['e0'], d['tfr'])
            else:
                z = development(ctx, dem.base2100['e0'], dem.base2100['tfr'])
            inp['T'] = sw.matrices(year, z, E.shares(P))
            inp['Tg'] = sw.generation_matrices(inp['T'], inten)
            if year in (2025, 2050, 2100, 2200, 2500, 3030) and hasattr(sw, 'last_rates'):
                res['lifetime_rates'][year] = tuple(x.copy() for x in sw.last_rates)
        mfn = (lambda Q, y=year, dd=d: mig.realise(y, dd, Q)) if mig is not None else None
        rho = residual(year, P) if residual is not None else None
        P, rec = E.step(P, inp, migration_fn=mfn, rho=rho, natural_growth=d['natural_growth'])
        if rec.rescale is not None:
            res['rescale'].append(float(np.mean(np.abs(np.log(np.maximum(rec.rescale, 1e-12))))))
        if res['group_tfr_2025'] is None:
            res['group_tfr_2025'] = rec.group_tfr
        if record:
            for pr in periods:
                if pr[0] < year <= pr[1]:
                    comp[pr].add(rec)
                    mig_out[pr] += -rec.persons[:, :, 4]
                    mig_in[pr] += rec.persons[:, :, 5]
                    if pr in od and mig is not None:
                        od[pr] += mig.last_F
        save(year, P)
    if 3026 in keep or keep_years is None:
        s25, s30 = res['shares'].get(3025), res['shares'].get(3030)
        if s25 is not None and s30 is not None:
            res['shares'][3026] = 0.8 * s25 + 0.2 * s30
            res['pop'][3026] = np.exp(0.8 * np.log(np.maximum(res['pop'][3025], 1)) + 0.2 * np.log(np.maximum(res['pop'][3030], 1)))
            res['foreign_born'][3026] = 0.8 * res['foreign_born'][3025] + 0.2 * res['foreign_born'][3030]
            res['second_gen'][3026] = 0.8 * res['second_gen'][3025] + 0.2 * res['second_gen'][3030]
    res['components'] = comp
    res['mig_out'], res['mig_in'], res['od'] = mig_out, mig_in, od
    res['final_state'] = P
    res['migration_shortfall'] = 0.0 if mig is None else mig.shortfall
    return res


# ------------------------------------------------------------------------------ hindcast
def hindcast(ctx, p, start_year, start_shares, years=10, hier=None, draw_idx=None, scenario_cfg=None,
             migration=True, return_state=False):
    """Historical run from observed shares at start_year for `years` with WPP estimates.
    Without `hier` there is no switching. Returns (predicted shares, initial state), plus the final
    state when return_state is True."""
    cfg = scenario_cfg or {'switching': {'dev_link_until': 3030}, 'migration': {
        'multiplier_knots': [[1900, 1.0], [3100, 1.0]]}, 'fertility': {}}
    P0 = initial_population(ctx, p, start_year, start_shares)
    P = P0.copy()
    dem = Demography(ctx, p)
    fert = Fertility(ctx, p, cfg)
    fert.gap0 = fert.gap0                     # within-country gaps as in the forecast
    inten = default_intensity(p)
    mig = MigrationPlan(ctx, p, cfg) if migration else None
    if mig is not None and ctx.stock_df is not None:
        S, sy = D.stock_matrix(ctx.stock_df, ctx.ids, start_year)
        mig.network = S
        mig.mobility = ctx.mobility_from(S, sy)
        mig.omega0 = 1.0 if S is None else p['omega']
    sw = SwitchPlan(ctx, p, hier, draw_idx, cfg, every=1) if hier is not None else None
    for year in range(start_year + 5, start_year + years + 1, 5):
        d = dem.period(year)
        s_, so, sb = E.life_tables(d['e0'], d['q5'])
        inp = dict(tfr=d['tfr'], shape=E.asfr_shapes(d['mac']), rel=fert.rel(2022.5, d['tfr']),
                   female_share=d['female_share'], s=s_, s_open=so, s_birth=sb, intensity=inten, T=None)
        if sw is not None:
            z = development(ctx, ctx.wpp_at('e0', start_year), ctx.wpp_at('tfr', start_year))
            inp['T'] = sw.matrices(year, z, E.shares(P))
        mfn = (lambda Q, y=year, dd=d: mig.realise(y, dd, Q)) if mig is not None else None
        P, _ = E.step(P, inp, migration_fn=mfn, natural_growth=d['natural_growth'])
    if return_state:
        return E.shares(P), P0, P
    return E.shares(P), P0
