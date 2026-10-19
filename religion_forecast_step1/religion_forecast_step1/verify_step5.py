"""Independent structural checks for Step 5 scenario outputs."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from step5_forecast_scenarios import CATEGORIES, SHARES, OUT, YEARS, TARGET_YEARS


def verify():
    report=json.loads((OUT/'step5_report.json').read_text(encoding='utf-8'))
    runs=int(report['ensemble_runs']); years=report['forecast_output_years']; n=int(report['country_anchors'])
    if runs < 100 or runs % 4:
        raise AssertionError('Expected at least 100 runs divisible by four')
    anchors=pd.read_csv(Path(__file__).resolve().parent / 'data/features/pew_2020_anchor_context.csv')
    initial=anchors.loc[anchors.year.eq(2020)].set_index('country_id')[SHARES]
    if not set(TARGET_YEARS).issubset(years) or list(years)!=YEARS:
        raise AssertionError('Missing target or five-year forecast dates')
    arr=np.load(OUT/'ensemble_shares_float32.npy',mmap_mode='r')
    pop=np.load(OUT/'ensemble_populations_float32.npy',mmap_mode='r')
    if arr.shape!=(runs,len(years),n,len(CATEGORIES)) or pop.shape!=(runs,len(years),n):
        raise AssertionError('Unexpected ensemble array shape')
    # Chunked checks to avoid materializing arrays on older laptops.
    for i,yr in enumerate(years):
        x=np.asarray(arr[:,i],dtype=float)
        if not np.isfinite(x).all() or (x< -1e-6).any() or (x>1+1e-6).any():
            raise AssertionError(f'{yr}: share out of range')
        if not np.allclose(x.sum(axis=2),1,atol=2e-6):
            raise AssertionError(f'{yr}: composition not normalized')
        if not np.isfinite(pop[:,i]).all() or (pop[:,i]<=0).any():
            raise AssertionError(f'{yr}: invalid population')
    i25=years.index(3025); i26=years.index(3026); i30=years.index(3030)
    if not np.allclose(arr[:,i26],.8*arr[:,i25]+.2*arr[:,i30],atol=2e-6):
        raise AssertionError('3026 interpolation is not the stated one-year interpolation')
    params=pd.read_csv(OUT/'scenario_parameters.csv')
    if len(params)!=runs or params[['fertility_scenario','secularization_scenario']].drop_duplicates().shape[0]!=4:
        raise AssertionError('Scenario grid incomplete')
    country=pd.read_csv(OUT/'country_year_uncertainty.csv')
    world=pd.read_csv(OUT/'global_share_by_run.csv')
    global_ci=pd.read_csv(OUT/'global_share_uncertainty.csv')
    if len(country)!=n*len(years) or len(world)!=runs*len(years) or len(global_ci)!=8*len(years):
        raise AssertionError('CSV output row count mismatch')
    if not country.dominant_agreement_fraction.between(1/8-1e-6,1+1e-6).all():
        raise AssertionError('Dominance agreement outside [0,1]')
    for cat in CATEGORIES:
        if not (country[f'q05_{cat}'] <= country[f'q50_{cat}']+1e-8).all():
            raise AssertionError(f'Inconsistent {cat} quantiles')
        if not (country[f'q50_{cat}'] <= country[f'q95_{cat}']+1e-8).all():
            raise AssertionError(f'Inconsistent {cat} quantiles')
    if not np.allclose(world[CATEGORIES].sum(axis=1),1,atol=2e-6):
        raise AssertionError('Global religion shares not normalized')
    tracks=pd.read_csv(OUT/'deterministic_tracks.csv',low_memory=False)
    pers=tracks[tracks.track.eq('persistence')]
    base=pers[pers.year.eq(2020)].sort_values('country_id')
    if len(base)!=n:
        raise AssertionError('Unexpected baseline count')
    for yr in years:
        current=pers[pers.year.eq(yr)].sort_values('country_id')
        if not np.allclose(current[CATEGORIES],base[CATEGORIES],atol=1e-6):
            raise AssertionError(f'Persistence changed religious composition in {yr}')
    print('PASS: Ensemble has >=100 runs, 4 scenarios, all 5-year steps plus 3026.')
    print('PASS: Every simulated country share is finite, nonnegative, and sums to 1.')
    print('PASS: 3026 is interpolated exactly from 3025 and 3030.')
    print('PASS: Population, confidence, quantiles and global shares are consistent.')
    print('PASS: Persistence religion shares remain identical to 2020 across all years.')
    print(f'SUCCESS: Step 5 verified — {runs} runs, {n} country anchors, {len(years)} reported years.')

if __name__=='__main__':verify()
