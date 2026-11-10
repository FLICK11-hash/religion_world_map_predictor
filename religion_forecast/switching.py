"""Religious switching: lifetime transition matrices, age-specific rates, and a hierarchical
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
  survey observed lifetime matrix cells (raised r, current s, proportion, effective n), one
        multinomial per survey row, with unreported cells pooled into a complement.
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


_LANCZOS = np.array([0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
                     -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
                     1.5056327351493116e-7])


def lgamma(x):
    """log Gamma(x) for x > 0, vectorised (Lanczos approximation, g = 7; relative error ~1e-15),
    with the reflection formula below 0.5."""
    x = np.asarray(x, float)
    small = x < 0.5
    z = np.where(small, 1.0 - x, x) - 1.0
    acc = np.full(z.shape, _LANCZOS[0])
    for i in range(1, 9):
        acc = acc + _LANCZOS[i] / (z + i)
    t = z + 7.5
    big = 0.5 * np.log(2 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(acc)
    return np.where(small, np.log(np.pi) - np.log(np.abs(np.sin(np.pi * x))) - big, big)


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
    generation intensity, divided by the total population. The engine ages people before it
    switches them, so a cohort in age group a at the start meets the matrices of groups
    a + 1, ..., a + steps."""
    P = np.asarray(P, float)
    wsum = np.zeros(A)
    for a in range(A):
        wsum[a] = _W_AGE[min(a + 1, A - 1):min(a + 1 + steps, A)].sum()
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
LATENT = K + 2          # per country: xi_u, xi_e (one per religion that can disaffiliate), xi_a, xi_v
FIT_VERSION = 3          # bump when the estimation algorithm changes (invalidates cached fits)
DEFAULT_BOUNDS = {'delta': [-3.0, 5.0], 'beta_d': [-1.0, 4.0], 'tau_u': [0.1, 5.0]}


