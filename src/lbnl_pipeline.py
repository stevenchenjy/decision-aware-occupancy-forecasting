"""Legacy cleaned-release replay for the LBNL occupancy forecasting study.

This module was extracted from ``LBNL_occupancy_forecasting_main.ipynb`` so the
notebook can remain a report while the executable research logic lives in
``src/``. The execution order and numerical operations intentionally mirror the
original notebook. It is not a provenance-qualified empirical rerun: source
observation-end timestamps, source-side imputation lineage, and corrected deep
seed initialization are outside this legacy path.
"""

from __future__ import annotations

import json
import math
import os
import random
import time
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
import torch.nn as nn
from pandas.tseries.holiday import USFederalHolidayCalendar
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset

try:
    from lightgbm import LGBMClassifier
except Exception:
    LGBMClassifier = None

try:  # Optional: only needed when showing report-style output interactively.
    from IPython.display import Image as _IPythonImage
    from IPython.display import Markdown as _IPythonMarkdown
    from IPython.display import display as _ipython_display
except Exception:  # pragma: no cover - script execution does not require IPython.
    _IPythonImage = None
    _IPythonMarkdown = None
    _ipython_display = None

_SHOW_NOTEBOOK_OUTPUT = False


def set_notebook_output(enabled: bool) -> None:
    global _SHOW_NOTEBOOK_OUTPUT
    _SHOW_NOTEBOOK_OUTPUT = bool(enabled)


def Markdown(text):
    return _IPythonMarkdown(text) if _IPythonMarkdown is not None else text


class Image:
    def __init__(self, filename=None, **kwargs):
        self.filename = filename
        self.kwargs = kwargs

    def __repr__(self):
        return f"Image(filename={self.filename!r})"


def display(*args, **kwargs):
    if _SHOW_NOTEBOOK_OUTPUT and _ipython_display is not None:
        return _ipython_display(*args, **kwargs)
    return None

@dataclass
class Config:
    data_dir: str = 'doi_10_7941_D1N33Q__v20220202/Building_59/Bldg59_clean data'
    figure_dir: str = 'runs/legacy_cleaned_replay/figures'
    result_dir: str = 'runs/legacy_cleaned_replay/results'
    prediction_dir: str = 'runs/legacy_cleaned_replay/predictions'
    raw_timestamp_timezone: str = 'UTC'
    local_timezone: str = 'America/Los_Angeles'
    freq: str = '15min'
    history_steps: int = 96
    horizon_steps: int = 96
    forecast_stride: int = 1
    train_fraction: float = 0.70
    val_fraction: float = 0.15
    split_gap_steps: int = 96
    occupied_count_threshold: float = 0.0
    default_empty_threshold: float = 0.65
    stable_empty_min_steps: int = 4
    threshold_min: float = 0.05
    threshold_max: float = 0.95
    threshold_step: float = 0.025
    risk_deltas: tuple = (0.05, 0.10, 0.20)
    main_models: tuple = ('Historical average', 'LightGBM', 'Random forest', 'DLinear', 'Transformer')
    random_seeds: tuple = (42, 43, 44)
    tabular_max_train_rows: int = 200_000
    rf_estimators: int = 70
    lgbm_estimators: int = 320
    permutation_sample_rows: int = 30_000
    bootstrap_reps: int = 200
    deep_epochs: int = 12
    early_stop_patience: int = 4
    batch_size: int = 256
    d_model: int = 32
    n_heads: int = 4
    n_layers: int = 1
    dropout: float = 0.10
    learning_rate: float = 1e-3

def read_timeseries(path, cfg):
    raw = pd.read_csv(path)
    if 'date' not in raw.columns:
        raw = raw.rename(columns={raw.columns[0]: 'date'})
    raw = raw.loc[:, [c for c in raw.columns if not str(c).startswith('Unnamed')]]
    dt = pd.to_datetime(raw['date'], errors='coerce')
    raw = raw.loc[dt.notna()].copy()
    dt = dt.loc[dt.notna()]
    # This is an unverified working assumption: solar radiation peaks look
    # plausible after UTC-to-Pacific conversion, but the source documentation
    # does not explicitly confirm the raw timestamp timezone.
    raw['date'] = dt.dt.tz_localize(cfg.raw_timestamp_timezone).dt.tz_convert(cfg.local_timezone)
    for col in raw.columns:
        if col != 'date':
            raw[col] = pd.to_numeric(raw[col], errors='coerce')
    return raw.sort_values('date')

def resample_mean(df, freq):
    # Make pandas' default bin convention explicit.  A row labelled ``t``
    # summarizes the left-closed interval [t, t + freq).  Forecast code that
    # consumes this row must therefore treat the effective issue boundary as
    # the *end* of the bin, not as the label t itself.
    return df.set_index('date').sort_index().resample(freq, closed='left', label='left').mean()

def make_timezone_audit(cfg):
    p = Path(cfg.data_dir) / 'site_weather.csv'
    weather = pd.read_csv(p, usecols=['date', 'solar_radiation_set_1'])
    raw_dt = pd.to_datetime(weather['date'], errors='coerce')
    weather = weather.loc[raw_dt.notna()].copy()
    raw_dt = raw_dt.loc[raw_dt.notna()]
    weather['raw_hour'] = raw_dt.dt.hour
    local_dt = raw_dt.dt.tz_localize(cfg.raw_timestamp_timezone).dt.tz_convert(cfg.local_timezone)
    weather['local_hour_if_raw_utc'] = local_dt.dt.hour
    sample = weather[(raw_dt >= pd.Timestamp('2018-05-22')) & (raw_dt < pd.Timestamp('2018-06-22'))]
    hour_rows = []
    for mode, col in [('raw_timestamp_hour', 'raw_hour'), ('utc_to_pacific_hour', 'local_hour_if_raw_utc')]:
        prof = sample.groupby(col)['solar_radiation_set_1'].mean()
        for hour, value in prof.items():
            hour_rows.append({'profile': mode, 'hour': int(hour), 'mean_solar_radiation': float(value)})
    hour_df = pd.DataFrame(hour_rows)
    raw_peak = hour_df[hour_df['profile'] == 'raw_timestamp_hour'].sort_values('mean_solar_radiation', ascending=False).iloc[0]
    local_peak = hour_df[hour_df['profile'] == 'utc_to_pacific_hour'].sort_values('mean_solar_radiation', ascending=False).iloc[0]
    audit = pd.DataFrame([
        {
            'check': 'source_documentation_timezone',
            'status': 'not_explicitly_stated',
            'evidence': 'README and metadata identify Berkeley, CA but do not explicitly state timestamp timezone.',
        },
        {
            'check': 'solar_radiation_peak_test',
            'status': 'inferred_not_documented',
            'evidence': f"Raw timestamp solar peak is around hour {int(raw_peak['hour'])}; after UTC->Pacific conversion it peaks around local hour {int(local_peak['hour'])}, consistent with daylight but not source-confirmed.",
        },
        {
            'check': 'time_feature_basis',
            'status': 'working_assumption_applied',
            'evidence': 'All hour/day/weekend/holiday features are generated after the assumed UTC->Pacific conversion; source timezone provenance remains unresolved.',
        },
        {
            'check': 'raw_hour_10_12_empty_anomaly',
            'status': 'explained',
            'evidence': 'Raw 10:00-12:00 UTC maps to early morning Pacific time for much of the data, so apparent late-morning emptiness was a timezone artifact before conversion.',
        },
    ])
    return audit, hour_df

def time_features(index, cfg):
    minutes = index.hour * 60 + index.minute
    hour_angle = 2 * np.pi * minutes / (24 * 60)
    dow_angle = 2 * np.pi * index.dayofweek / 7
    month_angle = 2 * np.pi * (index.month - 1) / 12
    naive_start = index.min().tz_localize(None)
    naive_end = index.max().tz_localize(None)
    holidays = USFederalHolidayCalendar().holidays(naive_start, naive_end)
    holiday_dates = set(pd.DatetimeIndex(holidays).date)
    out = pd.DataFrame(index=index)
    out['hour_sin'] = np.sin(hour_angle)
    out['hour_cos'] = np.cos(hour_angle)
    out['dow_sin'] = np.sin(dow_angle)
    out['dow_cos'] = np.cos(dow_angle)
    out['month_sin'] = np.sin(month_angle)
    out['month_cos'] = np.cos(month_angle)
    out['is_weekend'] = (index.dayofweek >= 5).astype(float)
    out['is_business_hour'] = ((index.dayofweek < 5) & (index.hour >= 7) & (index.hour < 19)).astype(float)
    out['is_holiday'] = pd.Series([d in holiday_dates for d in index.date], index=index, dtype=float)
    return out, list(out.columns)

def prepare_dataset(cfg):
    data_dir = Path(cfg.data_dir)
    timezone_audit, timezone_hour_audit = make_timezone_audit(cfg)

    occ_raw = read_timeseries(data_dir / 'occ.csv', cfg).set_index('date')
    occ_cols = [c for c in occ_raw.columns if c.startswith('occ_')]
    occ_raw['occ_count'] = occ_raw[occ_cols].sum(axis=1, min_count=1)
    occ = pd.DataFrame({
        'occ_count_mean': occ_raw['occ_count'].resample(cfg.freq, closed='left', label='left').mean(),
        'occ_count_max': occ_raw['occ_count'].resample(cfg.freq, closed='left', label='left').max(),
    })
    occ['occupied'] = (occ['occ_count_max'] > cfg.occupied_count_threshold).astype(float)
    occ['empty'] = 1.0 - occ['occupied']
    occ = occ.dropna(subset=['occ_count_mean', 'occupied']).sort_index()
    occ.index.name = 'date_local'
    idx = occ.index

    features = occ.copy()
    source_rows = []

    def add_source(name, filename, build_cols):
        raw = read_timeseries(data_dir / filename, cfg)
        res = resample_mean(raw, cfg.freq).reindex(idx)
        before_cols = set(features.columns)
        build_cols(res)
        new_cols = [c for c in features.columns if c not in before_cols]
        coverage = 1.0 - features[new_cols].isna().mean().mean() if new_cols else 0.0
        source_rows.append({
            'source': name,
            'file': filename,
            'raw_rows': len(raw),
            'local_start': raw['date'].min(),
            'local_end': raw['date'].max(),
            'used_columns': ', '.join(new_cols) if new_cols else '(excluded)',
            'mean_coverage_before_fill': coverage,
        })

    def add_wifi(res):
        cols = [c for c in ['wifi_third_south', 'wifi_fourth_south'] if c in res.columns]
        features['wifi_south_total'] = res[cols].sum(axis=1, min_count=1)
        features['wifi_south_mean'] = res[cols].mean(axis=1)

    def add_weather(res):
        for col in ['air_temp_set_1', 'air_temp_set_2', 'dew_point_temperature_set_1d', 'relative_humidity_set_1', 'solar_radiation_set_1']:
            if col in res.columns:
                features[col] = res[col]

    def add_temp(res):
        features['temp_interior_mean'] = res.mean(axis=1)

    def add_ele(res):
        for col in ['mels_S', 'lig_S', 'hvac_S']:
            if col in res.columns:
                features[col] = res[col]
        present = [c for c in ['mels_S', 'lig_S', 'hvac_S'] if c in features.columns]
        features['ele_south_total'] = features[present].sum(axis=1, min_count=1)

    def add_co2(res):
        overlap = res.notna().any(axis=1).mean()
        if overlap >= 0.25:
            features['co2_mean'] = res.mean(axis=1)

    add_source('WiFi association counts', 'wifi.csv', add_wifi)
    add_source('site weather', 'site_weather.csv', add_weather)
    add_source('interior zone temperature', 'zone_temp_interior.csv', add_temp)
    add_source('south electrical meters', 'ele.csv', add_ele)
    add_source('zone CO2', 'zone_co2.csv', add_co2)

    time_df, time_cols = time_features(idx, cfg)
    features = pd.concat([features, time_df], axis=1)

    protected = {'occupied', 'empty', 'occ_count_mean', 'occ_count_max'}
    feature_cols = [c for c in features.columns if c not in protected]
    missing_before_fill = features[feature_cols].isna().mean().rename('missing_before_fill')
    # Post-import row-order preprocessing: no new interpolation or backward fill.
    # Sensor/load values are carried forward from preceding rows only; leading
    # missing values use a fixed 0.0 constant.  This cannot establish causal
    # provenance for any imputation already present in the imported clean release.
    features[feature_cols] = features[feature_cols].ffill().fillna(0.0)

    predictor_sensor_cols = [c for c in [
        'wifi_south_total', 'wifi_south_mean', 'temp_interior_mean', 'air_temp_set_1',
        'air_temp_set_2', 'dew_point_temperature_set_1d', 'relative_humidity_set_1',
        'solar_radiation_set_1', 'co2_mean'
    ] if c in features.columns]
    controllable_load_cols = [c for c in ['hvac_S', 'lig_S'] if c in features.columns]
    excluded_predictor_cols = [c for c in ['mels_S', 'lig_S', 'hvac_S', 'ele_south_total'] if c in features.columns]

    data_summary = pd.DataFrame([{
        'resampled_rows': len(features),
        'start_local': features.index.min(),
        'end_local': features.index.max(),
        'frequency': cfg.freq,
        'resample_bin_convention': 'left-closed, left-labelled [t, t + 15 min); input-bin values are available only at bin close',
        'timezone': cfg.local_timezone,
        'target_occupied_definition': f'occupied=1 if max south-zone camera count > {cfg.occupied_count_threshold} in the 15-minute bin',
        'occupied_rate': features['occupied'].mean(),
        'empty_rate': features['empty'].mean(),
        'mean_occupant_count': features['occ_count_mean'].mean(),
        'max_occupant_count': features['occ_count_max'].max(),
    }])
    label_semantics = pd.DataFrame([
        {'item': 'binary_label', 'definition': 'occupied=1, empty=0 for occupancy prediction; evaluation flips the positive class so Empty=1 for recommendations.'},
        {'item': 'threshold_logic', 'definition': f'occupied is derived from occ_count_max > {cfg.occupied_count_threshold}; any detected occupant in either south-zone sensor marks the 15-minute interval occupied.'},
        {'item': 'count_columns', 'definition': ', '.join(occ_cols)},
        {'item': 'forecast_anchor_timing', 'definition': 'anchor_time records the start of a left-labelled 15-minute input bin. Models consume that completed bin; its effective issue boundary is anchor_time + 15 minutes and the first target interval starts at that boundary.'},
    ])
    feature_policy = pd.DataFrame([
        {'feature_group': 'known_future_inputs', 'columns': ', '.join(time_cols), 'used_for_prediction': True, 'reason': 'Calendar/time variables are known at the effective post-bin availability boundary.', 'scope': 'post-bin saved-row convention; not a real-time source-availability proof'},
        {'feature_group': 'completed_input_bin_sensors', 'columns': ', '.join(predictor_sensor_cols), 'used_for_prediction': True, 'reason': 'Only sensor values from the completed anchor bin or earlier are repeated across the horizon; no future sensor rows are used. A forward-filled value can be stale.', 'scope': 'upstream cleaned-release provenance remains unresolved'},
        {'feature_group': 'model_input_missing_value_preprocessing', 'columns': ', '.join(predictor_sensor_cols), 'used_for_prediction': True, 'reason': 'After importing the cleaned release, missing model-input sensors are forward-filled only in row order; leading values use fixed 0.0. This does not establish causal provenance for upstream dataset imputation.', 'scope': 'not a prospective imputation guarantee'},
        {'feature_group': 'load_proxy_missing_value_preprocessing', 'columns': ', '.join(excluded_predictor_cols), 'used_for_prediction': False, 'reason': 'Electrical streams are forward-filled only for the offline load-proxy calculation and are excluded from predictor features.', 'scope': 'offline accounting only'},
        {'feature_group': 'processed_load_proxy_streams_for_offline_accounting', 'columns': ', '.join(controllable_load_cols), 'used_for_prediction': False, 'reason': 'HVAC and lighting power are excluded from predictors and used only for offline processed-load-proxy accounting; no controllability is verified.', 'scope': 'not verified savings or an executed action'},
        {'feature_group': 'excluded_electrical_load_predictors', 'columns': ', '.join(excluded_predictor_cols), 'used_for_prediction': False, 'reason': 'Processed electrical-load streams are not used as occupancy predictors.', 'scope': 'prevents this model-input pathway; does not resolve upstream provenance'},
    ])
    feature_coverage = missing_before_fill.reset_index().rename(columns={'index': 'feature'}).sort_values('missing_before_fill', ascending=False)

    return features, data_summary, pd.DataFrame(source_rows), feature_coverage, label_semantics, feature_policy, timezone_audit, timezone_hour_audit, time_cols, predictor_sensor_cols, controllable_load_cols

