"""Step 7 engine: country x religion x generation x age cohort-component model (numpy only).

State P has shape [n, K, G, A] and holds persons:
  n countries, K = 8 religions, G = 3 generations, A = 17 five-year age groups (0-4 ... 75-79, 80+).
  Generation 0 = natives (third generation or later), 1 = first generation (foreign-born),
  2 = second generation (native-born children of first-generation mothers).

One 5-year step applies these sub-steps, in this order:
  1 survival     people move up one age group; deaths leave (one life table per country)
  2 births       group fertility; a child takes the mother's religion; mother g0 -> child g0,
                 g1 -> g2, g2 -> g0
  3 switching    age-specific transition matrices (rows sum to one), with a generation intensity
  4 emigration   persons leave the origin (step7_migration computes who and how many)
  5 immigration  the same persons arrive at the destination as first generation
  6 residual     optional zero-sum share adjustment (weight chosen by validation; default 0)
  calibration    (applied right after births, recorded separately) uniform rescale so the country's
                 NATURAL growth over the step equals WPP's (to 2100 only). It acts like a common
                 correction to fertility and mortality, leaves shares unchanged, and never touches
                 migrants, so migration stays exactly conserved and migration scenarios can move
                 national totals away from WPP.
Each sub-step's change in persons and in religious shares is recorded, so the component
breakdowns add up exactly to the simulated change. Nothing here reads files.
"""
from __future__ import annotations

import numpy as np

CATS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism',
        'Folk_Traditional', 'Other', 'Unaffiliated']
K = len(CATS)
U = CATS.index('Unaffiliated')
G = 3
GEN_NAMES = ['native', 'first_generation', 'second_generation']
CHILD_GEN = np.array([0, 2, 0])            # generation of a child, by mother's generation
A = 17
F0, F1 = 3, 10                             # reproductive ages 15-19 ... 45-49
AGE_MID = np.array([2.5 + 5 * i for i in range(A - 1)] + [85.0])
COMPONENTS = ['births', 'deaths', 'switch_in', 'switch_out', 'emigration', 'immigration',
              'residual', 'calibration']
SHARE_STEPS = ['survival', 'births', 'switching', 'emigration', 'immigration', 'residual', 'calibration']

# ----------------------------------------------------------------------------- life tables
_FINE = np.arange(0.0, 110.0, 0.25)
_LT_CACHE: dict = {}


def _survival_fine(b, c):
    h = 0.0004 + c * np.exp(-0.9 * _FINE) + b * np.exp(0.09 * _FINE)
    return np.exp(-np.concatenate([[0.0], np.cumsum(h[:-1] * 0.25)]))


def _child_term(b, q5):
    """Child hazard scale c so that the probability of dying before age 5 equals q5."""
    target = -np.log(max(1e-6, 1.0 - q5))
    gomp = b * (np.exp(0.45) - 1.0) / 0.09
    return max(0.0, (target - 0.002 - gomp) / ((1.0 - np.exp(-4.5)) / 0.9))


def life_table(e0, q5=None):
    """Survival quantities for one life expectancy e0 (and optional under-5 mortality q5, a
    probability). Returns (s [A-1], s_open, s_birth):
      s[a]    person-year ratio 5L(a+1)/5L(a): survival from age group a to a+1 over 5 years,
              with s[A-2] = T80/T75 (75-79 into 80+)
      s_open  T85/T80, survival of the open 80+ group over 5 years
      s_birth L(0-5)/5, average survival to the end of the period of births spread over it."""
    e0 = float(np.clip(e0, 40.0, 95.0))
    q5 = None if q5 is None or not np.isfinite(q5) else float(np.clip(q5, 0.001, 0.4))
    key = (round(e0, 2), None if q5 is None else round(q5, 4))
    if key in _LT_CACHE:
        return _LT_CACHE[key]
    lo, hi = 1e-9, 5e-2
    for _ in range(70):
        b = np.sqrt(lo * hi)
        c = 0.02 if q5 is None else _child_term(b, q5)
        S = _survival_fine(b, c)
        if (S * 0.25).sum() > e0:
            lo = b
        else:
            hi = b
    b = np.sqrt(lo * hi)
    S = _survival_fine(b, 0.02 if q5 is None else _child_term(b, q5))
    py = S * 0.25
    L = np.array([py[(_FINE >= 5 * i) & (_FINE < 5 * i + 5)].sum() for i in range(A - 1)])
    T = lambda x: py[_FINE >= x].sum()
    s = np.empty(A - 1)
    s[:-1] = L[1:] / np.maximum(L[:-1], 1e-300)
    s[-1] = T(80.0) / max(T(75.0), 1e-300)
    out = (s, float(T(85.0) / max(T(80.0), 1e-300)), float(L[0] / 5.0))
    _LT_CACHE[key] = out
    return out


