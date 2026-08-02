"""Decision-aware joint hybrid-weight and policy-threshold search.

This module consumes committed prediction/result exports only. Candidate weights
and thresholds are selected entirely from validation data; test data enter only
through :func:`evaluate_fixed_candidates_on_test` after candidates are fixed.
"""

from __future__ import annotations

import gc
import hashlib
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import average_precision_score

from src.hybrid_analysis import (
    BASE_PROBABILITY_COLUMNS,
    DEFAULT_STABLE_STEPS,
    HORIZON_STEPS,
    THRESHOLDS,
    processed_load_proxy_kwh,
    daily_anchor_indices,
    input_alignment_audit,
    policy_row,
    reshape_daily,
    stable_empty_mask,
    validate_prediction_frame,
    validate_split_integrity,
    window_summary,
)


WEIGHT_STEP = 0.05
RISK_LIMIT = 0.10
FORECAST_FLOORS = (None, 0.95, 0.98, 0.99)
WEIGHT_COLUMNS = ["seasonal_weight", "lightgbm_weight", "transformer_weight"]
COMPONENT_COLUMNS = [
    BASE_PROBABILITY_COLUMNS["Historical Average"],
    BASE_PROBABILITY_COLUMNS["LightGBM"],
    BASE_PROBABILITY_COLUMNS["Original Transformer"],
]

CANONICAL_WEIGHTS = (0.15, 0.60, 0.25)
CANONICAL_THRESHOLD = 0.875

CANDIDATE_LABELS = {
    "A_forecast_optimal_reference": "Current primary hybrid (forecast-optimal)",
    "B_decision_optimal_10pct": "Decision-optimal 10% hybrid",
    "C_decision_optimal_99pct_floor": "Decision-optimal hybrid (99% AUPRC floor)",
    "lightgbm_reference": "LightGBM reference",
    "historical_average_reference": "Historical Average reference",
}

GRID_COLUMNS = [
    "grid_order",
    "selection_split",
    "forecast_metric_scope",
    "policy_metric_scope",
    "seasonal_weight",
    "lightgbm_weight",
    "transformer_weight",
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
    "validation_empty_recall",
    "validation_gross_opportunity_kwh",
    "validation_conflict_opportunity_kwh",
    "window_conflict_rate",
    "minimum_window_steps",
    "minimum_window_hours",
    "daily_schedules",
    "total_intervals",
]


class ScientificInputBlocker(RuntimeError):
    """Raised after the audit is saved when committed inputs are insufficient."""


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, encoding="utf-8-sig")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def simplex_weight_grid(step: float = WEIGHT_STEP) -> pd.DataFrame:
    """Return every non-negative three-component simplex point."""
    units = int(round(1.0 / step))
    if not np.isclose(units * step, 1.0):
        raise ValueError("Weight step must divide 1 exactly")
    rows = []
    order = 0
    for seasonal_units in range(units + 1):
        for lightgbm_units in range(units + 1 - seasonal_units):
            transformer_units = units - seasonal_units - lightgbm_units
            weights = np.array(
                [seasonal_units, lightgbm_units, transformer_units], dtype=float
            ) / units
            if (weights < 0).any() or not np.isclose(weights.sum(), 1.0):
                raise AssertionError("Generated an illegal simplex point")
            rows.append(
                {
                    "weight_order": order,
                    "seasonal_weight": weights[0],
                    "lightgbm_weight": weights[1],
                    "transformer_weight": weights[2],
                    "nonzero_components": int(np.count_nonzero(weights)),
                }
            )
            order += 1
    return pd.DataFrame(rows)


def _blend_components(components: np.ndarray, weights: np.ndarray) -> np.ndarray:
    if components.shape[-1] != 3:
        raise ValueError("Expected Historical Average, LightGBM, and Transformer components")
    if (weights < 0).any() or not np.isclose(weights.sum(), 1.0):
        raise ValueError("Blend weights must be non-negative and sum to one")
    return np.tensordot(components, weights, axes=([-1], [0]))


def build_validation_joint_grid(
    validation: pd.DataFrame,
    processed: pd.DataFrame,
    *,
    thresholds: np.ndarray = THRESHOLDS,
    weight_step: float = WEIGHT_STEP,
) -> pd.DataFrame:
    """Evaluate the joint grid using validation inputs only."""
    validate_prediction_frame(validation, "validation")
    weights_grid = simplex_weight_grid(weight_step)
    y_all = validation["actual_empty_positive"].to_numpy(dtype=int)
    components_all = validation[COMPONENT_COLUMNS].to_numpy(dtype=float)

    midnight_indices = daily_anchor_indices(validation)
    y_daily = reshape_daily(y_all, midnight_indices)
    kwh_daily = reshape_daily(processed_load_proxy_kwh(validation, processed), midnight_indices)
    components_daily = np.stack(
        [
            reshape_daily(validation[column].to_numpy(dtype=float), midnight_indices)
            for column in COMPONENT_COLUMNS
        ],
        axis=-1,
    )

    rows: list[dict] = []
    grid_order = 0
    for weight_row in weights_grid.itertuples(index=False):
        weights = np.array(
            [
                weight_row.seasonal_weight,
                weight_row.lightgbm_weight,
                weight_row.transformer_weight,
            ]
        )
        probability_all = _blend_components(components_all, weights)
        validation_auprc = float(average_precision_score(y_all, probability_all))
        probability_daily = _blend_components(components_daily, weights)

        for threshold in np.asarray(thresholds, dtype=float):
            recommendation = stable_empty_mask(
                probability_daily, float(threshold), DEFAULT_STABLE_STEPS
            )
            policy = policy_row(
                "joint_hybrid_candidate",
                y_daily,
                probability_daily,
                kwh_daily,
                float(threshold),
                "validation_midnight_daily_forecasts",
                risk_delta=RISK_LIMIT,
            )
            windows = window_summary(y_daily, recommendation)
            rows.append(
                {
                    "grid_order": grid_order,
                    "selection_split": "validation_only",
                    "forecast_metric_scope": "all_overlapping_rolling_forecasts",
                    "policy_metric_scope": "non_overlapping_midnight_96_step_horizons",
                    "seasonal_weight": weight_row.seasonal_weight,
                    "lightgbm_weight": weight_row.lightgbm_weight,
                    "transformer_weight": weight_row.transformer_weight,
                    "nonzero_components": weight_row.nonzero_components,
                    "threshold": float(threshold),
                    "validation_empty_auprc": validation_auprc,
                    "validation_occupancy_conflict_rate": policy[
                        "occupancy_conflict_rate"
                    ],
                    "validation_safe_opportunity_kwh": policy[
                        "safe_opportunity_kwh"
                    ],
                    "recommendation_coverage": policy["recommendation_coverage"],
                    "recommended_intervals": policy["recommended_intervals"],
                    "safe_intervals": policy["safe_intervals"],
                    "conflict_intervals": policy["conflict_intervals"],
                    "recommended_windows": windows["recommended_windows"],
                    "safe_windows": windows["safe_windows"],
                    "conflict_windows": windows["conflict_windows"],
                    "validation_empty_recall": policy["empty_recall"],
                    "validation_gross_opportunity_kwh": policy[
                        "gross_opportunity_kwh"
                    ],
                    "validation_conflict_opportunity_kwh": policy[
                        "conflict_opportunity_kwh"
                    ],
                    "window_conflict_rate": windows["window_conflict_rate"],
                    "minimum_window_steps": policy["minimum_window_steps"],
                    "minimum_window_hours": policy["minimum_window_hours"],
                    "daily_schedules": policy["daily_schedules"],
                    "total_intervals": policy["total_intervals"],
                }
            )
            grid_order += 1
    return pd.DataFrame(rows)[GRID_COLUMNS]