def future_positions(anchors, horizon_steps):
    return anchors[:, None] + np.arange(1, horizon_steps + 1)[None, :]

def floor_to_week_start(ts):
    return (ts - pd.Timedelta(days=int(ts.dayofweek))).normalize()

def make_splits(df, cfg):
    n = len(df)
    anchors = np.arange(cfg.history_steps - 1, n - cfg.horizon_steps, cfg.forecast_stride)
    hist_starts = anchors - cfg.history_steps + 1
    target_ends = anchors + cfg.horizon_steps
    raw_train_boundary = df.index[int(n * cfg.train_fraction)]
    raw_val_boundary = df.index[int(n * (cfg.train_fraction + cfg.val_fraction))]
    train_boundary = floor_to_week_start(raw_train_boundary)
    val_boundary = floor_to_week_start(raw_val_boundary)
    gap = pd.Timedelta(minutes=15 * cfg.split_gap_steps)
    hist_start_times = df.index.take(hist_starts)
    target_end_times = df.index.take(target_ends)
    splits = {
        'train': anchors[target_end_times < train_boundary],
        'val': anchors[(hist_start_times >= train_boundary + gap) & (target_end_times < val_boundary)],
        'test': anchors[hist_start_times >= val_boundary + gap],
    }
    rows = []
    for name, a in splits.items():
        if len(a) == 0:
            rows.append({'split': name, 'anchor_count': 0})
            continue
        rows.append({
            'split': name,
            'anchor_count': len(a),
            'forecasted_intervals': len(a) * cfg.horizon_steps,
            'first_history': df.index[a[0] - cfg.history_steps + 1],
            'first_anchor': df.index[a[0]],
            'last_anchor': df.index[a[-1]],
            'first_target': df.index[a[0] + 1],
            'last_target': df.index[min(a[-1] + cfg.horizon_steps, len(df) - 1)],
        })
    split_summary = pd.DataFrame(rows)
    audit = []
    audit.append({'check': 'chronological_week_boundary_split', 'status': 'pass', 'detail': f'Train boundary={train_boundary}, validation boundary={val_boundary}; boundaries are Monday 00:00 local time.'})
    if len(splits['train']) and len(splits['val']):
        gap_hours = (df.index[splits['val'][0] - cfg.history_steps + 1] - df.index[splits['train'][-1] + cfg.horizon_steps]).total_seconds() / 3600
        audit.append({'check': 'train_to_validation_gap_hours', 'status': 'pass' if gap_hours >= 24 else 'fail', 'detail': gap_hours})
    if len(splits['val']) and len(splits['test']):
        gap_hours = (df.index[splits['test'][0] - cfg.history_steps + 1] - df.index[splits['val'][-1] + cfg.horizon_steps]).total_seconds() / 3600
        audit.append({'check': 'validation_to_test_gap_hours', 'status': 'pass' if gap_hours >= 24 else 'fail', 'detail': gap_hours})
    audit.extend([
        {'check': 'train_only_scaling', 'status': 'pass', 'detail': 'Deep-model normalization statistics are fit using rows before the train boundary only; tree models use no scaler.'},
        {'check': 'post_import_row_order_preprocessing', 'status': 'post_import_only', 'detail': 'After import, missing sensor/load values use forward-fill from preceding rows plus fixed 0.0 for leading gaps; no new interpolation, backfill, or test-set statistics. Source-side imputation provenance remains unverified.'},
        {'check': 'historical_average_train_only', 'status': 'pass', 'detail': 'Historical averages use occupied labels before train boundary only.'},
        {'check': 'rolling_features_shift', 'status': 'pass', 'detail': 'Rolling occupancy/count features are shifted and exclude the current/future labels: arr[anchor-window:anchor].'},
        {'check': 'future_sensor_rows', 'status': 'post_bin_saved_row_check_only', 'detail': 'Known future inputs are calendar/time only; sensor features come from the completed anchor bin or preceding rows and are repeated across the horizon. Their effective availability is post-bin, but source observation-end provenance is unverified.'},
        {'check': 'processed_load_proxy_predictor_exclusion', 'status': 'pass', 'detail': 'HVAC, lighting, MELS, and total south electricity are excluded from predictors and used only for offline load-proxy accounting.'},
    ])
    return splits, split_summary, pd.DataFrame(audit), train_boundary, val_boundary

def safe_auc(y_true, prob):
    return float('nan') if len(np.unique(y_true)) < 2 else float(roc_auc_score(y_true, prob))

def safe_log_loss(y_true, prob):
    prob = np.clip(prob, 1e-6, 1 - 1e-6)
    return float('nan') if len(np.unique(y_true)) < 2 else float(log_loss(y_true, prob))

def empty_model_metrics(name, y_occupied, occupied_prob):
    y_empty = 1 - y_occupied.ravel().astype(int)
    p_empty = np.clip(1.0 - occupied_prob.ravel(), 1e-6, 1 - 1e-6)
    pred_empty = (p_empty >= 0.5).astype(int)
    return {
        'model': name,
        'positive_class': 'empty',
        'recall_empty': recall_score(y_empty, pred_empty, zero_division=0),
        'precision_empty': precision_score(y_empty, pred_empty, zero_division=0),
        'f1_empty': f1_score(y_empty, pred_empty, zero_division=0),
        'auroc_empty': safe_auc(y_empty, p_empty),
        'auprc_empty': average_precision_score(y_empty, p_empty),
        'brier_empty': brier_score_loss(y_empty, p_empty),
        'log_loss_empty': safe_log_loss(y_empty, p_empty),
    }

def stable_empty_mask_from_prob(empty_prob, threshold, min_steps):
    high = np.asarray(empty_prob) >= threshold
    stable = np.zeros_like(high, dtype=bool)
    for i, row in enumerate(high):
        padded = np.concatenate([[False], row.astype(bool), [False]])
        changes = np.diff(padded.astype(int))
        starts = np.flatnonzero(changes == 1)
        ends = np.flatnonzero(changes == -1)
        for start, end in zip(starts, ends):
            if end - start >= min_steps:
                stable[i, start:end] = True
    return stable

def recommendation_metrics_from_mask(name, y_occupied, recommend_empty, threshold, policy):
    y_occ = y_occupied.ravel().astype(int)
    rec = recommend_empty.ravel().astype(bool)
    actual_empty = y_occ == 0
    actual_occupied = y_occ == 1
    fp = rec & actual_occupied
    tp = rec & actual_empty
    n_rec = int(rec.sum())
    n_occ = int(actual_occupied.sum())
    n_empty = int(actual_empty.sum())
    return {
        'model': name,
        'policy': policy,
        'empty_probability_threshold': threshold,
        'stable_empty_min_steps': cfg.stable_empty_min_steps,
        'recommendation_rate': float(rec.mean()) if len(rec) else 0.0,
        'occupancy_conflict_rate': int(fp.sum()) / n_rec if n_rec else 0.0,
        'standard_fpr_occupied_denominator': int(fp.sum()) / n_occ if n_occ else 0.0,
        'missed_opportunity_rate': int(((~rec) & actual_empty).sum()) / n_empty if n_empty else 0.0,
        'empty_window_precision': int(tp.sum()) / n_rec if n_rec else 0.0,
        'empty_window_recall': int(tp.sum()) / n_empty if n_empty else 0.0,
        'recommendation_count': n_rec,
        'occupancy_conflict_count': int(fp.sum()),
    }

def controllable_energy_matrix(df, anchors, cfg, controllable_load_cols):
    """Map recorded meter values for offline load-proxy accounting only."""
    positions = future_positions(anchors, cfg.horizon_steps)
    if not controllable_load_cols:
        return np.zeros_like(positions, dtype=np.float32)
    load = df[controllable_load_cols].sum(axis=1).to_numpy(np.float32)
    return np.clip(load[positions], 0, None) * 0.25

def energy_metrics_from_mask(name, y_occupied, recommend_empty, controllable_kwh, cfg, threshold, policy):
    """Return legacy-named fields for offline camera-label-empty proxy overlap.

    The established CSV column names are retained for artifact compatibility;
    they do not establish controllability, a counterfactual action, or savings.
    """
    actual_empty = y_occupied == 0
    safe = recommend_empty & actual_empty
    conflict = recommend_empty & (~actual_empty)
    total_empty_kwh = float((controllable_kwh * actual_empty).sum())
    safe_kwh = float((controllable_kwh * safe).sum())
    return {
        'model': name,
        'policy': policy,
        'empty_probability_threshold': threshold,
        'safe_shiftable_load_opportunity_kwh': safe_kwh,
        'gross_shiftable_load_opportunity_kwh': float((controllable_kwh * recommend_empty).sum()),
        'raw_recommended_controllable_kwh': float((controllable_kwh * recommend_empty).sum()),
        'conflict_controllable_kwh': float((controllable_kwh * conflict).sum()),
        'available_empty_controllable_kwh': total_empty_kwh,
        'safe_energy_capture_rate': safe_kwh / total_empty_kwh if total_empty_kwh else 0.0,
        'safe_recommended_intervals': int(safe.sum()),
    }

def threshold_grid_values(cfg):
    return np.round(np.arange(cfg.threshold_min, cfg.threshold_max + cfg.threshold_step / 2, cfg.threshold_step), 3)

