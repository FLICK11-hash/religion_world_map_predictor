"""Step 7 religious switching: lifetime transition matrices, age-specific rates, and a hierarchical
(empirical Bayes) estimate for every country with uncertainty.

Vocabulary
  lifetime matrix L[r, s]  share of adults RAISED in r who CURRENTLY identify with s. This is what a
                           survey comparing childhood and current religion measures. It is NOT an
                           annual probability.
  five-year matrices T_a   probability of moving r -> s during one 5-year step while in age group a.
                           Switching is spread over ages 15-49 with weights SWITCH_AGE_WEIGHTS (an
                           assumption: most switching happens in the late teens and twenties). The
                           per-age outflow rate is solved so that the product over ages reproduces
                           the lifetime outflow exactly (row by row).

Parameters per country c (all lifetime probabilities):
  d[c, r]  raised r -> unaffiliated (disaffiliation), r != Unaffiliated
  v[c, r]  raised r -> another religion (conversion); destinations in proportion to local prevalence
  a[c]     raised unaffiliated -> any religion (affiliation / return); destinations by prevalence

Hierarchical model (logit scale):
  logit d[c, r] = mu_d[r] + delta + beta_d * z[c, t] + tau_u * xi_u[c] + tau_e * xi_e[c, r]
  logit a[c]    = mu_a + beta_a * z[c, t] + tau_a * xi_a[c]
  logit v[c, r] = mu_v[r] + tau_v * xi_v[c]
z = development index (standardised life expectancy and log fertility, from WPP). mu_* are prior
centres (assumptions, see config/assumptions.json). delta, beta_d and tau_u are estimated by
maximising the marginal likelihood of the evidence over a grid (empirical Bayes); country effects
xi are then sampled from their posterior by importance weighting.

Evidence used (each optional):
  net   residual share change over a decade that births, deaths, ageing and migration do not
        explain (from a demographic hindcast). Linked to the rates through the exposure of each
        religion's population to switching ages. Student-t likelihood (robust to source breaks).
  survey observed lifetime matrix cells (raised r, current s, proportion, effective n), binomial.
Only the hindcast's UNEXPLAINED part informs switching, so demographic and migration change is
not counted twice; the part switching cannot explain is treated as noise and not extrapolated.
"""
from __future__ import annotations

import numpy as np

from religion_forecast import engine as E

K, U, A = E.K, E.U, E.A
REL = [k for k in range(K) if k != U]          # religions that can disaffiliate
SWITCH_AGES = np.arange(3, 10)                 # 15-19 ... 45-49
SWITCH_AGE_WEIGHTS = np.array([0.20, 0.27, 0.22, 0.14, 0.09, 0.05, 0.03])
_W_AGE = np.zeros(A)
_W_AGE[SWITCH_AGES] = SWITCH_AGE_WEIGHTS


def logit(p):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def expit(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40, 40)))


# ---------------------------------------------------------------------- matrices
def destination_weights(shares, floor=0.002, eta=1.0):
    """Prevalence weights [..., K] for where converts go (higher share, more converts)."""
    w = (np.asarray(shares, float) + floor) ** eta
    return w


def lifetime_matrix(d, v, a, shares, floor=0.002, eta=1.0):
    """Row-stochastic lifetime matrices [..., K, K] from d [..., K-1], v [..., K-1], a [...]
    (ordered as REL). Total outflow per row is capped at 0.95."""
    d = np.asarray(d, float)
    v = np.asarray(v, float)
    a = np.asarray(a, float)
    lead = d.shape[:-1]
    L = np.zeros(lead + (K, K))
    w = destination_weights(shares, floor, eta)
    w = np.broadcast_to(w, lead + (K,))
    out = np.minimum(d + v, 0.95)
    scale = np.where(d + v > 0, out / np.maximum(d + v, 1e-300), 0.0)
    d, v = d * scale, v * scale
    for j, r in enumerate(REL):
        wr = w.copy()
        wr[..., r] = 0.0
        wr[..., U] = 0.0
        wr = wr / np.maximum(wr.sum(-1, keepdims=True), 1e-300)
        L[..., r, :] = v[..., j, None] * wr
        L[..., r, U] += d[..., j]
        L[..., r, r] = 1.0 - d[..., j] - v[..., j]
    wa = w.copy()
    wa[..., U] = 0.0
    wa = wa / np.maximum(wa.sum(-1, keepdims=True), 1e-300)
    a = np.minimum(a, 0.95)
    L[..., U, :] = a[..., None] * wa
    L[..., U, U] = 1.0 - a
    return L