class Hierarchy:
    """Empirical Bayes fit of switching rates for n countries.

    prior: dict from config/assumptions.json['switching'] with keys mu_d (dict by religion, lifetime
    probabilities at z = 0), mu_a, mu_v (dicts / float), beta_a, tau_e, tau_a, tau_v and a coarse
    starting grid over delta, beta_d, tau_u. M latent draws per country (fixed seed).

    The marginal likelihood of the hyperparameters H = (delta, beta_d, tau_u) integrates each
    country's ten latent effects xi out by importance sampling. Draws from the prior N(0, I) are
    inefficient for countries whose evidence is sharp (a survey row with n = 500 leaves a few prior
    draws carrying all the weight), and the estimate then depends on the seed. The fit therefore
    adapts the proposal: each country gets a Gaussian fitted to its own weighted draws, mixed with
    the prior (a defensive mixture, so the estimator stays valid wherever the posterior is), and
    the importance weights carry log prior - log proposal. Because the latent effects are standard
    normal whatever H is, one set of draws serves every H, which makes the estimated marginal
    likelihood a smooth function of H that can be maximised continuously."""

    def __init__(self, n, prior, M=256, seed=7):
        self.n, self.M, self.prior = n, M, prior
        self.seed = seed
        rng = np.random.default_rng(seed)
        self._set_latent(rng.standard_normal((n, M, LATENT)))
        self.log_ratio = np.zeros((n, M))            # log prior density - log proposal density
        names = [E.CATS[r] for r in REL]
        self.mu_d = logit(np.array([prior['mu_d'][c] for c in names]))
        self.mu_v = logit(np.array([prior['mu_v'][c] for c in names]))
        self.mu_a = float(logit(prior['mu_a']))
        self.H = None
        self.logw = None
        self.grid_table = None
        self.search = []

    def _latent(self):
        return np.concatenate([self.xi_u[..., None], self.xi_e, self.xi_a[..., None], self.xi_v[..., None]], -1)

    def _set_latent(self, Z):
        self.xi_u, self.xi_e = Z[..., 0].copy(), Z[..., 1:K].copy()
        self.xi_a, self.xi_v = Z[..., K].copy(), Z[..., K + 1].copy()

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
            # Only the countries observed in a decade are evaluated, and the conversion rates v,
            # which depend on neither H nor development, once for all decades. The factor 7/8
            # counts the K shares, which sum to one, as K - 1 independent residuals.
            delta, beta, tau_u = H
            p = self.prior
            v_all = expit(self.mu_v[None, None, :] + p['tau_v'] * self.xi_v[:, :, None])
            base_d = self.mu_d[None, None, :] + delta + tau_u * self.xi_u[:, :, None] + p['tau_e'] * self.xi_e
            base_a = self.mu_a + p['tau_a'] * self.xi_a
            for t in range(net['y'].shape[1]):
                idx = np.flatnonzero(net['mask'][:, t])
                if not len(idx):
                    continue
                z = net['z'][idx, t]
                d = expit(base_d[idx] + beta * z[:, None, None])
                a = expit(base_a[idx] + p['beta_a'] * z[:, None])
                pred = (np.matmul(d, net['Bd'][idx, t]) + np.matmul(v_all[idx], net['Bv'][idx, t])
                        + a[:, :, None] * net['Ba'][idx, t][:, None, :])
                r = net['y'][idx, t][:, None, :] - pred
                lk = self._t_loglik(r, net['scale'][None, None, :]).sum(-1) * (7.0 / 8.0)
                ll[idx] += lk * net['weight'][idx, t][:, None]
        if survey is not None and len(survey['group_country']):
            # survey: one Dirichlet-multinomial per survey row (a country's adults raised in one
            # religion, in one survey). Cell arrays: group [S], raised [S], current [S], p [S]
            # (observed share of the row), dest_frac [S] (the model's split of conversions over
            # destinations, by local prevalence, exactly as in lifetime_matrix). Row arrays:
            # group_country [R], group_n [R], group_z [R]. Cells a survey did not report are pooled
            # into one complement cell, so a row reporting only "raised r, now unaffiliated" is
            # counted once and a row reporting several cells is not counted several times over.
            # The concentration `alpha` allows for survey design effects and for the model's
            # simplifications (one conversion effect per country, converts placed by prevalence):
            # a row carries the information of at most about alpha respondents, however large the
            # survey. alpha -> infinity is the multinomial.
            alpha = float(survey.get('alpha', np.inf))
            for i in np.unique(survey['group_country']):
                rows = np.flatnonzero(survey['group_country'] == i)
                d, v, a = self.rates(np.array([survey['group_z'][rows[0]]]), H, idx=np.array([i]))
                d, v, a = d[0], v[0], a[0]                                   # [M, K-1], [M, K-1], [M]
                for g in rows:
                    cells = np.flatnonzero(survey['group'] == g)
                    n_eff = float(survey['group_n'][g])
                    probs, counts = [], []
                    for c in cells:
                        r, s_ = int(survey['raised'][c]), int(survey['current'][c])
                        if r == U:
                            prob = 1.0 - a if s_ == U else a * survey['dest_frac'][c]
                        else:
                            j = REL.index(r)
                            if s_ == r:
                                prob = 1.0 - d[:, j] - v[:, j]
                            elif s_ == U:
                                prob = d[:, j]
                            else:
                                prob = v[:, j] * survey['dest_frac'][c]
                        probs.append(np.clip(prob, 1e-9, 1.0))
                        counts.append(n_eff * survey['p'][c])
                    rest = max(1.0 - sum(survey['p'][c] for c in cells), 0.0)
                    probs.append(np.clip(1.0 - np.sum(probs, axis=0), 1e-9, 1.0))
                    counts.append(n_eff * rest)
                    probs, counts = np.array(probs), np.array(counts)[:, None]       # [C, M], [C, 1]
                    if np.isfinite(alpha):
                        ll[i] += (lgamma(alpha) - lgamma(n_eff + alpha)
                                  + (lgamma(counts + alpha * probs) - lgamma(alpha * probs)).sum(0))
                    else:
                        ll[i] += (counts * np.log(probs)).sum(0)
        return ll

    def log_marginal(self, H, net=None, survey=None):
        """Estimated log marginal likelihood (summed over countries) and the per-draw log weights."""
        ll = self.loglik(H, net, survey) + self.log_ratio
        mx = ll.max(1, keepdims=True)
        return float((mx[:, 0] + np.log(np.exp(ll - mx).mean(1))).sum()), ll

    def log_posterior(self, Z, H, net=None, survey=None):
        """Unnormalised log posterior of the country effects, log N(Z; 0, I) + log-likelihood, at
        arbitrary latent values Z [n, m, LATENT] (the stored draws are left untouched)."""
        saved = (self.xi_u, self.xi_e, self.xi_a, self.xi_v, self.M)
        self._set_latent(Z)
        self.M = Z.shape[1]
        try:
            ll = self.loglik(H, net, survey)
        finally:
            self.xi_u, self.xi_e, self.xi_a, self.xi_v, self.M = saved
        return ll - 0.5 * (Z ** 2).sum(-1)

    def posterior_modes(self, H, net=None, survey=None, iters=25, h=1e-3, floor=1.0):
        """Each country's posterior mode of the effects and the curvature there, by damped Newton
        steps with finite-difference derivatives (all countries at once: the 1 + 2D + 2D(D-1)
        stencil points of every country are one likelihood evaluation). Starts from the best
        stored draw. Returns (mode [n, D], precision [n, D, D]); the precision's eigenvalues are
        floored at `floor` (the prior's own precision), so a direction the evidence does not inform
        is never proposed more widely than the prior."""
        D = LATENT
        I = np.eye(D)
        start = self.log_posterior(self._latent(), H, net, survey)
        x = self._latent()[np.arange(self.n), start.argmax(1)]
        fx = start.max(1)
        pairs = [(i, j) for i in range(D) for j in range(i + 1, D)]
        offs = [np.zeros(D)] + [s * h * I[i] for i in range(D) for s in (1, -1)]
        offs += [h * (si * I[i] + sj * I[j]) for i, j in pairs for si, sj in ((1, 1), (1, -1), (-1, 1), (-1, -1))]
        offs = np.array(offs)
        mu = np.full(self.n, 1e-3)
        prec = np.tile(I, (self.n, 1, 1))
        for _ in range(iters):
            v = self.log_posterior(x[:, None, :] + offs[None], H, net, survey)        # [n, P]
            f0 = v[:, 0]
            g = (v[:, 1:2 * D + 1:2] - v[:, 2:2 * D + 2:2]) / (2 * h)
            Hs = np.zeros((self.n, D, D))
            idx = np.arange(D)
            Hs[:, idx, idx] = (v[:, 1:2 * D + 1:2] - 2 * f0[:, None] + v[:, 2:2 * D + 2:2]) / h ** 2
            q = v[:, 2 * D + 1:].reshape(self.n, len(pairs), 4)
            cross = (q[..., 0] - q[..., 1] - q[..., 2] + q[..., 3]) / (4 * h * h)
            for k, (i, j) in enumerate(pairs):
                Hs[:, i, j] = Hs[:, j, i] = cross[:, k]
            ev, V = np.linalg.eigh(-Hs)
            prec = np.einsum('nij,nj,nkj->nik', V, np.maximum(ev, floor), V)
            step = np.linalg.solve(prec + mu[:, None, None] * I, g[..., None])[..., 0]
            trial = x + step
            ft = self.log_posterior(trial[:, None, :], H, net, survey)[:, 0]
            ok = ft > f0 - 1e-9
            x = np.where(ok[:, None], trial, x)
            fx = np.where(ok, ft, f0)
            mu = np.where(ok, mu * 0.3, mu * 10.0)
            if np.abs(step[ok]).max(initial=0.0) < 1e-6 and ok.all():
                break
        self.mode_log_posterior = fx
        return x, prec

    def adapt(self, H, net=None, survey=None, weights=(0.2, 0.4, 0.4), inflate=1.5, df=5.0, shrink=20.0,
              weak=50.0):
        """Laplace importance sampling with a moment-matched second component. Country c's draws
        are replaced by draws from the mixture

            q_c = w0 N(0, I) + w1 t_df(m_c, inflate P_c^-1) + w2 t_df(mu_c, inflate S_c),

        where m_c is the country's posterior mode at H and P_c the (floored) curvature there, and
        mu_c, S_c are the importance-weighted mean and covariance of draws from the first two
        components, S_c shrunk towards P_c^-1 by `shrink` pseudo-draws when the weights are few.
        The Laplace component finds sharp posteriors (a survey row with n = 500); the moment
        component covers curved or skewed ones, where the curvature at the mode understates the
        spread (two effects trading off along a ridge); the prior component keeps the estimator
        valid wherever the posterior is. Countries whose effective sample size is still below
        `weak` get one more pass: the moment component is refitted to their weighted draws, with
        twice the inflation, and their draws are replaced by fresh draws from it. Every weight
        carries log prior - log q, so the estimator is unbiased for every H whatever the proposal."""
        rng = np.random.default_rng([self.seed, 31])
        D = LATENT
        m, P = self.posterior_modes(H, net, survey)
        C_lap = inflate * np.linalg.inv(P)
        comps = [(m, np.linalg.cholesky(C_lap))]
        # pilot: prior and Laplace components only
        pilot_w = np.array([weights[0], weights[1] + weights[2]])
        Z, logq = self._mixture_draws(rng, comps, pilot_w / pilot_w.sum(), df)
        lw = self.log_posterior(Z, H, net, survey) - 0.5 * D * np.log(2 * np.pi) - logq
        w = np.exp(lw - lw.max(1, keepdims=True))
        w = w / w.sum(1, keepdims=True)
        ess = 1.0 / (w ** 2).sum(1)
        mu = np.einsum('nm,nmd->nd', w, Z)
        dZ = Z - mu[:, None, :]
        S = np.einsum('nm,nmd,nme->nde', w, dZ, dZ)
        lam = (ess / (ess + shrink))[:, None, None]
        S = lam * inflate * S + (1 - lam) * C_lap
        S = 0.5 * (S + S.transpose(0, 2, 1)) + 1e-8 * np.eye(D)
        comps.append((mu, np.linalg.cholesky(S)))
        Z, logq = self._mixture_draws(rng, comps, np.asarray(weights, float), df)
        logp = -0.5 * (Z ** 2).sum(-1) - 0.5 * D * np.log(2 * np.pi)
        # second pass for the countries the mixture still serves poorly
        lw = self.log_posterior(Z, H, net, survey) - 0.5 * D * np.log(2 * np.pi) - logq
        w = np.exp(lw - lw.max(1, keepdims=True))
        w = w / w.sum(1, keepdims=True)
        ess = 1.0 / (w ** 2).sum(1)
        low = ess < weak
        if low.any():
            mu2 = np.einsum('nm,nmd->nd', w, Z)
            dZ = Z - mu2[:, None, :]
            S2 = np.einsum('nm,nmd,nme->nde', w, dZ, dZ)
            lam = (ess / (ess + shrink))[:, None, None]
            S2 = lam * 2.0 * inflate * S2 + (1 - lam) * 2.0 * C_lap
            S2 = 0.5 * (S2 + S2.transpose(0, 2, 1)) + 1e-8 * np.eye(D)
            comps2 = [comps[0], (mu2, np.linalg.cholesky(S2))]
            Z2, logq2 = self._mixture_draws(rng, comps2, np.asarray(weights, float), df)
            Z = np.where(low[:, None, None], Z2, Z)
            logq = np.where(low[:, None], logq2, logq)
            logp = -0.5 * (Z ** 2).sum(-1) - 0.5 * D * np.log(2 * np.pi)
        self.weak_countries_repassed = int(low.sum())
        self._set_latent(Z)
        self.log_ratio = logp - logq
        return self

    def _mixture_draws(self, rng, comps, weights, df):
        """M draws per country from w0 N(0, I) + sum_k w_k t_df(loc_k, L_k L_k'), and log q at them."""
        from math import lgamma as _lg
        D = LATENT
        k = rng.choice(len(weights), size=(self.n, self.M), p=weights)
        Z = rng.standard_normal((self.n, self.M, D))
        for j, (loc, L) in enumerate(comps, start=1):
            eps = rng.standard_normal((self.n, self.M, D))
            chi = rng.chisquare(df, (self.n, self.M))
            draw = loc[:, None, :] + np.einsum('nde,nme->nmd', L, eps) * np.sqrt(df / chi)[..., None]
            Z = np.where((k == j)[..., None], draw, Z)
        logs = [np.log(weights[0]) - 0.5 * (Z ** 2).sum(-1) - 0.5 * D * np.log(2 * np.pi)]
        const = _lg((df + D) / 2) - _lg(df / 2) - 0.5 * D * np.log(df * np.pi)
        for j, (loc, L) in enumerate(comps, start=1):
            sol = np.linalg.solve(L[:, None], (Z - loc[:, None, :])[..., None])[..., 0]
            logs.append(np.log(weights[j]) + const - np.log(np.diagonal(L, axis1=1, axis2=2)).sum(-1)[:, None]
                        - 0.5 * (df + D) * np.log1p((sol ** 2).sum(-1) / df))
        return Z, np.logaddexp.reduce(np.array(logs), axis=0)

    def fit(self, net=None, survey=None, adapt=True, starts=3, refits=4, settle=0.02):
        """Maximise the estimated marginal likelihood over H = (delta, beta_d, tau_u).

        1 coarse grid with prior draws; 2 adapt the proposal at the best point and repeat the grid;
        3 maximise continuously with Nelder-Mead from the `starts` best points of that grid;
        4 re-centre the proposal on the current optimum and restart Nelder-Mead from it, until the
        optimum moves by less than `settle` (in delta, beta_d, log tau_u) or `refits` times. Step 4
        matters because a country's posterior moves with H: a proposal fitted at a grid point can miss
        a sharp posterior at the optimum, which biases the estimate there. Restarting also guards
        against the simplex stalling. The search runs in unbounded coordinates, a scaled logit of
        (delta, beta_d, log tau_u) within config/assumptions.json switching.bounds, so the bounds
        hold without clipping (clipping makes the objective flat beyond a bound and can stall the
        simplex there). Then the Laplace approximation of the hyperparameters' posterior under a
        flat hyperprior on the box is computed (`laplace`). Keeps the best H, its importance
        log-weights per country and the evidence; `search` records every evaluation."""
        g = self.prior['grid']
        b = self.prior.get('bounds', DEFAULT_BOUNDS)
        self.lo = np.array([b['delta'][0], b['beta_d'][0], np.log(b['tau_u'][0])])
        self.hi = np.array([b['delta'][1], b['beta_d'][1], np.log(b['tau_u'][1])])
        self.evidence = (net, survey)

        def grid(stage):
            vals = []
            for delta in g['delta']:
                for beta in g['beta_d']:
                    for tau in g['tau_u']:
                        H = (float(delta), float(beta), float(tau))
                        lm, _ = self.log_marginal(H, net, survey)
                        self.search.append({'stage': stage, 'delta': H[0], 'beta_d': H[1], 'tau_u': H[2],
                                            'log_marginal': lm})
                        vals.append((lm, H))
            return sorted(vals, key=lambda t: -t[0])

        best = grid('grid')
        H = best[0][1]
        self.optimisation = None
        if adapt:
            self.adapt(H, net, survey)
            best = grid('grid, adapted')

            def f(x, stage):
                Hx = self._from_free(x)
                lm, _ = self.log_marginal(Hx, net, survey)
                self.search.append({'stage': stage, 'delta': Hx[0], 'beta_d': Hx[1], 'tau_u': Hx[2],
                                    'log_marginal': lm})
                return -lm

            runs = []
            for k, (_, H0) in enumerate(best[:starts]):
                x, fx, ok = nelder_mead(lambda x, k=k: f(x, f'nelder-mead start {k + 1}'), self._to_free(H0),
                                        np.full(3, 0.6))
                runs.append((fx, x, ok))
            fx, x, _ = min(runs, key=lambda t: t[0])
            tops = sorted(-r[0] for r in runs)[::-1]
            spread = float(tops[0] - tops[-1])
            moves = []
            for k in range(refits):
                before = self._from_free(x)
                self.adapt(before, net, survey)
                x, fx, ok = nelder_mead(lambda x, k=k: f(x, f'nelder-mead refit {k + 1}'), x,
                                        np.full(3, 0.25 / (k + 1)), max_eval=100)
                moves.append(float(np.abs(self._theta(self._from_free(x)) - self._theta(before)).max()))
                if moves[-1] < settle:
                    break
            H = self._from_free(x)
            self.optimisation = dict(starts=len(runs), starts_within_0_1=int(sum(tops[0] - t <= 0.1 for t in tops)),
                                     best_minus_worst_start=spread, converged=bool(ok),
                                     largest_move_at_each_refit=moves)
        lm, ll = self.log_marginal(H, net, survey)
        self.H = H
        self.log_marginal_value = lm
        self.logw = ll - ll.max(1, keepdims=True)
        self.grid_table = self.search
        self.H_cov = self.laplace() if adapt else None
        return self

    # ---- hyperparameter coordinates and uncertainty -----------------------------------
    @staticmethod
    def _theta(H):
        return np.array([H[0], H[1], np.log(H[2])], float)

    def _to_free(self, H, margin=0.02):
        u = np.clip((self._theta(H) - self.lo) / (self.hi - self.lo), margin, 1.0 - margin)
        return np.log(u / (1.0 - u))

    def _from_free(self, x):
        th = self.lo + (self.hi - self.lo) * expit(np.asarray(x, float))
        return (float(th[0]), float(th[1]), float(np.exp(th[2])))

    def laplace(self, steps=(0.15, 0.08, 0.10)):
        """Covariance of the hyperparameters theta = (delta, beta_d, log tau_u) from the curvature of
        the estimated log marginal likelihood at the optimum. Under a flat hyperprior on the bounds
        this is the Laplace approximation of their posterior, truncated to the box.

        The curvature is the quadratic term of a least-squares quadratic fitted to the 27 points
        theta + {-1, 0, 1}^3 x steps, about one standard error out. The estimate carries Monte
        Carlo error, and a narrow finite-difference stencil turns that error into a noisy
        curvature (standard errors varying four-fold between replications of the same design);
        a wider design averages it out. If the fitted curvature is not negative definite, its
        eigenvalues are floored at the precision of a uniform distribution over the box, a
        conservative fallback, and `laplace_fallback` is set."""
        net, survey = self.evidence
        th = self._theta(self.H)
        h = np.asarray(steps, float)
        grid = np.array(np.meshgrid(*[[-1.0, 0.0, 1.0]] * 3, indexing='ij')).reshape(3, -1).T      # [27, 3]
        X = grid * h
        y = np.array([self.log_marginal((float(t[0]), float(t[1]), float(np.exp(t[2]))), net, survey)[0]
                      for t in th + X])
        iu = np.triu_indices(3)
        quad = np.stack([X[:, i] * X[:, j] * (0.5 if i == j else 1.0) for i, j in zip(*iu, strict=True)], 1)
        design = np.column_stack([np.ones(len(X)), X, quad])
        coef = np.linalg.lstsq(design, y, rcond=None)[0]
        A = np.zeros((3, 3))
        for k, (i, j) in enumerate(zip(*iu, strict=True)):
            A[i, j] = A[j, i] = coef[4 + k]
        info = -A
        ev, V = np.linalg.eigh(info)
        floor = 12.0 / (self.hi - self.lo) ** 2                       # precision of uniform(lo, hi)
        self.laplace_fallback = bool(np.any(ev <= 0))
        if self.laplace_fallback:
            ev = np.maximum(ev, float(floor.min()))
        return V @ np.diag(1.0 / ev) @ V.T

    @property
    def H_se(self):
        """Standard errors of (delta, beta_d, log tau_u) from the Laplace approximation (NaN if none)."""
        if getattr(self, 'H_cov', None) is None:
            return (np.nan, np.nan, np.nan)
        return tuple(float(v) for v in np.sqrt(np.diag(self.H_cov)))

    def draw_hyper(self, rng, tries=100):
        """One draw of H from the truncated Laplace approximation (the fitted H if there is none)."""
        if getattr(self, 'H_cov', None) is None:
            return self.H
        th, C = self._theta(self.H), np.linalg.cholesky(self.H_cov)
        for _ in range(tries):
            x = th + C @ rng.standard_normal(3)
            if np.all(x >= self.lo) and np.all(x <= self.hi):
                break
        else:
            x = np.clip(x, self.lo, self.hi)
        return (float(x[0]), float(x[1]), float(np.exp(x[2])))

    def posterior_weights(self, H=None):
        """Importance weights of the country effects' posterior [n, M] at the fitted H, or at H."""
        if H is None or tuple(H) == tuple(self.H):
            w = np.exp(self.logw)
        else:
            net, survey = self.evidence
            ll = self.loglik(H, net, survey) + self.log_ratio
            w = np.exp(ll - ll.max(1, keepdims=True))
        return w / w.sum(1, keepdims=True)

    def effective_sample_size(self, H=None):
        w = self.posterior_weights(H)
        return 1.0 / (w ** 2).sum(1)

    def sample_indices(self, rng, R, H=None):
        """R posterior draws per country [n, R] (indices into the M latent draws), at H if given."""
        w = self.posterior_weights(H)
        c = np.cumsum(w, 1)
        u = rng.random((self.n, R))
        return np.minimum((u[:, :, None] > c[:, None, :]).sum(2), self.M - 1)

    def posterior_summary(self, z):
        """Posterior mean and 5-95% of each rate at development z [n] (for reporting)."""
        d, v, a = self.rates(z, self.H)
        return _summary(d, v, a, self.posterior_weights())


