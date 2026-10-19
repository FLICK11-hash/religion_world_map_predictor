"""Step 4B: leakage-aware, rolling-origin calibration of WRP one-step blends.

Usage (from the same folder as Step 4):
    .\\.venv\\Scripts\\python.exe step4b_blend_validate.py

Read ONLY previously validated, out-of-sample Step 4 predictions. At each
forecast origin T, choose blend parameters using scored predictions whose
TARGET years are <= T. Evaluate on T+5. No data from the evaluation fold is
used to choose that fold's blend, and no model is refit.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / 'data' / 'models'
OUT = MODEL_DIR / 'step4b'
PREDICTION_FILE = MODEL_DIR / 'one_step_predictions.csv'
KEYS = ['forecast_origin', 'target_year', 'horizon_years', 'country_id']
RELIGIONS = [
    'Christianity', 'Islam', 'Hinduism', 'Buddhism',
    'Judaism', 'Folk_Traditional', 'Other', 'Unaffiliated',
]
SEED = 2026
BOOTSTRAPS = 1000


def load_predictions() -> pd.DataFrame:
    if not PREDICTION_FILE.exists():
        raise FileNotFoundError(f'Run Step 4 first: {PREDICTION_FILE}')
    df = pd.read_csv(PREDICTION_FILE, low_memory=False)
    necessary = set(KEYS + ['model', 'origin_dominant', 'observed_dominant']
                    + [f'pred_{r}' for r in RELIGIONS]
                    + [f'actual_{r}' for r in RELIGIONS])
    missing = necessary - set(df.columns)
    if missing:
        raise ValueError(f'Missing prediction columns: {sorted(missing)}')
    df = df.loc[df.model.isin(['persistence', 'lightgbm']) & df.horizon_years.eq(5)].copy()
    p = df.loc[df.model.eq('persistence')].drop(columns='model')
    l = df.loc[df.model.eq('lightgbm')].drop(columns='model')
    if p.duplicated(KEYS).any() or l.duplicated(KEYS).any():
        raise ValueError('Duplicate model-country-origin keys')
    merged = p.merge(l, on=KEYS, suffixes=('_p', '_l'), validate='one_to_one', how='outer', indicator=True)
    if not merged['_merge'].eq('both').all():
        raise ValueError('Persistence and LightGBM predictions cover different observations')
    merged = merged.drop(columns='_merge').sort_values(KEYS).reset_index(drop=True)
    for text_col in ['origin_dominant', 'observed_dominant']:
        if not merged[f'{text_col}_p'].eq(merged[f'{text_col}_l']).all():
            raise ValueError(f'Inconsistent {text_col} between models')
    for r in RELIGIONS:
        if not np.allclose(merged[f'actual_{r}_p'].to_numpy(float),
                           merged[f'actual_{r}_l'].to_numpy(float), atol=1e-9):
            raise ValueError(f'Inconsistent ground truth for {r}')
    if not merged.target_year.eq(merged.forecast_origin + 5).all():
        raise ValueError('Found incorrectly dated predictions')
    for suffix in ['p', 'l']:
        cols = [f'pred_{r}_{suffix}' for r in RELIGIONS]
        arr = merged[cols].to_numpy(float)
        if not np.isfinite(arr).all() or (arr < -1e-9).any() or not np.allclose(arr.sum(1), 1, atol=1e-7):
            raise ValueError(f'Invalid {suffix} compositions')
    actual = merged[[f'actual_{r}_p' for r in RELIGIONS]].to_numpy(float)
    if not np.isfinite(actual).all() or (actual < -1e-9).any() or not np.allclose(actual.sum(1), 1, atol=1e-7):
        raise ValueError('Invalid target compositions')
    start = merged[[f'pred_{r}_p' for r in RELIGIONS]].to_numpy(float)
    for label, arr in [('origin', start), ('truth', actual)]:
        derived = np.asarray(RELIGIONS, dtype=object)[np.argmax(arr, axis=1)]
        expected = merged['origin_dominant_p' if label == 'origin' else 'observed_dominant_p']
        if not np.array_equal(derived, expected.to_numpy()):
            raise ValueError(f'{label} dominant labels disagree with shares')
    if len(merged) < 50 or merged.forecast_origin.nunique() < 3:
        raise ValueError('Need at least three chronological folds and 50 paired rows')
    return merged


def as_arrays(df):
    p = df[[f'pred_{r}_p' for r in RELIGIONS]].to_numpy(float)
    l = df[[f'pred_{r}_l' for r in RELIGIONS]].to_numpy(float)
    truth = df[[f'actual_{r}_p' for r in RELIGIONS]].to_numpy(float)
    return p, l, truth


def candidates():
    params = [('fixed', float(a), None) for a in [0., .05, .10, .20, .35, .50, .75, 1.]]
    params += [('margin', float(a), float(w)) for a in [.35, .75, 1.] for w in [.10, .25]]
    return params


def candidate_name(spec):
    kind, alpha, window = spec
    if kind == 'fixed':
        return f'fixed_alpha_{alpha:g}'
    return f'margin_alpha_{alpha:g}_window_{window:g}'


def calculate_blend(p: np.ndarray, l: np.ndarray, spec):
    kind, alpha, window = spec
    weights = np.full(len(p), alpha, dtype=float)
    if kind == 'margin':
        # The plurality margin is computed ONLY from the origin-year shares.
        top_two = np.sort(p, axis=1)[:, -2:]
        margin = top_two[:, 1] - top_two[:, 0]
        weights *= np.clip(1. - margin / window, 0., 1.)
    blended = p * (1. - weights[:, None]) + l * weights[:, None]
    if not np.isfinite(blended).all() or (blended < -1e-9).any() or not np.allclose(blended.sum(1), 1, atol=1e-7):
        raise AssertionError('Blend failed to produce valid religious shares')
    return blended, weights


def changed_flags(p, pred, truth):
    origin = np.argmax(p, axis=1)
    actual = np.argmax(truth, axis=1)
    predicted = np.argmax(pred, axis=1)
    real_change = actual != origin
    predicted_change = predicted != origin
    correct_change = real_change & (predicted == actual)
    false_change_alarm = predicted_change & ~real_change
    wrong_new_religion = predicted_change & real_change & (predicted != actual)
    return origin, actual, predicted, real_change, predicted_change, correct_change, false_change_alarm, wrong_new_religion


def metrics(p, pred, truth, *, weights=None):
    vals = np.abs(pred-truth).mean(axis=1)
    _, actual, predicted, real_change, predicted_change, correct_change, false_alarm, wrong_new = changed_flags(p, pred, truth)
    tp = int(correct_change.sum())
    fp = int((false_alarm | wrong_new).sum())
    n_change = int(real_change.sum())
    recall = tp / n_change if n_change else None
    precision = tp / (tp+fp) if (tp+fp) else None
    f1 = 2*precision*recall/(precision+recall) if precision is not None and recall is not None and precision+recall else None
    return {
        'n': int(len(pred)),
        'mae': float(vals.mean()),
        'dominant_accuracy': float((actual == predicted).mean()),
        'actual_changes': n_change,
        'correct_changes': tp,
        'predicted_changes': int(predicted_change.sum()),
        'false_change_alarms': int(false_alarm.sum()),
        'wrong_religion_switches': int(wrong_new.sum()),
        'change_precision': precision,
        'change_recall': recall,
        'change_f1': f1,
        'average_weight': float(np.mean(weights)) if weights is not None else None,
    }


def tune_spec(df: pd.DataFrame, *, change_weight=1.0):
    p, l, truth = as_arrays(df)
    real_change = np.argmax(p, axis=1) != np.argmax(truth, axis=1)
    row_weights = np.where(real_change, change_weight, 1.)
    # Strict historical selection. Ties favor lower alpha / persistence.
    scores = []
    for index, spec in enumerate(candidates()):
        blend, _ = calculate_blend(p, l, spec)
        errors = np.abs(blend-truth).mean(axis=1)
        loss = float(np.average(errors, weights=row_weights))
        scores.append((loss, index, spec))
    loss, _, selected = min(scores, key=lambda v: (round(v[0], 13), v[1]))
    return selected, loss


def make_records(df: pd.DataFrame, pred: np.ndarray, weights: np.ndarray, method: str, history_end: int | None, selected: str):
    p, _, truth = as_arrays(df)
    origin, actual, predicted, real_change, predicted_change, correct_change, false_alarm, wrong_new = changed_flags(p, pred, truth)
    rows = []
    for i, row in enumerate(df.itertuples(index=False)):
        rec = {
            'method': method, 'selected_blend': selected,
            'forecast_origin': int(row.forecast_origin), 'target_year': int(row.target_year),
            'country_id': str(row.country_id),
            'max_calibration_target_year': history_end,
            'alpha_used': float(weights[i]),
            'country_share_mae': float(np.abs(pred[i]-truth[i]).mean()),
            'actual_changed': bool(real_change[i]),
            'predicted_changed': bool(predicted_change[i]),
            'correct_change': bool(correct_change[i]),
            'false_change_alarm': bool(false_alarm[i]),
            'wrong_religion_switch': bool(wrong_new[i]),
            'actual_dominant': RELIGIONS[actual[i]],
            'origin_dominant': RELIGIONS[origin[i]],
            'predicted_dominant': RELIGIONS[predicted[i]],
        }
        for j, name in enumerate(RELIGIONS):
            rec[f'pred_{name}'] = float(pred[i,j])
            rec[f'actual_{name}'] = float(truth[i,j])
        rows.append(rec)
    return rows


def clustered_ci(evaluated: pd.DataFrame, *, method: str, baseline='persistence', n_boot=BOOTSTRAPS):
    left = evaluated.loc[evaluated.method.eq(method), ['forecast_origin', 'country_id', 'country_share_mae']]
    right = evaluated.loc[evaluated.method.eq(baseline), ['forecast_origin', 'country_id', 'country_share_mae']]
    pairs = left.merge(right, on=['forecast_origin', 'country_id'], validate='one_to_one', suffixes=('_method','_baseline'))
    if len(pairs) != len(left) or len(pairs) != len(right):
        raise ValueError('Could not pair all errors for bootstrap')
    pairs['delta'] = pairs.country_share_mae_method - pairs.country_share_mae_baseline
    groups = pairs.groupby('country_id')['delta'].agg(['sum','count'])
    sums = groups['sum'].to_numpy(float)
    counts = groups['count'].to_numpy(float)
    rng = np.random.default_rng(SEED)
    n_country = len(groups)
    sampled = rng.integers(0, n_country, (n_boot, n_country))
    draws = sums[sampled].sum(axis=1) / counts[sampled].sum(axis=1)
    low, high = np.percentile(draws, [2.5, 97.5])
    return {'mae_difference_vs_persistence': float(pairs.delta.mean()),
            'cluster_bootstrap_95ci_lower': float(low), 'cluster_bootstrap_95ci_upper': float(high),
            'bootstrap_draws': n_boot, 'country_clusters': n_country}


def make_plots(diagnostics: pd.DataFrame, summaries: pd.DataFrame):
    fixed = diagnostics[diagnostics.kind.eq('fixed')].sort_values('alpha')
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(fixed.alpha, fixed.mae * 100, marker='o')
    ax.set_xlabel('LightGBM blending weight (alpha)')
    ax.set_ylabel('Share MAE (percentage points)')
    ax.set_title('Fixed blending weights: exploratory comparison')
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(OUT / 'fixed_blend_mae.png', dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    summary = summaries.sort_values('mae')
    ax.bar(summary.method, summary.mae * 100)
    ax.set_ylabel('Share MAE (percentage points)')
    ax.set_title('Chronological evaluation (1980–2005 origins)')
    ax.tick_params(axis='x', rotation=20)
    fig.tight_layout()
    fig.savefig(OUT / 'rolling_blend_comparison.png', dpi=180)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = load_predictions()
    folds = sorted(data.forecast_origin.unique().tolist())
    if min(folds) < 1900:
        raise ValueError('Unexpected historical data')
    evaluation_folds = folds[1:]
    evaluated = data.loc[data.forecast_origin.isin(evaluation_folds)].copy()
    combined = []
    selections = []

    # True rolling selection: at origin T, calibration target <= T.
    for fold in evaluation_folds:
        current = data.loc[data.forecast_origin.eq(fold)].copy()
        available = data.loc[data.target_year.le(fold)].copy()
        if available.empty:
            raise AssertionError(f'No historical calibration examples by {fold}')
        hist_max = int(available.target_year.max())
        if hist_max > fold or (available.forecast_origin >= fold).any():
            raise AssertionError('Future information entered calibration')
        p, l, _ = as_arrays(current)
        for method, change_weight in [('rolling_mae', 1.), ('rolling_change_weighted', 5.)]:
            chosen, tuning_loss = tune_spec(available, change_weight=change_weight)
            chosen_name = candidate_name(chosen)
            result, weights = calculate_blend(p, l, chosen)
            combined.extend(make_records(current, result, weights, method, hist_max, chosen_name))
            selections.append({
                'method': method, 'forecast_origin': int(fold),
                'target_year': int(fold+5), 'selected_blend': chosen_name,
                'historical_calibration_examples': int(len(available)),
                'max_calibration_target_year': hist_max,
                'tuning_loss': tuning_loss,
                'selected_mean_weight_this_fold': float(weights.mean()),
            })
        for method, spec in [('persistence', ('fixed',0.,None)), ('lightgbm',('fixed',1.,None))]:
            pred, w = calculate_blend(p,l,spec)
            combined.extend(make_records(current, pred, w, method, None, candidate_name(spec)))

    evaluation = pd.DataFrame(combined).sort_values(['forecast_origin','country_id','method'])
    selection_df = pd.DataFrame(selections).sort_values(['forecast_origin','method'])
    evaluation.to_csv(OUT / 'rolling_blend_predictions.csv', index=False)
    selection_df.to_csv(OUT / 'rolling_blend_selections.csv', index=False)

    # Fixed candidates: useful diagnostic curves, NOT independent selection results.
    p, l, truth = as_arrays(evaluated)
    candidate_rows = []
    for spec in candidates():
        pred, w = calculate_blend(p,l,spec)
        candidate_rows.append({
            'candidate': candidate_name(spec), 'kind': spec[0], 'alpha': spec[1],
            'margin_window': spec[2], **metrics(p,pred,truth,weights=w),
        })
    diagnostics = pd.DataFrame(candidate_rows)
    diagnostics.to_csv(OUT / 'fixed_blend_diagnostics_EXPLORATORY.csv', index=False)

    summary_rows = []
    for method in ['persistence','lightgbm','rolling_mae','rolling_change_weighted']:
        d = evaluation.loc[evaluation.method.eq(method)]
        pred = d[[f'pred_{r}' for r in RELIGIONS]].to_numpy(float)
        actual = d[[f'actual_{r}' for r in RELIGIONS]].to_numpy(float)
        # Get exact persisted origin-year shares from paired, keyed Step 4 data.
        join = d[['forecast_origin','country_id']].merge(
            data[['forecast_origin','country_id']+[f'pred_{r}_p' for r in RELIGIONS]],
            on=['forecast_origin','country_id'], validate='one_to_one')
        start = join[[f'pred_{r}_p' for r in RELIGIONS]].to_numpy(float)
        result = metrics(start, pred, actual, weights=d.alpha_used.to_numpy(float))
        row = {'method': method, **result}
        if method != 'persistence':
            row.update(clustered_ci(evaluation, method=method))
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / 'rolling_blend_summary.csv', index=False)
    make_plots(diagnostics, summary)

    report = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'input_predictions': str(PREDICTION_FILE),
        'calibration_fold': int(folds[0]),
        'evaluated_forecast_origins': list(map(int, evaluation_folds)),
        'evaluated_target_years': [int(x+5) for x in evaluation_folds],
        'n_test_country_years': int(len(evaluated)),
        'selection_policy': 'At each forecast origin T, select using validation targets at or before T. Never use T+5 or later.',
        'adaptive_methods': {'rolling_mae': 'Minimize past share MAE',
                             'rolling_change_weighted': 'Minimize past share MAE with fivefold weight on true dominant changes'},
        'summary': json.loads(summary.to_json(orient='records')),
        'selected_blends_by_fold': json.loads(selection_df.to_json(orient='records')),
        'cautions': [
            'Uses already generated out-of-sample Step 4 WRP forecasts; no models retrained.',
            'This is retrospective rolling validation, not independent holdout nor vintage-realistic due to UN revisions.',
            'Change cases are rare; transition precision and recall estimates have large uncertainty.',
            'Fixed-blend diagnostic rankings are exploratory and MUST NOT be reported as independent model selection.',
            'Only five-year predictions are blended; long-horizon recursive hybrids must be independently implemented and backtested.',
            'Country-cluster bootstrap measures cross-country sampling variation, not structural forecast uncertainty.',
            'Pew is not used. No future religion observations enter the calibration at each evaluation origin.',
        ],
    }
    (OUT / 'step4b_report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    print('SUCCESS: Step 4B rolling-origin blending evaluation complete.')
    print('Evaluated origins:', evaluation_folds, '| country-year cases:', len(evaluated))
    print(summary[['method','n','mae','dominant_accuracy','actual_changes','correct_changes','false_change_alarms','wrong_religion_switches']].to_string(index=False, float_format=lambda x:f'{x:.5f}'))
    print('\nRolling selections:')
    print(selection_df[['method','forecast_origin','selected_blend','max_calibration_target_year']].to_string(index=False))
    print('\nOutputs:', OUT)
    print('NEXT: run verify_step4b.py and inspect the summary before forecasting.')


if __name__ == '__main__':
    main()