_GRID = {}
_GRID_E0 = np.arange(40.0, 95.01, 0.5)
_GRID_LQ = np.linspace(np.log(0.001), np.log(0.4), 40)


def _grid():
    """Life tables on an (e0, log q5) grid, built once (about 4,400 tables), for fast interpolation."""
    if not _GRID:
        S = np.zeros((len(_GRID_E0), len(_GRID_LQ), A + 1))
        for i, e in enumerate(_GRID_E0):
            for j, lq in enumerate(_GRID_LQ):
                s, so, sb = life_table(float(e), float(np.exp(lq)))
                S[i, j, :A - 1], S[i, j, A - 1], S[i, j, A] = s, so, sb
        _GRID['S'] = S
    return _GRID['S']


def life_tables(e0, q5=None):
    """Life tables for many countries: S [n, A-1], s_open [n], s_birth [n]. Bilinear interpolation
    on a precomputed (e0, log q5) grid; without q5 the default child mortality term is used."""
    e0 = np.clip(np.atleast_1d(np.asarray(e0, float)), 40.0, 95.0)
    if q5 is None:
        rows = [life_table(round(float(e), 1)) for e in e0]
        return (np.array([r[0] for r in rows]), np.array([r[1] for r in rows]), np.array([r[2] for r in rows]))
    lq = np.log(np.clip(np.atleast_1d(np.asarray(q5, float)), 0.001, 0.4))
    lq = np.where(np.isfinite(lq), lq, np.log(0.03))
    S = _grid()
    fi = (e0 - _GRID_E0[0]) / (_GRID_E0[1] - _GRID_E0[0])
    fj = (lq - _GRID_LQ[0]) / (_GRID_LQ[1] - _GRID_LQ[0])
    i0 = np.clip(np.floor(fi).astype(int), 0, len(_GRID_E0) - 2)
    j0 = np.clip(np.floor(fj).astype(int), 0, len(_GRID_LQ) - 2)
    ti, tj = (fi - i0)[:, None], (fj - j0)[:, None]
    v = ((1 - ti) * (1 - tj) * S[i0, j0] + ti * (1 - tj) * S[i0 + 1, j0]
         + (1 - ti) * tj * S[i0, j0 + 1] + ti * tj * S[i0 + 1, j0 + 1])
    return v[:, :A - 1], v[:, A - 1], v[:, A]


def life_expectancy_of(e0, q5=None):
    """Check helper: life expectancy implied by the fitted table (should equal e0)."""
    e0 = float(np.clip(e0, 40.0, 95.0))
    lo, hi = 1e-9, 5e-2
    for _ in range(70):
        b = np.sqrt(lo * hi)
        c = 0.02 if q5 is None else _child_term(b, q5)
        if (_survival_fine(b, c) * 0.25).sum() > e0:
            lo = b
        else:
            hi = b
    b = np.sqrt(lo * hi)
    return float((_survival_fine(b, 0.02 if q5 is None else _child_term(b, q5)) * 0.25).sum())


# ------------------------------------------------------------------ fertility age pattern
_ASFR_MID = AGE_MID[F0:F1]
_ASFR_CACHE: dict = {}


def asfr_shape(mac):
    """Share of the TFR born to each 5-year age group 15-19 ... 45-49 [7], a discretised normal
    curve (sd 6 years) whose mean equals the mean age at childbearing `mac` (WPP 'MAC')."""
    mac = float(np.clip(mac if np.isfinite(mac) else 28.5, 22.0, 36.0))
    key = round(mac, 2)
    if key not in _ASFR_CACHE:
        lo, hi = 10.0, 50.0
        for _ in range(60):
            mu = 0.5 * (lo + hi)
            w = np.exp(-0.5 * ((_ASFR_MID - mu) / 6.0) ** 2)
            if (w * _ASFR_MID).sum() / w.sum() > mac:
                hi = mu
            else:
                lo = mu
        w = np.exp(-0.5 * ((_ASFR_MID - 0.5 * (lo + hi)) / 6.0) ** 2)
        _ASFR_CACHE[key] = w / w.sum()
    return _ASFR_CACHE[key]