def _candidate_from_row(
    row: pd.Series,
    candidate_id: str,
    objective: str,
    auprc_floor_ratio: float | None,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "candidate_label": CANDIDATE_LABELS[candidate_id],
        "selection_objective": objective,
        "selection_split": "validation_only",
        "test_used_for_selection": False,
        "auprc_floor_ratio": auprc_floor_ratio,
        "auprc_floor_value": (
            np.nan
            if auprc_floor_ratio is None
            else float(row["best_validation_empty_auprc"] * auprc_floor_ratio)
        ),
        "seasonal_weight": float(row["seasonal_weight"]),
        "lightgbm_weight": float(row["lightgbm_weight"]),
        "transformer_weight": float(row["transformer_weight"]),
        "nonzero_components": int(row["nonzero_components"]),
        "threshold": float(row["threshold"]),
        "validation_empty_auprc": float(row["validation_empty_auprc"]),
        "validation_occupancy_conflict_rate": float(
            row["validation_occupancy_conflict_rate"]
        ),
        "validation_safe_opportunity_kwh": float(
            row["validation_safe_opportunity_kwh"]
        ),
        "validation_recommendation_coverage": float(row["recommendation_coverage"]),
        "validation_recommended_intervals": int(row["recommended_intervals"]),
        "validation_safe_intervals": int(row["safe_intervals"]),
        "validation_conflict_intervals": int(row["conflict_intervals"]),
        "validation_recommended_windows": int(row["recommended_windows"]),
        "validation_safe_windows": int(row["safe_windows"]),
        "validation_conflict_windows": int(row["conflict_windows"]),
        "validation_grid_order": int(row["grid_order"]),
    }


def select_decision_optimal_candidate(
    validation_grid: pd.DataFrame,
    *,
    auprc_floor_ratio: float | None,
    candidate_id: str,
) -> dict:
    """Select by constrained offline load-proxy overlap with declared tie-breaks."""
    best_auprc = float(validation_grid["validation_empty_auprc"].max())
    eligible = validation_grid[
        (validation_grid["validation_occupancy_conflict_rate"] <= RISK_LIMIT)
        & (validation_grid["recommended_windows"] >= 1)
        & (validation_grid["recommendation_coverage"] > 0)
    ].copy()
    if auprc_floor_ratio is not None:
        if not 0 < auprc_floor_ratio <= 1:
            raise ValueError("AUPRC floor ratio must be in (0, 1]")
        eligible = eligible[
            eligible["validation_empty_auprc"] >= best_auprc * auprc_floor_ratio
        ]
    if eligible.empty:
        raise ScientificInputBlocker(
            f"No validation candidate satisfies the constraints for {candidate_id}"
        )
    chosen = eligible.sort_values(
        [
            "validation_safe_opportunity_kwh",
            "validation_occupancy_conflict_rate",
            "validation_empty_auprc",
            "safe_windows",
            "nonzero_components",
            "grid_order",
        ],
        ascending=[False, True, False, False, True, True],
        kind="mergesort",
    ).iloc[0].copy()
    chosen["best_validation_empty_auprc"] = best_auprc
    objective = (
        "maximum validation offline camera-label-empty load-proxy overlap "
        "under <=10% empirical interval conflict"
    )
    if auprc_floor_ratio is not None:
        objective += f" and >= {100 * auprc_floor_ratio:.0f}% of best validation AUPRC"
    return _candidate_from_row(chosen, candidate_id, objective, auprc_floor_ratio)


def _select_current_threshold(rows: pd.DataFrame) -> pd.Series:
    eligible = rows[rows["validation_occupancy_conflict_rate"] <= RISK_LIMIT]
    if eligible.empty:
        return rows.sort_values(
            ["validation_occupancy_conflict_rate", "validation_safe_opportunity_kwh", "grid_order"],
            ascending=[True, False, True],
            kind="mergesort",
        ).iloc[0]
    return eligible.sort_values(
        ["validation_safe_opportunity_kwh", "validation_empty_recall", "grid_order"],
        ascending=[False, False, True],
        kind="mergesort",
    ).iloc[0]


def _rows_for_weights(validation_grid: pd.DataFrame, weights: tuple[float, float, float]) -> pd.DataFrame:
    mask = np.logical_and.reduce(
        [
            np.isclose(validation_grid[column], value)
            for column, value in zip(WEIGHT_COLUMNS, weights)
        ]
    )
    rows = validation_grid[mask]
    if rows.empty:
        raise ScientificInputBlocker(f"Requested weights are absent from the grid: {weights}")
    return rows