def slot_index(index):
    return index.dayofweek * 96 + index.hour * 4 + (index.minute // 15)

def historical_average_prob(df, train_boundary, positions):
    slots = slot_index(df.index)
    train_mask = df.index < train_boundary
    train_table = pd.Series(df.loc[train_mask, 'occupied'].to_numpy(), index=slots[train_mask]).groupby(level=0).mean()
    global_mean = df.loc[train_mask, 'occupied'].mean()
    future_slots = slots[positions.ravel()]
    probs = np.array([train_table.get(s, global_mean) for s in future_slots], dtype=np.float32)
    return probs.reshape(positions.shape)

def rolling_mean_at_anchors(arr, anchors, window):
    # Explicit shift-before-rolling: use the window ending immediately before the
    # effective post-bin availability boundary, so hist_occ_mean_* never contains
    # current/future labels.
    arr = np.asarray(arr, dtype=np.float64)
    csum = np.concatenate([[0.0], np.cumsum(arr, dtype=np.float64)])
    out = np.full(len(anchors), np.nan, dtype=np.float32)
    valid = anchors - window >= 0
    if valid.any():
        a = anchors[valid]
        out[valid] = ((csum[a] - csum[a - window]) / window).astype(np.float32)
    fill = np.nanmean(out)
    if not np.isfinite(fill):
        fill = 0.0
    return np.nan_to_num(out, nan=fill).astype(np.float32)

def lag_at_anchors(arr, anchors, lag):
    out = np.full(len(anchors), np.nan, dtype=np.float32)
    valid = anchors - lag >= 0
    if valid.any():
        out[valid] = arr[anchors[valid] - lag]
    fill = np.nanmean(out)
    if not np.isfinite(fill):
        fill = 0.0
    return np.nan_to_num(out, nan=fill).astype(np.float32)

def make_tabular_arrays(df, anchors, cfg, future_time_cols, anchor_sensor_cols):
    target = df['occupied'].to_numpy(np.float32)
    count = df['occ_count_mean'].to_numpy(np.float32)
    pos = future_positions(anchors, cfg.horizon_steps)
    n = len(anchors)
    h = cfg.horizon_steps
    future_time = df[future_time_cols].to_numpy(np.float32)[pos.ravel()]
    future_steps = np.tile(np.arange(1, h + 1, dtype=np.float32), n).reshape(-1, 1) / h
    same_time_yesterday = target[(pos - cfg.horizon_steps).ravel()].reshape(-1, 1)
    # ``anchors`` identify the last completed, left-labelled input bin.  Its
    # values are available at the bin-close issue boundary; target positions
    # begin in the following bin.  This is a timing convention, not a claim
    # that a row is available at its left-hand timestamp label.
    anchor_blocks = [
        target[anchors], count[anchors], lag_at_anchors(target, anchors, 1), lag_at_anchors(target, anchors, 2),
        lag_at_anchors(target, anchors, 4), lag_at_anchors(target, anchors, 96), lag_at_anchors(target, anchors, 672),
        rolling_mean_at_anchors(target, anchors, 4), rolling_mean_at_anchors(target, anchors, 24),
        rolling_mean_at_anchors(target, anchors, 96), rolling_mean_at_anchors(count, anchors, 96),
    ]
    names = ['anchor_last_occupied', 'anchor_last_count', 'lag_occ_15min', 'lag_occ_30min', 'lag_occ_1h', 'lag_occ_24h', 'same_time_last_week_occ', 'hist_occ_mean_1h', 'hist_occ_mean_6h', 'hist_occ_mean_24h', 'hist_count_mean_24h']
    blocks = [np.repeat(np.asarray(v, dtype=np.float32).reshape(-1, 1), h, axis=0) for v in anchor_blocks]
    if anchor_sensor_cols:
        anchor_sensor = df[anchor_sensor_cols].to_numpy(np.float32)[anchors]
        blocks.append(np.repeat(anchor_sensor, h, axis=0))
        names.extend([f'anchor_{c}' for c in anchor_sensor_cols])
    x = np.concatenate(blocks + [same_time_yesterday, future_steps, future_time], axis=1)
    names += ['same_time_yesterday', 'horizon_fraction'] + future_time_cols
    y = target[pos.ravel()].astype(int)
    return x.astype(np.float32), y, names

def stratified_sample_indices(y, max_rows, seed):
    if len(y) <= max_rows:
        return np.arange(len(y))
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y == 1)
    neg = np.flatnonzero(y == 0)
    if len(pos) == 0 or len(neg) == 0:
        return rng.choice(np.arange(len(y)), size=max_rows, replace=False)
    pos_n = min(len(pos), max_rows // 2)
    neg_n = min(len(neg), max_rows - pos_n)
    idx = np.concatenate([rng.choice(pos, size=pos_n, replace=False), rng.choice(neg, size=neg_n, replace=False)])
    if len(idx) < max_rows:
        pool = np.setdiff1d(np.arange(len(y)), idx)
        idx = np.concatenate([idx, rng.choice(pool, size=max_rows - len(idx), replace=False)])
    rng.shuffle(idx)
    return idx

class ForecastWindowDataset(Dataset):
    def __init__(self, hist_values, future_values, target, anchors, cfg):
        self.hist_values = hist_values
        self.future_values = future_values
        self.target = target
        self.anchors = anchors
        self.cfg = cfg

    def __len__(self):
        return len(self.anchors)

    def __getitem__(self, idx):
        anchor = self.anchors[idx]
        # Include the final completed input bin.  With left-labelled bins, the
        # effective forecast issue is the right edge of this anchor bin.
        hist_start = anchor - self.cfg.history_steps + 1
        hist_end = anchor + 1
        future_start = anchor + 1
        future_end = anchor + self.cfg.horizon_steps + 1
        return (
            torch.from_numpy(self.hist_values[hist_start:hist_end]),
            torch.from_numpy(self.future_values[future_start:future_end]),
            torch.from_numpy(self.target[future_start:future_end].astype(np.float32)),
        )

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=512):
        super().__init__()
        position = torch.arange(max_len).float().unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x):
        return x + self.pe[:, :x.size(1)]

class SequenceTransformer(nn.Module):
    def __init__(self, n_hist, n_future, cfg):
        super().__init__()
        self.hist_proj = nn.Linear(n_hist, cfg.d_model)
        self.future_proj = nn.Linear(n_future, cfg.d_model)
        self.pos = PositionalEncoding(cfg.d_model, max_len=max(cfg.history_steps, cfg.horizon_steps) + 8)
        layer = nn.TransformerEncoderLayer(
            d_model=cfg.d_model, nhead=cfg.n_heads, dim_feedforward=cfg.d_model * 4,
            dropout=cfg.dropout, batch_first=True, activation='gelu',
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=cfg.n_layers)
        self.head = nn.Sequential(
            nn.LayerNorm(cfg.d_model * 2), nn.Linear(cfg.d_model * 2, cfg.d_model),
            nn.GELU(), nn.Dropout(cfg.dropout), nn.Linear(cfg.d_model, 1),
        )

    def forward(self, x_hist, x_future):
        enc = self.encoder(self.pos(self.hist_proj(x_hist)))
        context = enc[:, -1, :]
        future = self.future_proj(x_future)
        context = context.unsqueeze(1).expand(-1, x_future.size(1), -1)
        return self.head(torch.cat([context, future], dim=-1)).squeeze(-1)

class DLinear(nn.Module):
    def __init__(self, history_steps, horizon_steps, occupied_feature_index):
        super().__init__()
        self.occupied_feature_index = occupied_feature_index
        self.linear = nn.Linear(history_steps, horizon_steps)

    def forward(self, x_hist, x_future):
        occ_hist = x_hist[:, :, self.occupied_feature_index]
        return self.linear(occ_hist)

def set_all_seeds(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

def loader_loss(model, loader, criterion, device):
    model.eval()
    total = 0.0
    n = 0
    with torch.no_grad():
        for x_hist, x_future, y in loader:
            x_hist = x_hist.to(device)
            x_future = x_future.to(device)
            y = y.to(device)
            loss = criterion(model(x_hist, x_future), y)
            total += float(loss.item()) * len(y)
            n += len(y)
    return total / max(n, 1)

def train_deep_model(name, model, train_ds, val_ds, pos_weight, cfg, device, seed):
    set_all_seeds(seed)
    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=cfg.batch_size, shuffle=False, num_workers=0)
    model = model.to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight, dtype=torch.float32, device=device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=1e-4)
    best_state = None
    best_val = float('inf')
    best_epoch = 0
    stale = 0
    rows = []
    for epoch in range(1, cfg.deep_epochs + 1):
        model.train()
        running = 0.0
        count = 0
        for x_hist, x_future, y in train_loader:
            x_hist = x_hist.to(device)
            x_future = x_future.to(device)
            y = y.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x_hist, x_future)
            bce_loss = criterion(logits, y)
            # Decision-focused loss hook. Kept at zero weight for the main experiment;
            # future work can add false-empty and missed-opportunity penalties here.
            loss = bce_loss
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            running += float(loss.item()) * len(y)
            count += len(y)
        train_loss = running / max(count, 1)
        val_loss = loader_loss(model, val_loader, criterion, device)
        rows.append({'model': name, 'seed': seed, 'epoch': epoch, 'train_loss': train_loss, 'val_loss': val_loss})
        print(f'{name} seed {seed} epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}')
        if val_loss < best_val - 1e-4:
            best_val = val_loss
            best_epoch = epoch
            stale = 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= cfg.early_stop_patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    hist = pd.DataFrame(rows)
    hist['best_epoch'] = best_epoch
    return model, hist

def predict_deep(model, dataset, cfg, device):
    loader = DataLoader(dataset, batch_size=cfg.batch_size, shuffle=False, num_workers=0)
    model.eval()
    parts = []
    with torch.no_grad():
        for x_hist, x_future, _ in loader:
            logits = model(x_hist.to(device), x_future.to(device))
            parts.append(torch.sigmoid(logits).cpu().numpy())
    return np.concatenate(parts, axis=0)

def daily_anchor_indices(df, anchors, cfg):
    times = df.index.take(anchors)
    mask = (times.hour == 0) & (times.minute == 0)
    if mask.sum() == 0:
        mask = np.zeros(len(anchors), dtype=bool)
        mask[::cfg.horizon_steps] = True
    return np.flatnonzero(mask)

def sweep_one_split(pred_dict, anchors, y_occ, cfg, split_name, subset_indices=None):
    if subset_indices is None:
        use_anchors = anchors
        use_y = y_occ
        use_pred = pred_dict
    else:
        use_anchors = anchors[subset_indices]
        use_y = y_occ[subset_indices]
        use_pred = {m: p[subset_indices] for m, p in pred_dict.items()}
    controllable_kwh = controllable_energy_matrix(df, use_anchors, cfg, controllable_load_cols)
    rows = []
    for name, occ_prob in use_pred.items():
        empty_prob = 1.0 - occ_prob
        for threshold in threshold_grid_values(cfg):
            rec = stable_empty_mask_from_prob(empty_prob, threshold, cfg.stable_empty_min_steps)
            rec_row = recommendation_metrics_from_mask(name, use_y, rec, threshold, policy=f'{split_name}_threshold_sweep')
            en_row = energy_metrics_from_mask(name, use_y, rec, controllable_kwh, cfg, threshold, policy=f'{split_name}_threshold_sweep')
            rows.append({**rec_row, **{k: v for k, v in en_row.items() if k not in rec_row}, 'split': split_name, 'daily_anchor_count': len(use_anchors)})
    return pd.DataFrame(rows)

def select_constrained_policies(validation_sweep_df, cfg):
    selected = []
    for model in validation_sweep_df['model'].unique():
        part = validation_sweep_df[validation_sweep_df['model'] == model]
        for delta in cfg.risk_deltas:
            eligible = part[part['occupancy_conflict_rate'] <= delta]
            met = not eligible.empty
            if met:
                chosen = eligible.sort_values(['safe_shiftable_load_opportunity_kwh', 'empty_window_recall'], ascending=False).iloc[0]
                note = f'max validation offline camera-label-empty load-proxy overlap subject to empirical interval conflict <= {delta:.0%}'
            else:
                chosen = part.sort_values(['occupancy_conflict_rate', 'missed_opportunity_rate']).iloc[0]
                note = f'no validation threshold met empirical interval conflict <= {delta:.0%}; lowest-conflict fallback'
            selected.append({
                'model': model,
                'risk_delta': delta,
                'selected_empty_probability_threshold': float(chosen['empty_probability_threshold']),
                'validation_occupancy_conflict_rate': float(chosen['occupancy_conflict_rate']),
                'validation_standard_fpr': float(chosen['standard_fpr_occupied_denominator']),
                'validation_safe_shiftable_load_opportunity_kwh': float(chosen['safe_shiftable_load_opportunity_kwh']),
                'selection_met_constraint': bool(met),
                'selection_note': note,
            })
    return pd.DataFrame(selected)

def evaluate_selected_policies(selected_df, pred_dict, anchors, y_occ, cfg, split_name, subset_indices=None):
    if subset_indices is None:
        use_anchors = anchors
        use_y = y_occ
        use_pred = pred_dict
    else:
        use_anchors = anchors[subset_indices]
        use_y = y_occ[subset_indices]
        use_pred = {m: p[subset_indices] for m, p in pred_dict.items()}
    controllable_kwh = controllable_energy_matrix(df, use_anchors, cfg, controllable_load_cols)
    rows = []
    for _, sel in selected_df.iterrows():
        name = sel['model']
        threshold = float(sel['selected_empty_probability_threshold'])
        rec = stable_empty_mask_from_prob(1.0 - use_pred[name], threshold, cfg.stable_empty_min_steps)
        rec_row = recommendation_metrics_from_mask(name, use_y, rec, threshold, policy=f"risk_delta_{sel['risk_delta']:.0%}")
        en_row = energy_metrics_from_mask(name, use_y, rec, controllable_kwh, cfg, threshold, policy=f"risk_delta_{sel['risk_delta']:.0%}")
        rows.append({**rec_row, **{k: v for k, v in en_row.items() if k not in rec_row}, 'split': split_name, 'risk_delta': sel['risk_delta'], 'selection_met_constraint': sel['selection_met_constraint']})
    return pd.DataFrame(rows)

def slugify_model_name(name):
    return ''.join(ch.lower() if ch.isalnum() else '_' for ch in str(name)).strip('_')

def pareto_efficient_frontier(part):
    x_col = 'occupancy_conflict_rate'
    y_col = 'safe_shiftable_load_opportunity_kwh'
    ordered = part.sort_values([x_col, y_col], ascending=[True, False]).copy()
    ordered = ordered.drop_duplicates(subset=[x_col], keep='first')
    previous_best = ordered[y_col].cummax().shift(fill_value=-np.inf)
    frontier = ordered[ordered[y_col] > previous_best].copy()
    frontier['pareto_frontier'] = True
    return frontier

def save_all_model_predictions(split_name, anchors, y_occ, pred_dict):
    pos = future_positions(anchors, cfg.horizon_steps)
    bin_width = pd.Timedelta(cfg.freq)
    anchor_labels = pd.DatetimeIndex(df.index.take(anchors))
    target_labels = pd.DatetimeIndex(df.index.take(pos.ravel()))
    out = pd.DataFrame({
        'split': split_name,
        'anchor_time': np.repeat(anchor_labels.astype(str).to_numpy(), cfg.horizon_steps),
        'input_bin_start': np.repeat(anchor_labels.astype(str).to_numpy(), cfg.horizon_steps),
        'input_bin_end': np.repeat((anchor_labels + bin_width).astype(str).to_numpy(), cfg.horizon_steps),
        'effective_issue_time': np.repeat((anchor_labels + bin_width).astype(str).to_numpy(), cfg.horizon_steps),
        'target_time': target_labels.astype(str).to_numpy(),
        'target_bin_start': target_labels.astype(str).to_numpy(),
        'target_bin_end': (target_labels + bin_width).astype(str).to_numpy(),
        'horizon_step': np.tile(np.arange(1, cfg.horizon_steps + 1), len(anchors)),
        'actual_occupied': y_occ.ravel().astype(int),
        'actual_empty_positive': 1 - y_occ.ravel().astype(int),
        'positive_class': 'empty',
        'anchor_label_semantics': 'left label of completed [t, t+15 min) input bin',
        'availability_status': 'post-bin saved-row convention only; source provenance unverified',
    })
    for model, occ_prob in pred_dict.items():
        slug = slugify_model_name(model)
        out[f'{slug}_occupied_probability'] = occ_prob.ravel()
        out[f'{slug}_empty_probability'] = 1.0 - occ_prob.ravel()
    path = Path(cfg.result_dir) / f'forecast_predictions_{split_name}_all_models.csv'
    out.to_csv(path, index=False, encoding='utf-8-sig')
    return path

def extract_runs(mask, min_steps):
    mask = np.asarray(mask, dtype=bool)
    padded = np.concatenate([[False], mask, [False]])
    changes = np.diff(padded.astype(int))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return [(int(s), int(e)) for s, e in zip(starts, ends) if int(e - s) >= int(min_steps)]