def _summary(d, v, a, w):
    out = {}
    for name, x in (('d', d), ('v', v)):
        out[name + '_mean'] = np.einsum('nm,nmj->nj', w, x)
        out[name + '_q05'], out[name + '_q95'] = _weighted_quantiles(x, w, (0.05, 0.95))
    out['a_mean'] = (w * a).sum(1)
    qa = _weighted_quantiles(a[:, :, None], w, (0.05, 0.95))
    out['a_q05'], out['a_q95'] = qa[0][:, 0], qa[1][:, 0]
    return out


class Ensemble:
    """Replicate empirical Bayes fits of the same evidence with independent latent draws.

    The importance-sampling estimate of the marginal likelihood carries Monte Carlo error, so the
    fitted hyperparameters differ a little between seeds. Rather than pick one, the projection uses
    every replicate: Monte Carlo run r uses member r mod m, so that error is propagated into the
    projection's spread instead of being fixed at one arbitrary value, and its size is reported
    (`H_spread`)."""

    def __init__(self, members):
        self.members = list(members)
        self.n, self.M = self.members[0].n, self.members[0].M

    def member(self, r):
        return self.members[int(r) % len(self.members)]

    @property
    def H(self):
        return tuple(float(np.mean([m.H[i] for m in self.members])) for i in range(3))

    def H_spread(self):
        return tuple(float(np.std([m.H[i] for m in self.members], ddof=1)) if len(self.members) > 1 else 0.0
                     for i in range(3))

    @property
    def net_scale(self):
        return self.members[0].net_scale

    @property
    def survey_level(self):
        """The members' survey-level tables, averaged (numeric columns)."""
        tabs = [m.survey_level['table'] for m in self.members if getattr(m, 'survey_level', None) is not None]
        if not tabs:
            return None
        t = tabs[0].copy()
        num = t.select_dtypes('number').columns
        t[num] = np.mean([x[num].to_numpy(float) for x in tabs], axis=0)
        return dict(table=t)

    def effective_sample_size(self):
        return np.mean([m.effective_sample_size() for m in self.members], axis=0)

    def posterior_summary(self, z):
        """Pooled over members: each member's weighted draws, the members weighted equally."""
        parts = [m.rates(z, m.H) for m in self.members]
        w = np.concatenate([m.posterior_weights() / len(self.members) for m in self.members], 1)
        d = np.concatenate([x[0] for x in parts], 1)
        v = np.concatenate([x[1] for x in parts], 1)
        a = np.concatenate([x[2] for x in parts], 1)
        return _summary(d, v, a, w)


