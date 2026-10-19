"""Step 4: forward-origin WRP religious-share forecasting model comparison.

Run next to Step 3 scripts: .\\.venv\\Scripts\\python.exe step4_train_validate.py

Models: persistence, projected linear trend, LightGBM, MLP neural network.
All modeling targets are WRP five-year share changes expressed as centered
log-ratio deltas, inverted with softmax. Historical evaluation stays WRP-only.

IMPORTANT: This is retrospective, not strict vintage-available backtesting:
WPP2024 demographic reconstructions and modern geography are used in past folds.
For horizons >5, demographic covariates are FROZEN at each forecast origin.
Only simulated shares are fed back; no intermediate actual religious shares.
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import lightgbm as lgb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.multioutput import MultiOutputRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
FEATURE_DIR = ROOT / 'data' / 'features'
PROCESSED_DIR = ROOT / 'data' / 'processed'
OUT = ROOT / 'data' / 'models'
CATEGORIES = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism',
              'Folk_Traditional', 'Other', 'Unaffiliated']
SHARES = [f'share_{s}' for s in CATEGORIES]
TARGETS = [f'target_{s}' for s in SHARES]
MODELS = ['persistence', 'linear_trend', 'lightgbm', 'neural_network']
EPSILON = 1e-5
SEED = 42


def read_input_files():
    feature_info = json.loads((FEATURE_DIR / 'feature_columns.json').read_text(encoding='utf-8'))
    cols = feature_info['predictors']
    if any(c not in cols for c in SHARES) or feature_info['targets'] != TARGETS:
        raise ValueError('Unexpected Step 3 predictor or target definitions')
    samples = pd.read_csv(FEATURE_DIR / 'wrp_training_transitions.csv', low_memory=False)
    origins = pd.read_csv(FEATURE_DIR / 'wrp_origin_features.csv', low_memory=False)
    assignments = pd.read_csv(FEATURE_DIR / 'rolling_origin_one_step_splits.csv')
    plan = pd.read_csv(FEATURE_DIR / 'multihorizon_evaluation_plan.csv')
    wrp = pd.read_csv(PROCESSED_DIR / 'wrp_training_only_8groups.csv', low_memory=False)
    for label, frame, required in [
        ('samples', samples, ['row_id', 'country_id', 'origin_year', 'target_year', *cols, *TARGETS]),
        ('origins', origins, ['row_id', 'country_id', 'origin_year', *cols]),
        ('WRP', wrp, ['country_id', 'year', *SHARES]),
        ('splits', assignments, ['fold_origin', 'row_id', 'split']),
        ('plan', plan, ['forecast_origin', 'target_year', 'horizon_years']),
    ]:
        missing = set(required) - set(frame.columns)
        if missing:
            raise ValueError(f'{label} missing: {sorted(missing)}')
    if samples['row_id'].duplicated().any() or origins['row_id'].duplicated().any():
        raise ValueError('Step 3 features have duplicate row_id values')
    if wrp.duplicated(['country_id', 'year']).any():
        raise ValueError('WRP source has duplicate country-years')
    if not (samples.target_year - samples.origin_year).eq(5).all():
        raise ValueError('Training transitions not exactly 5 years')
    if not np.allclose(samples[TARGETS].sum(axis=1), 1, atol=1e-7):
        raise ValueError('Targets do not sum to 1')
    return cols, samples, origins, assignments, plan, wrp


def share_array(frame: pd.DataFrame, columns: list[str] = SHARES) -> np.ndarray:
    arr = frame[columns].to_numpy(dtype=float)
    if not np.isfinite(arr).all() or (arr < -1e-9).any() or not np.allclose(arr.sum(1), 1, atol=1e-7):
        raise ValueError('Invalid simplex values')
    return np.clip(arr, 0, 1)


def simplex_projection(v):
    """Project rows onto {x>=0, sum(x)=1}, for the linear extrapolation baseline."""
    v = np.asarray(v, dtype=float)
    if v.ndim != 2:
        raise ValueError('Expected 2D input')
    u = np.sort(v, axis=1)[:, ::-1]
    cssv = np.cumsum(u, axis=1) - 1
    j = np.arange(1, v.shape[1] + 1)
    cond = u - cssv / j > 0
    rho = np.maximum(cond.sum(axis=1), 1) - 1
    theta = cssv[np.arange(len(v)), rho] / (rho + 1)
    return np.maximum(v - theta[:, None], 0)


def clr_delta(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    d = np.log(np.maximum(after, EPSILON)) - np.log(np.maximum(before, EPSILON))
    return d - d.mean(axis=1, keepdims=True)


def apply_clr_delta(current: np.ndarray, changes: np.ndarray) -> np.ndarray:
    """Softmax inverse preserves exact share compositionality."""
    logits = np.log(np.maximum(current, EPSILON)) + np.clip(changes, -6., 6.)
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    return probs / probs.sum(axis=1, keepdims=True)


def make_estimator(name: str):
    if name == 'lightgbm':
        return Pipeline([
            ('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
            ('model', MultiOutputRegressor(lgb.LGBMRegressor(
                n_estimators=130, learning_rate=0.04, max_depth=-1,
                num_leaves=11, min_child_samples=30, reg_lambda=5.,
                colsample_bytree=0.85, subsample=1., random_state=SEED,
                n_jobs=2, verbosity=-1))),
        ])
    if name == 'neural_network':
        return Pipeline([
            ('imputer', SimpleImputer(strategy='median', keep_empty_features=True)),
            ('scaler', StandardScaler()),
            # Explicit epochs; no random holdout or within-sample future validation.
            ('model', MLPRegressor(hidden_layer_sizes=(48, 24), max_iter=175,
                learning_rate_init=0.001, alpha=0.1, batch_size=64,
                shuffle=False, early_stopping=False, random_state=SEED)),
        ])
    raise ValueError(name)


def fit_estimator(name: str, train: pd.DataFrame, predictors: list[str]):
    est = make_estimator(name)
    before = share_array(train, SHARES)
    target = share_array(train, TARGETS)
    y = clr_delta(before, target)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=ConvergenceWarning)
        est.fit(train[predictors], y)
    return est


def predict_shares(name: str, frame: pd.DataFrame, predictors: list[str], estimator=None):
    base = share_array(frame, SHARES)
    if name == 'persistence':
        return base.copy()
    if name == 'linear_trend':
        previous = frame[[f'lag5_{s}' for s in SHARES]].to_numpy(dtype=float)
        if not np.isfinite(previous).all():
            raise ValueError('Missing lag5 shares for linear trend')
        return simplex_projection(2 * base - previous)
    if estimator is None:
        raise ValueError('Trained model required')
    X = frame[predictors]
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='X does not have valid feature names', category=UserWarning)
        yhat = np.asarray(estimator.predict(X), dtype=float)
    if yhat.shape != base.shape:
        raise ValueError(f'Model {name} output wrong shape {yhat.shape}')
    return apply_clr_delta(base, yhat)


def record_scores(frame: pd.DataFrame, predictions: np.ndarray, observed: np.ndarray,
                  model: str, fold: int, horizon: int):
    truth_idx = np.argmax(observed, axis=1)
    predicted_idx = np.argmax(predictions, axis=1)
    start_idx = np.argmax(frame[SHARES].to_numpy(dtype=float), axis=1)
    changed = truth_idx != start_idx
    accuracy = float(np.mean(predicted_idx == truth_idx))
    metrics = {
        'model': model, 'forecast_origin': int(fold), 'horizon_years': int(horizon),
        'target_year': int(fold+horizon), 'n_countries': int(len(frame)),
        'share_mae': float(np.abs(predictions-observed).mean()),
        'dominant_accuracy': accuracy,
        'n_changed_dominant': int(changed.sum()),
        'changed_dominant_accuracy': float(np.mean(predicted_idx[changed] == truth_idx[changed]))
            if changed.any() else np.nan,
    }
    rows = []
    for i, (cid, year) in enumerate(zip(frame.country_id, [fold+horizon]*len(frame))):
        rec = {
            'model': model, 'forecast_origin': int(fold), 'horizon_years': int(horizon),
            'target_year': int(year), 'country_id': str(cid),
            'observed_dominant': CATEGORIES[truth_idx[i]],
            'predicted_dominant': CATEGORIES[predicted_idx[i]],
            'origin_dominant': CATEGORIES[start_idx[i]],
            'dominant_changed': bool(changed[i]),
            'country_share_mae': float(np.abs(predictions[i]-observed[i]).mean()),
        }
        for j, s in enumerate(CATEGORIES):
            rec[f'pred_{s}'] = float(predictions[i,j])
            rec[f'actual_{s}'] = float(observed[i,j])
        rows.append(rec)
    return metrics, rows


def build_neighbor_context():
    """Reuse Step 3's map interpretation for deterministic recursive spatial updates."""
    try:
        from step3_engineer_features import geographic_reference
    except ImportError as exc:
        raise RuntimeError('Keep step3_engineer_features.py next to this script') from exc
    return geographic_reference()