_MAC_GRID = np.round(np.arange(22.0, 36.0001, 0.05), 2)
_SHAPE_TABLE = None


def asfr_shapes(mac):
    """asfr_shape for many countries at once (linear interpolation on a 0.05-year MAC grid)."""
    global _SHAPE_TABLE
    if _SHAPE_TABLE is None:
        _SHAPE_TABLE = np.array([asfr_shape(m) for m in _MAC_GRID])
    m = np.clip(np.nan_to_num(np.atleast_1d(np.asarray(mac, float)), nan=28.5), 22.0, 36.0)
    f = (m - 22.0) / 0.05
    i0 = np.clip(np.floor(f).astype(int), 0, len(_MAC_GRID) - 2)
    t = (f - i0)[:, None]
    return (1 - t) * _SHAPE_TABLE[i0] + t * _SHAPE_TABLE[i0 + 1]


# ---------------------------------------------------------------------------- sub-steps
def shares(P):
    t = P.sum((2, 3))
    return t / np.maximum(t.sum(1, keepdims=True), 1e-300)


def survive(P, s, s_open):
    """Sub-step 1. Returns (aged population, deaths by [n, K, G])."""
    new = np.zeros_like(P)
    new[..., 1:] = P[..., :-1] * s[:, None, None, :]
    new[..., -1] += P[..., -1] * s_open[:, None, None]
    deaths = P.sum(-1) - new.sum(-1)
    return new, deaths


def births(P_start, P_aged, tfr, shape, rel, female_share, s_birth):
    """Sub-step 2. Births over the 5 years by mother's religion and generation.

    Women-years in each age group are the average of the start and end (survivor) populations
    times the female share (national [n], or by reproductive age group [n, 7] from WPP). Group
    fertility = national TFR x k x rel, where k makes the national total equal TFR applied to all
    women (so the national TFR is reproduced exactly).
    Returns (newborns placed in age group 0 by child's generation [n, K, G], live births by mother
    [n, K, G], infant deaths [n, K, G] by child's generation, group TFR [n, K, G])."""
    fs = np.asarray(female_share, float)
    fs = fs[:, None, None, None] if fs.ndim == 1 else fs[:, None, None, :]
    W = 0.5 * (P_start[..., F0:F1] + P_aged[..., F0:F1]) * fs
    base = (W * shape[:, None, None, :]).sum(-1)                     # [n, K, G]
    denom = (base * rel).sum((1, 2))
    k = np.where(denom > 0, base.sum((1, 2)) / np.maximum(denom, 1e-300), 1.0)
    group_tfr = tfr[:, None, None] * k[:, None, None] * rel
    born = group_tfr * base                                           # live births by mother
    by_child = np.zeros_like(born)
    for g in range(G):
        by_child[:, :, CHILD_GEN[g]] += born[:, :, g]
    survivors = by_child * s_birth[:, None, None]
    return survivors, born, by_child - survivors, group_tfr


def generation_matrices(T, intensity):
    """T [n, A, K, K] row-stochastic 5-year transition matrices (identity outside switching ages),
    intensity [G]: generation scaling of switching (natives 1). Returns [n, G, A, K, K]."""
    I = np.eye(T.shape[-1])
    return I + np.asarray(intensity, float)[None, :, None, None, None] * (T[:, None] - I)


def switch(P, Tg):
    """Sub-step 3. Apply religion transition matrices. Returns (new P, switch_in [n,K], switch_out [n,K])."""
    new = np.einsum('nkga,ngakl->nlga', P, Tg)
    stay = np.einsum('nkga,ngakk->nkga', P, Tg)
    switch_out = (P - stay).sum((2, 3))
    switch_in = (new - stay).sum((2, 3))
    return new, switch_in, switch_out


