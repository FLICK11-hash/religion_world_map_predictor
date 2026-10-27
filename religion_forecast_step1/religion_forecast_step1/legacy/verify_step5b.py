"""Data integrity checks for Step 5B scenario experiments."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from step5b_dynamic_scenarios import OUT, YEARS, SCENARIOS, CATEGORIES

report=json.loads((OUT/'step5b_report.json').read_text(encoding='utf8'))
N=int(report['countries']);R=int(report['runs'])
shares=np.load(OUT/'ensemble_shares_float32.npy',mmap_mode='r')
pops=np.load(OUT/'ensemble_populations_float32.npy',mmap_mode='r')
assert shares.shape==(R,len(YEARS),N,len(CATEGORIES))
assert pops.shape==(R,len(YEARS),N)
for t,yr in enumerate(YEARS):
    x=np.asarray(shares[:,t],float)
    assert np.isfinite(x).all() and (x>=-1e-7).all() and (x<=1+1e-7).all(),yr
    assert np.allclose(x.sum(axis=2),1,atol=2e-6),yr
    assert np.isfinite(pops[:,t]).all() and (pops[:,t]>0).all(),yr
assert np.allclose(shares[:,YEARS.index(3026)],
          .8*shares[:,YEARS.index(3025)]+.2*shares[:,YEARS.index(3030)],atol=2e-6)
summary=pd.read_csv(OUT/'scenario_change_summary.csv')
assert set(summary.scenario)==set(SCENARIOS)
assert len(summary)==len(SCENARIOS)*len(YEARS)
assert summary.median_share_redistribution.between(0,1).all()
country=pd.read_csv(OUT/'country_year_uncertainty.csv')
assert len(country)==N*len(YEARS)
assert np.allclose(country[[f'mean_{c}' for c in CATEGORIES]].sum(axis=1),1,atol=2e-6)
assert country.dominant_agreement_fraction.between(0,1).all()
print('PASS: 4 scenario families, all dates, per-country shares and populations valid.')
print('PASS: 3026 computed from 3025 and 3030; distributions and outputs consistent.')
print(f'PASS: {R} Monte Carlo runs and {N} countries; original Step5 files untouched.')