def update_spatial_features(frame: pd.DataFrame, continents: dict, neighbors: dict):
    """Compute t+5 spatial means from own cohort predicted values only.

    No ground-truth t+5 shares or country entries are used. Countries absent from
    the origin cohort cannot suddenly enter these simulations.
    """
    cur = frame.set_index('country_id', verify_integrity=True)[SHARES]
    countries = set(cur.index)
    result = frame.copy()
    for ridx, cid in enumerate(result['country_id'].astype(str)):
        cont = continents.get(cid)
        around = [n for n in neighbors.get(cid, []) if n in countries and n != cid]
        on_cont = [c for c in countries if c != cid and cont is not None and continents.get(c) == cont]
        result.at[ridx, 'n_land_neighbors_observed'] = len(around)
        result.at[ridx, 'n_continent_peers_observed'] = len(on_cont)
        result.at[ridx, 'border_mean_missing'] = int(not around)
        result.at[ridx, 'continent_mean_missing'] = int(not on_cont)
        border = cur.loc[around].mean().to_numpy() if around else [np.nan] * len(SHARES)
        continent = cur.loc[on_cont].mean().to_numpy() if on_cont else [np.nan] * len(SHARES)
        for j, col in enumerate(SHARES):
            result.at[ridx, f'border_mean_{col}'] = float(border[j])
            result.at[ridx, f'continent_mean_{col}'] = float(continent[j])
    return result