def solve_age_outflow(o, weights=SWITCH_AGE_WEIGHTS, iters=12):
    """x such that prod_a (1 - w_a x) = 1 - o (vectorised, o in [0, 0.98]).
    f(x) = sum_a log(1 - w_a x) - log(1 - o) is decreasing and concave with f(o) >= 0, so Newton's
    method overshoots once and then converges monotonically from the right."""
    o = np.clip(np.asarray(o, float), 0.0, 0.98)
    shape = o.shape
    o = o.reshape(-1)
    target = np.log1p(-o)
    w = weights[None, :]
    xmax = (1.0 - 1e-9) / weights.max()
    x = o.copy()
    for _ in range(iters):
        q = 1.0 - w * x[:, None]
        f = np.log(q).sum(1) - target
        fp = -(w / q).sum(1)
        x = np.clip(x - f / fp, o, xmax)
    return x.reshape(shape)


def five_year_matrices(L, weights=SWITCH_AGE_WEIGHTS, refine=8):
    """Age-specific 5-year matrices [n, A, K, K] (identity outside ages 15-49) whose product over the
    switching ages reproduces the lifetime matrix L. A first pass matches each row's outflow; a
    fixed-point refinement then corrects for people who leave and come back (r -> s -> r), so the
    product matches the whole matrix, not only the diagonal."""
    L = np.asarray(L, float)
    target = L.copy()
    idx = np.arange(K)
    for _ in range(refine):
        M = lifetime_from_five_year(_five_year_once(target, weights))
        target = np.clip(target + (L - M), 0.0, None)
        target[:, idx, idx] = np.maximum(target[:, idx, idx], 0.02)
        target = target / target.sum(2, keepdims=True)
    return _five_year_once(target, weights)


def _five_year_once(L, weights=SWITCH_AGE_WEIGHTS):
    L = np.asarray(L, float)
    n = L.shape[0]
    diag = np.einsum('nkk->nk', L)
    o = 1.0 - diag
    x = solve_age_outflow(o, weights)                              # [n, K]
    p = L.copy()
    idx = np.arange(K)
    p[:, idx, idx] = 0.0
    p = p / np.maximum(o[:, :, None], 1e-300)
    T = np.tile(np.eye(K), (n, A, 1, 1))
    for j, a in enumerate(SWITCH_AGES):
        rate = weights[j] * x                                      # [n, K]
        Ta = p * rate[:, :, None]
        Ta[:, idx, idx] = 1.0 - rate
        T[:, a] = Ta
    return T


def lifetime_from_five_year(T):
    """Product of the age-specific matrices over the switching ages (check helper)."""
    M = np.tile(np.eye(K), (T.shape[0], 1, 1))
    for a in SWITCH_AGES:
        M = M @ T[:, a]
    return M


# ----------------------------------------------------------- linear effect on shares
def exposure(P, intensity=(1.0, 0.5, 0.8), steps=2):
    """Fraction of the national population, by religion, exposed to switching over `steps` 5-year
    steps [n, K]: sum over ages of persons x (sum of age weights the cohort passes through) x
    generation intensity, divided by the total population."""
    P = np.asarray(P, float)
    wsum = np.zeros(A)
    for a in range(A):
        wsum[a] = _W_AGE[a:min(a + steps, A)].sum()
    h = np.asarray(intensity, float)
    ex = (P * wsum[None, None, None, :] * h[None, None, :, None]).sum((2, 3))
    return ex / np.maximum(P.sum((1, 2, 3))[:, None], 1e-300)


def effect_basis(ex, shares, floor=0.002, eta=1.0):
    """First-order change in national shares per unit of each lifetime rate.
    ex [..., K] exposure; shares [..., K]. Returns Bd [..., K-1, K], Bv [..., K-1, K], Ba [..., K]
    so that delta_shares ~ sum_j d_j Bd[j] + sum_j v_j Bv[j] + a Ba."""
    ex = np.asarray(ex, float)
    w = destination_weights(shares, floor, eta)
    lead = ex.shape[:-1]
    Bd = np.zeros(lead + (K - 1, K))
    Bv = np.zeros(lead + (K - 1, K))
    for j, r in enumerate(REL):
        Bd[..., j, U] += ex[..., r]
        Bd[..., j, r] -= ex[..., r]
        wr = w.copy()
        wr[..., r] = 0.0
        wr[..., U] = 0.0
        wr = wr / np.maximum(wr.sum(-1, keepdims=True), 1e-300)
        Bv[..., j, :] = ex[..., r, None] * wr
        Bv[..., j, r] -= ex[..., r]
    wa = w.copy()
    wa[..., U] = 0.0
    wa = wa / np.maximum(wa.sum(-1, keepdims=True), 1e-300)
    Ba = ex[..., U, None] * wa
    Ba[..., U] -= ex[..., U]
    return Bd, Bv, Ba


