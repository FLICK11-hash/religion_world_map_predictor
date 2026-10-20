"""Step 7 international migration: gross origin-destination flows that conserve persons exactly.

Convention: F[o, d] = persons moving from origin o to destination d during one 5-year step.

How many move (margins)
  To 2100, WPP net migration N_c fixes each country's net. Gross flows add two-way circulation at
  rate `turnover` per year, scaled by the country's observed mobility m_c (UN immigrant + emigrant
  stock per person, population-weighted mean 1; step7_model.Context.mobility_from):
  emigrants E_c = 5*turnover*m_c*pop_c + max(-N_c, 0) and immigrants I_c = 5*turnover*m_c*pop_c +
  max(N_c, 0), so I_c - E_c = N_c. WPP nets do not sum to exactly zero worldwide, so the larger side
  is scaled to the smaller (reported as the balance correction). A country cannot receive more than
  all others send; if one country is most of the world, its circulation is cut in both directions
  (net unchanged). This guard never binds with real 2020-2100 margins (largest: USA, 26% of flows).
  After 2100 there is no WPP: emigrants E_c = rate_c x pop_c x scenario multiplier, where rate_c is
  each country's last WPP-period emigration rate, and destinations keep their 2100 attraction with a
  congestion factor (attraction falls as a destination's population grows).
Where they go (pattern)
  kernel K[o, d] = (1 - omega) x network + omega x gravity. network = bilateral migrant stock
  (UN DESA International Migrant Stock: people born in o living in d), the main driver of new
  flows ("chain migration"); gravity = distance, land borders, same continent (used alone when no
  bilateral table is supplied, which the outputs flag). To 2100 the matrix is fitted to E and I by
  Sinkhorn scaling with softness rho: rho = 1 enforces both margins exactly; rho < 1 lets them give
  way where WPP's projected margins do not fit the network (see sinkhorn and margin_rho in
  step7_assumptions.json). World totals of emigrants and immigrants stay equal either way.
Who moves (composition)
  Each corridor o -> d draws from origin cells (religion r, generation g, age a) in proportion to
  persons x age propensity[a] x generation propensity[g] x corridor mix m[o, d, r], with
  m[o, d, r] proportional to share_o[r]^-lambda x (share_d[r] + 0.01)^kappa (realise_affinity):
  lambda > 0 means minorities are more likely to leave, kappa > 0 that migrants favour destinations
  where their religion is common. Both are fitted to Pew's published religion of migrants
  (step7_estimate.calibrate_affinity); lambda = kappa = 0 means migrants mirror their origin's
  (age-adjusted) mix. Nobody can leave more than `cap` of a cell in 5 years: full cells are capped and
  the rest of the outflow goes to cells with room (water-filling). Only if the whole origin is full
  is its outflow reduced, and that shortfall is reported.
Conservation
  immigrants[d, r, a] = sum_o F[o, d] / E_o x emigrants[o, r, a]: the persons who leave o are exactly
  the persons who arrive in d (as first generation). Global totals by religion and age are unchanged
  by migration, so migration cannot create adherents.
"""
from __future__ import annotations

import numpy as np

import step7_engine as E

K, G, A = E.K, E.G, E.A
# Relative migration propensity per person by age group (shape of a standard model migration
# schedule: children move with parents, a peak in the twenties, low at old ages). Assumption.
AGE_PROPENSITY = np.array([0.6, 0.4, 0.35, 0.9, 2.0, 2.2, 1.7, 1.2, 0.85, 0.6, 0.45, 0.35, 0.3,
                           0.25, 0.2, 0.15, 0.1])
GEN_PROPENSITY = np.array([1.0, 1.5, 1.0])     # foreign-born are more likely to move again