def continuous_window_metrics_for_arrays(model, y_occ, empty_prob, threshold, min_steps, split_name, policy):
    pred_mask = np.asarray(empty_prob) >= threshold
    actual_empty = np.asarray(y_occ) == 0
    pred_count = safe_count = conflict_count = 0
    true_count = detected_true_count = 0
    duration_hours = []
    for i in range(pred_mask.shape[0]):
        pred_windows = extract_runs(pred_mask[i], min_steps)
        true_windows = extract_runs(actual_empty[i], min_steps)
        pred_count += len(pred_windows)
        true_count += len(true_windows)
        duration_hours.extend([(e - s) * 0.25 for s, e in pred_windows])
        for s, e in pred_windows:
            if actual_empty[i, s:e].all():
                safe_count += 1
            else:
                conflict_count += 1
        detected = set()
        for tw, (ts, te) in enumerate(true_windows):
            for ps, pe in pred_windows:
                if max(ts, ps) < min(te, pe):
                    detected.add(tw)
                    break
        detected_true_count += len(detected)
    return {
        'split': split_name,
        'model': model,
        'policy': policy,
        'positive_class': 'empty',
        'empty_probability_threshold': threshold,
        'minimum_empty_window_hours': min_steps * 0.25,
        'predicted_empty_window_count': pred_count,
        'true_empty_window_count': true_count,
        'safe_predicted_window_count': safe_count,
        'conflict_predicted_window_count': conflict_count,
        'window_level_precision': safe_count / pred_count if pred_count else 0.0,
        'window_level_recall': detected_true_count / true_count if true_count else 0.0,
        'window_level_occupancy_conflict_rate': conflict_count / pred_count if pred_count else 0.0,
        'average_detected_window_duration_hours': float(np.mean(duration_hours)) if duration_hours else 0.0,
        'double_counting_policy': 'non-overlapping daily forecast anchors and disjoint run extraction',
    }

def controllable_load_assumptions(df):
    specs = [
        {'assumption': 'hvac_lighting_full_metered', 'description': 'HVAC south + lighting south at 100% of recorded meter values', 'hvac_S': 1.0, 'lig_S': 1.0, 'mels_S': 0.0, 'ele_south_total': 0.0},
        {'assumption': 'hvac_lighting_conservative', 'description': '30% HVAC south + 80% lighting south accounting coefficients', 'hvac_S': 0.30, 'lig_S': 0.80, 'mels_S': 0.0, 'ele_south_total': 0.0},
        {'assumption': 'lighting_only_full', 'description': 'Lighting south at 100% of recorded meter values', 'hvac_S': 0.0, 'lig_S': 1.0, 'mels_S': 0.0, 'ele_south_total': 0.0},
        {'assumption': 'hvac_only_conservative', 'description': '30% HVAC south accounting coefficient', 'hvac_S': 0.30, 'lig_S': 0.0, 'mels_S': 0.0, 'ele_south_total': 0.0},
        {'assumption': 'hvac_lighting_plug_conservative', 'description': '30% HVAC + 80% lighting + 10% plug/MELs south accounting coefficients', 'hvac_S': 0.30, 'lig_S': 0.80, 'mels_S': 0.10, 'ele_south_total': 0.0},
        {'assumption': 'total_south_30pct', 'description': '30% of total south electricity; component meters not added to avoid double counting', 'hvac_S': 0.0, 'lig_S': 0.0, 'mels_S': 0.0, 'ele_south_total': 0.30},
    ]
    cols = ['hvac_S', 'lig_S', 'mels_S', 'ele_south_total']
    return pd.DataFrame([
        {
            **s,
            'interpretation': 'hypothetical processed-load accounting coefficient; not verified controllability or savings',
            **{c: s.get(c, 0.0) if c in df.columns else 0.0 for c in cols},
        }
        for s in specs
    ])

def assumption_energy_matrix(df, anchors, cfg, assumption_row):
    positions = future_positions(anchors, cfg.horizon_steps)
    load = np.zeros(len(df), dtype=np.float32)
    for col in ['hvac_S', 'lig_S', 'mels_S', 'ele_south_total']:
        coef = float(assumption_row.get(col, 0.0))
        if coef and col in df.columns:
            load += coef * df[col].to_numpy(np.float32)
    return np.clip(load[positions], 0, None) * 0.25


def configure_runtime(config: Config, show: bool = False) -> Config:
    """Configure isolated legacy-replay outputs; this is not an empirical rerun."""
    global cfg
    cfg = config
    set_notebook_output(show)
    warnings.filterwarnings('ignore')
    sns.set_theme(style='whitegrid')
    Path(cfg.figure_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.result_dir).mkdir(parents=True, exist_ok=True)
    Path(cfg.prediction_dir).mkdir(parents=True, exist_ok=True)
    random.seed(cfg.random_seeds[0])
    np.random.seed(cfg.random_seeds[0])
    torch.manual_seed(cfg.random_seeds[0])
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    with open(Path(cfg.result_dir) / 'config.json', 'w', encoding='utf-8') as f:
        json.dump(asdict(cfg), f, indent=2)
    print('Torch:', torch.__version__, 'device:', 'cuda' if torch.cuda.is_available() else 'cpu')
    print('Timestamp working assumption (not source-confirmed):', cfg.raw_timestamp_timezone, '->', cfg.local_timezone)
    print('Replay status: legacy cleaned-release reproduction; not an empirical/prospective validation.')
    print('Main models:', ', '.join(cfg.main_models))
    print('LightGBM available:', LGBMClassifier is not None)
    return cfg


def write_individual_prediction_exports(split_name, anchors, y_occ, pred_dict, cfg, prediction_dir=None):
    """Write explicit post-bin long-form prediction exports for a legacy replay."""
    prediction_dir = Path(prediction_dir or cfg.prediction_dir)
    prediction_dir.mkdir(parents=True, exist_ok=True)
    pos = future_positions(anchors, cfg.horizon_steps)
    bin_width = pd.Timedelta(cfg.freq)
    anchor_labels = pd.DatetimeIndex(df.index.take(anchors))
    target_labels = pd.DatetimeIndex(df.index.take(pos.ravel()))
    base = pd.DataFrame({
        'timestamp': target_labels.astype(str).to_numpy(),
        'forecast_anchor_time': np.repeat(anchor_labels.astype(str).to_numpy(), cfg.horizon_steps),
        'input_bin_start': np.repeat(anchor_labels.astype(str).to_numpy(), cfg.horizon_steps),
        'input_bin_end': np.repeat((anchor_labels + bin_width).astype(str).to_numpy(), cfg.horizon_steps),
        'effective_issue_time': np.repeat((anchor_labels + bin_width).astype(str).to_numpy(), cfg.horizon_steps),
        'target_bin_start': target_labels.astype(str).to_numpy(),
        'target_bin_end': (target_labels + bin_width).astype(str).to_numpy(),
        'horizon_step': np.tile(np.arange(1, cfg.horizon_steps + 1), len(anchors)),
        'horizon_minutes': np.tile(np.arange(1, cfg.horizon_steps + 1) * 15, len(anchors)),
        'y_true_occupied': y_occ.ravel().astype(int),
        'y_true_empty': 1 - y_occ.ravel().astype(int),
        'anchor_label_semantics': 'left label of completed [t, t+15 min) input bin',
        'availability_status': 'post-bin saved-row convention only; source provenance unverified',
    })
    paths = []
    for model, occ_prob in pred_dict.items():
        out = base.copy()
        out['p_occupied'] = occ_prob.ravel()
        out['p_empty'] = 1.0 - occ_prob.ravel()
        out['model'] = model
        out['split'] = split_name
        path = prediction_dir / f"{slugify_model_name(model)}_{split_name}_predictions.csv"
        out.to_csv(path, index=False, encoding='utf-8-sig')
        paths.append(path)
    return paths