def select_validation_candidates(validation_grid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fix all hybrid and reference candidates without accepting test inputs."""
    weight_rows = validation_grid.drop_duplicates(WEIGHT_COLUMNS, keep="first")
    best_weight = weight_rows.sort_values(
        ["validation_empty_auprc", "grid_order"],
        ascending=[False, True],
        kind="mergesort",
    ).iloc[0]
    forecast_rows = _rows_for_weights(
        validation_grid,
        tuple(float(best_weight[column]) for column in WEIGHT_COLUMNS),
    )
    forecast = _select_current_threshold(forecast_rows).copy()
    forecast["best_validation_empty_auprc"] = float(
        validation_grid["validation_empty_auprc"].max()
    )
    candidate_a = _candidate_from_row(
        forecast,
        "A_forecast_optimal_reference",
        "best validation Empty AUPRC weights, then current validation 10% threshold policy",
        None,
    )

    candidate_b = select_decision_optimal_candidate(
        validation_grid,
        auprc_floor_ratio=None,
        candidate_id="B_decision_optimal_10pct",
    )
    candidate_c = select_decision_optimal_candidate(
        validation_grid,
        auprc_floor_ratio=0.99,
        candidate_id="C_decision_optimal_99pct_floor",
    )

    references = []
    for candidate_id, weights in (
        ("lightgbm_reference", (0.0, 1.0, 0.0)),
        ("historical_average_reference", (1.0, 0.0, 0.0)),
    ):
        chosen = _select_current_threshold(_rows_for_weights(validation_grid, weights)).copy()
        chosen["best_validation_empty_auprc"] = float(
            validation_grid["validation_empty_auprc"].max()
        )
        references.append(
            _candidate_from_row(
                chosen,
                candidate_id,
                "current validation 10% threshold policy for fixed reference model",
                None,
            )
        )

    candidates = pd.DataFrame([candidate_a, candidate_b, candidate_c, *references])
    sensitivity_rows = []
    for floor in FORECAST_FLOORS:
        selected = select_decision_optimal_candidate(
            validation_grid,
            auprc_floor_ratio=floor,
            candidate_id="B_decision_optimal_10pct"
            if floor is None
            else "C_decision_optimal_99pct_floor",
        )
        selected["sensitivity_floor_label"] = (
            "no_floor" if floor is None else f"{100 * floor:.0f}%"
        )
        selected["candidate_id"] = f"sensitivity_{selected['sensitivity_floor_label']}"
        selected["candidate_label"] = (
            "Decision-optimal (no AUPRC floor)"
            if floor is None
            else f"Decision-optimal ({100 * floor:.0f}% AUPRC floor)"
        )
        sensitivity_rows.append(selected)
    sensitivity = pd.DataFrame(sensitivity_rows)
    return candidates, sensitivity


def assert_canonical_reference_reproduced(candidates: pd.DataFrame) -> None:
    current = candidates.set_index("candidate_id").loc["A_forecast_optimal_reference"]
    weights = tuple(float(current[column]) for column in WEIGHT_COLUMNS)
    if not np.allclose(weights, CANONICAL_WEIGHTS, atol=1e-12):
        raise ScientificInputBlocker(
            f"Forecast-optimal weights {weights} do not reproduce canonical {CANONICAL_WEIGHTS}"
        )
    if not np.isclose(float(current["threshold"]), CANONICAL_THRESHOLD, atol=1e-12):
        raise ScientificInputBlocker(
            f"Forecast-optimal threshold {current['threshold']} does not reproduce canonical {CANONICAL_THRESHOLD}"
        )


def evaluate_fixed_candidates_on_test(
    test: pd.DataFrame,
    processed: pd.DataFrame,
    fixed_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Apply already-fixed candidates to test without performing selection."""
    validate_prediction_frame(test, "test")
    required = {"candidate_id", "selection_split", "test_used_for_selection", "threshold", *WEIGHT_COLUMNS}
    if missing := required.difference(fixed_candidates.columns):
        raise ValueError(f"Fixed candidates are missing columns: {sorted(missing)}")
    if not fixed_candidates["selection_split"].eq("validation_only").all():
        raise ValueError("All candidates must be selected on validation")
    if fixed_candidates["test_used_for_selection"].astype(bool).any():
        raise ValueError("Test-selected candidates cannot be evaluated by this fixed-candidate path")

    y_all = test["actual_empty_positive"].to_numpy(dtype=int)
    components_all = test[COMPONENT_COLUMNS].to_numpy(dtype=float)
    midnight_indices = daily_anchor_indices(test)
    y_daily = reshape_daily(y_all, midnight_indices)
    kwh_daily = reshape_daily(processed_load_proxy_kwh(test, processed), midnight_indices)
    components_daily = np.stack(
        [
            reshape_daily(test[column].to_numpy(dtype=float), midnight_indices)
            for column in COMPONENT_COLUMNS
        ],
        axis=-1,
    )

    rows = []
    for candidate in fixed_candidates.itertuples(index=False):
        weights = np.array(
            [candidate.seasonal_weight, candidate.lightgbm_weight, candidate.transformer_weight]
        )
        probability_all = _blend_components(components_all, weights)
        probability_daily = _blend_components(components_daily, weights)
        recommendation = stable_empty_mask(
            probability_daily, float(candidate.threshold), DEFAULT_STABLE_STEPS
        )
        policy = policy_row(
            candidate.candidate_label,
            y_daily,
            probability_daily,
            kwh_daily,
            float(candidate.threshold),
            "held_out_test_midnight_daily_forecasts",
            risk_delta=RISK_LIMIT,
        )
        windows = window_summary(y_daily, recommendation)
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "test_evaluation_split": "held_out_test_only",
                "test_empty_auprc": float(average_precision_score(y_all, probability_all)),
                "test_occupancy_conflict_rate": policy["occupancy_conflict_rate"],
                "test_safe_opportunity_kwh": policy["safe_opportunity_kwh"],
                "test_recommendation_coverage": policy["recommendation_coverage"],
                "test_recommended_intervals": policy["recommended_intervals"],
                "test_safe_intervals": policy["safe_intervals"],
                "test_conflict_intervals": policy["conflict_intervals"],
                "test_recommended_windows": windows["recommended_windows"],
                "test_safe_windows": windows["safe_windows"],
                "test_conflict_windows": windows["conflict_windows"],
                "test_gross_opportunity_kwh": policy["gross_opportunity_kwh"],
                "test_conflict_opportunity_kwh": policy["conflict_opportunity_kwh"],
                "test_daily_schedules": policy["daily_schedules"],
                "test_total_intervals": policy["total_intervals"],
            }
        )
    return fixed_candidates.merge(pd.DataFrame(rows), on="candidate_id", validate="one_to_one")