def nelder_mead(f, x0, step, max_eval=150, xtol=1e-3, ftol=1e-3):
    """Minimise f from x0 with the Nelder-Mead simplex (reflection 1, expansion 2, contraction 0.5,
    shrink 0.5). Small and dependency-free; f is the negative estimated log marginal likelihood.
    Returns (x, f(x), converged), converged meaning the simplex met both tolerances before
    `max_eval` evaluations."""
    n = len(x0)
    pts = [np.asarray(x0, float)] + [np.asarray(x0, float) + step[i] * np.eye(n)[i] for i in range(n)]
    vals = [f(x) for x in pts]
    evals = n + 1
    converged = False
    while evals < max_eval:
        order = np.argsort(vals)
        pts, vals = [pts[i] for i in order], [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < ftol and max(np.abs(p - pts[0]).max() for p in pts[1:]) < xtol:
            converged = True
            break
        c = np.mean(pts[:-1], axis=0)
        xr = c + (c - pts[-1])
        fr = f(xr)
        evals += 1
        if fr < vals[0]:
            xe = c + 2 * (c - pts[-1])
            fe = f(xe)
            evals += 1
            pts[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            pts[-1], vals[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c) if fr >= vals[-1] else c + 0.5 * (xr - c)
            fc = f(xc)
            evals += 1
            if fc < min(fr, vals[-1]):
                pts[-1], vals[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]
                vals = [vals[0]] + [f(p) for p in pts[1:]]
                evals += n
    i = int(np.argmin(vals))
    return pts[i], float(vals[i]), converged


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