def save_fig(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def generate_figures_from_pipeline_state(show: bool = False):
    """Regenerate figures using the in-memory state produced by ``run_pipeline``."""
    global _, actual, actual_empty, actual_occ, anchors, ap, assumption, auc, ax, base_empty_prob, base_score, best_daily_empty_prob, best_daily_pred, best_daily_rec, best_daily_y, best_empty_prob, best_long, best_model, best_policy, best_prob, best_rec, best_threshold, bin_id, boot, bootstrap_ci_df, bootstrap_rows, bucket_defs, bucket_rows, case_choice_df, case_choices, case_df, case_rows, cfg, chosen, chosen_rows, col, conflict, conflict_count, continuous_window_policy_df, continuous_window_sweep_df, controllable_load_cols, controllable_load_inventory_df, current_run_manifest_df, daily_idx, data_summary, dates, day_order, default_rec_metrics_df, default_rec_rows, delta, device, df, dlinear, eb, empty_prob, empty_reliability_df, en_metric, end, energy_sensitivity_df, energy_sensitivity_rows, example, f, feature, feature_coverage, feature_policy, fig, figure_files, fold, fold_train_boundary, fold_val_end, fold_y, folder, fp, fpr, frac, frac_pos, fractions, frontier, future_values, global_i, global_mean, heldout, hist, hist_feature_cols, hist_mean, hist_prob, hist_scaled, hist_starts, hist_std, hist_values, horizon_bucket_metrics_df, i, idx, inventory_rows, is_rec, j, kwh, label, label_semantics, leakage_audit, lgbm, lgbm_models, load_assumptions_df, local_i, m, manifest_rows, mean_pred, metric, metric_definitions, metric_long, min_steps, missed_count, model, model_metrics_by_split_df, model_metrics_by_split_rows, model_metrics_df, model_name, mp, n_blocks, name, neg, numeric_seed_cols, occ_prob, occ_zone_raw, occupied_feature_index, outputs, p, p_empty, pareto_frontier_df, pareto_rows, part, pb, perm_rows, permutation_importance_df, ph, policy, policy_plot, policy_results_df, pos, pos_weight, precision, predictions, predictor_sensor_cols, prob, profile, rec, rec_metric, rec_row, recall, recommendation_metrics_by_split_df, recommendation_metrics_by_split_rows, record, records, reliability_rows, rf, rf_cv, rf_models, rng, rolling_origin_cv_df, rolling_rows, row, run_summary, safe, safe_count, sample, sample_idx, score, seed, seed_metrics_df, seed_metrics_rows, seed_prediction_records, seed_summary_df, sel, selected_policies_df, sens_plot, source_cols, source_coverage, source_series, source_slots, spatial_rows, spatial_validation_df, split_name, split_pred, split_summary, split_y, splits, start, start_train, table, tabular_feature_names, target, target_ends, test_daily_anchors, test_daily_energy, test_daily_idx, test_daily_predictions, test_daily_y, test_daily_y_for_windows, test_ds, test_positions, test_pred, test_rows, test_slots, test_sweep_df, threshold, time_cols, timezone_audit, timezone_hour_audit, top_perm, tpr, train_a, train_boundary, train_ds, train_future_y, train_row_mask, train_rows, training_control_rows, training_histories, training_history, transformer, transitions, val_a, val_boundary, val_daily_idx, val_ds, val_pos, val_positions, val_pred, val_predictions, valid_success, validation_sweep_df, values, window_duration_steps, window_plot, window_policy_rows, window_sweep_rows, x_holdout, x_perm, x_perm_base, x_source, x_test, x_train, x_val, xt, xv, y_empty_flat, y_empty_sample, y_holdout, y_source, y_test, y_train, y_val, yb, yd, yh, yt, yy, z, zone_cols, zone_feature_matrix, zone_labels
    set_notebook_output(show)
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    profile = df.assign(day=df.index.day_name(), hour=df.index.hour).groupby(['day', 'hour'])['occupied'].mean().unstack('hour').reindex(day_order)
    plt.figure(figsize=(12, 4.8))
    sns.heatmap(profile, cmap='YlGnBu', vmin=0, vmax=1)
    plt.title('Observed occupancy probability by local Pacific day and hour')
    plt.xlabel('Local hour of day')
    plt.ylabel('')
    save_fig(Path(cfg.figure_dir) / 'occupancy_profile_heatmap_pacific.png')
    plt.figure(figsize=(12, 5))
    metric_long = model_metrics_df.melt(id_vars='model', value_vars=['recall_empty', 'precision_empty', 'f1_empty', 'auroc_empty', 'auprc_empty'], var_name='metric', value_name='value')
    sns.barplot(data=metric_long, x='metric', y='value', hue='model')
    plt.ylim(0, 1)
    plt.xticks(rotation=20)
    plt.title('Model metrics with Empty=1 as positive class')
    plt.legend(loc='lower right', fontsize=8)
    save_fig(Path(cfg.figure_dir) / 'model_metrics_empty_positive.png')
    bucket_defs = [(1, 24, '0-6h'), (25, 48, '6-12h'), (49, 72, '12-18h'), (73, 96, '18-24h')]
    bucket_rows = []
    for name, prob in predictions.items():
        for start, end, label in bucket_defs:
            idx = np.arange(start - 1, end)
            yh = y_test[:, idx].ravel().astype(int)
            ph = prob[:, idx].ravel()
            row = empty_model_metrics(name, yh.reshape(-1, 1), ph.reshape(-1, 1))
            row['horizon_bucket'] = label
            bucket_rows.append(row)
    horizon_bucket_metrics_df = pd.DataFrame(bucket_rows)
    horizon_bucket_metrics_df.to_csv(Path(cfg.result_dir) / 'horizon_bucket_metrics_empty_positive.csv', index=False, encoding='utf-8-sig')
    plt.figure(figsize=(12, 5))
    sns.barplot(data=horizon_bucket_metrics_df, x='horizon_bucket', y='auprc_empty', hue='model')
    plt.ylim(0, 1)
    plt.title('Empty-positive AUPRC by forecast horizon bucket')
    plt.legend(fontsize=8, loc='lower left')
    save_fig(Path(cfg.figure_dir) / 'horizon_bucket_empty_auprc.png')
    pareto_rows = []
    fig, ax = plt.subplots(figsize=(11.5, 6.5))
    palette = dict(zip(test_sweep_df['model'].drop_duplicates(), sns.color_palette(n_colors=test_sweep_df['model'].nunique())))
    for model, part in test_sweep_df.groupby('model'):
        color = palette[model]
        part = part.sort_values(['occupancy_conflict_rate', 'safe_shiftable_load_opportunity_kwh'], ascending=[True, False])
        ax.scatter(part['occupancy_conflict_rate'], part['safe_shiftable_load_opportunity_kwh'], s=18, alpha=0.22, color=color, edgecolors='none')
        frontier = pareto_efficient_frontier(part)
        pareto_rows.append(frontier)
        ax.plot(frontier['occupancy_conflict_rate'], frontier['safe_shiftable_load_opportunity_kwh'], color=color, linewidth=2.2, label=model)
    marker_by_delta = {0.05: 'o', 0.10: 's', 0.20: 'D'}
    for _, row in policy_results_df[policy_results_df['risk_delta'].isin(marker_by_delta)].iterrows():
        model = row['model']
        if model not in palette:
            continue
        ax.scatter(
            row['occupancy_conflict_rate'],
            row['safe_shiftable_load_opportunity_kwh'],
            s=95,
            marker=marker_by_delta[float(row['risk_delta'])],
            color=palette[model],
            edgecolors='black',
            linewidths=0.8,
            zorder=5,
        )
    for delta in cfg.risk_deltas:
        ax.axvline(delta, color='gray', linestyle='--', linewidth=0.9)
    ax.set_xlabel('Occupancy conflict rate = false empty recommendations / all recommendations')
    ax.set_ylabel('Offline camera-label-empty load-proxy overlap (kWh)')
    ax.set_title('Empirical conflict--opportunity threshold sweep with Pareto-efficient frontiers')
    model_handles = [Line2D([0], [0], color=color, linewidth=2.2, label=model) for model, color in palette.items()]
    marker_handles = [
        Line2D([0], [0], marker=marker, color='black', linestyle='None', markersize=8, label=f'Selected {delta:.0%}')
        for delta, marker in [(0.05, 'o'), (0.10, 's'), (0.20, 'D')]
    ]
    ax.legend(handles=model_handles + marker_handles, title='Solid lines and selected policies', loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0, fontsize=8, title_fontsize=9)
    fig.text(
        0.02,
        0.02,
        'Raw dots = all threshold sweep points. Solid line = Pareto-efficient frontier after filtering dominated points. Large markers = validation-selected thresholds evaluated on held-out test days. Vertical dashed lines = empirical validation conflict cutoffs.',
        ha='left',
        va='bottom',
        fontsize=8,
    )
    fig.subplots_adjust(right=0.74, bottom=0.20)
    path = Path(cfg.figure_dir) / 'energy_risk_tradeoff_pareto.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)
    pareto_frontier_df = pd.concat(pareto_rows, ignore_index=True) if pareto_rows else pd.DataFrame()
    pareto_frontier_df.to_csv(Path(cfg.result_dir) / 'energy_risk_pareto_frontier.csv', index=False, encoding='utf-8-sig')
    policy_plot = policy_results_df.copy()
    policy_plot['risk_delta_label'] = (policy_plot['risk_delta'] * 100).round().astype(int).astype(str) + '%'
    plt.figure(figsize=(12, 5.5))
    sns.barplot(data=policy_plot, x='risk_delta_label', y='safe_shiftable_load_opportunity_kwh', hue='model')
    plt.title('Validation-selected policy: offline load-proxy overlap under a conflict cutoff')
    plt.xlabel('Empirical validation conflict cutoff')
    plt.ylabel('Offline camera-label-empty load-proxy overlap (kWh)')
    plt.legend(fontsize=8)
    save_fig(Path(cfg.figure_dir) / 'threshold_policy_safe_opportunity.png')
    plt.figure(figsize=(12, 5.5))
    sns.barplot(data=policy_plot, x='risk_delta_label', y='occupancy_conflict_rate', hue='model')
    plt.title('Realized occupancy conflict rate of validation-selected policies')
    plt.xlabel('Allowed validation conflict delta')
    plt.ylabel('Test occupancy conflict rate')
    plt.legend(fontsize=8)
    save_fig(Path(cfg.figure_dir) / 'threshold_policy_occupancy_conflict.png')
    window_plot = continuous_window_policy_df[np.isclose(continuous_window_policy_df['risk_delta'], 0.10)].copy()
    if len(window_plot):
        plt.figure(figsize=(12, 5.5))
        sns.barplot(data=window_plot, x='minimum_empty_window_hours', y='window_level_occupancy_conflict_rate', hue='model')
        plt.title('Continuous empty-window conflict rate by minimum duration, delta=10% policy')
        plt.xlabel('Minimum empty-window duration (hours)')
        plt.ylabel('Window-level occupancy conflict rate')
        plt.legend(fontsize=8)
        save_fig(Path(cfg.figure_dir) / 'continuous_empty_window_conflict_rate.png')
    sens_plot = energy_sensitivity_df[np.isclose(energy_sensitivity_df['risk_delta'], 0.10)].copy()
    if len(sens_plot):
        plt.figure(figsize=(13, 6))
        sns.barplot(data=sens_plot, x='load_assumption', y='safe_estimated_opportunity_kwh', hue='model')
        plt.title('Offline load-proxy sensitivity under the 10% empirical conflict cutoff')
        plt.xlabel('Controllable-load assumption')
        plt.ylabel('Offline load-proxy overlap (kWh)')
        plt.xticks(rotation=25, ha='right')
        plt.legend(fontsize=8)
        save_fig(Path(cfg.figure_dir) / 'energy_sensitivity_analysis.png')
    if len(permutation_importance_df):
        top_perm = permutation_importance_df.head(18).copy()
        plt.figure(figsize=(11, 6.5))
        sns.barplot(data=top_perm, x='importance', y='feature', color='tab:blue')
        plt.title('LightGBM permutation importance: validation Empty-AUPRC drop')
        plt.xlabel('AUPRC drop after feature permutation')
        plt.ylabel('Feature')
        save_fig(Path(cfg.figure_dir) / 'feature_importance_permutation_empty_auprc.png')
    y_empty_flat = 1 - y_test.ravel().astype(int)
    reliability_rows = []
    plt.figure(figsize=(8.5, 7))
    plt.plot([0, 1], [0, 1], '--', color='gray', linewidth=1, label='perfect calibration')
    for name, prob in predictions.items():
        p_empty = np.clip(1.0 - prob.ravel(), 1e-6, 1 - 1e-6)
        frac_pos, mean_pred = calibration_curve(y_empty_flat, p_empty, n_bins=10, strategy='quantile')
        for bin_id, (mp, fp) in enumerate(zip(mean_pred, frac_pos), start=1):
            reliability_rows.append({'model': name, 'positive_class': 'empty', 'bin': bin_id, 'mean_predicted_empty_probability': mp, 'observed_empty_fraction': fp})
        plt.plot(mean_pred, frac_pos, marker='o', linewidth=1.5, label=name)
    plt.xlabel('Mean predicted empty probability')
    plt.ylabel('Observed empty fraction')
    plt.title('Reliability curve with Empty=1')
    plt.legend(fontsize=8, loc='upper left')
    save_fig(Path(cfg.figure_dir) / 'empty_reliability_curve.png')
    empty_reliability_df = pd.DataFrame(reliability_rows)
    empty_reliability_df.to_csv(Path(cfg.result_dir) / 'empty_reliability_curve_points.csv', index=False, encoding='utf-8-sig')
    plt.figure(figsize=(8.5, 7))
    for name, prob in predictions.items():
        p_empty = np.clip(1.0 - prob.ravel(), 1e-6, 1 - 1e-6)
        precision, recall, _ = precision_recall_curve(y_empty_flat, p_empty)
        ap = average_precision_score(y_empty_flat, p_empty)
        plt.plot(recall, precision, linewidth=1.6, label=f'{name} ({ap:.3f})')
    plt.xlabel('Recall for Empty')
    plt.ylabel('Precision for Empty')
    plt.title('Precision-recall curves with Empty=1')
    plt.legend(fontsize=8, loc='lower left')
    save_fig(Path(cfg.figure_dir) / 'precision_recall_empty_positive.png')
    plt.figure(figsize=(8.5, 7))
    for name, prob in predictions.items():
        p_empty = np.clip(1.0 - prob.ravel(), 1e-6, 1 - 1e-6)
        fpr, tpr, _ = roc_curve(y_empty_flat, p_empty)
        auc = roc_auc_score(y_empty_flat, p_empty)
        plt.plot(fpr, tpr, linewidth=1.6, label=f'{name} ({auc:.3f})')
    plt.plot([0, 1], [0, 1], '--', color='gray', linewidth=1)
    plt.xlabel('FPR for Empty class')
    plt.ylabel('TPR for Empty class')
    plt.title('ROC curves with Empty=1')
    plt.legend(fontsize=8, loc='lower right')
    save_fig(Path(cfg.figure_dir) / 'roc_empty_positive.png')
    best_daily_pred = predictions[best_model][test_daily_idx]
    best_daily_y = y_test[test_daily_idx]
    best_daily_empty_prob = 1.0 - best_daily_pred
    best_daily_rec = stable_empty_mask_from_prob(best_daily_empty_prob, best_threshold, cfg.stable_empty_min_steps)
    case_rows = []
    for local_i, global_i in enumerate(test_daily_idx):
        yy = best_daily_y[local_i].astype(int)
        rec = best_daily_rec[local_i]
        actual_empty = yy == 0
        actual_occ = yy == 1
        conflict_count = int((rec & actual_occ).sum())
        safe_count = int((rec & actual_empty).sum())
        missed_count = int(((~rec) & actual_empty).sum())
        transitions = int(np.abs(np.diff(yy)).sum())
        case_rows.append({
            'daily_local_index': local_i,
            'test_anchor_index': int(global_i),
            'anchor_time': df.index[splits['test'][global_i]],
            'safe_count': safe_count,
            'conflict_count': conflict_count,
            'missed_count': missed_count,
            'recommendation_count': int(rec.sum()),
            'actual_empty_count': int(actual_empty.sum()),
            'transitions': transitions,
        })
    case_df = pd.DataFrame(case_rows)
    case_choices = []
    valid_success = case_df[(case_df['safe_count'] > 0) & (case_df['conflict_count'] == 0)]
    if len(valid_success):
        case_choices.append(('successful_recommendation_day', valid_success.sort_values('safe_count', ascending=False).iloc[0]))
    else:
        case_choices.append(('successful_recommendation_day', case_df.sort_values(['safe_count', 'conflict_count'], ascending=[False, True]).iloc[0]))
    case_choices.append(('false_positive_recommendation_day', case_df.sort_values(['conflict_count', 'recommendation_count'], ascending=False).iloc[0]))
    case_choices.append(('missed_opportunity_day', case_df.sort_values(['missed_count', 'actual_empty_count'], ascending=False).iloc[0]))
    case_choices.append(('irregular_schedule_day', case_df.sort_values(['transitions', 'actual_empty_count'], ascending=False).iloc[0]))
    chosen_rows = []
    for label, row in case_choices:
        chosen = row.to_dict()
        chosen['case_type'] = label
        chosen_rows.append(chosen)
    case_choice_df = pd.DataFrame(chosen_rows)
    case_choice_df.to_csv(Path(cfg.result_dir) / 'example_case_days.csv', index=False, encoding='utf-8-sig')
    for label, row in case_choices:
        global_i = int(row['test_anchor_index'])
        pos = future_positions(np.array([splits['test'][global_i]]), cfg.horizon_steps)[0]
        dates = df.index.take(pos)
        actual = df['occupied'].to_numpy()[pos]
        empty_prob = 1.0 - predictions[best_model][global_i]
        rec = stable_empty_mask_from_prob(empty_prob.reshape(1, -1), best_threshold, cfg.stable_empty_min_steps)[0]
        example = pd.DataFrame({'date': dates, 'actual_occupied': actual, 'predicted_empty_probability': empty_prob, 'recommend_empty_stable': rec})
        example.to_csv(Path(cfg.result_dir) / f'example_{label}.csv', index=False, encoding='utf-8-sig')
        fig, ax = plt.subplots(figsize=(13, 4.8))
        ax.step(example['date'], example['predicted_empty_probability'], where='post', label=f'{best_model} predicted empty probability')
        ax.fill_between(example['date'], 0, example['actual_occupied'], step='post', alpha=0.22, label='actual occupied')
        for i, is_rec in enumerate(rec):
            if is_rec:
                start = example['date'].iloc[i]
                ax.axvspan(start, start + pd.Timedelta(cfg.freq), color='tab:green', alpha=0.12)
        ax.axhline(best_threshold, color='tab:red', linestyle='--', linewidth=1, label='risk-delta 10% threshold')
        ax.set_ylim(-0.02, 1.05)
        ax.set_title(label.replace('_', ' ').title())
        ax.set_ylabel('Probability / occupancy')
        ax.legend(loc='upper right')
        save_fig(Path(cfg.figure_dir) / f'example_forecast_{label}.png')
    figure_files = sorted(Path(cfg.figure_dir).glob('*.png'))
    display(Markdown('## Saved figures'))
    for p in figure_files:
        display(Markdown(f'**{p.as_posix()}**'))
        display(Image(filename=str(p)))
    manifest_rows = []
    for folder in [Path(cfg.result_dir), Path(cfg.figure_dir)]:
        for p in sorted(folder.glob('*')):
            if p.is_file():
                manifest_rows.append({'folder': folder.as_posix(), 'file': p.name, 'relative_path': p.as_posix(), 'bytes': p.stat().st_size, 'modified_time': pd.Timestamp.fromtimestamp(p.stat().st_mtime)})
    current_run_manifest_df = pd.DataFrame(manifest_rows).sort_values(['folder', 'file'])
    current_run_manifest_df.to_csv(Path(cfg.result_dir) / 'current_run_manifest.csv', index=False, encoding='utf-8-sig')
    print('Saved result CSV files:')
    for p in sorted(Path(cfg.result_dir).glob('*.csv')):
        print('-', p.as_posix())
    return current_run_manifest_df


def run_pipeline(config: Config | None = None, make_figures: bool = True, show: bool = False):
    """Replay the legacy cleaned-release experiment and optional legacy figures.

    It must not be presented as a new empirical or prospective experiment.
    """
    global _, actual, actual_empty, actual_occ, anchors, ap, assumption, auc, ax, base_empty_prob, base_score, best_daily_empty_prob, best_daily_pred, best_daily_rec, best_daily_y, best_empty_prob, best_long, best_model, best_policy, best_prob, best_rec, best_threshold, bin_id, boot, bootstrap_ci_df, bootstrap_rows, bucket_defs, bucket_rows, case_choice_df, case_choices, case_df, case_rows, cfg, chosen, chosen_rows, col, conflict, conflict_count, continuous_window_policy_df, continuous_window_sweep_df, controllable_load_cols, controllable_load_inventory_df, current_run_manifest_df, daily_idx, data_summary, dates, day_order, default_rec_metrics_df, default_rec_rows, delta, device, df, dlinear, eb, empty_prob, empty_reliability_df, en_metric, end, energy_sensitivity_df, energy_sensitivity_rows, example, f, feature, feature_coverage, feature_policy, fig, figure_files, fold, fold_train_boundary, fold_val_end, fold_y, folder, fp, fpr, frac, frac_pos, fractions, frontier, future_values, global_i, global_mean, heldout, hist, hist_feature_cols, hist_mean, hist_prob, hist_scaled, hist_starts, hist_std, hist_values, horizon_bucket_metrics_df, i, idx, inventory_rows, is_rec, j, kwh, label, label_semantics, leakage_audit, lgbm, lgbm_models, load_assumptions_df, local_i, m, manifest_rows, mean_pred, metric, metric_definitions, metric_long, min_steps, missed_count, model, model_metrics_by_split_df, model_metrics_by_split_rows, model_metrics_df, model_name, mp, n_blocks, name, neg, numeric_seed_cols, occ_prob, occ_zone_raw, occupied_feature_index, outputs, p, p_empty, pareto_frontier_df, pareto_rows, part, pb, perm_rows, permutation_importance_df, ph, policy, policy_plot, policy_results_df, pos, pos_weight, precision, predictions, predictor_sensor_cols, prob, profile, rec, rec_metric, rec_row, recall, recommendation_metrics_by_split_df, recommendation_metrics_by_split_rows, record, records, reliability_rows, rf, rf_cv, rf_models, rng, rolling_origin_cv_df, rolling_rows, row, run_summary, safe, safe_count, sample, sample_idx, score, seed, seed_metrics_df, seed_metrics_rows, seed_prediction_records, seed_summary_df, sel, selected_policies_df, sens_plot, source_cols, source_coverage, source_series, source_slots, spatial_rows, spatial_validation_df, split_name, split_pred, split_summary, split_y, splits, start, start_train, table, tabular_feature_names, target, target_ends, test_daily_anchors, test_daily_energy, test_daily_idx, test_daily_predictions, test_daily_y, test_daily_y_for_windows, test_ds, test_positions, test_pred, test_rows, test_slots, test_sweep_df, threshold, time_cols, timezone_audit, timezone_hour_audit, top_perm, tpr, train_a, train_boundary, train_ds, train_future_y, train_row_mask, train_rows, training_control_rows, training_histories, training_history, transformer, transitions, val_a, val_boundary, val_daily_idx, val_ds, val_pos, val_positions, val_pred, val_predictions, valid_success, validation_sweep_df, values, window_duration_steps, window_plot, window_policy_rows, window_sweep_rows, x_holdout, x_perm, x_perm_base, x_source, x_test, x_train, x_val, xt, xv, y_empty_flat, y_empty_sample, y_holdout, y_source, y_test, y_train, y_val, yb, yd, yh, yt, yy, z, zone_cols, zone_feature_matrix, zone_labels
    configure_runtime(config or Config(), show=show)
    df, data_summary, source_coverage, feature_coverage, label_semantics, feature_policy, timezone_audit, timezone_hour_audit, time_cols, predictor_sensor_cols, controllable_load_cols = prepare_dataset(cfg)
    outputs = {
        'data_summary': data_summary,
        'source_coverage': source_coverage,
        'feature_coverage': feature_coverage,
        'label_semantics_audit': label_semantics,
        'feature_availability_policy': feature_policy,
        'timezone_audit': timezone_audit,
        'timezone_hour_audit': timezone_hour_audit,
    }
    for name, table in outputs.items():
        table.to_csv(Path(cfg.result_dir) / f'{name}.csv', index=False, encoding='utf-8-sig')
    df.to_csv(Path(cfg.result_dir) / 'processed_lbnl_15min_pacific.csv', encoding='utf-8-sig')
    display(Markdown('## Data, timezone, and label audit'))
    display(data_summary)
    display(timezone_audit)
    display(label_semantics)
    display(feature_policy)
    print('Processed shape:', df.shape)
    splits, split_summary, leakage_audit, train_boundary, val_boundary = make_splits(df, cfg)
    split_summary.to_csv(Path(cfg.result_dir) / 'split_summary.csv', index=False, encoding='utf-8-sig')
    leakage_audit.to_csv(Path(cfg.result_dir) / 'leakage_audit.csv', index=False, encoding='utf-8-sig')
    display(Markdown('## Chronological split and leakage audit'))
    display(split_summary)
    display(leakage_audit)
    start_train = time.time()
    target = df['occupied'].to_numpy(np.float32)
    val_positions = future_positions(splits['val'], cfg.horizon_steps)
    test_positions = future_positions(splits['test'], cfg.horizon_steps)
    y_val = target[val_positions].astype(int)
    y_test = target[test_positions].astype(int)
    predictions = {}
    val_predictions = {}
    seed_prediction_records = []
    training_control_rows = []
    val_predictions['Historical average'] = historical_average_prob(df, train_boundary, val_positions)
    predictions['Historical average'] = historical_average_prob(df, train_boundary, test_positions)
    training_control_rows.append({'model': 'Historical average', 'seeds': 'deterministic', 'training_budget': 'train-only slot averages', 'early_stopping': 'not applicable', 'feature_input': 'known future local time slot only'})
    x_train, y_train, tabular_feature_names = make_tabular_arrays(df, splits['train'], cfg, time_cols, predictor_sensor_cols)
    x_val, _, _ = make_tabular_arrays(df, splits['val'], cfg, time_cols, predictor_sensor_cols)
    x_test, _, _ = make_tabular_arrays(df, splits['test'], cfg, time_cols, predictor_sensor_cols)
    pd.DataFrame({'tabular_feature': tabular_feature_names}).to_csv(Path(cfg.result_dir) / 'tabular_feature_set.csv', index=False, encoding='utf-8-sig')
    lgbm_models = []
    rf_models = []
    for seed in cfg.random_seeds:
        sample_idx = stratified_sample_indices(y_train, cfg.tabular_max_train_rows, seed)
        if LGBMClassifier is not None:
            lgbm = LGBMClassifier(
                n_estimators=cfg.lgbm_estimators, learning_rate=0.05, num_leaves=31,
                min_child_samples=50, colsample_bytree=0.85,
                subsample=1.0, subsample_freq=0,
                reg_lambda=1.0, class_weight='balanced', random_state=seed,
                n_jobs=-1, verbose=-1,
            )
            lgbm.fit(x_train[sample_idx], y_train[sample_idx])
            lgbm_models.append(lgbm)
            val_pred = lgbm.predict_proba(x_val)[:, 1].reshape(len(splits['val']), -1)
            test_pred = lgbm.predict_proba(x_test)[:, 1].reshape(len(splits['test']), -1)
            seed_prediction_records.append({'model': 'LightGBM', 'seed': seed, 'val_pred': val_pred, 'test_pred': test_pred})
        rf = RandomForestClassifier(
            n_estimators=cfg.rf_estimators, max_depth=14, min_samples_leaf=20,
            max_features='sqrt', class_weight='balanced_subsample', n_jobs=-1,
            random_state=seed,
        )
        rf.fit(x_train[sample_idx], y_train[sample_idx])
        rf_models.append(rf)
        val_pred = rf.predict_proba(x_val)[:, 1].reshape(len(splits['val']), -1)
        test_pred = rf.predict_proba(x_test)[:, 1].reshape(len(splits['test']), -1)
        seed_prediction_records.append({'model': 'Random forest', 'seed': seed, 'val_pred': val_pred, 'test_pred': test_pred})
    for model_name in ['LightGBM', 'Random forest']:
        records = [r for r in seed_prediction_records if r['model'] == model_name]
        if records:
            val_predictions[model_name] = np.mean([r['val_pred'] for r in records], axis=0)
            predictions[model_name] = np.mean([r['test_pred'] for r in records], axis=0)
            training_control_rows.append({'model': model_name, 'seeds': ', '.join(map(str, cfg.random_seeds)), 'training_budget': f'{cfg.tabular_max_train_rows} sampled rows per seed; fixed hyperparameters', 'early_stopping': 'not used', 'feature_input': 'same tabular feature matrix'})
    perm_rows = []
    if lgbm_models:
        rng = np.random.default_rng(cfg.random_seeds[0])
        sample = rng.choice(len(y_train) if False else len(x_val), size=min(cfg.permutation_sample_rows, len(x_val)), replace=False)
        x_perm_base = x_val[sample].copy()
        y_empty_sample = 1 - y_val.ravel()[sample].astype(int)
        base_empty_prob = 1.0 - lgbm_models[0].predict_proba(x_perm_base)[:, 1]
        base_score = average_precision_score(y_empty_sample, base_empty_prob)
        for j, feature in enumerate(tabular_feature_names):
            x_perm = x_perm_base.copy()
            rng.shuffle(x_perm[:, j])
            p_empty = 1.0 - lgbm_models[0].predict_proba(x_perm)[:, 1]
            score = average_precision_score(y_empty_sample, p_empty)
            perm_rows.append({'model': 'LightGBM', 'importance_type': 'permutation_importance_empty_auprc_drop', 'feature': feature, 'baseline_empty_auprc': base_score, 'permuted_empty_auprc': score, 'importance': base_score - score})
    permutation_importance_df = pd.DataFrame(perm_rows).sort_values('importance', ascending=False) if perm_rows else pd.DataFrame()
    permutation_importance_df.to_csv(Path(cfg.result_dir) / 'permutation_importance.csv', index=False, encoding='utf-8-sig')
    hist_feature_cols = ['occupied', 'occ_count_mean'] + predictor_sensor_cols + time_cols
    hist_feature_cols = [c for c in hist_feature_cols if c in df.columns]
    hist_values = df[hist_feature_cols].to_numpy(np.float32)
    train_row_mask = df.index < train_boundary
    hist_mean = hist_values[train_row_mask].mean(axis=0, keepdims=True)
    hist_std = hist_values[train_row_mask].std(axis=0, keepdims=True)
    hist_std[hist_std < 1e-6] = 1.0
    hist_scaled = ((hist_values - hist_mean) / hist_std).astype(np.float32)
    future_values = df[time_cols].to_numpy(np.float32)
    train_ds = ForecastWindowDataset(hist_scaled, future_values, target, splits['train'], cfg)
    val_ds = ForecastWindowDataset(hist_scaled, future_values, target, splits['val'], cfg)
    test_ds = ForecastWindowDataset(hist_scaled, future_values, target, splits['test'], cfg)
    train_future_y = target[future_positions(splits['train'], cfg.horizon_steps).ravel()]
    pos = max(train_future_y.sum(), 1.0)
    neg = max(len(train_future_y) - train_future_y.sum(), 1.0)
    pos_weight = float(np.clip(neg / pos, 0.25, 8.0))
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    occupied_feature_index = hist_feature_cols.index('occupied')
    training_histories = []
    for seed in cfg.random_seeds:
        # Historical saved-output behavior: the seed reset occurs inside
        # train_deep_model after these modules are constructed.  Keep this
        # ordering to preserve traceability of the committed legacy artifacts;
        # move set_all_seeds(seed) before construction only as part of a full,
        # protocol-locked empirical rerun that regenerates every dependent
        # prediction and policy artifact.
        dlinear, hist = train_deep_model('DLinear', DLinear(cfg.history_steps, cfg.horizon_steps, occupied_feature_index), train_ds, val_ds, pos_weight, cfg, device, seed)
        training_histories.append(hist)
        seed_prediction_records.append({'model': 'DLinear', 'seed': seed, 'val_pred': predict_deep(dlinear, val_ds, cfg, device), 'test_pred': predict_deep(dlinear, test_ds, cfg, device)})

        transformer, hist = train_deep_model('Transformer', SequenceTransformer(len(hist_feature_cols), len(time_cols), cfg), train_ds, val_ds, pos_weight, cfg, device, seed)
        training_histories.append(hist)
        seed_prediction_records.append({'model': 'Transformer', 'seed': seed, 'val_pred': predict_deep(transformer, val_ds, cfg, device), 'test_pred': predict_deep(transformer, test_ds, cfg, device)})
    for model_name in ['DLinear', 'Transformer']:
        records = [r for r in seed_prediction_records if r['model'] == model_name]
        val_predictions[model_name] = np.mean([r['val_pred'] for r in records], axis=0)
        predictions[model_name] = np.mean([r['test_pred'] for r in records], axis=0)
        training_control_rows.append({'model': model_name, 'seeds': ', '.join(map(str, cfg.random_seeds)), 'training_budget': f'max {cfg.deep_epochs} epochs per seed', 'early_stopping': f'patience={cfg.early_stop_patience}', 'feature_input': 'same historical features + known future local time'})
    training_history = pd.concat(training_histories, ignore_index=True) if training_histories else pd.DataFrame()
    training_history.to_csv(Path(cfg.result_dir) / 'training_history.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(training_control_rows).to_csv(Path(cfg.result_dir) / 'model_training_control.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame([
        {'model': 'TFT', 'main_experiment_status': 'moved_to_appendix_not_run', 'reason': 'Excluded from main comparison to keep feature inputs and tuning budget fair.'},
        {'model': 'PatchTST', 'main_experiment_status': 'moved_to_appendix_not_run', 'reason': 'Excluded from main comparison to keep feature inputs and tuning budget fair.'},
    ]).to_csv(Path(cfg.result_dir) / 'appendix_model_note.csv', index=False, encoding='utf-8-sig')
    print('Training completed in %.1f seconds' % (time.time() - start_train))
    print('Predicted models:', ', '.join(predictions.keys()))
    print('Tabular features:', len(tabular_feature_names), 'Deep hist features:', len(hist_feature_cols))
    del x_train, y_train, x_val, x_test
    model_metrics_df = pd.DataFrame([empty_model_metrics(name, y_test, prob) for name, prob in predictions.items()])
    model_metrics_df = model_metrics_df.sort_values('auprc_empty', ascending=False).reset_index(drop=True)
    model_metrics_df.to_csv(Path(cfg.result_dir) / 'model_metrics_empty_positive.csv', index=False, encoding='utf-8-sig')
    seed_metrics_rows = []
    for record in seed_prediction_records:
        row = empty_model_metrics(record['model'], y_test, record['test_pred'])
        row['seed'] = record['seed']
        seed_metrics_rows.append(row)
    seed_metrics_df = pd.DataFrame(seed_metrics_rows)
    if len(seed_metrics_df):
        numeric_seed_cols = [c for c in seed_metrics_df.select_dtypes(include=[np.number]).columns if c != 'seed']
        seed_summary_df = seed_metrics_df.groupby('model')[numeric_seed_cols].agg(['mean', 'std'])
    else:
        seed_summary_df = pd.DataFrame()
    seed_metrics_df.to_csv(Path(cfg.result_dir) / 'seed_model_metrics.csv', index=False, encoding='utf-8-sig')
    if len(seed_summary_df):
        seed_summary_df.to_csv(Path(cfg.result_dir) / 'seed_model_metrics_summary.csv', encoding='utf-8-sig')
    default_rec_rows = []
    for name, prob in predictions.items():
        rec = stable_empty_mask_from_prob(1.0 - prob, cfg.default_empty_threshold, cfg.stable_empty_min_steps)
        default_rec_rows.append(recommendation_metrics_from_mask(name, y_test, rec, cfg.default_empty_threshold, policy='fixed_default_threshold'))
    default_rec_metrics_df = pd.DataFrame(default_rec_rows).sort_values('occupancy_conflict_rate').reset_index(drop=True)
    default_rec_metrics_df.to_csv(Path(cfg.result_dir) / 'recommendation_metrics.csv', index=False, encoding='utf-8-sig')
    model_metrics_by_split_rows = []
    recommendation_metrics_by_split_rows = []
    for split_name, split_y, split_pred in [('validation', y_val, val_predictions), ('test', y_test, predictions)]:
        for name, prob in split_pred.items():
            row = empty_model_metrics(name, split_y, prob)
            row['split'] = split_name
            model_metrics_by_split_rows.append(row)
            rec = stable_empty_mask_from_prob(1.0 - prob, cfg.default_empty_threshold, cfg.stable_empty_min_steps)
            rec_row = recommendation_metrics_from_mask(name, split_y, rec, cfg.default_empty_threshold, policy='fixed_default_threshold')
            rec_row['split'] = split_name
            rec_row['positive_class'] = 'empty'
            recommendation_metrics_by_split_rows.append(rec_row)
    model_metrics_by_split_df = pd.DataFrame(model_metrics_by_split_rows)
    recommendation_metrics_by_split_df = pd.DataFrame(recommendation_metrics_by_split_rows)
    model_metrics_by_split_df.to_csv(Path(cfg.result_dir) / 'model_metrics_by_split_empty_positive.csv', index=False, encoding='utf-8-sig')
    recommendation_metrics_by_split_df.to_csv(Path(cfg.result_dir) / 'recommendation_metrics_by_split.csv', index=False, encoding='utf-8-sig')
    save_all_model_predictions('validation', splits['val'], y_val, val_predictions)
    save_all_model_predictions('test', splits['test'], y_test, predictions)
    pd.DataFrame({'empty_probability_threshold': threshold_grid_values(cfg), 'positive_class': 'empty'}).to_csv(Path(cfg.result_dir) / 'threshold_grid_metadata.csv', index=False, encoding='utf-8-sig')
    val_daily_idx = daily_anchor_indices(df, splits['val'], cfg)
    test_daily_idx = daily_anchor_indices(df, splits['test'], cfg)
    validation_sweep_df = sweep_one_split(val_predictions, splits['val'], y_val, cfg, 'validation_daily', val_daily_idx)
    test_sweep_df = sweep_one_split(predictions, splits['test'], y_test, cfg, 'test_daily', test_daily_idx)
    validation_sweep_df.to_csv(Path(cfg.result_dir) / 'threshold_sweep_validation_daily.csv', index=False, encoding='utf-8-sig')
    test_sweep_df.to_csv(Path(cfg.result_dir) / 'energy_risk_tradeoff_threshold_sweep.csv', index=False, encoding='utf-8-sig')
    selected_policies_df = select_constrained_policies(validation_sweep_df, cfg)
    selected_policies_df.to_csv(Path(cfg.result_dir) / 'selected_threshold_policies.csv', index=False, encoding='utf-8-sig')
    policy_results_df = evaluate_selected_policies(selected_policies_df, predictions, splits['test'], y_test, cfg, 'test_daily', test_daily_idx)
    policy_results_df.to_csv(Path(cfg.result_dir) / 'threshold_policy_results_test.csv', index=False, encoding='utf-8-sig')
    window_sweep_rows = []
    window_duration_steps = [4, 8, 16]
    for split_name, split_y, split_pred, daily_idx in [
        ('validation_daily', y_val, val_predictions, val_daily_idx),
        ('test_daily', y_test, predictions, test_daily_idx),
    ]:
        yd = split_y[daily_idx]
        for name, occ_prob in split_pred.items():
            empty_prob = 1.0 - occ_prob[daily_idx]
            for min_steps in window_duration_steps:
                for threshold in threshold_grid_values(cfg):
                    window_sweep_rows.append(continuous_window_metrics_for_arrays(name, yd, empty_prob, threshold, min_steps, split_name, 'threshold_sweep'))
    continuous_window_sweep_df = pd.DataFrame(window_sweep_rows)
    continuous_window_sweep_df.to_csv(Path(cfg.result_dir) / 'continuous_empty_window_threshold_sweep.csv', index=False, encoding='utf-8-sig')
    window_policy_rows = []
    test_daily_y_for_windows = y_test[test_daily_idx]
    for _, sel in selected_policies_df.iterrows():
        name = sel['model']
        threshold = float(sel['selected_empty_probability_threshold'])
        empty_prob = 1.0 - predictions[name][test_daily_idx]
        for min_steps in window_duration_steps:
            row = continuous_window_metrics_for_arrays(name, test_daily_y_for_windows, empty_prob, threshold, min_steps, 'test_daily', f"risk_delta_{sel['risk_delta']:.0%}")
            row['risk_delta'] = sel['risk_delta']
            row['selection_met_constraint'] = sel['selection_met_constraint']
            window_policy_rows.append(row)
    continuous_window_policy_df = pd.DataFrame(window_policy_rows)
    continuous_window_policy_df.to_csv(Path(cfg.result_dir) / 'continuous_empty_window_policy_results_test.csv', index=False, encoding='utf-8-sig')
    test_daily_anchors = splits['test'][test_daily_idx]
    test_daily_y = y_test[test_daily_idx]
    test_daily_predictions = {m: p[test_daily_idx] for m, p in predictions.items()}
    inventory_rows = []
    for col in ['hvac_S', 'lig_S', 'mels_S', 'ele_south_total']:
        inventory_rows.append({
            'load_variable': col,
            'available_in_dataset': col in df.columns,
            'unit_assumption': 'kW before multiplying by 0.25 h',
            'used_as_model_input': False,
            'role': 'offline_proxy_sensitivity_only' if col in ['mels_S', 'ele_south_total'] else 'default_offline_load_proxy',
            'interpretation': 'processed meter proxy only; not verified controllability or savings',
        })
    controllable_load_inventory_df = pd.DataFrame(inventory_rows)
    controllable_load_inventory_df.to_csv(Path(cfg.result_dir) / 'controllable_load_inventory.csv', index=False, encoding='utf-8-sig')
    load_assumptions_df = controllable_load_assumptions(df)
    load_assumptions_df.to_csv(Path(cfg.result_dir) / 'controllable_load_assumptions.csv', index=False, encoding='utf-8-sig')
    energy_sensitivity_rows = []
    for _, assumption in load_assumptions_df.iterrows():
        kwh = assumption_energy_matrix(df, test_daily_anchors, cfg, assumption)
        for _, sel in selected_policies_df.iterrows():
            name = sel['model']
            threshold = float(sel['selected_empty_probability_threshold'])
            rec = stable_empty_mask_from_prob(1.0 - test_daily_predictions[name], threshold, cfg.stable_empty_min_steps)
            actual_empty = test_daily_y == 0
            safe = rec & actual_empty
            conflict = rec & (~actual_empty)
            energy_sensitivity_rows.append({
                'split': 'test_daily',
                'model': name,
                'risk_delta': sel['risk_delta'],
                'empty_probability_threshold': threshold,
                'load_assumption': assumption['assumption'],
                'load_assumption_description': assumption['description'],
                'gross_recommended_estimated_opportunity_kwh': float((kwh * rec).sum()),
                'safe_estimated_opportunity_kwh': float((kwh * safe).sum()),
                'conflict_estimated_kwh': float((kwh * conflict).sum()),
                'available_actual_empty_estimated_opportunity_kwh': float((kwh * actual_empty).sum()),
                'energy_formula': 'sum over intervals of P_t_controllable * 0.25 hour',
                'counterfactual_status': 'estimated opportunity only; no counterfactual simulator',
            })
    energy_sensitivity_df = pd.DataFrame(energy_sensitivity_rows)
    energy_sensitivity_df.to_csv(Path(cfg.result_dir) / 'energy_sensitivity_analysis.csv', index=False, encoding='utf-8-sig')
    bootstrap_rows = []
    rng = np.random.default_rng(cfg.random_seeds[0])
    test_daily_anchors = splits['test'][test_daily_idx]
    test_daily_y = y_test[test_daily_idx]
    test_daily_predictions = {m: p[test_daily_idx] for m, p in predictions.items()}
    test_daily_energy = controllable_energy_matrix(df, test_daily_anchors, cfg, controllable_load_cols)
    for model in predictions:
        policy = selected_policies_df[(selected_policies_df['model'] == model) & (np.isclose(selected_policies_df['risk_delta'], 0.10))]
        threshold = float(policy.iloc[0]['selected_empty_probability_threshold']) if len(policy) else cfg.default_empty_threshold
        values = []
        n_blocks = len(test_daily_idx)
        for _ in range(cfg.bootstrap_reps):
            idx = rng.choice(np.arange(n_blocks), size=n_blocks, replace=True)
            yb = test_daily_y[idx]
            pb = test_daily_predictions[model][idx]
            eb = test_daily_energy[idx]
            rec = stable_empty_mask_from_prob(1.0 - pb, threshold, cfg.stable_empty_min_steps)
            metric = empty_model_metrics(model, yb, pb)
            rec_metric = recommendation_metrics_from_mask(model, yb, rec, threshold, policy='bootstrap_delta_10pct')
            en_metric = energy_metrics_from_mask(model, yb, rec, eb, cfg, threshold, policy='bootstrap_delta_10pct')
            values.append({
                'auprc_empty': metric['auprc_empty'],
                'f1_empty': metric['f1_empty'],
                'occupancy_conflict_rate': rec_metric['occupancy_conflict_rate'],
                'safe_shiftable_load_opportunity_kwh': en_metric['safe_shiftable_load_opportunity_kwh'],
            })
        boot = pd.DataFrame(values)
        for metric in boot.columns:
            bootstrap_rows.append({
                'model': model,
                'policy': 'risk_delta_10%',
                'metric': metric,
                'mean': boot[metric].mean(),
                'ci95_low': boot[metric].quantile(0.025),
                'ci95_high': boot[metric].quantile(0.975),
                'bootstrap_blocks': n_blocks,
                'bootstrap_reps': cfg.bootstrap_reps,
            })
    bootstrap_ci_df = pd.DataFrame(bootstrap_rows)
    bootstrap_ci_df.to_csv(Path(cfg.result_dir) / 'block_bootstrap_confidence_intervals.csv', index=False, encoding='utf-8-sig')
    # This retrospective test ranking is retained only for legacy display
    # exports. It is not a canonical model-selection rule.
    legacy_test_ranked_model = model_metrics_df.iloc[0]['model']
    best_model = legacy_test_ranked_model
    best_policy = selected_policies_df[(selected_policies_df['model'] == best_model) & (np.isclose(selected_policies_df['risk_delta'], 0.10))]
    best_threshold = float(best_policy.iloc[0]['selected_empty_probability_threshold']) if len(best_policy) else cfg.default_empty_threshold
    best_prob = predictions[best_model]
    best_empty_prob = 1.0 - best_prob
    best_rec = stable_empty_mask_from_prob(best_empty_prob, best_threshold, cfg.stable_empty_min_steps)
    best_long = pd.DataFrame({
        'anchor_time': np.repeat(df.index.take(splits['test']).to_numpy(), cfg.horizon_steps),
        'target_time': df.index.take(test_positions.ravel()).to_numpy(),
        'horizon_step': np.tile(np.arange(1, cfg.horizon_steps + 1), len(splits['test'])),
        'actual_occupied': y_test.ravel().astype(int),
        'actual_empty_positive': (1 - y_test.ravel().astype(int)),
        'predicted_occupied_probability': best_prob.ravel(),
        'predicted_empty_probability': best_empty_prob.ravel(),
        'recommend_empty_stable': best_rec.ravel(),
        'risk_delta_10pct_threshold': best_threshold,
    })
    best_long.to_csv(Path(cfg.result_dir) / 'test_forecast_probabilities_legacy_test_ranked_model.csv', index=False, encoding='utf-8-sig')
    metric_definitions = pd.DataFrame([
        {'metric': 'AUPRC/F1/Precision/Recall', 'definition': 'Computed with Empty=1 as the positive class.', 'scope': 'classification diagnostic over the stated saved-output rows'},
        {'metric': 'Occupancy conflict rate', 'definition': 'Occupied camera-labelled recommendations / all recommendations = 1 - empty-window precision.', 'scope': 'empirical interval conflict; not a probabilistic safety guarantee'},
        {'metric': 'Standard FPR', 'definition': 'Occupied camera-labelled recommendations / all actually occupied intervals.', 'scope': 'classification diagnostic'},
        {'metric': 'Offline camera-label-empty load-proxy overlap', 'definition': 'Sum over camera-label-empty recommended intervals of processed HVAC south plus lighting south meter kW times 0.25 hour.', 'scope': 'offline overlap only; not verified controllability or energy savings'},
        {'metric': 'Gross processed load-proxy overlap', 'definition': 'Processed HVAC-plus-lighting meter kWh over all recommended intervals before excluding occupied camera labels.', 'scope': 'offline accounting only'},
        {'metric': 'Continuous empty-window metrics', 'definition': 'Window-level precision, recall, and conflict are computed on disjoint runs from non-overlapping daily forecasts for 1h, 2h, and 4h minimum durations.', 'scope': 'post-bin saved-output diagnostic'},
    ])
    metric_definitions.to_csv(Path(cfg.result_dir) / 'metric_definitions.csv', index=False, encoding='utf-8-sig')
    run_summary = pd.DataFrame([{
        'legacy_test_ranked_model_for_display': legacy_test_ranked_model,
        'display_model_selection_scope': 'held-out test ranking; excluded from canonical model selection',
        'best_model_delta_10_threshold': best_threshold,
        'test_forecast_intervals': int(y_test.size),
        'test_forecast_anchors': int(len(splits['test'])),
        'daily_test_schedules': int(len(test_daily_idx)),
        'device': str(device),
        'positive_class': 'Empty=1',
        'result_dir': cfg.result_dir,
        'figure_dir': cfg.figure_dir,
    }])
    run_summary.to_csv(Path(cfg.result_dir) / 'run_summary.csv', index=False, encoding='utf-8-sig')
    display(Markdown('## Empty-positive model metrics'))
    display(model_metrics_df)
    display(Markdown('## Default stable recommendation metrics'))
    display(default_rec_metrics_df)
    display(Markdown('## Validation-selected constrained threshold policies'))
    display(selected_policies_df)
    display(Markdown('## Test daily policy results'))
    display(policy_results_df)
    display(Markdown('## Run summary'))
    display(run_summary)
    rolling_rows = []
    fractions = [0.50, 0.60, 0.70]
    for fold, frac in enumerate(fractions, start=1):
        fold_train_boundary = floor_to_week_start(df.index[int(len(df) * frac)])
        fold_val_end = fold_train_boundary + pd.Timedelta(days=21)
        anchors = np.arange(cfg.history_steps - 1, len(df) - cfg.horizon_steps, cfg.forecast_stride)
        hist_starts = anchors - cfg.history_steps + 1
        target_ends = anchors + cfg.horizon_steps
        train_a = anchors[df.index.take(target_ends) < fold_train_boundary]
        val_a = anchors[(df.index.take(hist_starts) >= fold_train_boundary + pd.Timedelta(hours=24)) & (df.index.take(target_ends) < fold_val_end)]
        if len(train_a) < 100 or len(val_a) < 100:
            continue
        val_pos = future_positions(val_a, cfg.horizon_steps)
        fold_y = target[val_pos].astype(int)
        hist_prob = historical_average_prob(df, fold_train_boundary, val_pos)
        row = empty_model_metrics('Historical average', fold_y, hist_prob)
        row.update({'fold': fold, 'train_boundary': fold_train_boundary, 'validation_end': fold_val_end, 'validation_anchors': len(val_a)})
        rolling_rows.append(row)
        xt, yt, _ = make_tabular_arrays(df, train_a, cfg, time_cols, predictor_sensor_cols)
        xv, _, _ = make_tabular_arrays(df, val_a, cfg, time_cols, predictor_sensor_cols)
        idx = stratified_sample_indices(yt, cfg.tabular_max_train_rows // 2, cfg.random_seeds[0] + fold)
        if LGBMClassifier is not None:
            m = LGBMClassifier(n_estimators=180, learning_rate=0.06, num_leaves=31, min_child_samples=50, colsample_bytree=0.85, subsample=1.0, subsample_freq=0, class_weight='balanced', random_state=cfg.random_seeds[0] + fold, n_jobs=-1, verbose=-1)
            m.fit(xt[idx], yt[idx])
            prob = m.predict_proba(xv)[:, 1].reshape(len(val_a), -1)
            row = empty_model_metrics('LightGBM', fold_y, prob)
            row.update({'fold': fold, 'train_boundary': fold_train_boundary, 'validation_end': fold_val_end, 'validation_anchors': len(val_a)})
            rolling_rows.append(row)
        rf_cv = RandomForestClassifier(n_estimators=40, max_depth=12, min_samples_leaf=25, max_features='sqrt', class_weight='balanced_subsample', n_jobs=-1, random_state=cfg.random_seeds[0] + fold)
        rf_cv.fit(xt[idx], yt[idx])
        prob = rf_cv.predict_proba(xv)[:, 1].reshape(len(val_a), -1)
        row = empty_model_metrics('Random forest', fold_y, prob)
        row.update({'fold': fold, 'train_boundary': fold_train_boundary, 'validation_end': fold_val_end, 'validation_anchors': len(val_a)})
        rolling_rows.append(row)
        del xt, yt, xv
    rolling_origin_cv_df = pd.DataFrame(rolling_rows)
    rolling_origin_cv_df.to_csv(Path(cfg.result_dir) / 'rolling_origin_cv.csv', index=False, encoding='utf-8-sig')
    occ_zone_raw = read_timeseries(Path(cfg.data_dir) / 'occ.csv', cfg).set_index('date')
    zone_cols = [c for c in occ_zone_raw.columns if c.startswith('occ_')]
    zone_labels = {}
    for col in zone_cols:
        z = occ_zone_raw[col].resample(cfg.freq, closed='left', label='left').max().reindex(df.index)
        zone_labels[col] = (z.ffill().fillna(0.0) > cfg.occupied_count_threshold).astype(float)
    zone_feature_matrix = df[time_cols].to_numpy(np.float32)
    train_rows = df.index < train_boundary
    test_rows = df.index >= val_boundary + pd.Timedelta(hours=24)
    spatial_rows = []
    for heldout in zone_cols:
        source_cols = [c for c in zone_cols if c != heldout]
        if not source_cols:
            continue
        y_source = pd.concat([zone_labels[c] for c in source_cols], axis=0).to_numpy().astype(int)
        x_source = np.vstack([zone_feature_matrix[train_rows] for _ in source_cols])
        y_source = np.concatenate([zone_labels[c].to_numpy()[train_rows].astype(int) for c in source_cols])
        x_holdout = zone_feature_matrix[test_rows]
        y_holdout = zone_labels[heldout].to_numpy()[test_rows].astype(int)
        if LGBMClassifier is not None and len(np.unique(y_source)) > 1 and len(np.unique(y_holdout)) > 1:
            m = LGBMClassifier(n_estimators=160, learning_rate=0.06, num_leaves=15, class_weight='balanced', random_state=cfg.random_seeds[0], n_jobs=-1, verbose=-1)
            m.fit(x_source, y_source)
            occ_prob = m.predict_proba(x_holdout)[:, 1]
            row = empty_model_metrics('LightGBM time-only leave-one-zone-out', y_holdout.reshape(-1, 1), occ_prob.reshape(-1, 1))
            row.update({'heldout_zone': heldout, 'train_zones': ', '.join(source_cols), 'test_rows': int(test_rows.sum())})
            spatial_rows.append(row)
        # Train-only local time historical average from source zones.
        source_series = pd.concat([zone_labels[c][train_rows] for c in source_cols])
        source_slots = np.concatenate([slot_index(df.index[train_rows]) for _ in source_cols])
        table = pd.Series(source_series.to_numpy(), index=source_slots).groupby(level=0).mean()
        global_mean = float(source_series.mean())
        test_slots = slot_index(df.index[test_rows])
        occ_prob = np.array([table.get(s, global_mean) for s in test_slots], dtype=np.float32)
        row = empty_model_metrics('Historical average leave-one-zone-out', y_holdout.reshape(-1, 1), occ_prob.reshape(-1, 1))
        row.update({'heldout_zone': heldout, 'train_zones': ', '.join(source_cols), 'test_rows': int(test_rows.sum())})
        spatial_rows.append(row)
    spatial_validation_df = pd.DataFrame(spatial_rows)
    spatial_validation_df.to_csv(Path(cfg.result_dir) / 'leave_one_zone_out_spatial_validation.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame([
        {'validation': 'rolling_origin_cv', 'status': 'implemented_lightweight', 'scope': 'Historical Average, LightGBM, Random Forest; deep models use final split multi-seed training due runtime.'},
        {'validation': 'leave_one_zone_out', 'status': 'implemented_lightweight', 'scope': 'Zone-level occupancy labels with time-only features to avoid cross-zone occupancy leakage.'},
        {'validation': 'block_bootstrap_ci', 'status': 'implemented', 'scope': '95% CIs over non-overlapping daily forecast blocks for main models.'},
    ]).to_csv(Path(cfg.result_dir) / 'research_validation_scope.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame([
        {'field': 'state', 'definition': 'Past occupancy sequence, completed-input-bin sensors, known future calendar features, and current uncalibrated forecast scores.', 'scope': 'future simulation design; no real-time availability proof'},
        {'field': 'action', 'definition': 'Future simulator placeholder: recommend or do not recommend a hypothetical schedule change for a predicted empty interval.', 'scope': 'not an executed building-control action'},
        {'field': 'reward', 'definition': 'Future simulator objective: offline camera-label-empty processed-load-proxy overlap minus empirical-conflict and missed-overlap penalties.', 'scope': 'not realized energy savings'},
        {'field': 'transition', 'definition': 'Future simulator placeholder: advance one interval or decision horizon; an external simulator could define physical dynamics.', 'scope': 'not executed in this study'},
    ]).to_csv(Path(cfg.result_dir) / 'state_action_reward_schema.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame([
        {'todo': 'decision_focused_loss', 'detail': 'Future study: Total Loss = BCE occupancy loss + lambda_fp * occupied-label recommendation penalty + lambda_miss * missed load-proxy-overlap penalty.'},
        {'todo': 'rl_environment_adapter', 'detail': 'Future study: expose forecast state, hypothetical action, and offline load-proxy-overlap objective in a physical control simulator.'},
        {'todo': 'appendix_advanced_models', 'detail': 'Run TFT/PatchTST only with matched splits, feature inputs, seeds, and tuning budget before comparing in main text.'},
    ]).to_csv(Path(cfg.result_dir) / 'future_work_todos.csv', index=False, encoding='utf-8-sig')
    display(Markdown('## Research-grade validation additions'))
    display(rolling_origin_cv_df.head())
    display(spatial_validation_df.head())
    write_individual_prediction_exports('validation', splits['val'], y_val, val_predictions, cfg)
    write_individual_prediction_exports('test', splits['test'], y_test, predictions, cfg)
    if make_figures:
        generate_figures_from_pipeline_state(show=show)
    return {name: globals().get(name) for name in (('_', 'actual', 'actual_empty', 'actual_occ', 'anchors', 'ap', 'assumption', 'auc', 'ax', 'base_empty_prob', 'base_score', 'best_daily_empty_prob', 'best_daily_pred', 'best_daily_rec', 'best_daily_y', 'best_empty_prob', 'best_long', 'best_model', 'best_policy', 'best_prob', 'best_rec', 'best_threshold', 'bin_id', 'boot', 'bootstrap_ci_df', 'bootstrap_rows', 'bucket_defs', 'bucket_rows', 'case_choice_df', 'case_choices', 'case_df', 'case_rows', 'cfg', 'chosen', 'chosen_rows', 'col', 'conflict', 'conflict_count', 'continuous_window_policy_df', 'continuous_window_sweep_df', 'controllable_load_cols', 'controllable_load_inventory_df', 'current_run_manifest_df', 'daily_idx', 'data_summary', 'dates', 'day_order', 'default_rec_metrics_df', 'default_rec_rows', 'delta', 'device', 'df', 'dlinear', 'eb', 'empty_prob', 'empty_reliability_df', 'en_metric', 'end', 'energy_sensitivity_df', 'energy_sensitivity_rows', 'example', 'f', 'feature', 'feature_coverage', 'feature_policy', 'fig', 'figure_files', 'fold', 'fold_train_boundary', 'fold_val_end', 'fold_y', 'folder', 'fp', 'fpr', 'frac', 'frac_pos', 'fractions', 'frontier', 'future_values', 'global_i', 'global_mean', 'heldout', 'hist', 'hist_feature_cols', 'hist_mean', 'hist_prob', 'hist_scaled', 'hist_starts', 'hist_std', 'hist_values', 'horizon_bucket_metrics_df', 'i', 'idx', 'inventory_rows', 'is_rec', 'j', 'kwh', 'label', 'label_semantics', 'leakage_audit', 'lgbm', 'lgbm_models', 'load_assumptions_df', 'local_i', 'm', 'manifest_rows', 'mean_pred', 'metric', 'metric_definitions', 'metric_long', 'min_steps', 'missed_count', 'model', 'model_metrics_by_split_df', 'model_metrics_by_split_rows', 'model_metrics_df', 'model_name', 'mp', 'n_blocks', 'name', 'neg', 'numeric_seed_cols', 'occ_prob', 'occ_zone_raw', 'occupied_feature_index', 'outputs', 'p', 'p_empty', 'pareto_frontier_df', 'pareto_rows', 'part', 'pb', 'perm_rows', 'permutation_importance_df', 'ph', 'policy', 'policy_plot', 'policy_results_df', 'pos', 'pos_weight', 'precision', 'predictions', 'predictor_sensor_cols', 'prob', 'profile', 'rec', 'rec_metric', 'rec_row', 'recall', 'recommendation_metrics_by_split_df', 'recommendation_metrics_by_split_rows', 'record', 'records', 'reliability_rows', 'rf', 'rf_cv', 'rf_models', 'rng', 'rolling_origin_cv_df', 'rolling_rows', 'row', 'run_summary', 'safe', 'safe_count', 'sample', 'sample_idx', 'score', 'seed', 'seed_metrics_df', 'seed_metrics_rows', 'seed_prediction_records', 'seed_summary_df', 'sel', 'selected_policies_df', 'sens_plot', 'source_cols', 'source_coverage', 'source_series', 'source_slots', 'spatial_rows', 'spatial_validation_df', 'split_name', 'split_pred', 'split_summary', 'split_y', 'splits', 'start', 'start_train', 'table', 'tabular_feature_names', 'target', 'target_ends', 'test_daily_anchors', 'test_daily_energy', 'test_daily_idx', 'test_daily_predictions', 'test_daily_y', 'test_daily_y_for_windows', 'test_ds', 'test_positions', 'test_pred', 'test_rows', 'test_slots', 'test_sweep_df', 'threshold', 'time_cols', 'timezone_audit', 'timezone_hour_audit', 'top_perm', 'tpr', 'train_a', 'train_boundary', 'train_ds', 'train_future_y', 'train_row_mask', 'train_rows', 'training_control_rows', 'training_histories', 'training_history', 'transformer', 'transitions', 'val_a', 'val_boundary', 'val_daily_idx', 'val_ds', 'val_pos', 'val_positions', 'val_pred', 'val_predictions', 'valid_success', 'validation_sweep_df', 'values', 'window_duration_steps', 'window_plot', 'window_policy_rows', 'window_sweep_rows', 'x_holdout', 'x_perm', 'x_perm_base', 'x_source', 'x_test', 'x_train', 'x_val', 'xt', 'xv', 'y_empty_flat', 'y_empty_sample', 'y_holdout', 'y_source', 'y_test', 'y_train', 'y_val', 'yb', 'yd', 'yh', 'yt', 'yy', 'z', 'zone_cols', 'zone_feature_matrix', 'zone_labels'))}


def main() -> int:
    run_pipeline()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