def advance_state(frame: pd.DataFrame, new_shares: np.ndarray, continents: dict, neighbors: dict):
    """Advance simulated state by one five-year step without actual intermediate religion data.

    Demographics are frozen at the forecast origin to avoid future feature leakage;
    these backtests test religion dynamics under a no-demographic-change scenario.
    """
    nxt = frame.copy().reset_index(drop=True)
    cur = frame[SHARES].to_numpy(dtype=float)
    prev = frame[[f'lag5_{s}' for s in SHARES]].to_numpy(dtype=float)
    oldlag10 = frame[[f'lag10_{s}' for s in SHARES]].to_numpy(dtype=float)
    for j, s in enumerate(SHARES):
        nxt[s] = new_shares[:,j]
        nxt[f'lag5_{s}'] = cur[:,j]
        nxt[f'lag10_{s}'] = prev[:,j]
        nxt[f'change5_{s}'] = new_shares[:,j] - cur[:,j]
        nxt[f'change10_{s}'] = new_shares[:,j] - prev[:,j]
    nxt['origin_year'] += 5
    nxt['row_id'] = nxt['country_id'].astype(str) + '__' + nxt['origin_year'].astype(str)
    return update_spatial_features(nxt, continents, neighbors)


def run_one_step(samples, assignments, predictors, results):
    alloc = assignments[['fold_origin','row_id','split']]
    if alloc.duplicated(['fold_origin','row_id']).any():
        raise ValueError('Repeated fold/row in assignments')
    folds = sorted(alloc.fold_origin.unique())
    saved_estimators = {}
    one_step_scores, one_step_predictions = [], []
    for fold in folds:
        selected = alloc[alloc.fold_origin.eq(fold)]
        train_ids = set(selected.loc[selected.split.eq('train'), 'row_id'])
        valid_ids = set(selected.loc[selected.split.eq('validation'), 'row_id'])
        train = samples[samples.row_id.isin(train_ids)].sort_values(['target_year','country_id'])
        valid = samples[samples.row_id.isin(valid_ids)].sort_values('country_id')
        if len(train) != len(train_ids) or len(valid) != len(valid_ids):
            raise ValueError(f'Fold {fold} has unknown row ids')
        if train.empty or valid.empty or train.target_year.max() > fold:
            raise ValueError(f'Invalid chronology in fold {fold}')
        if not (valid.origin_year.eq(fold) & valid.target_year.eq(fold + 5)).all():
            raise ValueError(f'Invalid validation years fold {fold}')
        ytrue = share_array(valid, TARGETS)
        fitted = {name: fit_estimator(name, train, predictors)
                  for name in ['lightgbm', 'neural_network']}
        saved_estimators[int(fold)] = fitted
        for model in MODELS:
            pred = predict_shares(model, valid, predictors, fitted.get(model))
            metric, rows = record_scores(valid, pred, ytrue, model, int(fold), 5)
            one_step_scores.append(metric)
            one_step_predictions.extend(rows)
        print(f'  One-step origin {fold}: train={len(train)}, validate={len(valid)}', flush=True)
    return pd.DataFrame(one_step_scores), pd.DataFrame(one_step_predictions), saved_estimators