def gravity_kernel(dist_km, adj, same_continent, gamma=1.5, b_adj=2.0, b_cont=0.5, min_km=100.0):
    d = np.maximum(np.asarray(dist_km, float), min_km)
    Kg = d ** (-gamma) * (1.0 + b_adj * np.asarray(adj, float)) * (1.0 + b_cont * np.asarray(same_continent, float))
    np.fill_diagonal(Kg, 0.0)
    return Kg


def mixed_kernel(gravity, network=None, omega=1.0):
    """(1 - omega) x network + omega x gravity, each normalised to sum to 1; zero diagonal.
    Without a network table the kernel is gravity only."""
    g = np.asarray(gravity, float)
    g = g / max(g.sum(), 1e-300)
    if network is None or omega >= 1.0:
        Km = g.copy()
    else:
        net = np.asarray(network, float).copy()
        np.fill_diagonal(net, 0.0)
        net = net / max(net.sum(), 1e-300)
        Km = (1.0 - omega) * net + omega * g
    np.fill_diagonal(Km, 0.0)
    return Km


def margins_from_net(net5, pop, turnover):
    """Emigrants E and immigrants I over 5 years with I - E = net (after a global balance)."""
    net5 = np.asarray(net5, float)
    circ = 5.0 * float(turnover) * np.asarray(pop, float)
    pos, neg = np.maximum(net5, 0.0), np.maximum(-net5, 0.0)
    sp, sn = pos.sum(), neg.sum()
    if sp > 0 and sn > 0:
        if sp > sn:
            pos = pos * (sn / sp)
        else:
            neg = neg * (sp / sn)
    E_o = circ + neg
    I_d = circ + pos
    # Nobody migrates to their own country, so a country cannot receive more than all the others
    # send (E_k + I_k <= total). If one country is most of the world this fails; remove the excess
    # from both its emigration and its immigration, which keeps its net migration unchanged.
    tot = E_o.sum()
    over = E_o + I_d - 0.98 * tot
    k = int(np.argmax(over))
    cut = 0.0
    if tot > 0 and over[k] > 0:
        cut = min(float(min(E_o[k], I_d[k])), float(over[k]) / 1.02)
        E_o, I_d = E_o.copy(), I_d.copy()
        E_o[k] -= cut
        I_d[k] -= cut
    return E_o, I_d, dict(net_requested=float(np.abs(net5).sum()), net_used=float((pos + neg).sum()),
                          balance_scale=float(min(sp, sn) / max(sp, sn)) if min(sp, sn) > 0 else 0.0,
                          feasibility_cut=cut)


def _div(x, y, fill=0.0):
    """x / y where y > 0, else `fill`; masked entries are never evaluated (no overflow warnings)."""
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    return np.divide(x, y, out=np.full(x.shape, float(fill)), where=y > 0)


def sinkhorn(Km, row, col, iters=500, tol=1e-10, rho=1.0, rho_col=1.0):
    """Flows F = diag(a) Km diag(b) fitted to row sums `row` (emigrants) and column sums `col` (immigrants).
    rho = rho_col = 1: doubly constrained, both margins exact. rho < 1 makes the rows a soft target,
    a = (row / Km b)^rho, so an origin whose network destinations cannot take its emigrants sends fewer
    instead of forcing them elsewhere (rho = 0: origins in proportion to the kernel); rho_col does the
    same for columns. The margins are scaled to sum to 1 (and the kernel sums to 1), so the result does
    not depend on population units and very unequal populations cannot overflow. Every row and column
    sum is a sum of the same F, so world emigrants always equal world immigrants.
    Returns (F, a, b, max relative error of the margins that are exact; 0 if none is)."""
    row0 = np.asarray(row, float)
    col0 = np.asarray(col, float)
    scale = max(float(row0.sum()), float(col0.sum()), 1e-300)
    row, col = row0 / scale, col0 / scale
    a = np.ones(len(row))
    b = np.ones(len(col))
    for _ in range(iters):
        a = _div(row, Km @ b)
        if rho != 1.0:
            a = a ** rho
        b_new = _div(col, Km.T @ a)
        if rho_col != 1.0:
            b_new = b_new ** rho_col
        if np.max(_div(np.abs(b_new - b), b, fill=0.0) + ((b == 0) & (b_new > 0))) < tol:
            b = b_new
            break
        b = b_new
    F = a[:, None] * Km * b[None, :] * scale
    errs = [np.abs(F.sum(1) - row0).max() / max(row0.max(), 1.0)] if rho == 1.0 else []
    errs += [np.abs(F.sum(0) - col0).max() / max(col0.max(), 1.0)] if rho_col == 1.0 else []
    return F, a * scale, b, float(max(errs, default=0.0))