# --------------------------------------------------------------- development index
def development_index(e0, tfr, cfg):
    """z: mean of standardised life expectancy and standardised -log(TFR), capped at z_max
    (development effects are not extrapolated beyond the most developed observed level)."""
    c = cfg['development_index']
    z = 0.5 * (np.asarray(e0, float) - c['e0_mean']) / c['e0_sd'] \
        + 0.5 * (-np.log(np.maximum(np.asarray(tfr, float), 0.3)) - c['neglogtfr_mean']) / c['neglogtfr_sd']
    return np.clip(z, c['z_min'], c['z_max'])


# ------------------------------------------------------------------ hierarchical model
class Hierarchy:
    """Empirical Bayes fit of switching rates for n countries.

    prior: dict from config/assumptions.json['switching'] with keys mu_d (dict by religion, lifetime
    probabilities at z = 0), mu_a, mu_v (dicts / float), beta_a, tau_e, tau_a, tau_v,
    grids: delta, beta_d, tau_u. M latent draws per country (fixed seed)."""

    def __init__(self, n, prior, M=256, seed=7):
        self.n, self.M, self.prior = n, M, prior
        rng = np.random.default_rng(seed)
        self.xi_u = rng.standard_normal((n, M))
        self.xi_e = rng.standard_normal((n, M, K - 1))
        self.xi_a = rng.standard_normal((n, M))
        self.xi_v = rng.standard_normal((n, M))
        names = [E.CATS[r] for r in REL]
        self.mu_d = logit(np.array([prior['mu_d'][c] for c in names]))
        self.mu_v = logit(np.array([prior['mu_v'][c] for c in names]))
        self.mu_a = float(logit(prior['mu_a']))
        self.H = None
        self.logw = None
        self.grid_table = None

    def rates(self, z, H, idx=None, shift_d=None, shift_a=0.0):
        """Rates for latent draws: d [n, M, K-1], v [n, M, K-1], a [n, M] at development z [n].
        shift_d [K-1] / shift_a: optional logit shifts (survey-level calibration)."""
        delta, beta, tau_u = H
        p = self.prior
        xi_u, xi_e, xi_a, xi_v = self.xi_u, self.xi_e, self.xi_a, self.xi_v
        if idx is not None:
            xi_u, xi_e, xi_a, xi_v = xi_u[idx], xi_e[idx], xi_a[idx], xi_v[idx]
        z = np.asarray(z, float)[:, None]
        if shift_d is None:
            sd = 0.0
        else:
            sd = np.asarray(shift_d, float)
            sd = sd[None, None, :] if sd.ndim == 1 else sd[:, None, :]       # [K-1] or [n, K-1]
        sa = np.asarray(shift_a, float)
        sa = sa[:, None] if sa.ndim == 1 else sa
        ld = (self.mu_d[None, None, :] + delta + beta * z[:, :, None] + tau_u * xi_u[:, :, None]
              + p['tau_e'] * xi_e + sd)
        la = self.mu_a + p['beta_a'] * z + p['tau_a'] * xi_a + sa
        lv = self.mu_v[None, None, :] + p['tau_v'] * xi_v[:, :, None] + sd
        return expit(ld), expit(lv), expit(la)

    # ---- likelihood pieces -------------------------------------------------------
    @staticmethod
    def _t_loglik(resid, scale, nu=4.0):
        x = resid / scale
        return -0.5 * (nu + 1.0) * np.log1p(x * x / nu) - np.log(scale)

    def loglik(self, H, net=None, survey=None):
        """Log-likelihood per country and draw [n, M] for hyperparameters H."""
        ll = np.zeros((self.n, self.M))
        if net is not None:
            # net: dict with z [n, D], Bd [n, D, K-1, K], Bv [n, D, K-1, K], Ba [n, D, K],
            #      y [n, D, K], mask [n, D], scale [K], weight [n, D]
            D = net['y'].shape[1]
            for t in range(D):
                m = net['mask'][:, t]
                if not m.any():
                    continue
                d, v, a = self.rates(net['z'][:, t], H)
                pred = (np.einsum('nmj,njk->nmk', d, net['Bd'][:, t])
                        + np.einsum('nmj,njk->nmk', v, net['Bv'][:, t])
                        + a[:, :, None] * net['Ba'][:, t][:, None, :])
                r = net['y'][:, t][:, None, :] - pred
                lk = self._t_loglik(r, net['scale'][None, None, :]).sum(-1) * (7.0 / 8.0)
                ll += np.where(m[:, None], lk * net['weight'][:, t][:, None], 0.0)
        if survey is not None and len(survey['country']):
            # survey: arrays country [S], raised [S], current [S], p [S], neff [S], z [S]
            for i in np.unique(survey['country']):
                rows = np.flatnonzero(survey['country'] == i)
                d, v, a = self.rates(np.array([survey['z'][rows[0]]]), H, idx=np.array([i]))
                d, v, a = d[0], v[0], a[0]
                for row in rows:
                    r, s = int(survey['raised'][row]), int(survey['current'][row])
                    if r == U and s != U:
                        prob = a
                    elif r != U and s == U:
                        prob = d[:, REL.index(r)]
                    elif r != U and s == r:
                        prob = 1.0 - d[:, REL.index(r)] - v[:, REL.index(r)]
                    elif r == U and s == U:
                        prob = 1.0 - a
                    else:
                        prob = v[:, REL.index(r)]
                    prob = np.clip(prob, 1e-6, 1 - 1e-6)
                    k_obs = survey['p'][row] * survey['neff'][row]
                    ll[i] += k_obs * np.log(prob) + (survey['neff'][row] - k_obs) * np.log1p(-prob)
        return ll

    def fit(self, net=None, survey=None):
        """Grid search over (delta, beta_d, tau_u) maximising the total log marginal likelihood
        log mean_m exp(loglik). Keeps the best H and its importance log-weights per country."""
        g = self.prior['grid']
        rows, best = [], (-np.inf, None, None)
        for delta in g['delta']:
            for beta in g['beta_d']:
                for tau in g['tau_u']:
                    H = (float(delta), float(beta), float(tau))
                    ll = self.loglik(H, net, survey)
                    mx = ll.max(1, keepdims=True)
                    lm = (mx[:, 0] + np.log(np.exp(ll - mx).mean(1)))
                    total = float(lm.sum())
                    rows.append({'delta': H[0], 'beta_d': H[1], 'tau_u': H[2], 'log_marginal': total})
                    if total > best[0]:
                        best = (total, H, ll)
        self.H = best[1]
        self.logw = best[2] - best[2].max(1, keepdims=True)
        self.grid_table = rows
        return self

    def posterior_weights(self):
        w = np.exp(self.logw)
        return w / w.sum(1, keepdims=True)

    def effective_sample_size(self):
        w = self.posterior_weights()
        return 1.0 / (w ** 2).sum(1)

    def sample_indices(self, rng, R):
        """R posterior draws per country [n, R] (indices into the M latent draws)."""
        w = self.posterior_weights()
        c = np.cumsum(w, 1)
        u = rng.random((self.n, R))
        return np.minimum((u[:, :, None] > c[:, None, :]).sum(2), self.M - 1)

    def posterior_summary(self, z):
        """Posterior mean and 5-95% of each rate at development z [n] (for reporting)."""
        d, v, a = self.rates(z, self.H)
        w = self.posterior_weights()
        out = {}
        for name, x in (('d', d), ('v', v)):
            mean = np.einsum('nm,nmj->nj', w, x)
            out[name + '_mean'] = mean
            out[name + '_q05'], out[name + '_q95'] = _weighted_quantiles(x, w, (0.05, 0.95))
        out['a_mean'] = (w * a).sum(1)
        qa = _weighted_quantiles(a[:, :, None], w, (0.05, 0.95))
        out['a_q05'], out['a_q95'] = qa[0][:, 0], qa[1][:, 0]
        return out