def run_multihorizon(origins, wrp, plan, predictors, estimators, geo_context,
                     one_step_scores, one_step_predictions):
    continents, neighbors = geo_context
    truth = wrp.set_index(['country_id','year'], verify_integrity=True)[SHARES]
    scores = []
    predictions = []
    # 5-year entries are precisely the one-step backtests; don't duplicate.
    for row in plan.itertuples(index=False):
        fold, horizon = int(row.forecast_origin), int(row.horizon_years)
        if horizon == 5:
            scores.extend(one_step_scores[one_step_scores.forecast_origin.eq(fold)].to_dict('records'))
            predictions.extend(one_step_predictions[
                one_step_predictions.forecast_origin.eq(fold)].to_dict('records'))
            continue
        initial = origins[origins.origin_year.eq(fold)].sort_values('country_id').reset_index(drop=True)
        if initial.empty:
            continue
        endpoint = fold + horizon
        endpoint_countries = set(wrp.loc[wrp.year.eq(endpoint), 'country_id'])
        # Freeze a cohort selected at the origin; never add future-only countries.
        # Cross-country predictions for cohort members without endpoint truth remain
        # in the recursion so they can influence predicted spatial peer features.
        for model in MODELS:
            state = initial.copy()
            estimator = estimators[fold].get(model)
            n_steps = horizon // 5
            for _ in range(n_steps):
                pred = predict_shares(model, state, predictors, estimator)
                state = advance_state(state, pred, continents, neighbors)
            scored = state.loc[state.country_id.isin(endpoint_countries)].copy()
            scored = scored.sort_values('country_id').reset_index(drop=True)
            if scored.empty:
                continue
            keys = pd.MultiIndex.from_arrays(
                [scored.country_id.to_numpy(), np.repeat(endpoint, len(scored))],
                names=['country_id','year'])
            actual = truth.loc[keys].to_numpy(dtype=float)
            start = initial.set_index('country_id').loc[scored.country_id, SHARES].to_numpy(dtype=float)
            # Metrics must assess changed dominance compared with true origin share,
            # not the final simulated share.
            assessment = scored.copy()
            assessment[SHARES] = start
            measured, rows = record_scores(assessment, scored[SHARES].to_numpy(float),
                                            actual, model, fold, horizon)
            scores.append(measured)
            predictions.extend(rows)
        print(f'  Recursive origin {fold} -> {endpoint} ({horizon} years)', flush=True)
    return pd.DataFrame(scores), pd.DataFrame(predictions)


def aggregate_scores(predictions: pd.DataFrame):
    """Country-weighted aggregate scores, not simple mean of per-fold percentages."""
    pred = predictions.copy()
    pred['correct_label'] = pred.predicted_dominant.eq(pred.observed_dominant)
    outputs = []
    for (model, horizon), group in pred.groupby(['model','horizon_years'], sort=True):
        changes = group[group.dominant_changed]
        outputs.append({
            'model': model, 'horizon_years': int(horizon), 'n_predictions': len(group),
            'share_mae': float(group.country_share_mae.mean()),
            'dominant_accuracy': float(group.correct_label.mean()),
            'n_changed_dominant': len(changes),
            'changed_dominant_accuracy': float(changes.correct_label.mean()) if len(changes) else np.nan,
        })
    summary = pd.DataFrame(outputs).sort_values(['horizon_years','share_mae','model']).reset_index(drop=True)
    persistence = summary[summary.model.eq('persistence')].set_index('horizon_years')
    summary['persistence_mae'] = summary.horizon_years.map(persistence.share_mae)
    summary['mae_improvement_vs_persistence'] = summary.persistence_mae - summary.share_mae
    summary['beats_persistence_mae'] = summary.mae_improvement_vs_persistence.gt(1e-10)
    return summary


def draw_horizon_plots(summary: pd.DataFrame):
    for metric, title, filename in [
        ('share_mae', 'Religion share MAE by forecast horizon', 'share_mae_by_horizon.png'),
        ('dominant_accuracy', 'Dominant-religion accuracy by forecast horizon', 'dominant_accuracy_by_horizon.png'),
    ]:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for name in MODELS:
            subset = summary[summary.model.eq(name)].sort_values('horizon_years')
            ax.plot(subset.horizon_years, subset[metric], marker='o', label=name)
        ax.set_title(title)
        ax.set_xlabel('Forecast horizon (years)')
        ax.set_ylabel('MAE (0-1 share units)' if metric == 'share_mae' else 'Accuracy (fraction)')
        ax.set_xticks(sorted(summary.horizon_years.unique()))
        ax.grid(alpha=0.2)
        ax.legend(loc='best')
        fig.tight_layout()
        fig.savefig(OUT / filename, dpi=170)
        plt.close(fig)


