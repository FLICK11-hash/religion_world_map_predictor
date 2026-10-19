"""Synthetic end-to-end test of step5d_cohort_forecast (no real data, no scipy/joblib needed)."""
import ast, sys, types
from pathlib import Path
import numpy as np, pandas as pd

import step5d_cohort_forecast as S

# Stub for the one function we reuse from step5 (pure numpy/pandas), extracted from the real source.
src = Path('step5_forecast_scenarios.py').read_text(encoding='utf8')
tree = ast.parse(src)
want = {'group_outputs', 'write_global_uncertainty'}
ns = {'np': np, 'pd': pd, 'CATEGORIES': S.CATEGORIES, 'K': S.K}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in want:
        exec(compile(ast.Module([node], []), 'step5', 'exec'), ns)
stub = types.ModuleType('step5_forecast_scenarios'); stub.__dict__.update(ns)
sys.modules['step5_forecast_scenarios'] = stub

rng = np.random.default_rng(7)
n, K = 15, S.K
ids = [f'C{i:02d}' for i in range(n)]
pew2010 = rng.dirichlet(np.ones(K) * .6, n)
shift = np.zeros(K); shift[0], shift[7] = -.01, .01
current = np.clip(pew2010 + shift, 0, None); current /= current.sum(1, keepdims=True)
pop0 = rng.uniform(2e6, 8e7, n); tfr0 = rng.uniform(1.3, 4.5, n); med0 = rng.uniform(18, 44, n)
mig0 = rng.normal(0, 8e4, n); mig0 -= mig0.mean()


def dem_at(year):
    g = np.exp(0.004 * min(year - 2020, 80))
    return dict(tfr=np.maximum(1.2, 2.1 + (tfr0 - 2.1) * np.exp(-max(year - 2020, 0) / 60)),
                median_age=med0 + 0.2 * min(year - 2020, 80), wpp_population=pop0 * g,
                net_migrations=mig0 * np.exp(-max(year - 2020, 0) / 65))


def dem_path(shift_):
    return {y: dem_at(y) for y in [2020] + S.STEP_YEARS}


missing = np.zeros(n, bool); missing[3] = True
adj = np.zeros((n, n)); [adj.__setitem__((i, (i + 1) % n), 1) or adj.__setitem__(((i + 1) % n, i), 1) for i in range(n)]
inp = dict(ids=ids, adj=adj, od=None, od_report={}, current=current, pew2010=pew2010, missing_2010=missing, cont=np.arange(n) % 3,
           dem_path=dem_path, dem_hist={2010: dict(dem_at(2010), wpp_population=pop0 * .93),
                                        2015: dict(dem_at(2015), wpp_population=pop0 * .965)},
           wpp_missing_2020=0, missing_2010_n=1)
a, rel, off = S.load_assumptions()
assert rel.shape == (K,) and off.shape == (K,)

R = 8
sh = np.zeros((R, len(S.YEARS), n, K)); pp = np.zeros((R, len(S.YEARS), n)); labels = []
for r in range(R):
    sc = S.SCENARIOS[r % 4]
    par = S.draw_params(rng, n, sc, a)
    res, drift, rho, led = S.simulate(inp, sc, par, rel, off)
    assert led['in_2100'].shape == (n, K) and (led['in_2100'] >= -1e-9).all() and (led['out_2050'] >= -1e-9).all()
    assert (rho is not None) == (sc == 'demography_plus_switching')
    if rho is not None:
        assert np.allclose(rho.sum(1), 0, atol=1e-9) and (rho[3] == 0).all()
        assert (0.5 * np.abs(rho).sum(1) <= .1 + 1e-9).all()
    for t, y in enumerate(S.YEARS):
        s, p = res[y]
        assert np.isfinite(s).all() and (s >= -1e-9).all() and np.allclose(s.sum(1), 1, atol=1e-9), (sc, y)
        assert np.isfinite(p).all() and (p > 0).all()
        sh[r, t], pp[r, t] = s, p
    assert np.allclose(res[2020][1], pop0)
    assert drift < 0.25, drift
    labels.append(sc)

# equal-fertility counterfactual with identical age offsets and no migration => shares only move via age structure
by_sc, sc_country, country, world = S.summarize(sh, pp, ids, labels, S.YEARS)
assert set(by_sc.scenario) == set(S.SCENARIOS) and len(by_sc) == 4 * len(S.YEARS)
assert np.allclose(country[[f'mean_{c}' for c in S.CATEGORIES]].sum(axis=1), 1, atol=1e-6)
assert not country[country.scenario.eq(S.HEADLINE)].duplicated(['country_id', 'year']).any()
assert {'mean_dominant', 'most_likely_dominant'} <= set(sc_country.columns)
cmp50 = S.global_vs_pew2050(world); assert 'Pew 2015 projection' in set(cmp50.scenario)
diag = S.central_diagnostics(inp, a, rel, off)
assert len(diag) == K and np.isfinite(diag.drop(columns='religion').to_numpy(float)).all()

scan = S.phi_scan(inp, a, rel, off, grid=np.array([0., .5, 1.]))
assert len(scan) == 3 and np.isfinite(scan.drop(columns='phi').to_numpy(float)).all()
assert scan.persistence_mean_country_tv_pp.nunique() == 1

# the Islam-rich, high-TFR country should gain Islam share in demography_only relative to equal fertility
j = int(np.argmax(pew2010[:, 1] * (tfr0 > 3)))
ctl = S.draw_params(np.random.default_rng(1), n, 'demography_only', a)
ctl['eps'] = np.zeros((n, K)); ctl['phi'] = .7; ctl['Hf'] = 80.
dem_res, _, _, _ = S.simulate(inp, 'demography_only', ctl, rel, off)
ctl2 = dict(ctl, equal_fertility=True)
eq_res, _, _, _ = S.simulate(inp, 'equal_fertility_counterfactual', ctl2, rel, off)
print('country', j, 'Islam share 2100: gaps', round(dem_res[2100][0][j, 1], 4), 'equal', round(eq_res[2100][0][j, 1], 4))
assert dem_res[2100][0][j, 1] > eq_res[2100][0][j, 1]
print('PASS: step5d synthetic end-to-end (simulate, hindcast calibration, summaries, diagnostics)')
