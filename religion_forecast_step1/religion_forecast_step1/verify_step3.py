"""Check Step 3 output integrity against Step 2 WRP historical records."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'data'
FEATURES = BASE / 'features'
SHARES = ['share_' + r for r in ['Christianity', 'Islam', 'Hinduism', 'Buddhism',
          'Judaism', 'Folk_Traditional', 'Other', 'Unaffiliated']]


def main():
    wrp = pd.read_csv(BASE / 'processed' / 'wrp_training_only_8groups.csv', low_memory=False)
    examples = pd.read_csv(FEATURES / 'wrp_training_transitions.csv', low_memory=False)
    origins = pd.read_csv(FEATURES / 'wrp_origin_features.csv', low_memory=False)
    folds = pd.read_csv(FEATURES / 'rolling_origin_one_step_splits.csv')
    feature_spec = json.loads((FEATURES / 'feature_columns.json').read_text())

    assert len(examples) > 0 and len(origins) >= len(examples)
    assert examples['row_id'].is_unique and origins['row_id'].is_unique
    assert (examples.target_year - examples.origin_year == 5).all()
    assert np.allclose(examples[SHARES].sum(axis=1), 1, atol=1e-8)
    targets = ['target_' + s for s in SHARES]
    assert np.allclose(examples[targets].sum(axis=1), 1, atol=1e-8)
    assert set(feature_spec['targets']) == set(targets)
    assert not (set(feature_spec['predictors']) & set(targets))
    assert all(col in examples.columns for col in feature_spec['predictors'])

    # Check the observations underpinning all time offsets, not just year labels.
    historical = wrp.set_index(['country_id', 'year'], verify_integrity=True)
    for offset, prefix in [(0, ''), (-5, 'lag5_'), (-10, 'lag10_'), (5, 'target_')]:
        keys = pd.MultiIndex.from_arrays([
            examples.country_id.to_numpy(), (examples.origin_year + offset).to_numpy()
        ], names=['country_id', 'year'])
        actual = historical.loc[keys, SHARES].to_numpy(dtype=float)
        observed = examples[[prefix + s for s in SHARES]].to_numpy(dtype=float)
        assert np.allclose(actual, observed, atol=1e-8), f'Offset {offset} religion mismatch'
    for gap in (5, 10):
        actual = (examples[SHARES].to_numpy() -
                  examples[[f'lag{gap}_{s}' for s in SHARES]].to_numpy())
        observed = examples[[f'change{gap}_{s}' for s in SHARES]].to_numpy()
        assert np.allclose(actual, observed, atol=1e-8)

    train = folds.loc[folds.split.eq('train')]
    valid = folds.loc[folds.split.eq('validation')]
    assert set(folds['split']) == {'train', 'validation'}
    assert (train.target_year <= train.fold_origin).all()
    assert (valid.origin_year == valid.fold_origin).all()
    assert (valid.target_year == valid.fold_origin + 5).all()
    assert set(folds.row_id).issubset(set(examples.row_id))
    assert not examples[feature_spec['predictors']].select_dtypes('number').isin([np.inf, -np.inf]).any().any()

    print('PASS: Historical inputs are from t, t-5, t-10 only; labels from t+5.')
    print('PASS: Eight religion shares sum to one at origin and target.')
    print('PASS: Training label years never exceed their fold cutoff.')
    print('PASS: Predictor list excludes target columns.')
    print(f'Origin rows: {len(origins):,}; labeled transitions: {len(examples):,}')
    print(f'Rolling validation folds: {valid.fold_origin.nunique()}')


if __name__ == '__main__':
    main()