def apply_caps(d, v, a, caps):
    """Bound lifetime outflow by the highest values observed in surveys: d + v <= cap[r] (both scaled
    down together) and a <= cap['Unaffiliated']. caps: dict by religion name or None."""
    if not caps:
        return d, v, a
    cap = np.array([caps.get(E.CATS[r], 1.0) for r in REL])
    tot = d + v
    scale = np.where(tot > cap, cap / np.maximum(tot, 1e-300), 1.0)
    return d * scale, v * scale, np.minimum(a, caps.get('Unaffiliated', 1.0))


def _weighted_quantiles(x, w, qs):
    """x [n, M, J], w [n, M] -> tuple of [n, J] arrays."""
    order = np.argsort(x, axis=1)
    xs = np.take_along_axis(x, order, 1)
    ws = np.take_along_axis(np.broadcast_to(w[:, :, None], x.shape), order, 1)
    cw = np.cumsum(ws, 1)
    res = []
    for q in qs:
        k = np.minimum((cw < q).sum(1), x.shape[1] - 1)
        res.append(np.take_along_axis(xs, k[:, None, :], 1)[:, 0, :])
    return tuple(res)


def robust_scale(y, mask, floor=0.002):
    """Per-category noise scale from residuals y [n, D, K]: 1.4826 x median absolute deviation."""
    vals = y[mask]
    if len(vals) < 5:
        return np.full(K, 0.01)
    med = np.median(vals, 0)
    return np.maximum(1.4826 * np.median(np.abs(vals - med), 0), floor)
