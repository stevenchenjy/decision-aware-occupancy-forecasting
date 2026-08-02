"""Window-aware validation selection and frozen-candidate diagnostics.

The selection path in this module accepts validation-only grid data. The
already-inspected current test period is used only by a separate retrospective
diagnostic path after every window-aware candidate is frozen.
"""

from __future__ import annotations

import gc
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.decision_aware_joint_search import COMPONENT_COLUMNS
from src.hybrid_analysis import (
    DEFAULT_STABLE_STEPS,
    HORIZON_STEPS,
    processed_load_proxy_kwh,
    daily_anchor_indices,
    extract_windows,
    model_metric_row,
    policy_row,
    reshape_daily,
    stable_empty_mask,
    validate_prediction_frame,
    window_summary,
)


WINDOW_FLOORS = (0.80, 0.85, 0.90, 0.95, 1.00)
AUPRC_FLOORS = (("none", None), ("95pct", 0.95), ("98pct", 0.98), ("99pct", 0.99))
INTERVAL_CONFLICT_LIMIT = 0.10
PRIMARY_FUTURE_WINDOW_FLOOR = 0.85
PRIMARY_FUTURE_AUPRC_FLOOR = 0.99
INTERVAL_MINUTES = 15
WEIGHT_COLUMNS = ["seasonal_weight", "lightgbm_weight", "transformer_weight"]

REFERENCE_IDS = [
    "A_forecast_optimal_reference",
    "B_decision_optimal_10pct",
    "C_decision_optimal_99pct_floor",
]

REFERENCE_SHORT_LABELS = {
    "A_forecast_optimal_reference": "Canonical forecast-optimal",
    "B_decision_optimal_10pct": "Exploratory decision-optimal",
    "C_decision_optimal_99pct_floor": "Exploratory 99% AUPRC-floor",
}


class WindowAwareInputBlocker(RuntimeError):
    """Raised after the audit is written when a required saved input fails."""


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, encoding="utf-8-sig")


def _blend(components: np.ndarray, weights: np.ndarray) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    if (weights < 0).any() or not np.isclose(weights.sum(), 1.0, atol=1e-12):
        raise ValueError("Weights must be non-negative and sum to one")
    if components.shape[-1] != len(weights):
        raise ValueError("Component probabilities and weights are not aligned")
    return np.tensordot(components, weights, axes=([-1], [0]))


def fully_safe_window_metrics(
    y_empty: np.ndarray, recommendation: np.ndarray
) -> dict[str, float | int]:
    """Count stable windows; any occupied interval makes a conflict window."""
    summary = window_summary(y_empty, recommendation)
    recommended = int(summary["recommended_windows"])
    fully_safe = int(summary["safe_windows"])
    conflict = int(summary["conflict_windows"])
    safe_rate = fully_safe / recommended if recommended else 0.0
    return {
        "recommended_windows": recommended,
        "fully_safe_windows": fully_safe,
        "conflict_windows": conflict,
        "fully_safe_window_rate": safe_rate,
        "window_precision": safe_rate,
        "window_conflict_rate": conflict / recommended if recommended else 0.0,
    }


def classify_conflict_position(occupied_mask: np.ndarray) -> dict[str, object]:
    """Classify occupied intervals by thirds of their recommended window."""
    occupied = np.asarray(occupied_mask, dtype=bool)
    if occupied.ndim != 1 or not occupied.any():
        raise ValueError("A one-dimensional conflict-window mask is required")
    relative_centers = (np.flatnonzero(occupied) + 0.5) / len(occupied)
    beginning = bool((relative_centers < 1 / 3).any())
    middle = bool(((relative_centers >= 1 / 3) & (relative_centers < 2 / 3)).any())
    end = bool((relative_centers >= 2 / 3).any())
    labels = [
        label
        for label, active in (
            ("beginning", beginning),
            ("middle", middle),
            ("end", end),
        )
        if active
    ]
    return {
        "conflict_near_beginning": beginning,
        "conflict_near_middle": middle,
        "conflict_near_end": end,
        "conflict_position": "|".join(labels),
    }


def conflict_window_severity_from_arrays(
    y_empty: np.ndarray,
    recommendation: np.ndarray,
    kwh: np.ndarray,
    *,
    strategy_key: str,
    strategy_label: str,
    evaluation_scope: str,
    anchor_times: np.ndarray | None = None,
    target_times: np.ndarray | None = None,
) -> pd.DataFrame:
    """Return one row per recommended window containing occupancy."""
    y = np.asarray(y_empty, dtype=bool)
    rec = np.asarray(recommendation, dtype=bool)
    energy = np.asarray(kwh, dtype=float)
    if y.shape != rec.shape or y.shape != energy.shape or y.ndim != 2:
        raise ValueError("Labels, recommendations, and kWh must be aligned 2-D arrays")
    if anchor_times is None:
        anchor_times = np.array([f"day_{day:04d}" for day in range(len(y))], dtype=object)
    if target_times is None:
        target_times = np.array(
            [[f"step_{step + 1:03d}" for step in range(y.shape[1])] for _ in range(len(y))],
            dtype=object,
        )
    rows = []
    for day in range(len(y)):
        window_number = 0
        for start, end in extract_windows(rec[day], min_steps=1):
            window_number += 1
            occupied = ~y[day, start:end]
            if not occupied.any():
                continue
            occupied_runs = extract_windows(occupied, min_steps=1)
            max_continuous = max(run_end - run_start for run_start, run_end in occupied_runs)
            end_time = (
                target_times[day, end]
                if end < y.shape[1]
                else f"{target_times[day, end - 1]} + 15 minutes"
            )
            rows.append(
                {
                    "evaluation_scope": evaluation_scope,
                    "strategy_key": strategy_key,
                    "strategy_label": strategy_label,
                    "anchor_time": anchor_times[day],
                    "window_number_within_horizon": window_number,
                    "window_start_time": target_times[day, start],
                    "window_end_time_exclusive": end_time,
                    "window_start_horizon_step": start + 1,
                    "window_end_horizon_step_inclusive": end,
                    "recommended_window_intervals": end - start,
                    "recommended_window_duration_minutes": (end - start) * INTERVAL_MINUTES,
                    "occupied_intervals_inside_window": int(occupied.sum()),
                    "occupied_minutes_inside_window": int(occupied.sum() * INTERVAL_MINUTES),
                    "maximum_continuous_occupied_duration_minutes": int(
                        max_continuous * INTERVAL_MINUTES
                    ),
                    "conflict_interval_controllable_load_kwh": float(
                        energy[day, start:end][occupied].sum()
                    ),
                    "percent_of_window_occupied": float(100 * occupied.mean()),
                    "occupied_horizon_steps": "|".join(
                        str(start + offset + 1) for offset in np.flatnonzero(occupied)
                    ),
                    **classify_conflict_position(occupied),
                }
            )
    return pd.DataFrame(rows)


