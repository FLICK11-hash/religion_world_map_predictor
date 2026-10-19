"""Check shape, probabilities, population, provenance, and scenario metrics."""
import json
import numpy as np
import pandas as pd
from step5c_evidence_sensitivity import OUT, YEARS, CATEGORIES, SCENARIOS

report=json.loads((OUT/'step5c_report.json').read_text())
R=int(report['runs']);N=int(report['countries'])
s=np.load(OUT/'ensemble_shares_float32.npy',mmap_mode='r')
p=np.load(OUT/'ensemble_populations_float32.npy',mmap_mode='r')
assert s.shape==(R,len(YEARS),N,len(CATEGORIES))
assert p.shape==(R,len(YEARS),N)
for t,y in enumerate(YEARS):
    sh=np.asarray(s[:,t],float)
    assert np.isfinite(sh).all() and (sh>=-1e-7).all() and (sh<=1+1e-7).all(), y
    assert np.allclose(sh.sum(axis=-1),1,atol=2e-6),y
    assert np.isfinite(p[:,t]).all() and (p[:,t]>0).all(),y
assert np.allclose(s[:,YEARS.index(3026)], .8*s[:,YEARS.index(3025)]+.2*s[:,YEARS.index(3030)],atol=2e-6)
summary=pd.read_csv(OUT/'scenario_change_summary.csv')
assert set(summary.scenario)==set(SCENARIOS)
assert len(summary)==len(SCENARIOS)*len(YEARS)
assert summary.median_share_redistribution.between(0,1).all()
country=pd.read_csv(OUT/'country_year_uncertainty.csv')
assert len(country)==len(YEARS)*N
assert np.allclose(country[[f'mean_{c}' for c in CATEGORIES]].sum(axis=1),1,atol=2e-6)
print(f'PASS: Step 5C {R} runs, {N} countries, {len(SCENARIOS)} scenarios.')
print('PASS: Shares, population, 3026 interpolation, and summary integrity.')
print('WARNING: Sensitivity experiments, not historically validated 3026 forecasts.')
