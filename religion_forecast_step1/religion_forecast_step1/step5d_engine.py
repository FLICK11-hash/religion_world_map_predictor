"""Step 5D engine: country x religion x age cohort-component model (numpy only).

Shares are an OUTPUT of population mechanics, not an input that is tilted:
  births   - group fertility = national WPP TFR x relative-fertility multiplier,
             renormalised so the national aggregate TFR equals the WPP TFR
  deaths   - one model life table (differences come from age structure)
  migration- WPP net migrants; arrivals drawn from a pool of emigrants by religion
  switching- NET switching calibrated so a 2010->2020 hindcast reproduces Pew 2020
Every country is rescaled each step to the WPP (or rule-based) total population.

No file or network access here, so the engine can be unit-tested on synthetic data.
All religion-specific rates live in step5d_assumptions.json (with sources).
"""
from __future__ import annotations

import numpy as np

A = 17                      # age groups 0-4 ... 75-79, 80+
F0, F1 = 3, 10              # reproductive ages 15-19 ... 45-49 (index range)
M0, M1 = 3, 9               # migrant ages 15-19 ... 40-44
S0, S1 = 3, 11              # ages that can switch religion, 15-19 ... 50-54
ASFR_SHAPE = np.array([.09, .24, .26, .20, .13, .06, .02])   # sums to 1
MIGRANT_AGE = np.array([.15, .27, .25, .17, .10, .06])       # sums to 1
_FINE = np.arange(0.0, 100.0, 0.25)
_BIN = np.minimum((_FINE // 5).astype(int), A - 1)


# ---------------------------------------------------------------- life table
def _hazard(age, b):
    return 0.0004 + 0.02 * np.exp(-0.9 * age) + b * np.exp(0.09 * age)


def _survival_curve(b):
    h = _hazard(_FINE, b)
    return np.exp(-np.concatenate([[0.0], np.cumsum(h[:-1] * 0.25)]))


def life_table(e0):
    """5-year survival ratios between age groups, calibrated to life expectancy e0."""
    lo, hi = 1e-8, 1e-2
    for _ in range(60):
        mid = np.sqrt(lo * hi)
        if (_survival_curve(mid) * 0.25).sum() > e0:
            lo = mid
        else:
            hi = mid
    S = _survival_curve(np.sqrt(lo * hi))
    at = lambda a: S[min(int(round(a / 0.25)), len(S) - 1)]
    s = np.array([at(5 * (i + 1)) / at(5 * i) for i in range(A - 1)])
    s_last = float(at(91.0) / at(86.0))      # open 80+ group, mean age about 86
    return s, s_last, float(np.sqrt(s[0])), S


# ----------------------------------------------------------- age pyramids
def median_age_of(pop):
    """Median age of arrays [..., A] with linear interpolation inside bins."""
    pop = np.asarray(pop, float)
    tot = np.maximum(pop.sum(-1, keepdims=True), 1e-300)
    cum = np.cumsum(pop / tot, -1)
    j = np.minimum((cum < 0.5).sum(-1), A - 1)
    before = np.take_along_axis(cum, np.maximum(j[..., None] - 1, 0), -1)[..., 0]
    before = np.where(j == 0, 0.0, before)
    inbin = np.take_along_axis(pop / tot, j[..., None], -1)[..., 0]
    width = np.where(j == A - 1, 15.0, 5.0)
    return 5.0 * j + width * np.clip((0.5 - before) / np.maximum(inbin, 1e-300), 0, 1)


def _pyramid_table():
    _, _, _, S = life_table(72.0)
    r_grid = np.linspace(-0.03, 0.07, 201)
    table = np.zeros((len(r_grid), A))
    for i, r in enumerate(r_grid):
        w = np.exp(-r * _FINE) * S
        row = np.bincount(_BIN, weights=w, minlength=A)
        table[i] = row / row.sum()
    return table, median_age_of(table)


_TABLE, _TABLE_MEDIAN = _pyramid_table()


def pyramid_for_median(median):
    """Stable-population-like age shares [..., A] whose median age equals `median`."""
    m = np.asarray(median, float)
    order = np.arange(len(_TABLE_MEDIAN))
    pos = np.interp(m, _TABLE_MEDIAN[::-1], order[::-1].astype(float))
    lo = np.clip(np.floor(pos).astype(int), 0, len(_TABLE) - 2)
    frac = (pos - lo)[..., None]
    return (1 - frac) * _TABLE[lo] + frac * _TABLE[lo + 1]


def initial_population(total, shares, country_median, group_median_offset):
    """Persons [n, K, A]. Group medians = country median + offset, then ONE common
    shift per country so the aggregate median equals the national (WPP) median."""
    n, K = shares.shape
    lo, hi = np.full(n, -20.0), np.full(n, 20.0)
    for _ in range(40):
        d = 0.5 * (lo + hi)
        py = pyramid_for_median(country_median[:, None] + group_median_offset[None, :] + d[:, None])
        agg = (shares[:, :, None] * py).sum(1)
        too_old = median_age_of(agg) > country_median
        hi = np.where(too_old, d, hi)
        lo = np.where(too_old, lo, d)
    d = 0.5 * (lo + hi)
    py = pyramid_for_median(country_median[:, None] + group_median_offset[None, :] + d[:, None])
    return total[:, None, None] * shares[:, :, None] * py


# ----------------------------------------------------------------- the step
class Engine:
    def __init__(self, relative_tfr, median_offset, continent_index, params, adjacency=None):
        """relative_tfr [K]: group TFR / world TFR (global ratios, composition included).
        median_offset [K]: group median age - world median age (global).
        continent_index [n] int, -1 = unknown. params: dict (see step5d_cohort_forecast)."""
        self.rel_global = np.asarray(relative_tfr, float)
        self.p = dict(params)
        # Global gaps mix composition (where each group lives) with true within-country
        # gaps, so only a fraction `phi` is applied inside a country.
        self.rel_within = 1.0 + self.p['phi'] * (self.rel_global - 1.0)
        self.median_offset = self.p['psi'] * np.asarray(median_offset, float)
        self.cont = np.asarray(continent_index, int)
        self.ncont = int(self.cont.max()) + 1 if (self.cont >= 0).any() else 0
        self.s, self.s_last, self.s_birth, _ = life_table(self.p['e0'])
        self.adj = None if adjacency is None else np.asarray(adjacency, float)   # [n, n] 0/1 land borders
        self.eps = self.p.get('eps')          # [n, K] persistent country x group draw

    # ---- fertility multipliers at `years_since_2020` (gaps converge over time)
    def rel_tfr(self, years_since_2020, n, tfr=None):
        """Group TFR / national TFR. Two ways to apply a gap: multiplicative (same RATIO in every
        country) and additive (same number of CHILDREN, so a bigger ratio where fertility is low).
        Evidence on within-country gaps (e.g. Europe) leans additive, so the run blends them with
        weight `w_add`. Both reduce to 1 when gaps are zero."""
        eps = 0.0 if self.eps is None else self.eps
        gap = (self.rel_within[None, :] - 1.0 + eps) * np.exp(-max(years_since_2020, 0.0) / self.p['Hf'])
        if self.p.get('equal_fertility'):
            gap = gap * 0.0
        rel = 1.0 + gap
        w = float(self.p.get('w_add', 0.0))
        if w > 0 and tfr is not None:
            add = gap * float(self.p.get('world_tfr', 2.5)) / np.maximum(np.asarray(tfr, float), 0.8)[:, None]
            rel = (1 - w) * rel + w * (1.0 + add)
        return np.clip(rel, 0.4, 2.0) * np.ones((n, 1))

    def project(self, P, tfr, rel):
        W = 0.5 * P[:, :, F0:F1]
        B0 = (W * ASFR_SHAPE).sum(-1)
        denom = (B0 * rel).sum(1)
        k = np.where(denom > 0, B0.sum(1) / np.maximum(denom, 1e-300), 1.0)
        births5 = tfr[:, None] * k[:, None] * rel * B0
        new = np.zeros_like(P)
        new[:, :, 0] = births5 * self.s_birth
        new[:, :, 1:] = P[:, :, :-1] * self.s[None, None, :]
        new[:, :, -1] += P[:, :, -1] * self.s_last
        return new

    def migrate(self, P, net_annual):
        """Arrivals take the religious mix of an emigrant pool built from WPP net outflows:
        land-border neighbours (weight lam_nb), same continent (lam) and the whole world (rest).
        A pool with no emigrants is skipped and the other weights are renormalised."""
        n, K, _ = P.shape
        adults = P[:, :, M0:M1].sum((1, 2))
        out5 = 5.0 * np.maximum(-net_annual, 0.0)
        in5 = 5.0 * np.maximum(net_annual, 0.0)
        frac = np.minimum(out5 / np.maximum(adults, 1.0), 0.4)
        removed = np.zeros_like(P)
        removed[:, :, M0:M1] = P[:, :, M0:M1] * frac[:, None, None]
        by_group = removed.sum(2)                                   # [n, K]
        pool_g = by_group.sum(0)
        pool_g = pool_g / pool_g.sum() if pool_g.sum() > 0 else \
            P.sum((0, 2)) / max(P.sum(), 1e-300)
        comp = np.zeros((n, K)); weight = np.zeros(n)
        # continent pool (includes the country's own emigrants, as before)
        pc = np.zeros((n, K))
        for c in range(self.ncont):
            m = self.cont == c
            pc[m] = by_group[m].sum(0)
        has_c = pc.sum(1) > 0
        w_c = self.p['lam'] * has_c
        comp += w_c[:, None] * pc / np.maximum(pc.sum(1, keepdims=True), 1e-300); weight += w_c
        if self.adj is not None and self.p.get('lam_nb', 0.0) > 0:
            pn = self.adj @ by_group
            has_n = pn.sum(1) > 0
            w_n = self.p['lam_nb'] * has_n
            comp += w_n[:, None] * pn / np.maximum(pn.sum(1, keepdims=True), 1e-300); weight += w_n
        w_g = 1.0 - weight
        comp += w_g[:, None] * pool_g[None, :]
        mix = comp / np.maximum(comp.sum(1, keepdims=True), 1e-300)
        arrivals = np.zeros_like(P)
        arrivals[:, :, M0:M1] = (in5[:, None, None] * mix[:, :, None]) * MIGRANT_AGE[None, None, :]
        return P - removed + arrivals

    def switch(self, P, rho, factor):
        """Move persons between groups so shares change by `factor * rho` (zero-sum rho)."""
        total = P.sum((1, 2))
        want = factor * rho * total[:, None]
        loss = np.maximum(-want, 0.0)
        adult = P[:, :, S0:S1].sum(2)
        loss = np.minimum(loss, 0.3 * adult)
        gain = np.maximum(want, 0.0)
        gain *= np.where(gain.sum(1) > 0, loss.sum(1) / np.maximum(gain.sum(1), 1e-300), 0.0)[:, None]
        removed = np.zeros_like(P)
        removed[:, :, S0:S1] = P[:, :, S0:S1] * (loss / np.maximum(adult, 1e-300))[:, :, None]
        pooled = removed.sum(1)                                     # [n, A]
        pooled = pooled / np.maximum(pooled.sum(1, keepdims=True), 1e-300)
        return P - removed + gain[:, :, None] * pooled[:, None, :]

    def step(self, P, dem_prev, dem_cur, years_since_2020, rho=None, switch_factor=0.0,
             migration=True):
        n = P.shape[0]
        tfr = 0.5 * (dem_prev['tfr'] + dem_cur['tfr'])
        Q = self.project(P, tfr, self.rel_tfr(years_since_2020, n, tfr))
        if migration:
            Q = self.migrate(Q, 0.5 * (dem_prev['net_migrations'] + dem_cur['net_migrations']))
        if rho is not None and switch_factor > 0:
            Q = self.switch(Q, rho, switch_factor)
        scale = dem_cur['wpp_population'] / np.maximum(Q.sum((1, 2)), 1e-300)
        return Q * scale[:, None, None], np.abs(np.log(scale))


def shares_of(P):
    t = P.sum(2)
    return t / np.maximum(t.sum(1, keepdims=True), 1e-300)


# ------------------------------------------------------- switching calibration
def calibrate_switching(observed2020, predicted2020, categories, tv_cap=0.10, valid=None):
    """Net share change NOT explained by births/deaths/migration over 2010-2020.
    Folk/Other are combined (their split is a proxy), TV capped at 10 pp/decade,
    rows without a Pew 2010 baseline get zero."""
    rho = observed2020 - predicted2020
    i, j = categories.index('Folk_Traditional'), categories.index('Other')
    comb = rho[:, i] + rho[:, j]
    w = observed2020[:, [i, j]]
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-12)
    rho[:, i], rho[:, j] = comb * w[:, 0], comb * w[:, 1]
    tv = 0.5 * np.abs(rho).sum(1)
    rho *= np.minimum(1.0, tv_cap / np.maximum(tv, 1e-12))[:, None]
    if valid is not None:
        rho[~valid] = 0.0
    return rho
