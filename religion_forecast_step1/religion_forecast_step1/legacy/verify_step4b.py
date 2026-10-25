"""Verify Step 4B holdout calibration, labels and blended share predictions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
M = ROOT/'data'/'models'
O = M/'step4b'
RELIGIONS = ['Christianity','Islam','Hinduism','Buddhism','Judaism',
             'Folk_Traditional','Other','Unaffiliated']
rows = pd.read_csv(O/'rolling_blend_predictions.csv', low_memory=False)
selections = pd.read_csv(O/'rolling_blend_selections.csv')
summary = pd.read_csv(O/'rolling_blend_summary.csv')
report = json.loads((O/'step4b_report.json').read_text(encoding='utf-8'))
original = pd.read_csv(M/'one_step_predictions.csv', low_memory=False)
original = original.loc[original.model.eq('persistence')].copy()

preds = rows[[f'pred_{r}' for r in RELIGIONS]].to_numpy(float)
truth = rows[[f'actual_{r}' for r in RELIGIONS]].to_numpy(float)
assert np.isfinite(preds).all() and np.isfinite(truth).all()
assert (preds >= -1e-9).all() and np.allclose(preds.sum(axis=1), 1, atol=1e-7)
assert (truth >= -1e-9).all() and np.allclose(truth.sum(axis=1), 1, atol=1e-7)
assert rows.target_year.eq(rows.forecast_origin + 5).all()
assert not rows.duplicated(['forecast_origin','country_id','method']).any()
assert selections.max_calibration_target_year.le(selections.forecast_origin).all()
assert set(rows.method.unique()) == {'persistence','lightgbm','rolling_mae','rolling_change_weighted'}
assert set(rows.forecast_origin.unique()) == set(report['evaluated_forecast_origins'])
assert summary.n.nunique() == 1
for method in ['rolling_mae','rolling_change_weighted']:
    subset = rows.loc[rows.method.eq(method)]
    chosen = subset[['forecast_origin','selected_blend','max_calibration_target_year']].drop_duplicates()
    matching = selections[selections.method.eq(method)]
    assert len(chosen) == len(matching)
    match = chosen.merge(matching,on=['forecast_origin','selected_blend','max_calibration_target_year'], validate='one_to_one')
    assert len(match) == len(chosen)

unique = rows.loc[rows.method.eq('persistence')]
merged = unique.merge(original[['forecast_origin','country_id']+[f'actual_{r}' for r in RELIGIONS]],
                      on=['forecast_origin','country_id'], validate='one_to_one',suffixes=('','_orig'))
assert len(merged) == len(unique)
for religion in RELIGIONS:
    assert np.allclose(merged[f'actual_{religion}'], merged[f'actual_{religion}_orig'], atol=1e-10)

# Confirm accuracy and recall can be reproduced from the saved final outputs.
for _, line in summary.iterrows():
    s = rows.loc[rows.method.eq(line.method)]
    calculated_mae = np.mean(np.abs(s[[f'pred_{r}' for r in RELIGIONS]].to_numpy(float) -
                                    s[[f'actual_{r}' for r in RELIGIONS]].to_numpy(float)))
    assert abs(calculated_mae - line.mae) < 1e-9
    assert s.correct_change.sum() == line.correct_changes
    assert s.false_change_alarm.sum() == line.false_change_alarms
print('PASS: All Step 4B shares remain on the probability simplex.')
print('PASS: Calibration selection uses only prior observed target years.')
print('PASS: Original WRP target data and chronological model pairings agree.')
print('PASS: Model summaries match saved predictions and transition counts.')
print('SUCCESS: Step 4B verified.')