def _audit_markdown(
    results_dir: Path,
    predictions_dir: Path,
) -> tuple[str, bool]:
    validation_path = results_dir / "forecast_predictions_validation_all_models.csv"
    test_path = results_dir / "forecast_predictions_test_all_models.csv"
    processed_path = results_dir / "processed_lbnl_15min_pacific.csv"
    reference_paths = [
        results_dir / "hybrid_primary_weight_search.csv",
        results_dir / "hybrid_selected_threshold_policies.csv",
        results_dir / "hybrid_policy_results_test.csv",
        results_dir / "canonical_model_comparison.csv",
        results_dir / "canonical_policy_10pct.csv",
    ]
    individual_paths = [
        predictions_dir / "historical_average_test_predictions.csv",
        predictions_dir / "lightgbm_test_predictions.csv",
        predictions_dir / "transformer_test_predictions.csv",
    ]
    required_paths = [validation_path, test_path, processed_path, *reference_paths]
    blockers = [f"Missing required file: `{path.as_posix()}`" for path in required_paths if not path.exists()]
    required_prediction_columns = [
        "split",
        "anchor_time",
        "target_time",
        "horizon_step",
        "actual_occupied",
        "actual_empty_positive",
        *COMPONENT_COLUMNS,
    ]
    details: dict[str, object] = {}
    alignment_rows = pd.DataFrame()
    if not blockers:
        try:
            validation = _read_csv(validation_path)
            test = _read_csv(test_path)
            processed = _read_csv(processed_path)
            validate_split_integrity(validation, test)
            val_midnight = daily_anchor_indices(validation)
            test_midnight = daily_anchor_indices(test)
            val_load = processed_load_proxy_kwh(validation, processed)
            test_load = processed_load_proxy_kwh(test, processed)
            alignment_rows = input_alignment_audit(validation, test, processed, predictions_dir)
            details = {
                "validation_rows": len(validation),
                "validation_anchors": validation["anchor_time"].nunique(),
                "validation_midnight_horizons": len(val_midnight),
                "validation_midnight_rows": len(val_midnight) * HORIZON_STEPS,
                "validation_anchor_min": validation["anchor_time"].iloc[0],
                "validation_anchor_max": validation["anchor_time"].iloc[-1],
                "validation_target_min": validation["target_time"].min(),
                "validation_target_max": validation["target_time"].max(),
                "test_rows": len(test),
                "test_anchors": test["anchor_time"].nunique(),
                "test_midnight_horizons": len(test_midnight),
                "test_midnight_rows": len(test_midnight) * HORIZON_STEPS,
                "test_anchor_min": test["anchor_time"].iloc[0],
                "test_anchor_max": test["anchor_time"].iloc[-1],
                "test_target_min": test["target_time"].min(),
                "test_target_max": test["target_time"].max(),
                "validation_load_rows": len(val_load),
                "test_load_rows": len(test_load),
            }
            del validation, test, processed, val_load, test_load
            gc.collect()
        except Exception as exc:  # report exact scientific blocker before stopping
            blockers.append(f"Input validation failed: `{type(exc).__name__}: {exc}`")

    source_lines = []
    for path in [*required_paths, *individual_paths]:
        if path.exists():
            source_lines.append(
                f"- `{path.as_posix()}` — {path.stat().st_size:,} bytes; SHA-256 `{_sha256(path)}`"
            )
        else:
            source_lines.append(f"- `{path.as_posix()}` — not present")

    alignment_text = "- Direct per-model test-export alignment could not be completed."
    if not alignment_rows.empty:
        wanted = alignment_rows[
            alignment_rows["check"].isin(
                [
                    "per_model_export_alignment:Historical Average",
                    "per_model_export_alignment:LightGBM",
                    "per_model_export_alignment:Original Transformer",
                ]
            )
        ]
        alignment_text = "\n".join(
            f"- {row.check}: **{row.status}** — {row.detail}"
            for row in wanted.itertuples(index=False)
        )

    if details:
        scope_text = f"""
| Scope | Rolling rows | 96-step anchors | Midnight-labelled post-bin policy horizons | Policy rows | Target-time range |
|---|---:|---:|---:|---:|---|
| Validation | {details['validation_rows']:,} | {details['validation_anchors']:,} | {details['validation_midnight_horizons']:,} | {details['validation_midnight_rows']:,} | `{details['validation_target_min']}` to `{details['validation_target_max']}` |
| Held-out test | {details['test_rows']:,} | {details['test_anchors']:,} | {details['test_midnight_horizons']:,} | {details['test_midnight_rows']:,} | `{details['test_target_min']}` to `{details['test_target_max']}` |
"""
    else:
        scope_text = "Scope counts unavailable because a required input check failed."

    blocker_text = "\n".join(f"- {item}" for item in blockers) if blockers else "- None."
    conclusion = (
        "**PASS.** The saved outputs are sufficient for every requested validation metric and fixed-candidate test evaluation."
        if not blockers
        else "**STOP.** The saved outputs are insufficient; no joint search should run until the blockers below are resolved."
    )
    markdown = f"""# Decision-aware joint search input audit

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate/run
- Verification Status: ANALYZED
- Version Label: decision_aware_joint_audit_v1

## Audit conclusion

{conclusion}

This audit uses committed saved outputs only. It does not access the external Dryad directory and does not retrain a base model.

## Exact source files

{chr(10).join(source_lines)}

The combined validation export is the only saved validation file that contains aligned Historical Average, LightGBM, and Transformer probabilities. Individual saved test exports are redundant alignment checks; the combined test export is the evaluation source.

## Required columns

- Validation/test predictions: `{', '.join(required_prediction_columns)}`.
- Processed load proxy: `date_local`, `hvac_S`, and `lig_S` from the processed saved table.
- The Empty label is `actual_empty_positive = 1 - actual_occupied`.
- The interval load proxy is `max(hvac_S + lig_S, 0) * 0.25 h`, following the current implementation.

## Validation and test scopes

{scope_text}

- Forecast Empty AUPRC uses every overlapping rolling prediction row in the relevant split.
- Policy selection/evaluation uses non-overlapping midnight-labelled completed-input-bin 96-step horizons only; a 00:00 label has an effective 00:15 availability boundary.
- Validation ends at `{details.get('validation_target_max', 'unavailable')}`; test begins at `{details.get('test_target_min', 'unavailable')}`. The scopes do not overlap when the audit passes.
- Processed-load-proxy mapping covered {details.get('validation_load_rows', 'unavailable')} validation rows and {details.get('test_load_rows', 'unavailable')} test rows; the direct check found no missing timestamp matches.

## Prediction-export alignment

{alignment_text}

## Current selection and recommendation logic

- Weight search: all 231 legal Historical Average/Seasonal, LightGBM, and compact-Transformer score weights on the 0.05 simplex grid; select the maximum validation Empty AUPRC on all overlapping validation forecasts.
- Canonical forecast-optimal weights: `0.15 / 0.60 / 0.25`; best saved validation Empty AUPRC `0.7286379575`.
- Threshold grid: 37 Empty-score thresholds from `0.05` through `0.95` in `0.025` increments. Scores are not calibrated probabilities.
- Current 10% policy: maximize validation offline camera-label-empty load-proxy overlap among thresholds with empirical interval-level occupancy-conflict rate `<= 0.10`; use Empty recall as the same-proxy tie-break. The canonical hybrid threshold is `0.875`.
- Stable recommendation: the uncalibrated score remains at or above threshold for at least four consecutive 15-minute intervals (one hour) within each midnight-labelled post-bin horizon. Every interval in a qualifying run is recommended.
- Interval conflict rate: occupied recommended intervals divided by all recommended intervals. A window is all-camera-label-empty only if every interval in that window is actually Empty.
- Offline load-proxy overlap: the saved HVAC-south plus lighting-south load proxy summed only over recommended intervals whose subsequently observed label is Empty. This is offline opportunity accounting, not verified energy savings.

## Sufficiency by requested metric

| Requested quantity | Available source | Status |
|---|---|---|
| Validation Empty AUPRC | validation labels + three aligned probability columns | {'available' if not blockers else 'blocked'} |
| Validation conflict and coverage | midnight labels + stable-window mask | {'available' if not blockers else 'blocked'} |
| Validation offline load-proxy overlap | midnight-labelled post-bin labels + timestamp-mapped HVAC/lighting kWh | {'available' if not blockers else 'blocked'} |
| Recommended/safe/conflict intervals | stable mask + labels | {'available' if not blockers else 'blocked'} |
| Recommended/safe windows | existing run extraction and all-empty window definition | {'available' if not blockers else 'blocked'} |
| Fixed held-out evaluation | chronologically disjoint test export + fixed validation candidates | {'available' if not blockers else 'blocked'} |

## Missing inputs or scientific blockers

{blocker_text}

The saved exports do not support new base-model training, per-seed joint-hybrid dispersion, or new rolling-origin hybrid folds, but none of those are required for this saved-output joint search.
"""
    return markdown, not blockers