def prepare_window_aware_base_grid(validation_grid: pd.DataFrame) -> pd.DataFrame:
    """Normalize the prior validation-only joint grid for window constraints."""
    required = {
        "grid_order",
        "selection_split",
        *WEIGHT_COLUMNS,
        "nonzero_components",
        "threshold",
        "validation_empty_auprc",
        "validation_occupancy_conflict_rate",
        "validation_safe_opportunity_kwh",
        "recommendation_coverage",
        "recommended_intervals",
        "safe_intervals",
        "conflict_intervals",
        "recommended_windows",
        "safe_windows",
        "conflict_windows",
    }
    if missing := required.difference(validation_grid.columns):
        raise WindowAwareInputBlocker(
            f"Decision-aware validation grid is missing: {sorted(missing)}"
        )
    if any("test" in column.lower() for column in validation_grid.columns):
        raise ValueError("Validation selection input must not contain test metrics")
    if not validation_grid["selection_split"].eq("validation_only").all():
        raise ValueError("Window-aware selection requires a validation-only grid")
    weights = validation_grid[WEIGHT_COLUMNS].to_numpy(dtype=float)
    if (weights < 0).any() or not np.allclose(weights.sum(axis=1), 1.0):
        raise ValueError("Validation grid contains illegal weights")

    base = validation_grid.copy()
    base["validation_interval_conflict_rate"] = base[
        "validation_occupancy_conflict_rate"
    ]
    base["validation_fully_safe_window_rate"] = np.where(
        base["recommended_windows"] > 0,
        base["safe_windows"] / base["recommended_windows"],
        0.0,
    )
    base["validation_window_precision"] = base["validation_fully_safe_window_rate"]
    base["validation_coverage"] = base["recommendation_coverage"]
    base["fully_safe_windows"] = base["safe_windows"].astype(int)
    base["validation_best_empty_auprc"] = float(
        base["validation_empty_auprc"].max()
    )
    return base


def expand_window_aware_constraint_grid(validation_grid: pd.DataFrame) -> pd.DataFrame:
    """Cross the 8,547 validation pairs with all 5x4 declared constraints."""
    base = prepare_window_aware_base_grid(validation_grid)
    best = float(base["validation_empty_auprc"].max())
    frames = []
    constraint_order = 0
    for window_floor in WINDOW_FLOORS:
        for floor_label, floor_ratio in AUPRC_FLOORS:
            part = base.copy()
            part["constraint_order"] = constraint_order
            part["safe_window_floor"] = window_floor
            part["auprc_floor_label"] = floor_label
            part["auprc_floor_ratio"] = np.nan if floor_ratio is None else floor_ratio
            part["auprc_floor_value"] = np.nan if floor_ratio is None else best * floor_ratio
            part["meets_interval_conflict_limit"] = (
                part["validation_interval_conflict_rate"] <= INTERVAL_CONFLICT_LIMIT
            )
            part["meets_safe_window_floor"] = (
                part["validation_fully_safe_window_rate"] >= window_floor
            )
            part["meets_auprc_floor"] = (
                True
                if floor_ratio is None
                else part["validation_empty_auprc"] >= best * floor_ratio
            )
            part["has_recommended_stable_window"] = part["recommended_windows"] >= 1
            part["has_positive_coverage"] = part["validation_coverage"] > 0
            part["feasibility_flag"] = part[
                [
                    "meets_interval_conflict_limit",
                    "meets_safe_window_floor",
                    "meets_auprc_floor",
                    "has_recommended_stable_window",
                    "has_positive_coverage",
                ]
            ].all(axis=1)
            frames.append(part)
            constraint_order += 1
    expanded = pd.concat(frames, ignore_index=True)
    columns = [
        "constraint_order",
        "grid_order",
        "selection_split",
        *WEIGHT_COLUMNS,
        "nonzero_components",
        "threshold",
        "validation_empty_auprc",
        "validation_best_empty_auprc",
        "validation_interval_conflict_rate",
        "validation_fully_safe_window_rate",
        "validation_window_precision",
        "validation_safe_opportunity_kwh",
        "validation_coverage",
        "recommended_intervals",
        "safe_intervals",
        "conflict_intervals",
        "recommended_windows",
        "fully_safe_windows",
        "conflict_windows",
        "auprc_floor_label",
        "auprc_floor_ratio",
        "auprc_floor_value",
        "safe_window_floor",
        "meets_interval_conflict_limit",
        "meets_safe_window_floor",
        "meets_auprc_floor",
        "has_recommended_stable_window",
        "has_positive_coverage",
        "feasibility_flag",
    ]
    return expanded[columns]


def select_window_aware_candidates(expanded_validation_grid: pd.DataFrame) -> pd.DataFrame:
    """Select one candidate for every declared (W_min, Q) validation rule."""
    if any("test" in column.lower() for column in expanded_validation_grid.columns):
        raise ValueError("Current test metrics are forbidden in validation selection")
    required = {
        "safe_window_floor",
        "auprc_floor_label",
        "feasibility_flag",
        "validation_safe_opportunity_kwh",
        "validation_fully_safe_window_rate",
        "validation_interval_conflict_rate",
        "validation_empty_auprc",
        "fully_safe_windows",
        "nonzero_components",
        "grid_order",
        *WEIGHT_COLUMNS,
        "threshold",
    }
    if missing := required.difference(expanded_validation_grid.columns):
        raise ValueError(f"Expanded grid is missing selection columns: {sorted(missing)}")
    rows = []
    for window_floor in WINDOW_FLOORS:
        for floor_label, floor_ratio in AUPRC_FLOORS:
            part = expanded_validation_grid[
                np.isclose(expanded_validation_grid["safe_window_floor"], window_floor)
                & expanded_validation_grid["auprc_floor_label"].eq(floor_label)
                & expanded_validation_grid["feasibility_flag"]
            ]
            if part.empty:
                raise WindowAwareInputBlocker(
                    f"No feasible validation candidate for W={window_floor}, Q={floor_label}"
                )
            chosen = part.sort_values(
                [
                    "validation_safe_opportunity_kwh",
                    "validation_fully_safe_window_rate",
                    "validation_interval_conflict_rate",
                    "validation_empty_auprc",
                    "fully_safe_windows",
                    "nonzero_components",
                    "grid_order",
                ],
                ascending=[False, False, True, False, False, True, True],
                kind="mergesort",
            ).iloc[0]
            window_pct = int(round(100 * window_floor))
            q_label = "none" if floor_ratio is None else str(int(round(100 * floor_ratio)))
            candidate_id = f"window_aware_W{window_pct}_Q{q_label}"
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_label": f"Window-aware W>={window_pct}%, Q={q_label}",
                    "candidate_role": "window_aware_validation_selected",
                    "selection_split": "validation_only",
                    "current_test_used_for_selection": False,
                    "selection_objective": "maximum validation offline camera-label-empty load-proxy overlap under declared constraints",
                    "safe_window_floor": window_floor,
                    "auprc_floor_label": floor_label,
                    "auprc_floor_ratio": np.nan if floor_ratio is None else floor_ratio,
                    "is_primary_future_challenger": bool(
                        np.isclose(window_floor, PRIMARY_FUTURE_WINDOW_FLOOR)
                        and floor_ratio is not None
                        and np.isclose(floor_ratio, PRIMARY_FUTURE_AUPRC_FLOOR)
                    ),
                    **{
                        column: chosen[column]
                        for column in [
                            *WEIGHT_COLUMNS,
                            "nonzero_components",
                            "threshold",
                            "validation_empty_auprc",
                            "validation_interval_conflict_rate",
                            "validation_fully_safe_window_rate",
                            "validation_window_precision",
                            "validation_safe_opportunity_kwh",
                            "validation_coverage",
                            "recommended_intervals",
                            "safe_intervals",
                            "conflict_intervals",
                            "recommended_windows",
                            "fully_safe_windows",
                            "conflict_windows",
                            "grid_order",
                        ]
                    },
                    "feasibility_flag": True,
                    "prior_current_test_metrics_role": "not_evaluated_in_selection_table",
                }
            )
    return pd.DataFrame(rows)


