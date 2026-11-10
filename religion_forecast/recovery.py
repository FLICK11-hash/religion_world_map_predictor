"""Does the switching estimator recover what it estimates? A parametric simulation study under the
real design.

    python run.py recovery                 20 replications (config: switching.recovery_replications)
    python run.py recovery --reps 8        fewer
    python run.py recovery --workers 2     processes to use (default: all cores)

The empirical Bayes fit of religion_forecast.switching is a Monte Carlo estimator (importance
sampling inside a numerical optimiser) with a Laplace approximation for the uncertainty of its
hyperparameters, and none of that is guaranteed to behave. This study checks it the standard way.
The true hyperparameters are set to the projection's fitted values. Each replication then

  1 draws every country's effects from their prior, N(0, I);
  2 generates synthetic evidence with exactly the real design: the same 200 countries, the same
    decades with their exposure bases, masks and noise scale (Student-t, 4 degrees of freedom), and
    the same survey rows reporting the same cells with the same sample sizes (Dirichlet-multinomial
    with the model's concentration);
  3 fits the model to it as the projection does, and records the estimates, their Laplace standard
    errors, whether the 90% Laplace interval covers the truth, and the sampler's effective sample
    sizes.

The net-change likelihood is tempered (switching.net_evidence_weight = 0.5) to allow for
dependence between decades that the synthetic data, generated independently, do not have, so its
intervals should over-cover here; under-coverage would be the warning sign.

Writes data/validation/estimator_recovery_runs.csv and estimator_recovery.csv.
"""
from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from religion_forecast import calibration as ES
from religion_forecast import config
from religion_forecast import engine as E
from religion_forecast import switching as SW

OUT = config.VALIDATION
NAMES = ('delta', 'beta_d', 'log_tau_u')


def synthetic_evidence(h_true, H, net, survey, rng):
    """Evidence with the design of (net, survey), generated from hyperparameters H and country
    effects drawn from their prior. `h_true` is a Hierarchy with M = 1 whose latent draws are the
    true effects."""
    n = h_true.n
    syn_net = None
    if net is not None:
        syn_net = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in net.items()}
        for t in range(net['y'].shape[1]):
            d, v, a = h_true.rates(net['z'][:, t], H)
            mean = (np.einsum('nj,njk->nk', d[:, 0], net['Bd'][:, t])
                    + np.einsum('nj,njk->nk', v[:, 0], net['Bv'][:, t]) + a[:, 0, None] * net['Ba'][:, t])
            noise = rng.standard_t(4.0, size=(n, E.K)) * net['scale'][None, :]
            syn_net['y'][:, t] = np.where(net['mask'][:, t][:, None], mean + noise, 0.0)
    syn_survey = None
    if survey is not None and len(survey['group_country']):
        syn_survey = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in survey.items()}
        alpha = float(survey.get('alpha', np.inf))
        for g, c in enumerate(survey['group_country']):
            cells = np.flatnonzero(survey['group'] == g)
            d, v, a = h_true.rates(np.array([survey['group_z'][g]]), H, idx=np.array([c]))
            d, v, a = d[0, 0], v[0, 0], float(a[0, 0])
            probs = []
            for k in cells:
                r, s_ = int(survey['raised'][k]), int(survey['current'][k])
                if r == E.U:
                    probs.append(1.0 - a if s_ == E.U else a * survey['dest_frac'][k])
                else:
                    j = SW.REL.index(r)
                    probs.append(1.0 - d[j] - v[j] if s_ == r else d[j] if s_ == E.U else v[j] * survey['dest_frac'][k])
            probs = np.clip(np.array(probs + [max(1.0 - sum(probs), 0.0)]), 1e-9, None)
            probs /= probs.sum()
            pi = rng.dirichlet(alpha * probs) if np.isfinite(alpha) else probs
            size = max(int(round(survey['group_n'][g])), 1)
            counts = rng.multinomial(size, pi)
            syn_survey['p'][cells] = counts[:-1] / size
    return syn_net, syn_survey