def residual_transfer(P, rho, cap=0.3):
    """Sub-step 6 (optional). Move persons so religious shares change by rho [n, K] (rows sum to 0).
    Losses come from ages 15-54 in proportion; gains copy the age/generation mix of the losses."""
    rho = np.asarray(rho, float)
    total = P.sum((1, 2, 3))
    want = rho * total[:, None]
    adult = P[..., 3:11].sum((2, 3))
    loss = np.minimum(np.maximum(-want, 0.0), cap * adult)
    gain = np.maximum(want, 0.0)
    gsum = gain.sum(1)
    gain = gain * np.where(gsum > 0, loss.sum(1) / np.maximum(gsum, 1e-300), 0.0)[:, None]
    removed = np.zeros_like(P)
    removed[..., 3:11] = P[..., 3:11] * (loss / np.maximum(adult, 1e-300))[:, :, None, None]
    pooled = removed.sum(1)
    pooled = pooled / np.maximum(pooled.sum((1, 2), keepdims=True), 1e-300)
    new = P - removed + gain[:, :, None, None] * pooled[:, None]
    return new, new.sum((2, 3)) - P.sum((2, 3))


class StepRecord:
    """Persons by component [n, K, len(COMPONENTS)] and share change by sub-step [n, K, len(SHARE_STEPS)]."""

    def __init__(self, n):
        self.persons = np.zeros((n, K, len(COMPONENTS)))
        self.share = np.zeros((n, K, len(SHARE_STEPS)))
        self.world_share = np.zeros((K, len(SHARE_STEPS)))
        self.group_tfr = None
        self.rescale = None

    def add(self, other):
        self.persons += other.persons
        self.share += other.share
        self.world_share += other.world_share


def step(P, inp, emig=None, immig=None, migration_fn=None, rho=None, natural_growth=None):
    """One 5-year step. `inp` holds per-country arrays for the period:
      tfr [n], shape [n, 7], rel [n, K, G], female_share [n], s [n, A-1], s_open [n], s_birth [n],
      T [n, A, K, K] (or None for no switching), intensity [G].
    Migration: either precomputed (emig [n, K, G, A], immig [n, K, A]) or a callable
    migration_fn(P_after_switching) -> (emig, immig) so flows see the current religious mix.
    rho [n, K] optional residual. natural_growth [n] optional WPP natural growth factor
    (WPP population at the end minus WPP net migration, over WPP population at the start).
    Returns (P_next, StepRecord)."""
    n = P.shape[0]
    rec = StepRecord(n)
    s0 = shares(P)
    world = lambda X: X.sum((0, 2, 3)) / max(X.sum(), 1e-300)
    w0 = world(P)

    aged, deaths = survive(P, inp['s'], inp['s_open'])
    s1, w1 = shares(aged), world(aged)
    newborn, born, infant_deaths, group_tfr = births(P, aged, inp['tfr'], inp['shape'], inp['rel'],
                                                     inp['female_share'], inp['s_birth'])
    Q = aged.copy()
    Q[..., 0] += newborn
    s2, w2 = shares(Q), world(Q)
    rec.persons[:, :, 0] = born.sum(2)
    rec.persons[:, :, 1] = -(deaths.sum(2) + infant_deaths.sum(2))
    rec.group_tfr = group_tfr

    if natural_growth is not None:
        start, now = P.sum((1, 2, 3)), Q.sum((1, 2, 3))
        g = np.asarray(natural_growth, float)
        scale = np.where((now > 0) & np.isfinite(g), start * g / np.maximum(now, 1e-300), 1.0)
        before = Q.sum((2, 3))
        Q = Q * scale[:, None, None, None]
        rec.persons[:, :, 7] = Q.sum((2, 3)) - before
        rec.rescale = scale
    s2c, w2c = shares(Q), world(Q)

    if inp.get('T') is not None:
        Tg = inp.get('Tg')
        Q, s_in, s_out = switch(Q, Tg if Tg is not None else generation_matrices(inp['T'], inp['intensity']))
        rec.persons[:, :, 2] = s_in
        rec.persons[:, :, 3] = -s_out
    s3, w3 = shares(Q), world(Q)

    if migration_fn is not None:
        emig, immig = migration_fn(Q)
    if emig is not None:
        Q = Q - emig
        Q = np.maximum(Q, 0.0)
        rec.persons[:, :, 4] = -emig.sum((2, 3))
    s4, w4 = shares(Q), world(Q)
    if immig is not None:
        Q[:, :, 1, :] += immig
        rec.persons[:, :, 5] = immig.sum(2)
    s5, w5 = shares(Q), world(Q)

    if rho is not None:
        Q, moved = residual_transfer(Q, rho)
        rec.persons[:, :, 6] = moved
    s6, w6 = shares(Q), world(Q)

    for j, (a, b) in enumerate([(s0, s1), (s1, s2), (s2c, s3), (s3, s4), (s4, s5), (s5, s6), (s2, s2c)]):
        rec.share[:, :, j] = b - a
    for j, (a, b) in enumerate([(w0, w1), (w1, w2), (w2c, w3), (w3, w4), (w4, w5), (w5, w6), (w2, w2c)]):
        rec.world_share[:, j] = b - a
    return Q, rec