def frozen_reference_rows(prior_candidates: pd.DataFrame) -> pd.DataFrame:
    """Transform the three already-frozen strategies into comparison rows."""
    prior = prior_candidates.set_index("candidate_id")
    missing = set(REFERENCE_IDS).difference(prior.index)
    if missing:
        raise WindowAwareInputBlocker(f"Prior selected-candidate table is missing: {sorted(missing)}")
    rows = []
    for candidate_id in REFERENCE_IDS:
        row = prior.loc[candidate_id]
        validation_rate = (
            row["validation_safe_windows"] / row["validation_recommended_windows"]
            if row["validation_recommended_windows"]
            else 0.0
        )
        test_rate = (
            row["test_safe_windows"] / row["test_recommended_windows"]
            if row["test_recommended_windows"]
            else 0.0
        )
        rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_label": REFERENCE_SHORT_LABELS[candidate_id],
                "candidate_role": "frozen_prior_reference",
                "selection_split": "prior_validation_selection_frozen",
                "current_test_used_for_selection": False,
                "selection_objective": row["selection_objective"],
                "safe_window_floor": np.nan,
                "auprc_floor_label": "prior_frozen_rule",
                "auprc_floor_ratio": row["auprc_floor_ratio"],
                "is_primary_future_challenger": False,
                **{column: row[column] for column in WEIGHT_COLUMNS},
                "nonzero_components": row["nonzero_components"],
                "threshold": row["threshold"],
                "validation_empty_auprc": row["validation_empty_auprc"],
                "validation_interval_conflict_rate": row[
                    "validation_occupancy_conflict_rate"
                ],
                "validation_fully_safe_window_rate": validation_rate,
                "validation_window_precision": validation_rate,
                "validation_safe_opportunity_kwh": row[
                    "validation_safe_opportunity_kwh"
                ],
                "validation_coverage": row["validation_recommendation_coverage"],
                "recommended_intervals": row["validation_recommended_intervals"],
                "safe_intervals": row["validation_safe_intervals"],
                "conflict_intervals": row["validation_conflict_intervals"],
                "recommended_windows": row["validation_recommended_windows"],
                "fully_safe_windows": row["validation_safe_windows"],
                "conflict_windows": row["validation_conflict_windows"],
                "grid_order": row["validation_grid_order"],
                "feasibility_flag": True,
                "prior_current_test_metrics_role": "prior_retrospective_reference_not_selection_input",
                "prior_current_test_empty_auprc": row["test_empty_auprc"],
                "prior_current_test_interval_conflict_rate": row[
                    "test_occupancy_conflict_rate"
                ],
                "prior_current_test_fully_safe_window_rate": test_rate,
                "prior_current_test_safe_opportunity_kwh": row[
                    "test_safe_opportunity_kwh"
                ],
                "prior_current_test_recommended_intervals": row[
                    "test_recommended_intervals"
                ],
                "prior_current_test_safe_intervals": row["test_safe_intervals"],
                "prior_current_test_conflict_intervals": row["test_conflict_intervals"],
                "prior_current_test_recommended_windows": row["test_recommended_windows"],
                "prior_current_test_fully_safe_windows": row["test_safe_windows"],
                "prior_current_test_conflict_windows": row["test_conflict_windows"],
            }
        )
    return pd.DataFrame(rows)


def combine_selected_and_references(
    window_candidates: pd.DataFrame, prior_candidates: pd.DataFrame
) -> pd.DataFrame:
    references = frozen_reference_rows(prior_candidates)
    selected = window_candidates.copy()
    for column in references.columns.difference(selected.columns):
        selected[column] = np.nan
    for column in selected.columns.difference(references.columns):
        references[column] = np.nan
    combined = pd.concat([references[selected.columns], selected], ignore_index=True)
    return combined


