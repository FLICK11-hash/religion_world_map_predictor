"""Check Step 4 predictions, splits, share sums, and score consistency."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'data' / 'models'
FTR = ROOT / 'data' / 'features'
WRP = ROOT / 'data' / 'processed' / 'wrp_training_only_8groups.csv'
CATEGORIES = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism',
              'Folk_Traditional', 'Other', 'Unaffiliated']
MODELS = {'persistence', 'linear_trend', 'lightgbm', 'neural_network'}


def main():
    report = json.loads((OUT / 'step4_report.json').read_text())
    predictions = pd.read_csv(OUT / 'multihorizon_predictions.csv')
    one_step = pd.read_csv(OUT / 'one_step_predictions.csv')
    summary = pd.read_csv(OUT / 'model_comparison_by_horizon.csv')
    origins = pd.read_csv(FTR / 'wrp_origin_features.csv')
    samples = pd.read_csv(FTR / 'wrp_training_transitions.csv')
    splits = pd.read_csv(FTR / 'rolling_origin_one_step_splits.csv')
    wrp = pd.read_csv(WRP)
    predcols = [f'pred_{x}' for x in CATEGORIES]
    actualcols = [f'actual_{x}' for x in CATEGORIES]

    assert set(predictions.model) == MODELS
    assert set(one_step.model) == MODELS
    assert set(predictions.horizon_years) == {5, 10, 20, 30}
    assert predictions.duplicated(['model', 'forecast_origin', 'horizon_years', 'country_id']).sum() == 0
    assert np.isfinite(predictions[predcols + actualcols].to_numpy(float)).all()
    assert (predictions[predcols].to_numpy(float) >= -1e-10).all()
    assert (predictions[predcols].to_numpy(float) <= 1 + 1e-10).all()
    assert np.allclose(predictions[predcols].sum(axis=1), 1, atol=1e-7)
    assert np.allclose(predictions[actualcols].sum(axis=1), 1, atol=1e-7)
    assert (predictions.target_year == predictions.forecast_origin + predictions.horizon_years).all()

    truth = wrp.set_index(['country_id', 'year'], verify_integrity=True)
    idx = pd.MultiIndex.from_arrays([predictions.country_id, predictions.target_year],
                                    names=['country_id', 'year'])
    observed = truth.loc[idx, ['share_' + x for x in CATEGORIES]].to_numpy(float)
    assert np.allclose(observed, predictions[actualcols].to_numpy(float), atol=1e-7)

    src = origins.set_index(['country_id', 'origin_year'], verify_integrity=True)
    key = pd.MultiIndex.from_arrays([predictions.country_id, predictions.forecast_origin],
                                    names=['country_id', 'origin_year'])
    at_origin = src.loc[key, ['share_' + x for x in CATEGORIES]].to_numpy(float)
    changed = np.argmax(predictions[actualcols].to_numpy(float), axis=1) != np.argmax(at_origin, axis=1)
    assert np.array_equal(changed, predictions.dominant_changed.to_numpy(bool))
    baseline = predictions[ predictions.model.eq('persistence') ]
    k2 = pd.MultiIndex.from_arrays([baseline.country_id, baseline.forecast_origin],
                                   names=['country_id', 'origin_year'])
    baseline_ground = src.loc[k2, ['share_' + x for x in CATEGORIES]].to_numpy(float)
    assert np.allclose(baseline[predcols].to_numpy(float), baseline_ground, atol=1e-7)

    for fold in sorted(splits.fold_origin.unique()):
        f = splits[splits.fold_origin.eq(fold)]
        train = f.loc[f.split.eq('train')]
        valid = f.loc[f.split.eq('validation')]
        assert (train.target_year <= fold).all()
        assert (valid.target_year == fold + 5).all()
        assert not set(train.row_id) & set(valid.row_id)
    assert set(report['best_5year_model_by_country_weighted_mae'].split()) & MODELS
    assert (summary.n_predictions > 0).all()
    print('PASS: All model predictions stay on the eight-category probability simplex.')
    print('PASS: Target shares match original WRP truth at the claimed horizon.')
    print('PASS: Persistence uses only real origin shares, including at long horizons.')
    print('PASS: Dominant-religion change indicators and training fold cutoffs are consistent.')
    print(f'PASS: {len(predictions):,} scored model-country-horizon predictions across four models.')
    print('Best one-step model by average share MAE:', report['best_5year_model_by_country_weighted_mae'])


if __name__ == '__main__':
    main()
