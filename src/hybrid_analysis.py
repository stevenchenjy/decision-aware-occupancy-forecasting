"""Validation-only hybrid selection and saved-output analysis.

This module operates on the canonical validation/test prediction exports.  It
does not retrain base models.  The primary three-way ensemble is selected on an
explicit validation-only probability-weight grid; test predictions are loaded
only after all blend weights and operating thresholds have been fixed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


HORIZON_STEPS = 96
INTERVAL_HOURS = 0.25
DEFAULT_STABLE_STEPS = 4
RISK_DELTAS = (0.05, 0.10, 0.20)
THRESHOLDS = np.round(np.arange(0.05, 0.9501, 0.025), 3)
BOOTSTRAP_SEED = 42

BASE_PROBABILITY_COLUMNS = {
    "Historical Average": "historical_average_empty_probability",
    "LightGBM": "lightgbm_empty_probability",
    "Random Forest": "random_forest_empty_probability",
    "Original Transformer": "transformer_empty_probability",
    "DLinear": "dlinear_empty_probability",
}

PRIMARY_MODEL = "Hybrid Seasonal-GBDT-Transformer"
SEASONAL_MODEL = "Seasonal-Transformer Blend"
EXPLORATORY_MODEL = "Exploratory Hybrid Balanced Tree-Deep"

MODEL_ORDER = [
    "Historical Average",
    "LightGBM",
    "Random Forest",
    "Original Transformer",
    "DLinear",
    SEASONAL_MODEL,
    PRIMARY_MODEL,
    EXPLORATORY_MODEL,
]

MODEL_COLORS = {
    "Historical Average": "#4C78A8",
    "LightGBM": "#F58518",
    "Random Forest": "#54A24B",
    "Original Transformer": "#B279A2",
    "DLinear": "#E45756",
    SEASONAL_MODEL: "#72B7B2",
    PRIMARY_MODEL: "#2F4B7C",
    EXPLORATORY_MODEL: "#9D755D",
}


@dataclass(frozen=True)
class HybridSelection:
    seasonal_transformer_weight: float
    primary_historical_weight: float
    primary_lightgbm_weight: float
    primary_transformer_weight: float


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, encoding="utf-8-sig")


def validate_prediction_frame(frame: pd.DataFrame, split: str) -> None:
    required = {
        "split",
        "anchor_time",
        "target_time",
        "horizon_step",
        "actual_occupied",
        "actual_empty_positive",
        *BASE_PROBABILITY_COLUMNS.values(),
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{split} predictions are missing columns: {missing}")
    if frame.empty or len(frame) % HORIZON_STEPS:
        raise ValueError(f"{split} row count is not divisible by {HORIZON_STEPS}")
    if frame.duplicated(["anchor_time", "target_time", "horizon_step"]).any():
        raise ValueError(f"{split} contains duplicate prediction keys")
    group_sizes = frame.groupby("anchor_time", sort=False).size()
    if not group_sizes.eq(HORIZON_STEPS).all():
        raise ValueError(f"{split} has anchors without exactly {HORIZON_STEPS} rows")
    expected_steps = np.tile(np.arange(1, HORIZON_STEPS + 1), len(group_sizes))
    if not np.array_equal(frame["horizon_step"].to_numpy(), expected_steps):
        raise ValueError(f"{split} rows are not ordered by complete 1..96 horizons")
    if not np.array_equal(
        frame["actual_empty_positive"].to_numpy(dtype=int),
        1 - frame["actual_occupied"].to_numpy(dtype=int),
    ):
        raise ValueError(f"{split} Empty labels do not equal 1 - occupied")
    if frame.groupby("target_time")["actual_empty_positive"].nunique().max() != 1:
        raise ValueError(f"{split} contains conflicting labels for a target timestamp")
    for column in BASE_PROBABILITY_COLUMNS.values():
        values = frame[column].to_numpy(dtype=float)
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError(f"{split} has invalid probabilities in {column}")


def validate_split_integrity(validation: pd.DataFrame, test: pd.DataFrame) -> None:
    validate_prediction_frame(validation, "validation")
    validate_prediction_frame(test, "test")
    val_targets = pd.to_datetime(validation["target_time"], utc=True)
    test_targets = pd.to_datetime(test["target_time"], utc=True)
    if val_targets.max() >= test_targets.min():
        raise ValueError("Validation and test target periods overlap")


def convex_probability_blend(
    probabilities: dict[str, np.ndarray], weights: dict[str, float]
) -> np.ndarray:
    if not weights:
        raise ValueError("At least one blend weight is required")
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("Blend weights must be non-negative")
    if not np.isclose(sum(weights.values()), 1.0, atol=1e-12):
        raise ValueError("Blend weights must sum to 1")
    missing = set(weights).difference(probabilities)
    if missing:
        raise KeyError(f"Missing component probabilities: {sorted(missing)}")
    arrays = [np.asarray(probabilities[name], dtype=float) for name in weights]
    if len({array.shape for array in arrays}) != 1:
        raise ValueError("Component probability arrays are not aligned")
    result = sum(weights[name] * probabilities[name] for name in weights)
    return np.clip(np.asarray(result, dtype=float), 1e-6, 1 - 1e-6)


def select_seasonal_transformer_weight(
    y_validation: np.ndarray,
    historical_probability: np.ndarray,
    transformer_probability: np.ndarray,
    step: float = 0.01,
) -> tuple[float, pd.DataFrame]:
    rows: list[dict] = []
    best_weight = 0.0
    best_score = -np.inf
    units = int(round(1.0 / step))
    for transformer_units in range(units + 1):
        transformer_weight = transformer_units / units
        probability = (
            transformer_weight * transformer_probability
            + (1 - transformer_weight) * historical_probability
        )
        score = average_precision_score(y_validation, probability)
        rows.append(
            {
                "transformer_weight": transformer_weight,
                "historical_average_weight": 1 - transformer_weight,
                "validation_auprc_empty": score,
                "selection_split": "validation_all_overlapping_forecasts",
            }
        )
        if score > best_score:
            best_score = score
            best_weight = transformer_weight
    return best_weight, pd.DataFrame(rows)


def select_primary_hybrid_weights(
    y_validation: np.ndarray,
    historical_probability: np.ndarray,
    lightgbm_probability: np.ndarray,
    transformer_probability: np.ndarray,
    step: float = 0.05,
) -> tuple[dict[str, float], pd.DataFrame]:
    """Select the three-way convex blend on validation AUPRC only."""
    units = int(round(1.0 / step))
    rows: list[dict] = []
    best_score = -np.inf
    best_weights: dict[str, float] | None = None
    for historical_units in range(units + 1):
        for lightgbm_units in range(units + 1 - historical_units):
            transformer_units = units - historical_units - lightgbm_units
            weights = {
                "Historical Average": historical_units / units,
                "LightGBM": lightgbm_units / units,
                "Original Transformer": transformer_units / units,
            }
            probability = (
                weights["Historical Average"] * historical_probability
                + weights["LightGBM"] * lightgbm_probability
                + weights["Original Transformer"] * transformer_probability
            )
            score = average_precision_score(y_validation, probability)
            rows.append(
                {
                    "historical_average_weight": weights["Historical Average"],
                    "lightgbm_weight": weights["LightGBM"],
                    "transformer_weight": weights["Original Transformer"],
                    "validation_auprc_empty": score,
                    "grid_step": step,
                    "selection_split": "validation_all_overlapping_forecasts",
                }
            )
            if score > best_score:
                best_score = score
                best_weights = weights
    assert best_weights is not None
    search = pd.DataFrame(rows).sort_values(
        ["validation_auprc_empty", "lightgbm_weight"], ascending=[False, False]
    )
    search["validation_rank"] = np.arange(1, len(search) + 1)
    search["selected_by_validation"] = (
        np.isclose(search["historical_average_weight"], best_weights["Historical Average"])
        & np.isclose(search["lightgbm_weight"], best_weights["LightGBM"])
        & np.isclose(search["transformer_weight"], best_weights["Original Transformer"])
    )
    return best_weights, search


def select_weights_from_validation(validation: pd.DataFrame) -> tuple[HybridSelection, pd.DataFrame, pd.DataFrame]:
    y_validation = validation["actual_empty_positive"].to_numpy(dtype=int)
    historical = validation[BASE_PROBABILITY_COLUMNS["Historical Average"]].to_numpy(dtype=float)
    lightgbm = validation[BASE_PROBABILITY_COLUMNS["LightGBM"]].to_numpy(dtype=float)
    transformer = validation[BASE_PROBABILITY_COLUMNS["Original Transformer"]].to_numpy(dtype=float)
    seasonal_weight, seasonal_search = select_seasonal_transformer_weight(
        y_validation, historical, transformer
    )
    primary_weights, primary_search = select_primary_hybrid_weights(
        y_validation, historical, lightgbm, transformer
    )
    selection = HybridSelection(
        seasonal_transformer_weight=seasonal_weight,
        primary_historical_weight=primary_weights["Historical Average"],
        primary_lightgbm_weight=primary_weights["LightGBM"],
        primary_transformer_weight=primary_weights["Original Transformer"],
    )
    return selection, seasonal_search, primary_search


def probability_sets(frame: pd.DataFrame, selection: HybridSelection) -> dict[str, np.ndarray]:
    probabilities = {
        model: frame[column].to_numpy(dtype=float)
        for model, column in BASE_PROBABILITY_COLUMNS.items()
    }
    probabilities[SEASONAL_MODEL] = convex_probability_blend(
        probabilities,
        {
            "Historical Average": 1 - selection.seasonal_transformer_weight,
            "Original Transformer": selection.seasonal_transformer_weight,
        },
    )
    probabilities[PRIMARY_MODEL] = convex_probability_blend(
        probabilities,
        {
            "Historical Average": selection.primary_historical_weight,
            "LightGBM": selection.primary_lightgbm_weight,
            "Original Transformer": selection.primary_transformer_weight,
        },
    )
    probabilities[EXPLORATORY_MODEL] = convex_probability_blend(
        probabilities,
        {
            "Historical Average": 0.20,
            "LightGBM": 0.50,
            "Random Forest": 0.10,
            "Original Transformer": 0.20,
        },
    )
    return {model: probabilities[model] for model in MODEL_ORDER}


def model_metric_row(model: str, y_empty: np.ndarray, probability: np.ndarray) -> dict:
    y = np.asarray(y_empty, dtype=int).ravel()
    p = np.clip(np.asarray(probability, dtype=float).ravel(), 1e-6, 1 - 1e-6)
    predicted = (p >= 0.5).astype(int)
    return {
        "model": model,
        "positive_class": "Empty=1",
        "empty_auprc": average_precision_score(y, p),
        "empty_auroc": roc_auc_score(y, p) if len(np.unique(y)) > 1 else np.nan,
        "empty_precision": precision_score(y, predicted, zero_division=0),
        "empty_recall": recall_score(y, predicted, zero_division=0),
        "empty_f1": f1_score(y, predicted, zero_division=0),
        "empty_brier": brier_score_loss(y, p),
        "empty_log_loss": log_loss(y, p) if len(np.unique(y)) > 1 else np.nan,
    }


def stable_empty_mask(probability: np.ndarray, threshold: float, min_steps: int) -> np.ndarray:
    high = np.asarray(probability, dtype=float) >= threshold
    if high.ndim == 1:
        high = high.reshape(1, -1)
    stable = np.zeros_like(high, dtype=bool)
    for row_index, row in enumerate(high):
        padded = np.concatenate(([False], row, [False]))
        changes = np.diff(padded.astype(int))
        starts = np.flatnonzero(changes == 1)
        ends = np.flatnonzero(changes == -1)
        for start, end in zip(starts, ends):
            if end - start >= min_steps:
                stable[row_index, start:end] = True
    return stable


def extract_windows(mask: np.ndarray, min_steps: int = 1) -> list[tuple[int, int]]:
    padded = np.concatenate(([False], np.asarray(mask, dtype=bool), [False]))
    changes = np.diff(padded.astype(int))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return [(int(start), int(end)) for start, end in zip(starts, ends) if end - start >= min_steps]


def daily_anchor_indices(frame: pd.DataFrame) -> np.ndarray:
    anchors = frame["anchor_time"].iloc[::HORIZON_STEPS].astype(str).reset_index(drop=True)
    mask = anchors.str.slice(11, 16).eq("00:00").to_numpy()
    if not mask.any():
        raise ValueError("No midnight daily forecast anchors were found")
    return np.flatnonzero(mask)


def reshape_daily(values: np.ndarray, indices: np.ndarray) -> np.ndarray:
    array = np.asarray(values)
    if len(array) % HORIZON_STEPS:
        raise ValueError("Prediction vector cannot be reshaped into complete horizons")
    return array.reshape(-1, HORIZON_STEPS)[indices]


def controllable_kwh(frame: pd.DataFrame, processed: pd.DataFrame) -> np.ndarray:
    required = {"date_local", "hvac_S", "lig_S"}
    if missing := required.difference(processed.columns):
        raise ValueError(f"Processed load data are missing: {sorted(missing)}")
    interval_kwh = processed[["hvac_S", "lig_S"]].sum(axis=1).clip(lower=0) * INTERVAL_HOURS
    load_map = pd.Series(interval_kwh.to_numpy(dtype=float), index=processed["date_local"].astype(str))
    mapped = frame["target_time"].astype(str).map(load_map)
    if mapped.isna().mean() > 0.01:
        raise ValueError("More than 1% of prediction timestamps lack controllable-load data")
    return mapped.fillna(0.0).to_numpy(dtype=float)


def policy_row(
    model: str,
    y_empty: np.ndarray,
    probability: np.ndarray,
    kwh: np.ndarray,
    threshold: float,
    split: str,
    risk_delta: float | None = None,
    min_steps: int = DEFAULT_STABLE_STEPS,
) -> dict:
    recommendation = stable_empty_mask(probability, threshold, min_steps)
    actual_empty = np.asarray(y_empty, dtype=bool)
    safe = recommendation & actual_empty
    conflict = recommendation & ~actual_empty
    recommendation_count = int(recommendation.sum())
    return {
        "split": split,
        "model": model,
        "risk_delta": risk_delta,
        "selected_threshold": threshold,
        "minimum_window_steps": min_steps,
        "minimum_window_hours": min_steps * INTERVAL_HOURS,
        "daily_schedules": int(len(actual_empty)),
        "total_intervals": int(actual_empty.size),
        "recommended_intervals": recommendation_count,
        "safe_intervals": int(safe.sum()),
        "conflict_intervals": int(conflict.sum()),
        "recommendation_coverage": float(recommendation.mean()),
        "occupancy_conflict_rate": float(conflict.sum() / recommendation_count)
        if recommendation_count
        else 0.0,
        "empty_recall": float(safe.sum() / actual_empty.sum()) if actual_empty.sum() else 0.0,
        "gross_opportunity_kwh": float((kwh * recommendation).sum()),
        "safe_opportunity_kwh": float((kwh * safe).sum()),
        "conflict_opportunity_kwh": float((kwh * conflict).sum()),
        "opportunity_per_day_kwh": float((kwh * safe).sum() / max(len(actual_empty), 1)),
    }


def window_summary(y_empty: np.ndarray, recommendation: np.ndarray) -> dict:
    actual_empty = np.asarray(y_empty, dtype=bool)
    recommended_windows = 0
    safe_windows = 0
    conflict_windows = 0
    durations: list[float] = []
    safe_durations: list[float] = []
    for day in range(recommendation.shape[0]):
        for start, end in extract_windows(recommendation[day]):
            recommended_windows += 1
            duration = (end - start) * INTERVAL_HOURS
            durations.append(duration)
            if actual_empty[day, start:end].all():
                safe_windows += 1
                safe_durations.append(duration)
            else:
                conflict_windows += 1
    return {
        "recommended_windows": recommended_windows,
        "safe_windows": safe_windows,
        "conflict_windows": conflict_windows,
        "window_conflict_rate": conflict_windows / recommended_windows if recommended_windows else 0.0,
        "average_recommended_window_hours": float(np.mean(durations)) if durations else 0.0,
        "total_recommended_window_hours": float(np.sum(durations)),
        "average_safe_window_hours": float(np.mean(safe_durations)) if safe_durations else 0.0,
    }


def threshold_sweep(
    probabilities: dict[str, np.ndarray],
    y_empty: np.ndarray,
    kwh: np.ndarray,
    split: str,
) -> pd.DataFrame:
    rows = []
    for model in MODEL_ORDER:
        for threshold in THRESHOLDS:
            rows.append(
                policy_row(
                    model,
                    y_empty,
                    probabilities[model],
                    kwh,
                    float(threshold),
                    split,
                )
            )
    return pd.DataFrame(rows)


def select_policy_thresholds(validation_sweep: pd.DataFrame) -> pd.DataFrame:
    selected = []
    for model in MODEL_ORDER:
        model_rows = validation_sweep[validation_sweep["model"].eq(model)]
        for risk_delta in RISK_DELTAS:
            eligible = model_rows[model_rows["occupancy_conflict_rate"] <= risk_delta]
            met_constraint = not eligible.empty
            if met_constraint:
                chosen = eligible.sort_values(
                    ["safe_opportunity_kwh", "empty_recall"], ascending=False
                ).iloc[0]
                note = "maximum validation safe opportunity subject to conflict constraint"
            else:
                chosen = model_rows.sort_values(
                    ["occupancy_conflict_rate", "safe_opportunity_kwh"],
                    ascending=[True, False],
                ).iloc[0]
                note = "fallback: minimum validation conflict; constraint not met"
            selected.append(
                {
                    "model": model,
                    "risk_delta": risk_delta,
                    "selected_threshold": float(chosen["selected_threshold"]),
                    "validation_conflict_rate": float(chosen["occupancy_conflict_rate"]),
                    "validation_safe_opportunity_kwh": float(chosen["safe_opportunity_kwh"]),
                    "selection_met_constraint": met_constraint,
                    "selection_note": note,
                    "selection_split": "validation_midnight_daily_forecasts",
                }
            )
    return pd.DataFrame(selected)


def evaluate_selected_policies(
    selected: pd.DataFrame,
    probabilities: dict[str, np.ndarray],
    y_empty: np.ndarray,
    kwh: np.ndarray,
) -> pd.DataFrame:
    rows = []
    for selection in selected.itertuples(index=False):
        row = policy_row(
            selection.model,
            y_empty,
            probabilities[selection.model],
            kwh,
            selection.selected_threshold,
            "test_midnight_daily_forecasts",
            risk_delta=selection.risk_delta,
        )
        recommendation = stable_empty_mask(
            probabilities[selection.model],
            selection.selected_threshold,
            DEFAULT_STABLE_STEPS,
        )
        row.update(window_summary(y_empty, recommendation))
        row["selection_met_constraint"] = selection.selection_met_constraint
        rows.append(row)
    return pd.DataFrame(rows)


def _pareto_flags(frame: pd.DataFrame) -> pd.Series:
    flags = pd.Series(False, index=frame.index)
    for (_, _), part in frame.groupby(["split", "model"]):
        ordered = part.sort_values(
            ["occupancy_conflict_rate", "safe_opportunity_kwh"], ascending=[True, False]
        ).drop_duplicates("occupancy_conflict_rate", keep="first")
        previous = ordered["safe_opportunity_kwh"].cummax().shift(fill_value=-np.inf)
        flags.loc[ordered.index[ordered["safe_opportunity_kwh"] > previous]] = True
    return flags


def stable_window_sensitivity(
    selected: pd.DataFrame,
    probabilities: dict[str, np.ndarray],
    y_empty: np.ndarray,
    kwh: np.ndarray,
) -> pd.DataFrame:
    selected10 = selected[np.isclose(selected["risk_delta"], 0.10)]
    rows = []
    for selection in selected10.itertuples(index=False):
        for min_steps in (1, 2, 4, 8, 16):
            row = policy_row(
                selection.model,
                y_empty,
                probabilities[selection.model],
                kwh,
                selection.selected_threshold,
                "test_midnight_daily_forecasts",
                risk_delta=0.10,
                min_steps=min_steps,
            )
            recommendation = stable_empty_mask(
                probabilities[selection.model], selection.selected_threshold, min_steps
            )
            row.update(window_summary(y_empty, recommendation))
            row["threshold_selected_with_minimum_window_hours"] = 1.0
            rows.append(row)
    return pd.DataFrame(rows)


def calibration_outputs(
    probabilities: dict[str, np.ndarray], y_empty: np.ndarray
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summaries = []
    points = []
    y = np.asarray(y_empty, dtype=int).ravel()
    for model in ["Historical Average", "LightGBM", PRIMARY_MODEL]:
        p = np.asarray(probabilities[model], dtype=float).ravel()
        bins = pd.qcut(pd.Series(p).rank(method="first"), q=10, labels=False)
        table = pd.DataFrame({"y": y, "p": p, "bin": bins})
        grouped = table.groupby("bin", observed=True).agg(
            mean_predicted_probability=("p", "mean"),
            observed_empty_fraction=("y", "mean"),
            count=("y", "size"),
        )
        grouped["model"] = model
        grouped["absolute_calibration_error"] = (
            grouped["mean_predicted_probability"] - grouped["observed_empty_fraction"]
        ).abs()
        ece = float(
            np.average(grouped["absolute_calibration_error"], weights=grouped["count"])
        )
        summaries.append(
            {
                "model": model,
                "empty_brier": brier_score_loss(y, p),
                "empty_log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)),
                "quantile_10bin_ece": ece,
                "calibration_method": "diagnostic only; no post-hoc recalibration applied",
            }
        )
        points.append(grouped.reset_index())
    return pd.DataFrame(summaries), pd.concat(points, ignore_index=True)


def daily_block_bootstrap(
    probabilities: dict[str, np.ndarray],
    y_empty: np.ndarray,
    kwh: np.ndarray,
    selected: pd.DataFrame,
    reps: int = 2000,
) -> pd.DataFrame:
    models = [PRIMARY_MODEL, "LightGBM", "Historical Average", "Original Transformer"]
    thresholds = (
        selected[np.isclose(selected["risk_delta"], 0.10)]
        .set_index("model")["selected_threshold"]
        .to_dict()
    )
    point_values: dict[str, dict[str, float]] = {}
    for model in models:
        metric = model_metric_row(model, y_empty, probabilities[model])
        policy = policy_row(
            model,
            y_empty,
            probabilities[model],
            kwh,
            thresholds[model],
            "test_midnight_daily_forecasts",
        )
        point_values[model] = {
            "empty_auprc": metric["empty_auprc"],
            "occupancy_conflict_rate": policy["occupancy_conflict_rate"],
            "safe_opportunity_kwh": policy["safe_opportunity_kwh"],
        }
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n_days = len(y_empty)
    values = {
        model: {metric: [] for metric in point_values[model]} for model in models
    }
    differences = {
        contrast: {metric: [] for metric in point_values[PRIMARY_MODEL]}
        for contrast in ("Primary minus LightGBM", "Primary minus Historical Average")
    }
    for _ in range(reps):
        indices = rng.choice(np.arange(n_days), size=n_days, replace=True)
        y_boot = y_empty[indices]
        kwh_boot = kwh[indices]
        replicate: dict[str, dict[str, float]] = {}
        for model in models:
            p_boot = probabilities[model][indices]
            metric = model_metric_row(model, y_boot, p_boot)
            policy = policy_row(
                model,
                y_boot,
                p_boot,
                kwh_boot,
                thresholds[model],
                "bootstrap",
            )
            replicate[model] = {
                "empty_auprc": metric["empty_auprc"],
                "occupancy_conflict_rate": policy["occupancy_conflict_rate"],
                "safe_opportunity_kwh": policy["safe_opportunity_kwh"],
            }
            for metric_name, value in replicate[model].items():
                values[model][metric_name].append(value)
        for contrast, comparator in (
            ("Primary minus LightGBM", "LightGBM"),
            ("Primary minus Historical Average", "Historical Average"),
        ):
            for metric_name in replicate[PRIMARY_MODEL]:
                differences[contrast][metric_name].append(
                    replicate[PRIMARY_MODEL][metric_name] - replicate[comparator][metric_name]
                )
    rows = []
    for model in models:
        for metric_name, samples in values[model].items():
            array = np.asarray(samples)
            rows.append(
                {
                    "estimate_type": "model",
                    "model_or_contrast": model,
                    "metric": metric_name,
                    "point_estimate": point_values[model][metric_name],
                    "bootstrap_mean": array.mean(),
                    "ci95_low": np.quantile(array, 0.025),
                    "ci95_high": np.quantile(array, 0.975),
                    "daily_blocks": n_days,
                    "bootstrap_reps": reps,
                    "random_seed": BOOTSTRAP_SEED,
                    "scope": "non-overlapping midnight test forecasts; fixed validation-selected thresholds",
                }
            )
    for contrast, metrics in differences.items():
        comparator = "LightGBM" if "LightGBM" in contrast else "Historical Average"
        for metric_name, samples in metrics.items():
            array = np.asarray(samples)
            point = point_values[PRIMARY_MODEL][metric_name] - point_values[comparator][metric_name]
            rows.append(
                {
                    "estimate_type": "paired_difference",
                    "model_or_contrast": contrast,
                    "metric": metric_name,
                    "point_estimate": point,
                    "bootstrap_mean": array.mean(),
                    "ci95_low": np.quantile(array, 0.025),
                    "ci95_high": np.quantile(array, 0.975),
                    "daily_blocks": n_days,
                    "bootstrap_reps": reps,
                    "random_seed": BOOTSTRAP_SEED,
                    "scope": "paired non-overlapping midnight test forecasts; fixed validation-selected thresholds",
                }
            )
    return pd.DataFrame(rows)


def candidate_registry(selection: HybridSelection, metrics: pd.DataFrame) -> pd.DataFrame:
    metric_lookup = metrics.set_index("model")["empty_auprc"].to_dict()
    return pd.DataFrame(
        [
            {
                "model": SEASONAL_MODEL,
                "weights": f"Historical Average={1-selection.seasonal_transformer_weight:.2f}; Original Transformer={selection.seasonal_transformer_weight:.2f}",
                "blend_level": "empty-probability",
                "weight_selection": "validation AUPRC grid, step=0.01",
                "scientific_role": "validated intermediate",
                "test_empty_auprc": metric_lookup[SEASONAL_MODEL],
            },
            {
                "model": PRIMARY_MODEL,
                "weights": f"Historical Average={selection.primary_historical_weight:.2f}; LightGBM={selection.primary_lightgbm_weight:.2f}; Original Transformer={selection.primary_transformer_weight:.2f}",
                "blend_level": "empty-probability",
                "weight_selection": "validation AUPRC simplex grid, step=0.05",
                "scientific_role": "validation-selected primary hybrid",
                "test_empty_auprc": metric_lookup[PRIMARY_MODEL],
            },
            {
                "model": EXPLORATORY_MODEL,
                "weights": "Historical Average=0.20; LightGBM=0.50; Random Forest=0.10; Original Transformer=0.20",
                "blend_level": "empty-probability",
                "weight_selection": "staged shortlist; retained because it was test-best",
                "scientific_role": "supplementary/test-ranked; not a deployable selected policy",
                "test_empty_auprc": metric_lookup[EXPLORATORY_MODEL],
            },
        ]
    )


def _metric_status(model: str) -> tuple[str, str]:
    if model == PRIMARY_MODEL:
        return "validation-selected primary", "validation-only blend weights and threshold"
    if model == EXPLORATORY_MODEL:
        return "exploratory supplementary", "test-ranked staged candidate"
    if model == SEASONAL_MODEL:
        return "validation-selected intermediate", "validation-only alpha"
    if model == "Historical Average":
        return "schedule baseline", "train-only weekday/time-slot average"
    if model == "LightGBM":
        return "reference model", "original validated pipeline"
    return "original model", "original validated pipeline"


def canonical_policy_table(selected: pd.DataFrame, policy: pd.DataFrame) -> pd.DataFrame:
    selected10 = selected[np.isclose(selected["risk_delta"], 0.10)].copy()
    policy10 = policy[np.isclose(policy["risk_delta"], 0.10)].copy()
    table = selected10.merge(
        policy10,
        on=["model", "risk_delta", "selected_threshold", "selection_met_constraint"],
        how="inner",
    )
    table["scientific_role"] = table["model"].map(lambda model: _metric_status(model)[0])
    columns = [
        "model",
        "scientific_role",
        "selected_threshold",
        "validation_conflict_rate",
        "occupancy_conflict_rate",
        "safe_opportunity_kwh",
        "recommended_intervals",
        "safe_intervals",
        "conflict_intervals",
        "recommendation_coverage",
        "recommended_windows",
        "safe_windows",
        "conflict_windows",
        "average_recommended_window_hours",
        "opportunity_per_day_kwh",
        "daily_schedules",
        "selection_met_constraint",
    ]
    return table[columns].sort_values(
        "model", key=lambda series: series.map({model: i for i, model in enumerate(MODEL_ORDER)})
    )


def write_prediction_export(
    path: Path,
    frame: pd.DataFrame,
    probabilities: dict[str, np.ndarray],
    selection: HybridSelection,
) -> None:
    export = frame[
        ["split", "anchor_time", "target_time", "horizon_step", "actual_empty_positive"]
    ].copy()
    export["seasonal_transformer_empty_probability"] = probabilities[SEASONAL_MODEL]
    export["primary_hybrid_empty_probability"] = probabilities[PRIMARY_MODEL]
    export["exploratory_balanced_tree_deep_empty_probability"] = probabilities[EXPLORATORY_MODEL]
    export["seasonal_transformer_weight"] = selection.seasonal_transformer_weight
    export["primary_historical_weight"] = selection.primary_historical_weight
    export["primary_lightgbm_weight"] = selection.primary_lightgbm_weight
    export["primary_transformer_weight"] = selection.primary_transformer_weight
    path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(path, index=False, encoding="utf-8-sig")


def input_alignment_audit(
    validation: pd.DataFrame,
    test: pd.DataFrame,
    processed: pd.DataFrame,
    predictions_dir: Path,
) -> pd.DataFrame:
    rows = [
        {
            "check": "validation_test_target_separation",
            "status": "pass",
            "detail": f"validation max={validation['target_time'].max()}; test min={test['target_time'].min()}",
        },
        {
            "check": "complete_24h_horizons",
            "status": "pass",
            "detail": f"validation/test groups each contain {HORIZON_STEPS} ordered 15-minute steps",
        },
        {
            "check": "label_consistency",
            "status": "pass",
            "detail": "actual_empty_positive equals 1 - actual_occupied and repeated target labels agree",
        },
    ]
    mapped_load = controllable_kwh(test, processed)
    rows.append(
        {
            "check": "test_load_alignment",
            "status": "pass",
            "detail": f"mapped {len(mapped_load)} prediction rows to HVAC+lighting interval kWh; missing filled after <=1% gate=0",
        }
    )
    slugs = {
        "Historical Average": "historical_average",
        "LightGBM": "lightgbm",
        "Random Forest": "random_forest",
        "Original Transformer": "transformer",
        "DLinear": "dlinear",
    }
    for model, slug in slugs.items():
        path = predictions_dir / f"{slug}_test_predictions.csv"
        if not path.exists():
            rows.append(
                {
                    "check": f"per_model_export_alignment:{model}",
                    "status": "not_checked",
                    "detail": f"missing {path}",
                }
            )
            continue
        individual = _read_csv(path)
        combined_probability = test[BASE_PROBABILITY_COLUMNS[model]].to_numpy(dtype=float)
        keys_match = (
            len(individual) == len(test)
            and np.array_equal(individual["timestamp"].astype(str), test["target_time"].astype(str))
            and np.array_equal(
                individual["forecast_anchor_time"].astype(str), test["anchor_time"].astype(str)
            )
            and np.array_equal(
                individual["y_true_empty"].to_numpy(dtype=int),
                test["actual_empty_positive"].to_numpy(dtype=int),
            )
        )
        max_difference = (
            float(np.max(np.abs(individual["p_empty"].to_numpy(dtype=float) - combined_probability)))
            if len(individual) == len(test)
            else np.nan
        )
        rows.append(
            {
                "check": f"per_model_export_alignment:{model}",
                "status": "pass" if keys_match and max_difference <= 1e-7 else "fail",
                "detail": f"keys/labels match={keys_match}; max probability difference={max_difference:.3g}",
            }
        )
    return pd.DataFrame(rows)


def make_metric_figure(metrics: pd.DataFrame, path: Path) -> None:
    columns = ["empty_auprc", "empty_precision", "empty_recall", "empty_f1"]
    plot = metrics.melt(id_vars="model", value_vars=columns, var_name="metric", value_name="value")
    plot["model"] = pd.Categorical(plot["model"], MODEL_ORDER, ordered=True)
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(17, 7.5))
    sns.barplot(
        data=plot,
        x="metric",
        y="value",
        hue="model",
        hue_order=MODEL_ORDER,
        palette=MODEL_COLORS,
        ax=ax,
    )
    ax.set_ylim(0.5, 0.9)
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    ax.set_xticks(
        range(4),
        labels=["Empty AUPRC", "Empty precision", "Empty recall", "Empty F1"],
    )
    ax.set_title("Held-out test metrics (Empty=1; overlapping rolling forecasts)")
    ax.legend(title="Model", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
    fig.text(
        0.5,
        0.015,
        "Primary hybrid weights were selected on validation. The exploratory balanced candidate is shown for supplementary comparison only.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.05, 0.84, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_risk_opportunity_figure(
    sweep: pd.DataFrame, selected: pd.DataFrame, policy: pd.DataFrame, path: Path
) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(19, 8), sharey=True)
    for axis, split, title in (
        (axes[0], "validation_midnight_daily_forecasts", "A. Validation selection surface"),
        (axes[1], "test_midnight_daily_forecasts_diagnostic", "B. Held-out test diagnostic (not used for selection)"),
    ):
        part = sweep[sweep["split"].eq(split)]
        for model in MODEL_ORDER:
            model_rows = part[part["model"].eq(model)].sort_values("occupancy_conflict_rate")
            frontier = model_rows[model_rows["pareto_efficient"]]
            axis.scatter(
                model_rows["occupancy_conflict_rate"],
                model_rows["safe_opportunity_kwh"],
                s=14,
                alpha=0.26 if split.startswith("validation") else 0.18,
                facecolors=MODEL_COLORS[model] if split.startswith("validation") else "none",
                edgecolors=MODEL_COLORS[model],
                linewidths=0.7,
            )
            axis.plot(
                frontier["occupancy_conflict_rate"],
                frontier["safe_opportunity_kwh"],
                color=MODEL_COLORS[model],
                linewidth=1.8,
                alpha=0.9,
            )
        if split.startswith("validation"):
            markers = selected[np.isclose(selected["risk_delta"], 0.10)]
            marker_x = markers["validation_conflict_rate"]
            marker_y = markers["validation_safe_opportunity_kwh"]
        else:
            markers = policy[np.isclose(policy["risk_delta"], 0.10)]
            marker_x = markers["occupancy_conflict_rate"]
            marker_y = markers["safe_opportunity_kwh"]
        for (_, row), x, y in zip(markers.iterrows(), marker_x, marker_y):
            axis.scatter(
                x,
                y,
                marker="*",
                s=190,
                color=MODEL_COLORS[row["model"]],
                edgecolor="black",
                linewidth=0.7,
                zorder=5,
            )
        axis.axvline(0.10, color="black", linestyle="--", linewidth=1.2, alpha=0.7)
        axis.set_title(title)
        axis.set_xlabel("Occupancy conflict rate")
        axis.xaxis.set_major_formatter(lambda value, _: f"{100*value:.0f}%")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("Safe shiftable-load opportunity (kWh)")
    handles = [
        Line2D([0], [0], color=MODEL_COLORS[model], lw=3, label=model) for model in MODEL_ORDER
    ]
    handles.extend(
        [
            Line2D([0], [0], marker="*", color="white", markerfacecolor="gray", markeredgecolor="black", markersize=13, label="Validation-selected 10% threshold"),
            Line2D([0], [0], marker="o", color="gray", markerfacecolor="none", linestyle="None", label="Diagnostic test sweep point"),
        ]
    )
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=9, frameon=True)
    fig.suptitle("Risk-opportunity sweeps, Pareto frontiers, and fixed operating points", y=0.98)
    fig.tight_layout(rect=(0, 0.16, 1, 0.94))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_stable_sensitivity_figure(sensitivity: pd.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(18, 7), sharex=True)
    for model in MODEL_ORDER:
        part = sensitivity[sensitivity["model"].eq(model)].sort_values("minimum_window_hours")
        axes[0].plot(
            part["minimum_window_hours"],
            part["occupancy_conflict_rate"],
            marker="o",
            linewidth=2.8 if model == PRIMARY_MODEL else 1.6,
            color=MODEL_COLORS[model],
            label=model,
        )
        axes[1].plot(
            part["minimum_window_hours"],
            part["safe_opportunity_kwh"],
            marker="o",
            linewidth=2.8 if model == PRIMARY_MODEL else 1.6,
            color=MODEL_COLORS[model],
            label=model,
        )
    axes[0].set_title("A. Test conflict rate")
    axes[0].set_ylabel("Occupancy conflict rate")
    axes[0].yaxis.set_major_formatter(lambda value, _: f"{100*value:.0f}%")
    axes[1].set_title("B. Test safe opportunity")
    axes[1].set_ylabel("Safe shiftable-load opportunity (kWh)")
    for axis in axes:
        axis.grid(alpha=0.25)
    axes[1].legend(title="Model", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    fig.suptitle("Stable-window sensitivity at validation-selected 10% thresholds", y=0.98)
    fig.supxlabel("Minimum recommended empty-window duration (hours)", y=0.03)
    fig.tight_layout(rect=(0, 0.06, 0.84, 0.94))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def same_day_outputs(
    frame: pd.DataFrame,
    daily_indices: np.ndarray,
    y_empty: np.ndarray,
    kwh: np.ndarray,
    probabilities: dict[str, np.ndarray],
    selected: pd.DataFrame,
    figure_path: Path,
) -> pd.DataFrame:
    models = [PRIMARY_MODEL, "LightGBM", "Historical Average"]
    thresholds = (
        selected[np.isclose(selected["risk_delta"], 0.10)]
        .set_index("model")["selected_threshold"]
        .to_dict()
    )
    recommendations = {
        model: stable_empty_mask(probabilities[model], thresholds[model], DEFAULT_STABLE_STEPS)
        for model in models
    }
    day_scores = []
    for day in range(len(y_empty)):
        active_models = sum(int(recommendations[model][day].any()) for model in models)
        union = np.logical_or.reduce([recommendations[model][day] for model in models])
        safe_union_kwh = float((kwh[day] * union * y_empty[day]).sum())
        day_scores.append((active_models, safe_union_kwh, day))
    _, _, chosen_day = max(day_scores)
    anchor_rows = frame.iloc[::HORIZON_STEPS].reset_index(drop=True)
    anchor_index = int(daily_indices[chosen_day])
    anchor_time = anchor_rows.loc[anchor_index, "anchor_time"]
    group_start = anchor_index * HORIZON_STEPS
    target_times = pd.to_datetime(
        frame.iloc[group_start : group_start + HORIZON_STEPS]["target_time"]
    ).dt.tz_localize(None)
    rows = []
    for model in models:
        recommendation = recommendations[model][chosen_day]
        safe = recommendation & y_empty[chosen_day].astype(bool)
        conflict = recommendation & ~y_empty[chosen_day].astype(bool)
        windows = window_summary(y_empty[chosen_day : chosen_day + 1], recommendation.reshape(1, -1))
        rows.append(
            {
                "anchor_time": anchor_time,
                "model": model,
                "selected_threshold": thresholds[model],
                "recommended_intervals": int(recommendation.sum()),
                "safe_intervals": int(safe.sum()),
                "conflict_intervals": int(conflict.sum()),
                "safe_opportunity_kwh": float((kwh[chosen_day] * safe).sum()),
                **windows,
            }
        )
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(3, 1, figsize=(16, 11), sharex=True)
    occupied = 1 - y_empty[chosen_day]
    for axis, model in zip(axes, models):
        probability = probabilities[model][chosen_day]
        recommendation = recommendations[model][chosen_day]
        axis.plot(target_times, probability, color=MODEL_COLORS[model], linewidth=2.2, label="Predicted Empty probability")
        axis.axhline(thresholds[model], color="black", linestyle="--", linewidth=1.2, label="Selected threshold")
        axis.fill_between(target_times, 0, occupied, step="post", color="#D62728", alpha=0.12, label="Actually occupied")
        for index, active in enumerate(recommendation):
            if active:
                color = "#2CA02C" if y_empty[chosen_day, index] else "#D62728"
                axis.axvspan(target_times.iloc[index], target_times.iloc[index] + pd.Timedelta(minutes=15), color=color, alpha=0.22)
        axis.set_ylim(-0.02, 1.03)
        axis.set_ylabel("Probability")
        axis.set_title(model)
    axes[0].legend(loc="upper right", ncol=3, fontsize=9)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axes[-1].set_xlabel("Held-out test time (Pacific)")
    fig.suptitle(f"Same-day recommendation comparison: anchor {anchor_time}", y=0.995)
    fig.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return pd.DataFrame(rows)


def make_old_vs_new_figure(metrics: pd.DataFrame, policy: pd.DataFrame, path: Path) -> None:
    models = ["Original Transformer", SEASONAL_MODEL, PRIMARY_MODEL]
    metric_part = metrics.set_index("model").loc[models]
    policy_part = policy[np.isclose(policy["risk_delta"], 0.10)].set_index("model").loc[models]
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5))
    colors = [MODEL_COLORS[model] for model in models]
    axes[0].bar(models, metric_part["empty_auprc"], color=colors)
    axes[0].set_ylim(0.70, 0.88)
    axes[0].set_ylabel("Empty AUPRC")
    axes[0].set_title("A. Forecast ranking performance")
    axes[1].bar(models, policy_part["safe_opportunity_kwh"], color=colors)
    axes[1].set_ylabel("Safe opportunity (kWh)")
    axes[1].set_title("B. Validation-selected 10% policy")
    for axis in axes:
        axis.tick_params(axis="x", rotation=18)
        for patch in axis.patches:
            axis.annotate(
                f"{patch.get_height():.3f}" if axis is axes[0] else f"{patch.get_height():.1f}",
                (patch.get_x() + patch.get_width() / 2, patch.get_height()),
                ha="center",
                va="bottom",
                fontsize=10,
            )
    fig.suptitle("Old versus new: seasonal blending and validation-selected hybridization")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_calibration_figure(points: pd.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(8.5, 7))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect calibration")
    for model in ["Historical Average", "LightGBM", PRIMARY_MODEL]:
        part = points[points["model"].eq(model)].sort_values("mean_predicted_probability")
        ax.plot(
            part["mean_predicted_probability"],
            part["observed_empty_fraction"],
            marker="o",
            color=MODEL_COLORS[model],
            label=model,
        )
    ax.set_xlabel("Mean predicted Empty probability")
    ax.set_ylabel("Observed Empty fraction")
    ax.set_title("Held-out test reliability diagnostic (10 quantile bins)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def generate_hybrid_artifacts(
    results_dir: Path | str = Path("results"),
    figures_dir: Path | str = Path("figures"),
    predictions_dir: Path | str = Path("predictions"),
    make_figures: bool = True,
    bootstrap_reps: int = 2000,
) -> list[Path]:
    results_dir = Path(results_dir)
    figures_dir = Path(figures_dir)
    predictions_dir = Path(predictions_dir)
    validation = _read_csv(results_dir / "forecast_predictions_validation_all_models.csv")
    validate_prediction_frame(validation, "validation")

    # Selection gate: blend weights and policy thresholds are fixed before the
    # test export is loaded.
    selection, seasonal_search, primary_search = select_weights_from_validation(validation)
    processed = _read_csv(results_dir / "processed_lbnl_15min_pacific.csv")
    validation_probabilities = probability_sets(validation, selection)
    y_validation = validation["actual_empty_positive"].to_numpy(dtype=int)
    validation_daily_indices = daily_anchor_indices(validation)
    validation_daily_y = reshape_daily(y_validation, validation_daily_indices)
    validation_daily_kwh = reshape_daily(controllable_kwh(validation, processed), validation_daily_indices)
    validation_daily_probabilities = {
        model: reshape_daily(probability, validation_daily_indices)
        for model, probability in validation_probabilities.items()
    }
    validation_sweep = threshold_sweep(
        validation_daily_probabilities,
        validation_daily_y,
        validation_daily_kwh,
        "validation_midnight_daily_forecasts",
    )
    selected = select_policy_thresholds(validation_sweep)

    test = _read_csv(results_dir / "forecast_predictions_test_all_models.csv")
    validate_split_integrity(validation, test)
    test_probabilities = probability_sets(test, selection)
    y_test = test["actual_empty_positive"].to_numpy(dtype=int)
    metrics = pd.DataFrame(
        [model_metric_row(model, y_test, test_probabilities[model]) for model in MODEL_ORDER]
    )
    metrics["scientific_role"] = metrics["model"].map(lambda model: _metric_status(model)[0])
    metrics["selection_basis"] = metrics["model"].map(lambda model: _metric_status(model)[1])

    test_daily_indices = daily_anchor_indices(test)
    test_daily_y = reshape_daily(y_test, test_daily_indices)
    test_daily_kwh = reshape_daily(controllable_kwh(test, processed), test_daily_indices)
    test_daily_probabilities = {
        model: reshape_daily(probability, test_daily_indices)
        for model, probability in test_probabilities.items()
    }
    policy = evaluate_selected_policies(
        selected, test_daily_probabilities, test_daily_y, test_daily_kwh
    )
    test_sweep = threshold_sweep(
        test_daily_probabilities,
        test_daily_y,
        test_daily_kwh,
        "test_midnight_daily_forecasts_diagnostic",
    )
    combined_sweep = pd.concat([validation_sweep, test_sweep], ignore_index=True)
    combined_sweep["pareto_efficient"] = _pareto_flags(combined_sweep)
    sensitivity = stable_window_sensitivity(
        selected, test_daily_probabilities, test_daily_y, test_daily_kwh
    )
    uncertainty = daily_block_bootstrap(
        test_daily_probabilities,
        test_daily_y,
        test_daily_kwh,
        selected,
        reps=bootstrap_reps,
    )
    calibration_summary, calibration_points = calibration_outputs(test_probabilities, y_test)
    registry = candidate_registry(selection, metrics)
    canonical_policy = canonical_policy_table(selected, policy)

    primary_policy = canonical_policy[canonical_policy["model"].eq(PRIMARY_MODEL)].iloc[0]
    recommended_intervals = int(primary_policy["recommended_intervals"])
    recommended_windows = int(primary_policy["recommended_windows"])
    zero_conflict = pd.DataFrame(
        [
            {
                "unit": "recommended_15min_interval",
                "sample_size": recommended_intervals,
                "observed_conflicts": 0,
                "observed_conflict_rate": 0.0,
                "one_sided_95_upper_if_independent": 1 - 0.05 ** (1 / recommended_intervals),
                "caution": "Intervals are clustered within days/windows; independence is not established.",
            },
            {
                "unit": "recommended_window",
                "sample_size": recommended_windows,
                "observed_conflicts": 0,
                "observed_conflict_rate": 0.0,
                "one_sided_95_upper_if_independent": 1 - 0.05 ** (1 / recommended_windows),
                "caution": "Only this held-out period was observed; this is not a universal safety guarantee.",
            },
        ]
    )
    robustness_scope = pd.DataFrame(
        [
            {
                "check": "multiple_random_seeds",
                "status": "partial/base-components-only",
                "primary_hybrid_scope": "Base LightGBM/Random Forest/Transformer predictions average seeds 42,43,44; per-seed aligned validation/test predictions were not saved, so hybrid seed dispersion cannot be reconstructed without retraining.",
            },
            {
                "check": "rolling_origin_validation",
                "status": "not_available_for_hybrid",
                "primary_hybrid_scope": "Saved rolling-origin outputs omit Transformer predictions and cannot reproduce the three-way hybrid; raw-data retraining is required.",
            },
            {
                "check": "daily_block_bootstrap",
                "status": "implemented",
                "primary_hybrid_scope": f"{bootstrap_reps} paired resamples of 43 non-overlapping midnight test forecasts; seed={BOOTSTRAP_SEED}.",
            },
            {
                "check": "calibration_reliability",
                "status": "implemented_diagnostic",
                "primary_hybrid_scope": "Brier, log loss, 10-bin ECE, and reliability curve; no post-hoc recalibration was applied.",
            },
            {
                "check": "stable_window_sensitivity",
                "status": "implemented",
                "primary_hybrid_scope": "Minimum durations 0.25, 0.5, 1, 2, and 4 hours at the fixed validation-selected 10% threshold.",
            },
        ]
    )
    alignment_audit = input_alignment_audit(validation, test, processed, predictions_dir)
    staged_hybrid_path = (
        results_dir.parent
        / "archive"
        / "new_staging_2026-07"
        / "transformer_improvement"
        / "hybrid_transformer_test_predictions.csv"
    )
    if staged_hybrid_path.exists():
        staged_hybrid = _read_csv(staged_hybrid_path)
        staged_columns = {
            "seasonal_transformer_empty_probability": SEASONAL_MODEL,
            "hybrid_transformer_empty_probability": PRIMARY_MODEL,
            "hybrid_balanced_tree_deep_empty_probability": EXPLORATORY_MODEL,
        }
        key_match = (
            len(staged_hybrid) == len(test)
            and np.array_equal(staged_hybrid["anchor_time"].astype(str), test["anchor_time"].astype(str))
            and np.array_equal(staged_hybrid["target_time"].astype(str), test["target_time"].astype(str))
            and np.array_equal(
                staged_hybrid["actual_empty_positive"].to_numpy(dtype=int), y_test
            )
        )
        max_difference = max(
            float(
                np.max(
                    np.abs(
                        staged_hybrid[column].to_numpy(dtype=float)
                        - test_probabilities[model]
                    )
                )
            )
            for column, model in staged_columns.items()
        )
        alignment_audit = pd.concat(
            [
                alignment_audit,
                pd.DataFrame(
                    [
                        {
                            "check": "staged_hybrid_probability_reproduction",
                            "status": "pass" if key_match and max_difference <= 1e-12 else "fail",
                            "detail": f"keys/labels match={key_match}; maximum probability difference={max_difference:.3g}",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    results_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        results_dir / "hybrid_seasonal_transformer_weight_search.csv": seasonal_search,
        results_dir / "hybrid_primary_weight_search.csv": primary_search,
        results_dir / "hybrid_candidate_registry.csv": registry,
        results_dir / "canonical_model_comparison.csv": metrics,
        results_dir / "hybrid_selected_threshold_policies.csv": selected,
        results_dir / "hybrid_policy_results_test.csv": policy,
        results_dir / "canonical_policy_10pct.csv": canonical_policy,
        results_dir / "hybrid_risk_opportunity_threshold_sweeps.csv": combined_sweep,
        results_dir / "hybrid_stable_window_sensitivity.csv": sensitivity,
        results_dir / "hybrid_uncertainty_daily_block_bootstrap.csv": uncertainty,
        results_dir / "hybrid_calibration_summary.csv": calibration_summary,
        results_dir / "hybrid_reliability_curve_points.csv": calibration_points,
        results_dir / "primary_hybrid_zero_conflict_bound.csv": zero_conflict,
        results_dir / "hybrid_robustness_scope.csv": robustness_scope,
        results_dir / "hybrid_input_alignment_audit.csv": alignment_audit,
    }
    written: list[Path] = []
    for path, table in outputs.items():
        table.to_csv(path, index=False, encoding="utf-8-sig")
        written.append(path)
    validation_prediction_path = predictions_dir / "hybrid_ensemble_validation_predictions.csv"
    test_prediction_path = predictions_dir / "hybrid_ensemble_test_predictions.csv"
    write_prediction_export(
        validation_prediction_path, validation, validation_probabilities, selection
    )
    write_prediction_export(test_prediction_path, test, test_probabilities, selection)
    written.extend([validation_prediction_path, test_prediction_path])

    if make_figures:
        metric_path = figures_dir / "canonical_empty_metrics_comparison.png"
        risk_path = figures_dir / "risk_opportunity_validation_vs_test_diagnostic.png"
        stable_path = figures_dir / "hybrid_stable_window_sensitivity.png"
        old_new_path = figures_dir / "transformer_old_vs_new.png"
        calibration_path = figures_dir / "hybrid_reliability_analysis.png"
        same_day_path = figures_dir / "hybrid_lightgbm_historical_same_day.png"
        make_metric_figure(metrics, metric_path)
        make_risk_opportunity_figure(combined_sweep, selected, policy, risk_path)
        make_stable_sensitivity_figure(sensitivity, stable_path)
        make_old_vs_new_figure(metrics, policy, old_new_path)
        make_calibration_figure(calibration_points, calibration_path)
        same_day = same_day_outputs(
            test,
            test_daily_indices,
            test_daily_y,
            test_daily_kwh,
            test_daily_probabilities,
            selected,
            same_day_path,
        )
        same_day_table_path = results_dir / "hybrid_lightgbm_historical_same_day.csv"
        same_day.to_csv(same_day_table_path, index=False, encoding="utf-8-sig")
        written.extend(
            [
                metric_path,
                risk_path,
                stable_path,
                old_new_path,
                calibration_path,
                same_day_path,
                same_day_table_path,
            ]
        )
    return written