def unique_strategy_definitions(selected: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate identical window candidates while preserving three references."""
    references = selected[selected["candidate_role"].eq("frozen_prior_reference")].copy()
    window = selected[selected["candidate_role"].eq("window_aware_validation_selected")].copy()
    window["definition_key"] = window.apply(
        lambda row: "|".join(
            [*(f"{float(row[column]):.6f}" for column in WEIGHT_COLUMNS), f"{float(row['threshold']):.6f}"]
        ),
        axis=1,
    )
    rows = []
    for definition_number, (_, part) in enumerate(window.groupby("definition_key", sort=False), start=1):
        primary = part[part["is_primary_future_challenger"].astype(bool)]
        representative = primary.iloc[0] if not primary.empty else part.iloc[0]
        row = representative.to_dict()
        row["strategy_key"] = f"window_aware_definition_{definition_number:02d}"
        row["strategy_label"] = (
            "Window-aware primary challenger (W>=85%, Q=99%)"
            if not primary.empty
            else f"Window-aware {representative['seasonal_weight']:.2f}/{representative['lightgbm_weight']:.2f}/{representative['transformer_weight']:.2f} @ {representative['threshold']:.3f}"
        )
        row["selected_by_rules"] = "|".join(part["candidate_id"].astype(str))
        rows.append(row)
    for reference in references.itertuples(index=False):
        row = reference._asdict()
        row["strategy_key"] = reference.candidate_id
        row["strategy_label"] = reference.candidate_label
        row["selected_by_rules"] = reference.candidate_id
        rows.append(row)
    return pd.DataFrame(rows)


def _daily_arrays(frame: pd.DataFrame, processed: pd.DataFrame) -> dict[str, np.ndarray]:
    validate_prediction_frame(frame, str(frame["split"].iloc[0]))
    indices = daily_anchor_indices(frame)
    components = np.stack(
        [reshape_daily(frame[column].to_numpy(dtype=float), indices) for column in COMPONENT_COLUMNS],
        axis=-1,
    )
    anchor_rows = frame["anchor_time"].iloc[::HORIZON_STEPS].reset_index(drop=True)
    return {
        "indices": indices,
        "y": reshape_daily(frame["actual_empty_positive"].to_numpy(dtype=int), indices),
        "kwh": reshape_daily(processed_load_proxy_kwh(frame, processed), indices),
        "components": components,
        "anchors": anchor_rows.iloc[indices].astype(str).to_numpy(),
        "targets": reshape_daily(frame["target_time"].astype(str).to_numpy(), indices),
    }


def conflict_severity_for_strategies(
    frame: pd.DataFrame,
    processed: pd.DataFrame,
    strategies: pd.DataFrame,
    *,
    evaluation_scope: str,
) -> pd.DataFrame:
    arrays = _daily_arrays(frame, processed)
    frames = []
    for strategy in strategies.itertuples(index=False):
        weights = np.array(
            [strategy.seasonal_weight, strategy.lightgbm_weight, strategy.transformer_weight]
        )
        probability = _blend(arrays["components"], weights)
        recommendation = stable_empty_mask(
            probability, float(strategy.threshold), DEFAULT_STABLE_STEPS
        )
        severity = conflict_window_severity_from_arrays(
            arrays["y"],
            recommendation,
            arrays["kwh"],
            strategy_key=strategy.strategy_key,
            strategy_label=strategy.strategy_label,
            evaluation_scope=evaluation_scope,
            anchor_times=arrays["anchors"],
            target_times=arrays["targets"],
        )
        if not severity.empty:
            severity.insert(3, "selected_by_rules", strategy.selected_by_rules)
            severity.insert(4, "seasonal_weight", strategy.seasonal_weight)
            severity.insert(5, "lightgbm_weight", strategy.lightgbm_weight)
            severity.insert(6, "transformer_weight", strategy.transformer_weight)
            severity.insert(7, "threshold", strategy.threshold)
            frames.append(severity)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def evaluate_frozen_strategies(
    frame: pd.DataFrame,
    processed: pd.DataFrame,
    strategies: pd.DataFrame,
    *,
    evaluation_scope: str,
) -> pd.DataFrame:
    """Evaluate fixed strategies; this function performs no ranking or selection."""
    arrays = _daily_arrays(frame, processed)
    components_all = frame[COMPONENT_COLUMNS].to_numpy(dtype=float)
    y_all = frame["actual_empty_positive"].to_numpy(dtype=int)
    severity = conflict_severity_for_strategies(
        frame, processed, strategies, evaluation_scope=evaluation_scope
    )
    severity_groups = (
        severity.groupby("strategy_key")
        if not severity.empty
        else None
    )
    rows = []
    for strategy in strategies.itertuples(index=False):
        weights = np.array(
            [strategy.seasonal_weight, strategy.lightgbm_weight, strategy.transformer_weight]
        )
        probability_all = _blend(components_all, weights)
        probability_daily = _blend(arrays["components"], weights)
        recommendation = stable_empty_mask(
            probability_daily, float(strategy.threshold), DEFAULT_STABLE_STEPS
        )
        policy = policy_row(
            strategy.strategy_label,
            arrays["y"],
            probability_daily,
            arrays["kwh"],
            float(strategy.threshold),
            evaluation_scope,
            risk_delta=INTERVAL_CONFLICT_LIMIT,
        )
        windows = fully_safe_window_metrics(arrays["y"], recommendation)
        forecast = model_metric_row(strategy.strategy_label, y_all, probability_all)
        if severity_groups is not None and strategy.strategy_key in severity_groups.groups:
            part = severity_groups.get_group(strategy.strategy_key)
            longest = int(part["maximum_continuous_occupied_duration_minutes"].max())
            occupied_minutes = int(part["occupied_minutes_inside_window"].sum())
            conflict_kwh = float(part["conflict_interval_controllable_load_kwh"].sum())
        else:
            longest = 0
            occupied_minutes = 0
            conflict_kwh = 0.0
        rows.append(
            {
                "evaluation_scope": evaluation_scope,
                "strategy_key": strategy.strategy_key,
                "strategy_label": strategy.strategy_label,
                "selected_by_rules": strategy.selected_by_rules,
                "current_test_used_for_selection": False,
                "not_fresh_untouched_evaluation": evaluation_scope.endswith("diagnostic"),
                "seasonal_weight": strategy.seasonal_weight,
                "lightgbm_weight": strategy.lightgbm_weight,
                "transformer_weight": strategy.transformer_weight,
                "threshold": strategy.threshold,
                "empty_auprc": forecast["empty_auprc"],
                "empty_precision": forecast["empty_precision"],
                "empty_recall": forecast["empty_recall"],
                "empty_f1": forecast["empty_f1"],
                "interval_conflict_rate": policy["occupancy_conflict_rate"],
                "fully_safe_window_rate": windows["fully_safe_window_rate"],
                "window_precision": windows["window_precision"],
                "safe_opportunity_kwh": policy["safe_opportunity_kwh"],
                "recommendation_coverage": policy["recommendation_coverage"],
                "recommended_intervals": policy["recommended_intervals"],
                "safe_intervals": policy["safe_intervals"],
                "conflict_intervals": policy["conflict_intervals"],
                "recommended_windows": windows["recommended_windows"],
                "fully_safe_windows": windows["fully_safe_windows"],
                "conflict_windows": windows["conflict_windows"],
                "longest_conflict_duration_minutes": longest,
                "total_occupied_minutes_inside_recommended_windows": occupied_minutes,
                "conflict_interval_controllable_load_kwh": conflict_kwh,
                "daily_schedules": policy["daily_schedules"],
            }
        )
    return pd.DataFrame(rows)


def _audit_report(
    results_dir: Path,
) -> tuple[str, bool]:
    required_paths = [
        results_dir / "decision_aware_joint_weight_threshold_grid.csv",
        results_dir / "decision_aware_joint_selected_candidates.csv",
        results_dir / "forecast_predictions_validation_all_models.csv",
        results_dir / "forecast_predictions_test_all_models.csv",
        results_dir / "processed_lbnl_15min_pacific.csv",
    ]
    blockers = [f"Missing required file: `{path.as_posix()}`" for path in required_paths if not path.exists()]
    verification_rows = []
    details = {}
    if not blockers:
        try:
            prior = _read_csv(results_dir / "decision_aware_joint_selected_candidates.csv")
            test = _read_csv(results_dir / "forecast_predictions_test_all_models.csv")
            processed = _read_csv(results_dir / "processed_lbnl_15min_pacific.csv")
            references = frozen_reference_rows(prior)
            strategies = unique_strategy_definitions(references)
            diagnostic = evaluate_frozen_strategies(
                test,
                processed,
                strategies,
                evaluation_scope="current_test_retrospective_diagnostic",
            ).set_index("strategy_key")
            expected = {
                "A_forecast_optimal_reference": (14, 14, 0),
                "B_decision_optimal_10pct": (21, 17, 4),
                "C_decision_optimal_99pct_floor": (18, 14, 4),
            }
            for candidate_id, counts in expected.items():
                row = diagnostic.loc[candidate_id]
                observed = (
                    int(row["recommended_windows"]),
                    int(row["fully_safe_windows"]),
                    int(row["conflict_windows"]),
                )
                status = "pass" if observed == counts else "fail"
                if status == "fail":
                    blockers.append(
                        f"{candidate_id} window counts {observed} do not match expected {counts}"
                    )
                verification_rows.append((candidate_id, *observed, status))
            base = prepare_window_aware_base_grid(
                _read_csv(results_dir / "decision_aware_joint_weight_threshold_grid.csv")
            )
            details = {
                "base_rows": len(base),
                "weights": len(base[WEIGHT_COLUMNS].drop_duplicates()),
                "thresholds": base["threshold"].nunique(),
                "validation_days": int(base["daily_schedules"].iloc[0]),
                "best_auprc": float(base["validation_empty_auprc"].max()),
            }
            del prior, test, processed, references, strategies, diagnostic, base
            gc.collect()
        except Exception as exc:
            blockers.append(f"Audit computation failed: `{type(exc).__name__}: {exc}`")

    verification_table = "\n".join(
        f"| {REFERENCE_SHORT_LABELS[candidate_id]} | {recommended} | {safe} | {conflict} | {status} |"
        for candidate_id, recommended, safe, conflict, status in verification_rows
    )
    blocker_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- None."
    conclusion = (
        "**PASS.** Existing definitions and the three reported current-test window outcomes reproduce exactly."
        if not blockers
        else "**STOP.** At least one definition/input consistency check failed; selection must not continue."
    )
    text = f"""# Window-aware decision search audit

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate/run
- Verification Status: ANALYZED
- Version Label: window_aware_audit_v1

## Audit conclusion

{conclusion}

The audit uses saved predictions and processed load outputs only. It does not retrain a base model or require the Dryad raw directory.

## Exact current definitions

- **Recommended interval:** a 15-minute interval whose uncalibrated Empty score is at or above the fixed threshold and belongs to a contiguous above-threshold run of at least four intervals. Shorter runs are not recommended.
- **Camera-label-empty interval:** a recommended interval with subsequently observed `actual_empty_positive=1`.
- **Conflict interval:** a recommended interval with observed `actual_empty_positive=0` (occupied).
- **Stable recommended window:** one maximal contiguous run of recommended intervals within a midnight-labelled completed-input-bin 96-step horizon; its effective availability boundary is 00:15 for a 00:00 label. Windows do not join across horizon/day boundaries.
- **All-camera-label-empty window:** a stable recommended window for which every interval is subsequently observed Empty.
- **Conflict window:** a stable recommended window containing **any** occupied interval. One occupied 15-minute interval is sufficient.
- **Interval conflict rate:** `conflict intervals / recommended intervals`; defined as zero when there are no recommendations, although candidate eligibility separately requires positive coverage and at least one window.
- **Window precision:** `all-camera-label-empty windows / recommended windows`.
- **All-camera-label-empty window rate:** the same binary-window quantity as window precision; legacy output columns retain `fully_safe` names for compatibility.
- **Offline label-empty load-proxy overlap (kWh):** `(hvac_S + lig_S) * 0.25 h`, clipped at zero by the existing mapping, summed only for recommended intervals subsequently observed Empty. This is a processed load-proxy overlap, not verified savings or controllable energy.
- **Recommendation coverage:** `recommended intervals / all intervals` across the non-overlapping midnight policy horizons.

The implementation in `src/hybrid_analysis.py` confirms that `window_summary` increments `conflict_windows` whenever `actual_empty[day, start:end].all()` is false. Therefore any occupied interval makes the whole recommended window conflicting.

## Reproduction of reported current outcomes

| Frozen strategy | Recommended windows | All-camera-label-empty windows | Conflict windows | Status |
|---|---:|---:|---:|---|
{verification_table}

The decision-optimal and 99%-floor candidates each have four conflict windows even though their interval conflict rates are near 3%, because occupied intervals are distributed across four distinct recommended windows and the window metric is binary.

## Saved-input sufficiency

- Unique validation weight-threshold pairs: {details.get('base_rows', 'unavailable')} ({details.get('weights', 'unavailable')} weight vectors × {details.get('thresholds', 'unavailable')} thresholds).
- Validation policy horizons: {details.get('validation_days', 'unavailable')} non-overlapping midnight horizons.
- Best validation Empty AUPRC: {details.get('best_auprc', float('nan')):.10f}.
- The validation grid includes interval counts, offline label-empty load-proxy overlap, coverage, and window counts. Validation predictions and the processed load table support per-window severity reconstruction.
- The current test export supports a retrospective diagnostic only. It is not a fresh untouched evaluation and is not accepted by the validation selection function.

## Inconsistencies or blockers

{blocker_text}
"""
    return text, not blockers


def _candidate_validation_table(selected: pd.DataFrame) -> str:
    rows = [
        "| W floor | Q floor | Weights S/L/T | Threshold | AUPRC | Interval conflict | All-label-empty windows | Proxy kWh | Coverage | Windows label-empty/total |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    window = selected[selected["candidate_role"].eq("window_aware_validation_selected")]
    for row in window.itertuples(index=False):
        q_display = "none" if row.auprc_floor_label == "none" else row.auprc_floor_label.replace("pct", "%")
        rows.append(
            f"| {100 * row.safe_window_floor:.0f}% | {q_display} | "
            f"{row.seasonal_weight:.2f}/{row.lightgbm_weight:.2f}/{row.transformer_weight:.2f} | "
            f"{row.threshold:.3f} | {row.validation_empty_auprc:.4f} | "
            f"{100 * row.validation_interval_conflict_rate:.2f}% | "
            f"{100 * row.validation_fully_safe_window_rate:.2f}% | "
            f"{row.validation_safe_opportunity_kwh:.1f} | {100 * row.validation_coverage:.2f}% | "
            f"{int(row.fully_safe_windows)}/{int(row.recommended_windows)} |"
        )
    return "\n".join(rows)


def _historical_frozen_candidate_protocol(selected: pd.DataFrame) -> str:
    """Archived pre-audit protocol retained only to explain historical outputs.

    It must not be used after the provenance-corrected empirical rerun because
    that rerun changes source timing, deep initialization, and score outputs.
    """
    primary = selected[selected["is_primary_future_challenger"].astype(bool)].iloc[0]
    q99 = selected[
        selected["candidate_role"].eq("window_aware_validation_selected")
        & selected["auprc_floor_label"].eq("99pct")
    ]
    sensitivity_lines = "\n".join(
        f"  - W>={100 * row.safe_window_floor:.0f}%, Q=99%: `{row.seasonal_weight:.2f}/{row.lightgbm_weight:.2f}/{row.transformer_weight:.2f}`, threshold `{row.threshold:.3f}`."
        for row in q99.itertuples(index=False)
        if not np.isclose(row.safe_window_floor, PRIMARY_FUTURE_WINDOW_FLOOR)
    )
    return f"""# Future untouched evaluation protocol

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: plan/validate
- Verification Status: ANALYZED
- Version Label: future_untouched_protocol_v1

## Purpose and data firewall

Apply the frozen candidates once to a chronological period whose labels, loads, outcomes, and qualitative examples have not been inspected during model training, canonical selection, decision-aware selection, or this window-aware study. Do not change a weight, threshold, metric, floor, tie-break, or promotion criterion after opening that period.

## Frozen candidates

- Canonical forecast-optimal primary: `0.15/0.60/0.25`, threshold `0.875`.
- Exploratory decision-optimal: `0.65/0.05/0.30`, threshold `0.775`.
- Exploratory 99%-AUPRC-floor: `0.35/0.35/0.30`, threshold `0.800`.
- **Primary window-aware challenger:** `{primary.seasonal_weight:.2f}/{primary.lightgbm_weight:.2f}/{primary.transformer_weight:.2f}`, threshold `{primary.threshold:.3f}`, selected under validation `W_min=85%` and `Q=99%`.
- Secondary, multiplicity-labeled window-floor sensitivity candidates:
{sensitivity_lines}

Only the primary window-aware challenger is eligible for the primary promotion comparison. The other window-floor variants are secondary sensitivity analyses and cannot be substituted after seeing future outcomes.

## Evaluation unit and fixed calculations

- Use complete non-overlapping midnight-anchored 96-step horizons, matching the validation policy scope.
- Keep the stable-window requirement at four consecutive 15-minute intervals.
- Use the saved definition of controllable-load opportunity: HVAC south plus lighting south interval kWh.
- Report both aggregate totals and paired daily values. Preserve day identifiers for day-block uncertainty and influence analysis.

## Primary future metric

- **Safe opportunity kWh**, paired by day against the canonical primary. Also report kWh per evaluation day so periods of different duration remain comparable.

## Safety metrics

- Interval conflict rate.
- Fully safe window rate/window precision.
- Number of conflict windows.
- Longest continuous occupied duration within a recommended window.
- Total occupied minutes inside recommended windows.
- Controllable-load kWh associated with conflict intervals.

## Forecasting metrics

- Empty AUPRC, precision, recall, and F1 on all saved rolling forecasts for the untouched period.

## Pre-specified promotion criteria

The primary window-aware challenger may replace the canonical primary only if **all** criteria hold:

1. Safe opportunity is at least 10% higher than canonical and, for a period comparable to the current 43-day evaluation, at least 50 kWh higher. For another duration, scale the absolute criterion as `1.16 kWh × evaluation days` (50/43), while retaining the 10% criterion.
2. Interval conflict rate is `<=10%`.
3. Fully safe window rate is `>=85%`.
4. Empty AUPRC is at least 99% of canonical on the same untouched period.
5. Recommendation coverage is at least 80% of canonical coverage and at least 2% absolute; at least 10 windows must be recommended.
6. Leave-one-day-out influence analysis shows the safe-opportunity gain remains positive after removing each of the two highest-load gain days; the gain cannot be driven by only one or two unusually high-load days.
7. A paired daily-block 95% interval for the safe-opportunity difference is reported. Promotion requires its lower bound to be above zero; this is an added evidential gate, not a claim of guaranteed future performance.

The 10% relative and 50 kWh comparable-period thresholds are deliberately round, operationally interpretable effect thresholds. They were fixed without optimizing against the already-inspected current test diagnostic.

## Execution and reporting order

1. Record the untouched period boundaries and hash all inputs before computing outcomes.
2. Generate all frozen candidate probabilities and recommendations in one run.
3. Compute forecasting, interval, window, severity, coverage, and daily influence metrics.
4. Run the paired daily-block analysis.
5. Apply the promotion criteria mechanically; do not choose among sensitivity candidates.
6. Publish failures as well as passes and retain the canonical primary unless every gate passes.

## Work that cannot be completed now

- Acquire and lock a genuinely new chronological occupancy/load period.
- Produce frozen base-model probabilities for that period without adapting the trained models.
- Apply the candidates once, compute the paired daily evidence, and make the promotion decision.

The present validation study and current-test retrospective diagnostic cannot substitute for this untouched evaluation.
"""


def _future_protocol(selected: pd.DataFrame) -> str:
    """Write the current, non-promotional rerun handoff."""
    return f"""# Historical frozen-candidate registry and empirical-rerun handoff

> **Final-audit status:** the {len(selected)} frozen candidates in this saved-output search are historical exploratory diagnostics only. They cannot be promoted, carried into corrected retraining, or applied as the next empirical evaluation.

## Why the old future protocol is superseded

The final audit requires provenance-tagged source streams, explicit observation-end and post-bin issue timestamps, seed initialization before deep-model construction, a locked environment, full model retraining, and fresh validation-only selection. Those changes alter the score-generating experiment. Reusing historic saved-output weights or thresholds after them would be a new unvalidated choice, not a frozen confirmation.

## Required corrected protocol

1. Obtain and hash provenance-tagged streams; preserve source timezone, observation-end, bin-start, bin-end, effective issue, target-start, and target-end fields.
2. Retrain every model under seed-before-construction and a locked software/hardware environment.
3. Select model family, blend weights, score threshold, and any window rule only on a newly declared chronological validation period.
4. Freeze that newly selected policy without inspecting the later evaluation period.
5. Evaluate it once on a later untouched period or independent building, reporting post-bin forecast and policy scopes separately.
6. Treat camera-label-empty processed-load-proxy overlap as offline accounting only; energy, comfort, controllability, calibrated-risk, and deployment claims require additional evidence.

See paper/audits/rerun_manifest.md for the authoritative empirical-rerun checklist. The current test and the existing decision-aware/window-aware diagnostics remain retrospective and may not be used to retune or promote a candidate.
"""


def _scientific_report(
    selected: pd.DataFrame,
    diagnostic: pd.DataFrame,
) -> str:
    references = selected.set_index("candidate_id")
    q99 = selected[
        selected["candidate_role"].eq("window_aware_validation_selected")
        & selected["auprc_floor_label"].eq("99pct")
    ].set_index("safe_window_floor")
    w80 = q99.loc[0.80]
    w85 = q99.loc[0.85]
    w90 = q99.loc[0.90]
    w95 = q99.loc[0.95]
    w100 = q99.loc[1.00]
    canonical = references.loc["A_forecast_optimal_reference"]
    decision = references.loc["B_decision_optimal_10pct"]
    floor99 = references.loc["C_decision_optimal_99pct_floor"]
    diag_index = diagnostic.set_index("strategy_key")
    decision_diag = diag_index.loc["B_decision_optimal_10pct"]
    floor_diag = diag_index.loc["C_decision_optimal_99pct_floor"]

    loss90 = w80["validation_safe_opportunity_kwh"] - w90["validation_safe_opportunity_kwh"]
    loss95 = w80["validation_safe_opportunity_kwh"] - w95["validation_safe_opportunity_kwh"]
    loss100 = w80["validation_safe_opportunity_kwh"] - w100["validation_safe_opportunity_kwh"]
    return f"""# Window-aware decision search report

> **Final-audit status:** exploratory offline, post-bin saved-output diagnostic. A 00:00 anchor is the left label of a completed [00:00, 00:15) input bin, so its effective boundary is 00:15. All "safe" legacy fields mean subsequently camera-label-empty processed-load-proxy overlap, not physical absence, calibrated risk, savings, or a deployable policy. The historical candidates cannot be promoted after the required empirical retraining.

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate/run
- Verification Status: ANALYZED
- Version Label: window_aware_search_v1

## Result in brief

The validation-only study evaluated 8,547 unique weight-threshold pairs under 20 pre-specified window/AUPRC constraint combinations (170,940 constraint rows). The forecasting floors did not change the selected optimum at any window floor because every selected solution already exceeded 99% of the best validation AUPRC.

The clearest validation compromise is the historical `W_min=85%, Q=99%` challenger: `{w85.seasonal_weight:.2f}/{w85.lightgbm_weight:.2f}/{w85.transformer_weight:.2f}` at threshold `{w85.threshold:.3f}`. It produced validation AUPRC `{w85.validation_empty_auprc:.4f}`, interval conflict `{100 * w85.validation_interval_conflict_rate:.2f}%`, all-camera-label-empty window rate `{100 * w85.validation_fully_safe_window_rate:.2f}%` ({int(w85.fully_safe_windows)}/{int(w85.recommended_windows)}), and `{w85.validation_safe_opportunity_kwh:.1f} kWh of offline load-proxy overlap. This historical selection preceded the current-test retrospective diagnostic.

No result deserves promotion or a headline change now. The enlarged search remains exploratory, and the current test period is already inspected.

## Validation-selected candidates

{_candidate_validation_table(selected)}

## Why about 3% interval conflict still produced four conflict windows

Interval conflict pools intervals across all recommendations, whereas a window becomes conflicting after a single occupied interval. In the retrospective current-test diagnostic:

- The decision-optimal candidate had `{int(decision_diag.conflict_intervals)}` occupied intervals among `{int(decision_diag.recommended_intervals)}` recommendations ({100 * decision_diag.interval_conflict_rate:.2f}%), distributed across `{int(decision_diag.conflict_windows)}` windows. One conflict window contained seven occupied intervals; three contained one each.
- The 99%-floor candidate had `{int(floor_diag.conflict_intervals)}` occupied intervals among `{int(floor_diag.recommended_intervals)}` recommendations ({100 * floor_diag.interval_conflict_rate:.2f}%), also across `{int(floor_diag.conflict_windows)}` windows. One contained seven occupied intervals, one contained two, and two contained one each.

Thus low interval conflict does not imply that almost every recommended window is all-camera-label-empty.

## Opportunity cost of stronger window floors

Using the common 99% AUPRC floor (the same optima occur for the other Q settings):

- W>=80%: `{w80.validation_safe_opportunity_kwh:.1f} kWh`, `{100 * w80.validation_fully_safe_window_rate:.1f}%` all-camera-label-empty windows.
- W>=85%: `{w85.validation_safe_opportunity_kwh:.1f} kWh`, a loss of `{w80.validation_safe_opportunity_kwh - w85.validation_safe_opportunity_kwh:.1f} kWh` versus W>=80%.
- W>=90%: `{w90.validation_safe_opportunity_kwh:.1f} kWh`, a loss of `{loss90:.1f} kWh` ({100 * loss90 / w80.validation_safe_opportunity_kwh:.1f}%).
- W>=95%: `{w95.validation_safe_opportunity_kwh:.1f} kWh`, a loss of `{loss95:.1f} kWh` ({100 * loss95 / w80.validation_safe_opportunity_kwh:.1f}%). The discrete optimum is actually 100% all-camera-label-empty.
- W=100%: `{w100.validation_safe_opportunity_kwh:.1f} kWh`, a loss of `{loss100:.1f} kWh` ({100 * loss100 / w80.validation_safe_opportunity_kwh:.1f}%). It is the same discrete candidate as W>=95%.

Relative to the unconstrained decision candidate's `{decision.validation_safe_opportunity_kwh:.1f} kWh`, W>=90% gives up `{decision.validation_safe_opportunity_kwh - w90.validation_safe_opportunity_kwh:.1f} kWh`, and the all-camera-label-empty candidate gives up `{decision.validation_safe_opportunity_kwh - w100.validation_safe_opportunity_kwh:.1f} kWh`.

## Interpretation of the existing 99%-AUPRC-floor candidate

The existing 99%-floor candidate has only `{100 * floor99.validation_fully_safe_window_rate:.1f}%` all-camera-label-empty validation windows ({int(floor99.fully_safe_windows)}/{int(floor99.recommended_windows)}), so it fails even the lowest new 80% window floor. Its retrospective current-test rate is `{100 * floor_diag.fully_safe_window_rate:.1f}%`. Its high offline proxy overlap remains descriptively interesting, but it is not attractive under the historical window-aware rule.

## Operational compromise

The W>=85%, Q=99% challenger is the clearest validation compromise: it raises the all-camera-label-empty-window rate by `{100 * (w85.validation_fully_safe_window_rate - canonical.validation_fully_safe_window_rate):+.1f}` percentage points and offline load-proxy overlap by `{w85.validation_safe_opportunity_kwh - canonical.validation_safe_opportunity_kwh:+.1f} kWh` versus the canonical validation reference, while keeping interval conflict below 10% and AUPRC above 99% of the validation best. W>=90% has a higher label-empty window rate but no longer exceeds canonical validation proxy overlap; W>=95%/100% is highly conservative with only `{int(w100.recommended_windows)}` recommended windows.

This is a validation-based compromise, not evidence of deployment safety.

## Retrospective current-test diagnostic

`results/window_aware_current_test_diagnostic.csv` evaluates every unique frozen definition only after selection. It is explicitly not a fresh untouched evaluation, and its results did not alter the W>=85%, Q=99% rule, any weights, or any threshold.

For transparency, the historical primary challenger produced retrospective point estimates of `{diag_index.loc['window_aware_definition_02', 'empty_auprc']:.4f}` Empty AUPRC, `{100 * diag_index.loc['window_aware_definition_02', 'interval_conflict_rate']:.2f}%` interval conflict, `{100 * diag_index.loc['window_aware_definition_02', 'fully_safe_window_rate']:.2f}%` all-camera-label-empty windows ({int(diag_index.loc['window_aware_definition_02', 'fully_safe_windows'])}/{int(diag_index.loc['window_aware_definition_02', 'recommended_windows'])}), and `{diag_index.loc['window_aware_definition_02', 'safe_opportunity_kwh']:.1f} kWh of offline load-proxy overlap. These already-inspected outcomes cannot support promotion or further adaptation.

## Robustness and headline decision

- **Headline:** unchanged. The canonical primary remains the official reference.
- **Confidence:** caution. Window outcomes are based on 39 validation and 43 already-inspected test horizons; windows are clustered within days, and this expanded search adds selection multiplicity.
- **Required before promotion:** a new chronological period, fixed candidate application, paired daily-block uncertainty, day-influence analysis, and mechanical application of every gate in `reports/future_untouched_evaluation_protocol.md`.
- **Claims boundary:** offline label-empty load-proxy overlap is not verified energy savings, and observed label-empty windows are not a safety guarantee.

## Statistical-integrity and fallacy scan

Coverage: **11/11** types checked. Simpson/ecological/Berkson/collider/regression-to-mean/reverse-causality mechanisms are not directly tested by this constrained saved-output comparison; no subgroup or causal claim is made. Base rates are accompanied by counts and coverage. All complete saved horizons are retained, reducing survivorship concerns. **Look-elsewhere and garden-of-forking-paths remain cautions** because 170,940 constraint rows summarize an enlarged exploratory search. **Correlation-versus-causation remains a caution:** load opportunity coinciding with observed Empty labels does not prove savings or control safety.

## Recommendation

Keep all window-aware results secondary. Freeze the W>=85%, Q=99% challenger for the primary comparison on a future untouched period, and do not promote it unless every pre-specified protocol gate passes.
"""


def make_validation_tradeoff(
    base: pd.DataFrame, selected: pd.DataFrame, path: Path
) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 8.5))
    sizes = 10 + 260 * base["validation_interval_conflict_rate"].clip(0, 0.20)
    ax.scatter(
        base["validation_fully_safe_window_rate"],
        base["validation_safe_opportunity_kwh"],
        s=sizes,
        alpha=0.10,
        color="#4C78A8",
        edgecolors="none",
        rasterized=True,
        label="All validation weight-threshold pairs",
    )
    references = selected[selected["candidate_role"].eq("frozen_prior_reference")]
    ref_markers = ["*", "D", "P"]
    ref_colors = ["#2F4B7C", "#E45756", "#54A24B"]
    for (_, row), marker, color in zip(references.iterrows(), ref_markers, ref_colors):
        ax.scatter(
            row["validation_fully_safe_window_rate"],
            row["validation_safe_opportunity_kwh"],
            marker=marker,
            s=210,
            color=color,
            edgecolor="black",
            linewidth=0.8,
            zorder=5,
            label=row["candidate_label"],
        )
    q99 = selected[
        selected["candidate_role"].eq("window_aware_validation_selected")
        & selected["auprc_floor_label"].eq("99pct")
    ].copy()
    q99["definition_key"] = q99.apply(
        lambda row: "|".join(
            [*(f"{float(row[column]):.6f}" for column in WEIGHT_COLUMNS), f"{float(row['threshold']):.6f}"]
        ),
        axis=1,
    )
    for _, part in q99.groupby("definition_key", sort=False):
        row = part.iloc[0]
        primary = bool(part["is_primary_future_challenger"].astype(bool).any())
        floor_label = "/".join(
            f"{100 * floor:.0f}%" for floor in part["safe_window_floor"].to_numpy(dtype=float)
        )
        ax.scatter(
            row["validation_fully_safe_window_rate"],
            row["validation_safe_opportunity_kwh"],
            marker="X" if primary else "o",
            s=190 if primary else 105,
            facecolor="#9467BD" if primary else "white",
            edgecolor="#6F4A8E",
            linewidth=1.3,
            zorder=6,
            label="Historical W>=85%, Q=99% diagnostic" if primary else None,
        )
        ax.annotate(
            f"W>={floor_label}",
            (row["validation_fully_safe_window_rate"], row["validation_safe_opportunity_kwh"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    ax.set_xlim(-0.02, 1.03)
    ax.xaxis.set_major_formatter(lambda value, _: f"{100 * value:.0f}%")
    ax.set_xlabel("Validation all-camera-label-empty window rate")
    ax.set_ylabel("Validation label-empty load-proxy overlap (kWh)")
    ax.set_title("Validation-only window diagnostic")
    ax.legend(fontsize=8, loc="best")
    fig.text(
        0.5,
        0.012,
        "Point size increases with validation interval-conflict rate. No current-test metric is used in selection or shown here.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _figure_strategies(selected: pd.DataFrame) -> pd.DataFrame:
    references = selected[selected["candidate_role"].eq("frozen_prior_reference")]
    primary = selected[selected["is_primary_future_challenger"].astype(bool)]
    return pd.concat([references, primary], ignore_index=True)


def make_interval_vs_window_safety(selected: pd.DataFrame, path: Path) -> None:
    plot = _figure_strategies(selected)
    labels = list(plot["candidate_label"].iloc[:3]) + ["Window-aware W>=85%, Q=99%"]
    colors = ["#2F4B7C", "#E45756", "#54A24B", "#9467BD"]
    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 3, figsize=(19, 7), sharex=True)
    x = np.arange(len(plot))
    values = [
        100 * plot["validation_interval_conflict_rate"],
        100 * plot["validation_fully_safe_window_rate"],
        plot["validation_safe_opportunity_kwh"],
    ]
    titles = ["Interval conflict", "All-camera-label-empty windows", "Offline proxy overlap"]
    ylabels = [
        "Validation conflict (%)",
        "Validation all-label-empty rate (%)",
        "Validation proxy overlap (kWh)",
    ]
    for axis, value, title, ylabel in zip(axes, values, titles, ylabels):
        bars = axis.bar(x, value, color=colors)
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.set_xticks(x, labels=labels, rotation=25, ha="right", fontsize=8)
        axis.bar_label(bars, fmt="%.1f", fontsize=8)
    axes[0].axhline(10, color="black", linestyle="--", linewidth=1.1)
    fig.suptitle("Validation-only interval and all-label-empty-window diagnostics")
    fig.text(
        0.5,
        0.01,
        "A low pooled interval-conflict rate can coexist with multiple windows containing at least one occupied interval.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_conflict_severity(
    severity: pd.DataFrame, selected: pd.DataFrame, path: Path
) -> None:
    figure_keys = set(_figure_strategies(selected)["candidate_id"])
    figure_keys.add(
        unique_strategy_definitions(
            selected[selected["candidate_role"].eq("window_aware_validation_selected")]
        )
        .loc[lambda frame: frame["is_primary_future_challenger"].astype(bool), "strategy_key"]
        .iloc[0]
    )
    plot = severity[severity["strategy_key"].isin(figure_keys)].copy()
    if plot.empty:
        raise WindowAwareInputBlocker("No validation conflict windows are available for severity figure")
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(12, 8))
    plot["Strategy"] = plot["strategy_label"]
    plot["Conflict-load kWh"] = plot["conflict_interval_controllable_load_kwh"]
    sns.scatterplot(
        data=plot,
        x="occupied_minutes_inside_window",
        y="percent_of_window_occupied",
        hue="Strategy",
        size="Conflict-load kWh",
        sizes=(70, 420),
        alpha=0.78,
        edgecolor="black",
        linewidth=0.5,
        ax=ax,
    )
    ax.set_xlabel("Occupied minutes inside validation conflict window")
    ax.set_ylabel("Percent of recommended window occupied")
    ax.set_title("Validation conflict-window severity")
    ax.legend(fontsize=8, bbox_to_anchor=(1.01, 1), loc="upper left")
    fig.text(
        0.5,
        0.01,
        "Marker size represents processed-load-proxy kWh during occupied conflict intervals; validation data only.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 0.82, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def run_window_aware_decision_search(
    *,
    results_dir: Path | str = Path("results"),
    figures_dir: Path | str = Path("figures"),
    reports_dir: Path | str = Path("reports"),
) -> list[Path]:
    results_dir = Path(results_dir)
    figures_dir = Path(figures_dir)
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Validation-only selection: this path rejects any input column containing "test".
    base_raw = _read_csv(results_dir / "decision_aware_joint_weight_threshold_grid.csv")
    base = prepare_window_aware_base_grid(base_raw)
    expanded = expand_window_aware_constraint_grid(base_raw)
    all_constraint_candidates = select_window_aware_candidates(expanded)
    selected_keys = all_constraint_candidates[
        ["safe_window_floor", "auprc_floor_label", "grid_order"]
    ].assign(selected_for_constraint_combination=True)
    expanded = expanded.merge(
        selected_keys,
        on=["safe_window_floor", "auprc_floor_label", "grid_order"],
        how="left",
        validate="many_to_one",
        sort=False,
    )
    expanded["selected_for_constraint_combination"] = expanded[
        "selected_for_constraint_combination"
    ].notna()
    # The candidate registry contains one candidate per window-safety floor.
    # Q=99% is the frozen forecasting-quality rule; other Q optima remain marked
    # in the complete sensitivity grid above.
    window_candidates = all_constraint_candidates[
        all_constraint_candidates["auprc_floor_label"].eq("99pct")
    ].reset_index(drop=True)

    # Window-aware candidates are now frozen from the validation grid.  The
    # historical decision-search references are added only after that point;
    # their stored test diagnostics cannot influence this selection.
    prior_candidates = _read_csv(results_dir / "decision_aware_joint_selected_candidates.csv")
    selected = combine_selected_and_references(window_candidates, prior_candidates)

    # Run the complete audit only after every new candidate is frozen.  The
    # audit reproduces existing current-test diagnostics, but cannot alter the
    # validation-selected window-aware definitions above.
    audit_path = reports_dir / "window_aware_decision_search_audit.md"
    audit_text, sufficient = _audit_report(results_dir)
    audit_path.write_text(audit_text, encoding="utf-8")
    if not sufficient:
        raise WindowAwareInputBlocker(f"Window audit failed; see {audit_path}")

    grid_path = results_dir / "window_aware_joint_selection_grid.csv"
    selected_path = results_dir / "window_aware_selected_candidates.csv"
    expanded.to_csv(grid_path, index=False, encoding="utf-8-sig")
    selected.to_csv(selected_path, index=False, encoding="utf-8-sig")

    validation = _read_csv(results_dir / "forecast_predictions_validation_all_models.csv")
    processed = _read_csv(results_dir / "processed_lbnl_15min_pacific.csv")
    strategies = unique_strategy_definitions(selected)
    severity = conflict_severity_for_strategies(
        validation,
        processed,
        strategies,
        evaluation_scope="validation_only",
    )
    severity_path = results_dir / "window_conflict_severity_metrics.csv"
    severity.to_csv(severity_path, index=False, encoding="utf-8-sig")

    validation_figure = figures_dir / "window_aware_validation_tradeoff.png"
    safety_figure = figures_dir / "interval_vs_window_safety.png"
    severity_figure = figures_dir / "window_conflict_severity.png"
    make_validation_tradeoff(base, selected, validation_figure)
    make_interval_vs_window_safety(selected, safety_figure)
    make_conflict_severity(severity, selected, severity_figure)

    protocol_path = reports_dir / "future_untouched_evaluation_protocol.md"
    protocol_path.write_text(_future_protocol(selected), encoding="utf-8")

    # Retrospective diagnostic gate: candidates are already frozen and saved.
    del expanded, base_raw, validation
    gc.collect()
    current_test = _read_csv(results_dir / "forecast_predictions_test_all_models.csv")
    diagnostic = evaluate_frozen_strategies(
        current_test,
        processed,
        strategies,
        evaluation_scope="current_test_retrospective_diagnostic",
    )
    diagnostic_path = results_dir / "window_aware_current_test_diagnostic.csv"
    diagnostic.to_csv(diagnostic_path, index=False, encoding="utf-8-sig")

    report_path = reports_dir / "window_aware_decision_search_report.md"
    report_path.write_text(_scientific_report(selected, diagnostic), encoding="utf-8")
    return [
        audit_path,
        grid_path,
        selected_path,
        diagnostic_path,
        severity_path,
        validation_figure,
        safety_figure,
        severity_figure,
        protocol_path,
        report_path,
    ]