def origin_constrained(Km, E_o, attraction):
    """F[o, d] = E_o x Km[o, d] x attraction[d] / sum_d' Km[o, d'] x attraction[d'] (post-2100 rule)."""
    W = Km * np.asarray(attraction, float)[None, :]
    rs = W.sum(1, keepdims=True)
    return np.where(rs > 0, W / np.maximum(rs, 1e-300), 0.0) * np.asarray(E_o, float)[:, None]


def propensity(P, selectivity=None):
    """Who leaves: persons x selectivity[o, r] x age propensity x generation propensity [n, K, G, A]."""
    pi = P * AGE_PROPENSITY[None, None, None, :] * GEN_PROPENSITY[None, None, :, None]
    if selectivity is not None:
        pi = pi * np.asarray(selectivity, float)[:, :, None, None]
    return pi


def realise(F, P, selectivity=None, cap=0.5, iters=12):
    """Turn a flow matrix into emigrants [n, K, G, A] and immigrants [n, K, A] (persons), drawing
    emigrants from the current population P [n, K, G, A] in proportion to propensity. No cell can
    lose more than `cap` of its people in 5 years: full cells are capped and the rest of the
    origin's outflow is redistributed over cells with room (water-filling). Only if the whole origin
    is full is its outflow reduced (reported as the shortfall). Returns (emig, immig, F_used, shortfall)."""
    F = np.asarray(F, float).copy()
    np.fill_diagonal(F, 0.0)
    E_req = F.sum(1)
    pi = propensity(P, selectivity)
    room = cap * P
    emig = np.zeros_like(P)
    remaining = E_req.copy()
    active = pi.copy()
    for _ in range(iters):
        tot = active.sum((1, 2, 3))
        add = active * _div(remaining, tot)[:, None, None, None]
        new = np.minimum(emig + add, room)
        remaining = remaining - (new - emig).sum((1, 2, 3))
        emig = new
        if remaining.max(initial=0.0) <= 1e-9 * max(E_req.max(initial=0.0), 1.0):
            break
        active = np.where(emig < room * (1 - 1e-12), pi, 0.0)
    E_used = emig.sum((1, 2, 3))
    scale = np.where(E_req > 0, E_used / np.maximum(E_req, 1e-300), 1.0)
    F = F * scale[:, None]
    share = np.where(E_used[:, None] > 0, F / np.maximum(E_used[:, None], 1e-300), 0.0)     # [o, d]
    immig = np.einsum('od,ora->dra', share, emig.sum(2))
    return emig, immig, F, float(np.maximum(E_req - E_used, 0.0).sum())


def minority_selectivity(shares, lam):
    """Scenario option: religious minorities over-represented among emigrants,
    selectivity_r proportional to share_r^(-lam), normalised so the origin's mean is 1. lam = 0: none."""
    s = np.maximum(np.asarray(shares, float), 1e-4)
    sel = s ** (-float(lam))
    return sel / np.maximum((sel * s).sum(1, keepdims=True), 1e-300)


def selectivity_from_migrant_composition(origin_shares, emigrant_shares, lo=0.1, hi=10.0):
    """Data option: selectivity[o, r] = emigrants' religious share / origin population share
    (e.g. Pew 'Religious Composition of the World's Migrants'), clipped, NaN -> 1."""
    o = np.asarray(origin_shares, float)
    e = np.asarray(emigrant_shares, float)
    sel = np.where(o > 1e-4, e / np.maximum(o, 1e-300), 1.0)
    sel = np.where(np.isfinite(sel), np.clip(sel, lo, hi), 1.0)
    return sel


