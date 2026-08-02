import inspect

import numpy as np
import pandas as pd
import pytest

from src.decision_aware_joint_search import (
    CANDIDATE_LABELS,
    GRID_COLUMNS,
    evaluate_fixed_candidates_on_test,
    run_decision_aware_joint_search,
    select_decision_optimal_candidate,
    select_validation_candidates,
    simplex_weight_grid,
)
from src.hybrid_analysis import BASE_PROBABILITY_COLUMNS, HORIZON_STEPS, THRESHOLDS


def _grid_row(**updates):
    row = {
        "grid_order": 0,
        "selection_split": "validation_only",
        "forecast_metric_scope": "all_overlapping_rolling_forecasts",
        "policy_metric_scope": "non_overlapping_midnight_96_step_horizons",
        "seasonal_weight": 0.2,
        "lightgbm_weight": 0.6,
        "transformer_weight": 0.2,
        "nonzero_components": 3,
        "threshold": 0.8,
        "validation_empty_auprc": 0.8,
        "validation_occupancy_conflict_rate": 0.05,
        "validation_safe_opportunity_kwh": 10.0,
        "recommendation_coverage": 0.1,
        "recommended_intervals": 10,
        "safe_intervals": 9,
        "conflict_intervals": 1,
        "recommended_windows": 2,
        "safe_windows": 1,
        "conflict_windows": 1,
        "validation_empty_recall": 0.2,
        "validation_gross_opportunity_kwh": 11.0,
        "validation_conflict_opportunity_kwh": 1.0,
        "window_conflict_rate": 0.5,
        "minimum_window_steps": 4,
        "minimum_window_hours": 1.0,
        "daily_schedules": 2,
        "total_intervals": 192,
    }
    row.update(updates)
    return row


def test_simplex_weights_are_nonnegative_and_sum_to_one():
    grid = simplex_weight_grid(0.05)
    assert len(grid) == 231
    weights = grid[["seasonal_weight", "lightgbm_weight", "transformer_weight"]]
    assert (weights.to_numpy() >= 0).all()
    np.testing.assert_allclose(weights.sum(axis=1), 1.0)


def test_declared_joint_search_space_contains_8547_pairs():
    assert len(simplex_weight_grid(0.05)) == 231
    assert len(THRESHOLDS) == 37
    assert len(simplex_weight_grid(0.05)) * len(THRESHOLDS) == 8_547


def test_candidate_selection_interface_excludes_test_predictions():
    assert list(inspect.signature(select_validation_candidates).parameters) == [
        "validation_grid"
    ]
    source = inspect.getsource(select_validation_candidates)
    assert "forecast_predictions_test" not in source
    assert "evaluate_fixed_candidates_on_test" not in source


def test_joint_runner_freezes_validation_candidates_before_audit_or_test_load():
    source = inspect.getsource(run_decision_aware_joint_search)
    selection_position = source.index("candidates, sensitivity = select_validation_candidates(grid)")
    audit_position = source.index("audit_text, sufficient = _audit_markdown")
    test_load_position = source.index('test = _read_csv(results_dir / "forecast_predictions_test_all_models.csv")')
    assert selection_position < audit_position < test_load_position


def test_conflict_constraint_is_enforced():
    grid = pd.DataFrame(
        [
            _grid_row(grid_order=0, validation_safe_opportunity_kwh=100.0, validation_occupancy_conflict_rate=0.11),
            _grid_row(grid_order=1, validation_safe_opportunity_kwh=50.0, validation_occupancy_conflict_rate=0.10),
        ]
    )[GRID_COLUMNS]
    selected = select_decision_optimal_candidate(
        grid, auprc_floor_ratio=None, candidate_id="B_decision_optimal_10pct"
    )
    assert selected["validation_safe_opportunity_kwh"] == 50.0
    assert selected["validation_occupancy_conflict_rate"] <= 0.10