# ----------------------------------------------------------------------- initial state
def initial_state(total, religion_shares, age_dist, group_age_tilt, g1_total, g1_comp,
                  g1_age, g2_ratio, g2_age):
    """Persons [n, K, G, A] in the start year.

    total [n] persons; religion_shares [n, K] (observed, e.g. Pew 2020); age_dist [n, A] national
    age shares; group_age_tilt [n, K, A] relative age profile of each religion (rows normalised
    inside); g1_total [n] foreign-born persons; g1_comp [n, K] their religious mix; g1_age [A];
    g2_ratio [n] second generation as a multiple of first; g2_age [A].
    Observed national totals by religion are kept exactly: migrants are carved out of each
    religion's total, capped at 90% of it, with any excess moved to religions with room."""
    n = len(total)
    by_rel = total[:, None] * religion_shares                         # [n, K]
    want1 = g1_total[:, None] * g1_comp
    want2 = (g1_total * g2_ratio)[:, None] * g1_comp
    room = 0.9 * by_rel
    mig = want1 + want2
    over = np.maximum(mig - room, 0.0)
    mig = np.minimum(mig, room)
    excess = over.sum(1)
    slack = np.maximum(room - mig, 0.0)
    mig = mig + slack * np.where(slack.sum(1) > 0, np.minimum(excess / np.maximum(slack.sum(1), 1e-300), 1.0),
                                 0.0)[:, None]
    frac1 = np.where(want1 + want2 > 0, want1 / np.maximum(want1 + want2, 1e-300), 0.5)
    m1, m2 = mig * frac1, mig * (1 - frac1)
    natives = np.maximum(by_rel - m1 - m2, 0.0)
    P = np.zeros((n, K, G, A))
    P[:, :, 1, :] = m1[:, :, None] * g1_age[None, None, :]
    P[:, :, 2, :] = m2[:, :, None] * g2_age[None, None, :]
    # natives: national age distribution minus migrants' ages, tilted by religion, then each
    # religion's native total is matched exactly
    nat_age = np.maximum(total[:, None] * age_dist - P[:, :, 1:, :].sum((1, 2)), 0.0)
    nat_age = nat_age / np.maximum(nat_age.sum(1, keepdims=True), 1e-300)
    tilt = group_age_tilt * nat_age[:, None, :]
    tilt = tilt / np.maximum(tilt.sum(2, keepdims=True), 1e-300)
    P[:, :, 0, :] = natives[:, :, None] * tilt
    return P


def age_tilt_from_offsets(age_dist, offsets_years, width=12.0):
    """Relative age profiles per religion [n, K, A]: exp(offset * (age - mean) / width^2), a mild
    exponential tilt that makes a group older (offset > 0) or younger (offset < 0) than the country.
    Offsets in years (e.g. psi x Pew global median-age gaps)."""
    mean = (age_dist * AGE_MID).sum(1, keepdims=True)
    x = (AGE_MID[None, :] - mean)[:, None, :]
    return np.exp(np.clip(np.asarray(offsets_years)[..., None] * x / width ** 2, -30, 30))


def stock_age_profile(flow_age, s, years=50):
    """Age distribution of a migrant STOCK built from constant arrivals with age profile flow_age,
    aged forward with survival s [A-1] for `years`."""
    stock = np.zeros(A)
    cur = flow_age.copy()
    for _ in range(int(years // 5)):
        stock += cur
        nxt = np.zeros(A)
        nxt[1:] = cur[:-1] * s
        nxt[-1] += cur[-1] * s[-1]
        cur = nxt
    return stock / stock.sum()


def gini_simpson(sh):
    """Religious diversity: probability two random residents differ in religion (0 = one group)."""
    sh = np.asarray(sh, float)
    return 1.0 - (sh ** 2).sum(-1)


def effective_number(sh):
    return 1.0 / np.maximum((np.asarray(sh, float) ** 2).sum(-1), 1e-300)