def main():
    np.random.seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    predictors, samples, origins, assignments, plan, wrp = read_input_files()
    print(f'Step 4: {len(samples)} training rows, {len(origins)} origin rows, '
          f'{assignments.fold_origin.nunique()} chronological folds', flush=True)
    print('Training 4 models for one-step validation...', flush=True)
    scores5, preds5, fold_models = run_one_step(samples, assignments, predictors, OUT)
    print('Evaluating genuine recursive multihorizon backtests...', flush=True)
    geo_context = build_neighbor_context()
    multi_scores, multi_preds = run_multihorizon(origins, wrp, plan, predictors,
        fold_models, geo_context, scores5, preds5)
    summary = aggregate_scores(multi_preds)
    summary5 = summary[summary.horizon_years.eq(5)].sort_values('share_mae')
    best = str(summary5.iloc[0]['model'])
    print('Refitting historical models on all WRP transitions...', flush=True)
    fitted_full = {name: fit_estimator(name, samples.sort_values(['target_year','country_id']), predictors)
                   for name in ['lightgbm', 'neural_network']}
    for name, fitted in fitted_full.items():
        joblib.dump({'model_name': name, 'estimator': fitted,
                     'predictors': predictors, 'shares': SHARES,
                     'train_last_target_year': int(samples.target_year.max()),
                     'compositional_method': 'CLR change + softmax',
                     'seed': SEED}, OUT / f'{name}_all_wrp.joblib')
    # 'best_model.joblib' works even if the baseline wins.
    joblib.dump({'model_name': best, 'estimator': fitted_full.get(best),
                 'predictors': predictors, 'shares': SHARES,
                 'train_last_target_year': int(samples.target_year.max()),
                 'compositional_method': 'CLR change + softmax if learned model',
                 'seed': SEED}, OUT / 'best_model.joblib')
    scores5.to_csv(OUT / 'one_step_fold_metrics.csv', index=False)
    preds5.to_csv(OUT / 'one_step_predictions.csv', index=False)
    multi_scores.to_csv(OUT / 'multihorizon_fold_metrics.csv', index=False)
    multi_preds.to_csv(OUT / 'multihorizon_predictions.csv', index=False)
    summary.to_csv(OUT / 'model_comparison_by_horizon.csv', index=False)
    draw_horizon_plots(summary)
    report = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'n_transition_examples': len(samples),
        'n_folds': int(assignments.fold_origin.nunique()),
        'n_multihorizon_origin_horizon_plans': len(plan),
        'best_5year_model_by_country_weighted_mae': best,
        'one_step_comparison': summary5.replace({np.nan: None}).to_dict('records'),
        'horizon_comparison': summary.replace({np.nan: None}).to_dict('records'),
        'cautions': [
            'All training outcomes and evaluation religion data come from WRP, not Pew.',
            'Folds select models on historical test years; no independent final test set.',
            'Changes in source methodology between WRP and Pew are not learned.',
            'For recursive backtests only forecast-origin demographics are used and held fixed; this measures performance under a frozen-demography scenario.',
            'Modern land borders are a proxy in historical spatial features.',
            'WPP2024 historical values are retrospectively revised; these are NOT vintage-realistic forecasts.',
            'One-step and multihorizon overall accuracies include unchanged countries; check changed-case counts.',
            'Pew 2020 is not yet an input to the learned historical models. Its use is planned in Step 5.',
            'The best model is chosen on 5-year MAE; 10/20/30-year errors are descriptive historical backtests.',
        ],
    }
    (OUT / 'step4_report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    print('\n===== HISTORICAL MODEL COMPARISON (country-weighted) =====')
    print(summary[['horizon_years','model','n_predictions','share_mae',
                   'dominant_accuracy','n_changed_dominant','changed_dominant_accuracy',
                   'beats_persistence_mae']].to_string(index=False,
                        float_format=lambda x: f'{x:.4f}'))
    print(f'\nBEST MODEL FOR 5-YEAR MAE: {best}')
    print(f'Outputs written to {OUT}')
    print('DO NOT begin Step 5 until you inspect these validation results.')


if __name__ == '__main__':
    main()