def test_auprc_floor_is_enforced():
    grid = pd.DataFrame(
        [
            _grid_row(grid_order=0, validation_empty_auprc=0.80, validation_safe_opportunity_kwh=100.0),
            _grid_row(grid_order=1, validation_empty_auprc=0.99, validation_safe_opportunity_kwh=40.0),
        ]
    )[GRID_COLUMNS]
    selected = select_decision_optimal_candidate(
        grid, auprc_floor_ratio=0.99, candidate_id="C_decision_optimal_99pct_floor"
    )
    assert selected["validation_empty_auprc"] >= 0.99 * grid["validation_empty_auprc"].max()
    assert selected["validation_safe_opportunity_kwh"] == 40.0


def test_candidate_selection_is_deterministic_after_all_declared_ties():
    grid = pd.DataFrame(
        [
            _grid_row(grid_order=5, threshold=0.85),
            _grid_row(grid_order=2, threshold=0.90),
        ]
    )[GRID_COLUMNS]
    first = select_decision_optimal_candidate(
        grid.sample(frac=1, random_state=1),
        auprc_floor_ratio=None,
        candidate_id="B_decision_optimal_10pct",
    )
    second = select_decision_optimal_candidate(
        grid.sample(frac=1, random_state=2),
        auprc_floor_ratio=None,
        candidate_id="B_decision_optimal_10pct",
    )
    assert first == second
    assert first["validation_grid_order"] == 2


def _test_prediction_frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    targets = pd.date_range("2019-01-09 00:15", periods=HORIZON_STEPS, freq="15min", tz="US/Pacific")
    y_empty = np.r_[np.ones(8, dtype=int), np.zeros(HORIZON_STEPS - 8, dtype=int)]
    frame = pd.DataFrame(
        {
            "split": "test",
            "anchor_time": "2019-01-09 00:00:00-08:00",
            "target_time": targets.astype(str),
            "horizon_step": np.arange(1, HORIZON_STEPS + 1),
            "actual_occupied": 1 - y_empty,
            "actual_empty_positive": y_empty,
        }
    )
    for column in BASE_PROBABILITY_COLUMNS.values():
        frame[column] = np.where(y_empty == 1, 0.9, 0.1)
    processed = pd.DataFrame(
        {
            "date_local": targets.astype(str),
            "hvac_S": np.ones(HORIZON_STEPS),
            "lig_S": np.ones(HORIZON_STEPS),
        }
    )
    return frame, processed


def test_fixed_candidate_test_evaluation_keeps_weights_and_threshold_fixed():
    frame, processed = _test_prediction_frame()
    fixed = pd.DataFrame(
        [
            {
                "candidate_id": "A_forecast_optimal_reference",
                "candidate_label": CANDIDATE_LABELS["A_forecast_optimal_reference"],
                "selection_split": "validation_only",
                "test_used_for_selection": False,
                "seasonal_weight": 0.15,
                "lightgbm_weight": 0.60,
                "transformer_weight": 0.25,
                "threshold": 0.80,
            }
        ]
    )
    evaluated = evaluate_fixed_candidates_on_test(frame, processed, fixed).iloc[0]
    assert evaluated["seasonal_weight"] == 0.15
    assert evaluated["lightgbm_weight"] == 0.60
    assert evaluated["transformer_weight"] == 0.25
    assert evaluated["threshold"] == 0.80
    assert evaluated["test_recommended_intervals"] == 8
    assert evaluated["test_conflict_intervals"] == 0


def test_fixed_candidate_evaluation_rejects_nonvalidation_selection():
    frame, processed = _test_prediction_frame()
    fixed = pd.DataFrame(
        [
            {
                "candidate_id": "bad",
                "candidate_label": "bad",
                "selection_split": "test",
                "test_used_for_selection": True,
                "seasonal_weight": 0.0,
                "lightgbm_weight": 1.0,
                "transformer_weight": 0.0,
                "threshold": 0.8,
            }
        ]
    )
    with pytest.raises(ValueError, match="selected on validation"):
        evaluate_fixed_candidates_on_test(frame, processed, fixed)