def congestion_attraction(b2100, pop, pop2100, theta=1.0):
    """Post-2100 destination attraction: the 2100 Sinkhorn attraction b, divided by
    (population / population in 2100)^theta, so a growing destination does not attract ever more."""
    ratio = np.maximum(np.asarray(pop, float), 1.0) / np.maximum(np.asarray(pop2100, float), 1.0)
    return np.asarray(b2100, float) * ratio ** (-float(theta))


def corridor_mix(P_or_shares, lam, kappa, eps=0.01, base=None):
    """Religious mix of each corridor m[o, d, r] (rows sum to 1 over r): origin availability (people
    who can move, times the minority effect share^-lam) x destination affinity (share_d,r + eps)^kappa.
    Pew (2024): migrants tend to move where their religion is common, and minorities emigrate more."""
    sh = np.asarray(P_or_shares, float)
    if base is None:
        base = sh * (minority_selectivity(sh, lam) if lam > 0 else 1.0)
    aff = (sh + eps) ** float(kappa)
    m = base[:, None, :] * aff[None, :, :]
    return m / np.maximum(m.sum(2, keepdims=True), 1e-300)


def realise_affinity(F, P, lam, kappa, cap=0.5, iters=12, eps=0.01):
    """Like realise(), but each corridor (o, d) carries its own religious mix (corridor_mix), so
    for example Christians from Kazakhstan go to Russia and Muslims to Turkey. Emigrants of religion r
    from o are drawn from its generation x age cells in proportion to age and generation propensity,
    each cell capped at `cap`; if a religion's cells are full the shortfall is reported and that
    religion's corridors shrink. Same persons leave and arrive. Returns (emig, immig, F_used, shortfall)."""
    F = np.asarray(F, float).copy()
    np.fill_diagonal(F, 0.0)
    w = P * AGE_PROPENSITY[None, None, None, :] * GEN_PROPENSITY[None, None, :, None]   # [n, K, G, A]
    avail = w.sum((2, 3))
    sh = P.sum((2, 3)) / np.maximum(P.sum((1, 2, 3))[:, None], 1e-300)
    base = avail * (minority_selectivity(sh, lam) if lam > 0 else 1.0)
    m = corridor_mix(sh, lam, kappa, eps, base=base)                      # [o, d, r]
    want = (F[:, :, None] * m).sum(1)                                     # emigrants by origin, religion
    room = cap * P
    emig = np.zeros_like(P)
    remaining = want.copy()
    active = w.copy()
    for _ in range(iters):
        tot = active.sum((2, 3))
        add = active * _div(remaining, tot)[:, :, None, None]
        new = np.minimum(emig + add, room)
        remaining = remaining - (new - emig).sum((2, 3))
        emig = new
        if remaining.max(initial=0.0) <= 1e-9 * max(want.max(initial=0.0), 1.0):
            break
        active = np.where(emig < room * (1 - 1e-12), w, 0.0)
    got = emig.sum((2, 3))
    f = np.where(want > 0, got / np.maximum(want, 1e-300), 1.0)           # realised fraction by (o, r)
    X = F[:, :, None] * m * f[:, None, :]                                 # [o, d, r] persons
    agefrac = emig.sum(2) / np.maximum(got[:, :, None], 1e-300)           # [o, r, a]
    # immig[d, r, a] = sum_o X[o, d, r] agefrac[o, r, a], as a batched matrix product over religions
    immig = np.matmul(X.transpose(2, 1, 0), agefrac.transpose(1, 0, 2)).transpose(1, 0, 2)
    return emig, immig, X.sum(2), float(np.maximum(want - got, 0.0).sum())