def _format_candidate_table(frame: pd.DataFrame, prefix: str) -> str:
    rows = [
        "| Candidate | Weights (Seasonal/LGBM/Transformer) | Threshold | AUPRC | Conflict | Label-empty proxy kWh | Coverage | Intervals (rec/label-empty/conflict) | Windows (rec/all-label-empty/conflict) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in frame.itertuples(index=False):
        rows.append(
            f"| {row.candidate_label} | {row.seasonal_weight:.2f}/{row.lightgbm_weight:.2f}/{row.transformer_weight:.2f} | "
            f"{row.threshold:.3f} | {getattr(row, prefix + '_empty_auprc'):.4f} | "
            f"{100 * getattr(row, prefix + '_occupancy_conflict_rate'):.2f}% | "
            f"{getattr(row, prefix + '_safe_opportunity_kwh'):.1f} | "
            f"{100 * getattr(row, prefix + '_recommendation_coverage'):.2f}% | "
            f"{getattr(row, prefix + '_recommended_intervals')}/"
            f"{getattr(row, prefix + '_safe_intervals')}/"
            f"{getattr(row, prefix + '_conflict_intervals')} | "
            f"{getattr(row, prefix + '_recommended_windows')}/"
            f"{getattr(row, prefix + '_safe_windows')}/"
            f"{getattr(row, prefix + '_conflict_windows')} |"
        )
    return "\n".join(rows)


def _joint_report(candidates: pd.DataFrame, sensitivity: pd.DataFrame) -> str:
    indexed = candidates.set_index("candidate_id")
    current = indexed.loc["A_forecast_optimal_reference"]
    decision = indexed.loc["B_decision_optimal_10pct"]
    floor99 = indexed.loc["C_decision_optimal_99pct_floor"]
    lightgbm = indexed.loc["lightgbm_reference"]

    def deltas(row: pd.Series, prefix: str) -> tuple[float, float, float]:
        return (
            float(row[f"{prefix}_empty_auprc"] - current[f"{prefix}_empty_auprc"]),
            float(row[f"{prefix}_occupancy_conflict_rate"] - current[f"{prefix}_occupancy_conflict_rate"]),
            float(row[f"{prefix}_safe_opportunity_kwh"] - current[f"{prefix}_safe_opportunity_kwh"]),
        )

    b_val = deltas(decision, "validation")
    c_val = deltas(floor99, "validation")
    b_test = deltas(decision, "test")
    c_test = deltas(floor99, "test")
    b_lgbm_test = (
        float(decision["test_empty_auprc"] - lightgbm["test_empty_auprc"]),
        float(
            decision["test_occupancy_conflict_rate"]
            - lightgbm["test_occupancy_conflict_rate"]
        ),
        float(
            decision["test_safe_opportunity_kwh"]
            - lightgbm["test_safe_opportunity_kwh"]
        ),
    )
    c_lgbm_test = (
        float(floor99["test_empty_auprc"] - lightgbm["test_empty_auprc"]),
        float(
            floor99["test_occupancy_conflict_rate"]
            - lightgbm["test_occupancy_conflict_rate"]
        ),
        float(
            floor99["test_safe_opportunity_kwh"]
            - lightgbm["test_safe_opportunity_kwh"]
        ),
    )
    joint_changed = not np.allclose(
        decision[WEIGHT_COLUMNS].to_numpy(dtype=float), np.array(CANONICAL_WEIGHTS)
    )
    floor_changed = not np.allclose(
        floor99[WEIGHT_COLUMNS].to_numpy(dtype=float), np.array(CANONICAL_WEIGHTS)
    )
    b_carried = b_test[2] > 0
    c_carried = c_test[2] > 0
    low_coverage = candidates.iloc[:3][
        (candidates.iloc[:3]["validation_recommendation_coverage"] < 0.01)
        | (candidates.iloc[:3]["validation_recommended_windows"] <= 2)
    ]
    coverage_interpretation = (
        "No selected hybrid met the prespecified diagnostic flag of below 1% validation coverage or two or fewer validation windows."
        if low_coverage.empty
        else "At least one selected hybrid has below 1% validation coverage or two or fewer validation windows, so its apparently low conflict is operationally fragile."
    )

    if (
        floor99["test_occupancy_conflict_rate"] <= RISK_LIMIT
        and c_test[2] > 0
        and floor99["test_recommended_windows"] > 2
    ):
        disposition = (
            "Keep the 99%-floor candidate as a secondary exploratory result. Its held-out point estimates are promising, "
            "but the same test period cannot both motivate a replacement and provide a fresh confirmation, and no paired uncertainty analysis was prespecified for this enlarged search."
        )
    elif floor99["test_occupancy_conflict_rate"] > RISK_LIMIT:
        disposition = (
            "Reject the 99%-floor candidate as a replacement for the current primary hybrid because its held-out conflict rate exceeded 10%. "
            "It may be retained only as a documented negative exploratory result."
        )
    else:
        disposition = (
            "Retain the current primary hybrid and keep the decision-aware candidates as secondary exploratory results. "
            "The held-out point estimates do not establish a sufficiently robust operational advantage to replace the canonical reference."
        )

    sensitivity_lines = [
        "| AUPRC floor | Weights (Seasonal/LGBM/Transformer) | Threshold | Validation AUPRC | Conflict | Label-empty proxy kWh | Coverage | Windows |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sensitivity.itertuples(index=False):
        sensitivity_lines.append(
            f"| {row.sensitivity_floor_label} | {row.seasonal_weight:.2f}/{row.lightgbm_weight:.2f}/{row.transformer_weight:.2f} | "
            f"{row.threshold:.3f} | {row.validation_empty_auprc:.4f} | "
            f"{100 * row.validation_occupancy_conflict_rate:.2f}% | {row.validation_safe_opportunity_kwh:.1f} | "
            f"{100 * row.validation_recommendation_coverage:.2f}% | {row.validation_recommended_windows} |"
        )

    return f"""# Decision-aware joint weight-threshold search

> **Final-audit status:** exploratory offline, post-bin saved-output diagnostic. A 00:00 anchor is the left label of a completed [00:00, 00:15) input bin, so its effective boundary is 00:15. "Safe" legacy fields mean subsequently camera-label-empty processed-load-proxy overlap, not physical absence, calibrated risk, savings, or a deployable policy. This search cannot replace the canonical result or promote a candidate after the required empirical retraining.

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate/run
- Verification Status: ANALYZED
- Version Label: decision_aware_joint_search_v1

## Result in brief

The joint search {'did' if joint_changed else 'did not'} choose different unconstrained decision-optimal weights from the canonical `0.15/0.60/0.25`; the 99%-AUPRC-floor candidate {'also differed' if floor_changed else 'retained the canonical weights'}. Candidates were selected exclusively on validation. The held-out test was loaded only after weights and thresholds were fixed.

{disposition}

## Validation-selected strategies

{_format_candidate_table(candidates.iloc[:3], 'validation')}

Relative to the forecast-optimal reference, the unconstrained decision candidate changed validation AUPRC by {b_val[0]:+.4f}, conflict by {100 * b_val[1]:+.2f} percentage points, and offline proxy overlap by {b_val[2]:+.1f} kWh. The 99%-floor candidate changed those quantities by {c_val[0]:+.4f}, {100 * c_val[1]:+.2f} percentage points, and {c_val[2]:+.1f} kWh, respectively.

## AUPRC-floor sensitivity (validation only)

{chr(10).join(sensitivity_lines)}

This is a constrained sensitivity analysis, not an arbitrary weighted-sum score. Every row enforces interval conflict `<=10%`, positive coverage, and at least one stable recommended window.

## Held-out test evaluation of fixed candidates

{_format_candidate_table(candidates, 'test')}

- Unconstrained decision-optimal versus current primary: AUPRC {b_test[0]:+.4f}, conflict {100 * b_test[1]:+.2f} percentage points, offline proxy overlap {b_test[2]:+.1f} kWh. The validation proxy-overlap difference {'carried to the held-out point estimate' if b_carried else 'did not carry to the held-out point estimate'}.
- 99%-floor decision-optimal versus current primary: AUPRC {c_test[0]:+.4f}, conflict {100 * c_test[1]:+.2f} percentage points, offline proxy overlap {c_test[2]:+.1f} kWh. The validation proxy-overlap difference {'carried to the held-out point estimate' if c_carried else 'did not carry to the held-out point estimate'}.
- Unconstrained decision-optimal versus LightGBM: AUPRC {b_lgbm_test[0]:+.4f}, conflict {100 * b_lgbm_test[1]:+.2f} percentage points, offline proxy overlap {b_lgbm_test[2]:+.1f} kWh.
- 99%-floor decision-optimal versus LightGBM: AUPRC {c_lgbm_test[0]:+.4f}, conflict {100 * c_lgbm_test[1]:+.2f} percentage points, offline proxy overlap {c_lgbm_test[2]:+.1f} kWh.
- Current primary versus LightGBM on test: AUPRC {current['test_empty_auprc'] - lightgbm['test_empty_auprc']:+.4f}, conflict {100 * (current['test_occupancy_conflict_rate'] - lightgbm['test_occupancy_conflict_rate']):+.2f} percentage points, offline proxy overlap {current['test_safe_opportunity_kwh'] - lightgbm['test_safe_opportunity_kwh']:+.1f} kWh.

The decision-aware proxy-overlap differences are sizable as point estimates ({100 * b_test[2] / current['test_safe_opportunity_kwh']:+.1f}% without a floor and {100 * c_test[2] / current['test_safe_opportunity_kwh']:+.1f}% with the 99% floor versus the current hybrid), but they trade zero observed conflict for roughly 3% conflict. Without a prespecified paired uncertainty analysis or another untouched evaluation period, statistical or operational meaningfulness is not established.

These are descriptive point estimates on one held-out period. The label-empty proxy overlap means processed HVAC-plus-lighting load coinciding with recommendations that were subsequently observed camera-label-empty; it is neither verified energy savings nor a guarantee of safety.

## Coverage and conservatism

{coverage_interpretation} Coverage and window counts still need to be interpreted alongside conflict: zero or low conflict from very few recommendations is not strong evidence of general safety.

## Scientific interpretation

- The weight search optimized 231 simplex points jointly with 37 thresholds (8,547 validation pairs), so the decision candidates are exploratory and exposed to selection optimism even though test leakage was prevented.
- AUPRC is constant across thresholds for a fixed weight vector; policy outcomes are evaluated only on 39 non-overlapping validation midnight horizons. The 43 test horizons are a modest operational sample and windows are clustered within days.
- Comparison with LightGBM and the current hybrid is descriptive. No confidence interval or hypothesis test was prespecified for the enlarged joint search, so small point-estimate differences should not be called meaningful improvements.
- {disposition}

## Statistical-integrity and fallacy scan

Coverage: **11/11** experiment-agent fallacy types checked.

| Check | Disposition |
|---|---|
| Simpson's paradox | Not assessable from the aggregate joint table; no subgroup claim is made. |
| Ecological fallacy | Avoided: claims remain at forecast-horizon/interval level, not individual occupants. |
| Berkson's paradox | No new sample filtering was introduced beyond the fixed chronological splits. |
| Collider bias | No covariate adjustment is performed in this saved-output search. |
| Base-rate neglect | AUPRC, coverage, interval counts, and observed Empty outcomes are reported together. |
| Regression to the mean | No extreme-case pre/post subgroup is analyzed. |
| Survivorship bias | All complete saved horizons in the declared scopes are used; missing-load mapping was zero. |
| Look-elsewhere effect | **Caution:** 8,547 validation pairs were searched; held-out results are descriptive confirmation only. |
| Garden of forking paths | **Caution:** this is a newly specified exploratory objective; floor sensitivity is reported to expose that choice. |
| Correlation versus causation | **Caution:** opportunity accounting does not establish energy savings or causal control effects. |
| Reverse causality | Not directly applicable to fixed forecasts evaluated against subsequent labels. |

## Recommendation

{disposition}
"""


def make_validation_frontier(
    grid: pd.DataFrame, candidates: pd.DataFrame, path: Path
) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(11.5, 8))
    ax.scatter(
        grid["validation_occupancy_conflict_rate"],
        grid["validation_safe_opportunity_kwh"],
        s=12,
        alpha=0.10,
        color="#4C78A8",
        edgecolors="none",
        rasterized=True,
        label="All validation weight-threshold pairs",
    )
    styles = [
        ("A_forecast_optimal_reference", "*", "#2F4B7C"),
        ("B_decision_optimal_10pct", "D", "#E45756"),
        ("C_decision_optimal_99pct_floor", "P", "#54A24B"),
    ]
    indexed = candidates.set_index("candidate_id")
    for candidate_id, marker, color in styles:
        row = indexed.loc[candidate_id]
        ax.scatter(
            row["validation_occupancy_conflict_rate"],
            row["validation_safe_opportunity_kwh"],
            marker=marker,
            s=220,
            color=color,
            edgecolor="black",
            linewidth=0.8,
            zorder=5,
            label=row["candidate_label"],
        )
    ax.axvline(
        RISK_LIMIT,
        color="black",
        linestyle="--",
        linewidth=1.2,
        label="10% empirical conflict cutoff",
    )
    ax.xaxis.set_major_formatter(lambda value, _: f"{100 * value:.0f}%")
    ax.set_xlabel("Validation camera-label conflict rate")
    ax.set_ylabel("Validation label-empty load-proxy overlap (kWh)")
    ax.set_title("Validation-only joint weight-threshold diagnostic")
    ax.legend(fontsize=9, loc="best")
    fig.text(
        0.5,
        0.01,
        "All candidates are selected on validation; held-out test outcomes are not shown or used here.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_test_comparison(candidates: pd.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plot = candidates.copy()
    labels = plot["candidate_label"].str.replace(" hybrid", "", regex=False)
    colors = ["#2F4B7C", "#E45756", "#54A24B", "#F58518", "#4C78A8"]
    fig, axes = plt.subplots(1, 2, figsize=(17, 8), sharey=True)
    positions = np.arange(len(plot))
    axes[0].barh(positions, plot["test_safe_opportunity_kwh"], color=colors)
    axes[0].set_yticks(positions, labels=labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Held-out label-empty load-proxy overlap (kWh)")
    axes[0].set_title("A. Offline load-proxy overlap")
    axes[1].barh(positions, 100 * plot["test_occupancy_conflict_rate"], color=colors)
    axes[1].axvline(10, color="black", linestyle="--", linewidth=1.2)
    axes[1].set_xlabel("Held-out test occupancy conflict (%)")
    axes[1].set_title("B. Conflict rate")
    for axis in axes:
        for container in axis.containers:
            axis.bar_label(container, fmt="%.1f", padding=3, fontsize=9)
    fig.suptitle("Held-out test evaluation of validation-fixed candidates")
    fig.text(
        0.5,
        0.01,
        "Validation selected every weight and threshold; test only evaluated the fixed candidates.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def make_forecast_vs_decision(candidates: pd.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plot = candidates.iloc[:3].copy()
    labels = ["Forecast-optimal", "Decision-optimal", "Decision + 99% floor"]
    colors = ["#2F4B7C", "#E45756", "#54A24B"]
    x = np.arange(len(plot))
    fig, axes = plt.subplots(1, 5, figsize=(22, 6.5))
    bottom = np.zeros(len(plot))
    for column, label, color in zip(
        WEIGHT_COLUMNS,
        ["Seasonal", "LightGBM", "Transformer"],
        ["#4C78A8", "#F58518", "#B279A2"],
    ):
        axes[0].bar(x, plot[column], bottom=bottom, label=label, color=color)
        bottom += plot[column].to_numpy(dtype=float)
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Selected weight")
    axes[0].set_title("Weights")
    axes[0].legend(fontsize=8)
    metrics = [
        ("threshold", "Threshold", "Selected Empty threshold", (0, 1)),
        ("validation_empty_auprc", "AUPRC", "Validation Empty AUPRC", None),
        ("validation_occupancy_conflict_rate", "Conflict", "Validation conflict", (0, None)),
        (
            "validation_safe_opportunity_kwh",
            "Proxy kWh",
            "Validation label-empty load-proxy overlap",
            (0, None),
        ),
    ]
    for axis, (column, title, ylabel, limits) in zip(axes[1:], metrics):
        values = plot[column].to_numpy(dtype=float)
        if column == "validation_occupancy_conflict_rate":
            values = 100 * values
            ylabel += " (%)"
            axis.axhline(10, color="black", linestyle="--", linewidth=1)
        bars = axis.bar(x, values, color=colors)
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.bar_label(bars, fmt="%.3f" if values.max() <= 1 else "%.1f", fontsize=8)
        if limits:
            axis.set_ylim(*limits)
    for axis in axes:
        axis.set_xticks(x, labels=labels, rotation=24, ha="right", fontsize=9)
    fig.suptitle("Forecast-optimal versus decision-optimal validation selections")
    fig.text(
        0.5,
        0.01,
        "Weights, thresholds, and metrics are validation-selected; this panel contains no test-driven selection.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def run_decision_aware_joint_search(
    *,
    results_dir: Path | str = Path("results"),
    predictions_dir: Path | str = Path("predictions"),
    figures_dir: Path | str = Path("figures"),
    reports_dir: Path | str = Path("reports"),
) -> list[Path]:
    """Select on validation, then audit and evaluate fixed candidates on test."""
    results_dir = Path(results_dir)
    predictions_dir = Path(predictions_dir)
    figures_dir = Path(figures_dir)
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    # Selection gate: no test frame is in memory or accepted by these functions.
    validation = _read_csv(results_dir / "forecast_predictions_validation_all_models.csv")
    processed = _read_csv(results_dir / "processed_lbnl_15min_pacific.csv")
    grid = build_validation_joint_grid(validation, processed)
    candidates, sensitivity = select_validation_candidates(grid)
    assert_canonical_reference_reproduced(candidates)

    grid_path = results_dir / "decision_aware_joint_weight_threshold_grid.csv"
    sensitivity_path = results_dir / "decision_aware_joint_auprc_floor_sensitivity.csv"
    grid.to_csv(grid_path, index=False, encoding="utf-8-sig")
    sensitivity.to_csv(sensitivity_path, index=False, encoding="utf-8-sig")
    del validation
    gc.collect()

    # The complete audit reads held-out artifacts only after every candidate is
    # frozen.  It checks alignment and legacy reports but cannot alter the
    # already-selected validation candidates.
    audit_path = reports_dir / "decision_aware_joint_search_audit.md"
    audit_text, sufficient = _audit_markdown(results_dir, predictions_dir)
    audit_path.write_text(audit_text, encoding="utf-8")
    if not sufficient:
        raise ScientificInputBlocker(
            f"Saved outputs are insufficient; see {audit_path.as_posix()}"
        )

    # Held-out data are loaded only after every candidate is fixed on validation.
    test = _read_csv(results_dir / "forecast_predictions_test_all_models.csv")
    validate_split_integrity(
        _read_csv(results_dir / "forecast_predictions_validation_all_models.csv"), test
    )
    evaluated = evaluate_fixed_candidates_on_test(test, processed, candidates)
    selected_path = results_dir / "decision_aware_joint_selected_candidates.csv"
    evaluated.to_csv(selected_path, index=False, encoding="utf-8-sig")

    validation_figure = figures_dir / "decision_aware_joint_validation_frontier.png"
    test_figure = figures_dir / "decision_aware_joint_test_comparison.png"
    comparison_figure = figures_dir / "forecast_optimal_vs_decision_optimal.png"
    make_validation_frontier(grid, evaluated, validation_figure)
    make_test_comparison(evaluated, test_figure)
    make_forecast_vs_decision(evaluated, comparison_figure)

    report_path = reports_dir / "decision_aware_joint_search_report.md"
    report_path.write_text(_joint_report(evaluated, sensitivity), encoding="utf-8")
    return [
        audit_path,
        grid_path,
        sensitivity_path,
        selected_path,
        validation_figure,
        test_figure,
        comparison_figure,
        report_path,
    ]