def _replicate(args):
    rep, prior, H_true, net, survey, M, seed = args
    rng = np.random.default_rng([seed, 5150, rep])
    n = net['y'].shape[0] if net is not None else len(survey['group_country'])
    truth = SW.Hierarchy(n, prior, M=1, seed=int(rng.integers(2 ** 31)))
    syn_net, syn_survey = synthetic_evidence(truth, H_true, net, survey, rng)
    t0 = time.time()
    h = SW.Hierarchy(n, prior, M=M, seed=int(rng.integers(2 ** 31))).fit(net=syn_net, survey=syn_survey)
    th, th_true, se = h._theta(h.H), h._theta(H_true), np.array(h.H_se)
    row = dict(replication=rep, seconds=round(time.time() - t0, 1), log_marginal=h.log_marginal_value,
               min_ess=float(h.effective_sample_size().min()), median_ess=float(np.median(h.effective_sample_size())),
               starts_agreeing=h.optimisation['starts_within_0_1'] if h.optimisation else None)
    for k, name in enumerate(NAMES):
        covered = bool(abs(th[k] - th_true[k]) <= 1.6449 * se[k]) if np.isfinite(se[k]) else None
        row.update({f'{name}_true': th_true[k], f'{name}_estimate': th[k], f'{name}_se': se[k],
                    f'{name}_covered_90': covered})
    return row


def summarise(runs):
    rows = []
    for name in NAMES:
        err = runs[f'{name}_estimate'] - runs[f'{name}_true']
        rows.append(dict(parameter=name, true_value=float(runs[f'{name}_true'].iloc[0]), replications=len(runs),
                         bias=float(err.mean()), bias_se=float(err.std(ddof=1) / np.sqrt(len(err))),
                         rmse=float(np.sqrt((err ** 2).mean())), sd_of_estimates=float(err.std(ddof=1)),
                         mean_laplace_se=float(runs[f'{name}_se'].mean()),
                         coverage_90=float(runs[f'{name}_covered_90'].astype(float).mean())))
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--reps', type=int, default=None)
    ap.add_argument('--workers', type=int, default=None)
    ap.add_argument('--quick', action='store_true', help='4 replications with fewer latent draws (plumbing only)')
    args = ap.parse_args(argv)
    from religion_forecast import model as SM
    from religion_forecast import projection as FC
    ctx = SM.Context()
    ens, wins = FC.prepare(ctx)
    sw = ctx.a['switching']
    net = ES.net_arrays(ctx, wins, sw['net_evidence_weight']['value'])
    survey = ES.survey_arrays(ctx)
    H_true = ens.H
    reps = 4 if args.quick else (args.reps or int(sw.get('recovery_replications', {}).get('value', 20)))
    M = 128 if args.quick else sw['latent_draws']
    workers = args.workers or max(1, min(reps, os.cpu_count() or 1))
    print(f'Estimator recovery: {reps} replications at the fitted H = {tuple(round(x, 3) for x in H_true)}, '
          f'{M} latent draws, {workers} processes')
    jobs = [(r, sw, H_true, net, survey, M, ctx.a['random_seed']) for r in range(reps)]
    t0 = time.time()
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(_replicate, jobs))
    else:
        rows = [_replicate(j) for j in jobs]
    runs = pd.DataFrame(rows)
    summ = summarise(runs)
    OUT.mkdir(parents=True, exist_ok=True)
    runs.to_csv(OUT / 'estimator_recovery_runs.csv', index=False)
    summ.to_csv(OUT / 'estimator_recovery.csv', index=False)
    pd.set_option('display.width', 200)
    print(summ.round(3).to_string(index=False))
    print(f'min ESS over replications {runs.min_ess.min():.0f}; wrote {OUT} in {time.time() - t0:.0f}s')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
