import inspect

import numpy as np
import pandas as pd
import pytest

from src.window_aware_decision_search import (
    AUPRC_FLOORS,
    WINDOW_FLOORS,
    classify_conflict_position,
    conflict_window_severity_from_arrays,
    expand_window_aware_constraint_grid,
    fully_safe_window_metrics,
    select_window_aware_candidates,
)


def test_correct_window_grouping_and_fully_safe_calculation():
    y_empty = np.array([[1, 1, 0, 1, 1, 1, 0, 1]], dtype=int)
    recommendation = np.array([[1, 1, 1, 0, 1, 1, 0, 1]], dtype=bool)
    result = fully_safe_window_metrics(y_empty, recommendation)
    assert result["recommended_windows"] == 3
    assert result["fully_safe_windows"] == 2
    assert result["conflict_windows"] == 1
    assert np.isclose(result["fully_safe_window_rate"], 2 / 3)
    assert np.isclose(result["window_precision"], 2 / 3)


def test_conflict_window_identification_uses_any_occupied_interval():
    y_empty = np.array([[1, 1, 1, 0]], dtype=int)
    recommendation = np.ones_like(y_empty, dtype=bool)
    result = fully_safe_window_metrics(y_empty, recommendation)
    assert result["fully_safe_windows"] == 0
    assert result["conflict_windows"] == 1


def _base_grid() -> pd.DataFrame:
    rows = []
    for order, values in enumerate(
        [
            (0.2, 0.6, 0.2, 0.80, 0.99, 0.09, 0.90, 100.0, 3, 10),
            (0.0, 1.0, 0.0, 0.85, 1.00, 0.05, 1.00, 80.0, 1, 5),
            (0.5, 0.5, 0.0, 0.75, 0.94, 0.02, 1.00, 200.0, 2, 5),
        ]
    ):
        sw, lw, tw, threshold, auprc, conflict, safe_rate, energy, components, windows = values
        safe_windows = int(round(windows * safe_rate))
        rows.append(
            {
                "grid_order": order,
                "selection_split": "validation_only",
                "seasonal_weight": sw,
                "lightgbm_weight": lw,
                "transformer_weight": tw,
                "nonzero_components": components,
                "threshold": threshold,
                "validation_empty_auprc": auprc,
                "validation_occupancy_conflict_rate": conflict,
                "validation_safe_opportunity_kwh": energy,
                "recommendation_coverage": 0.1,
                "recommended_intervals": 100,
                "safe_intervals": int(round(100 * (1 - conflict))),
                "conflict_intervals": int(round(100 * conflict)),
                "recommended_windows": windows,
                "safe_windows": safe_windows,
                "conflict_windows": windows - safe_windows,
            }
        )
    return pd.DataFrame(rows)


def test_window_and_auprc_floor_enforcement():
    expanded = expand_window_aware_constraint_grid(_base_grid())
    part = expanded[
        np.isclose(expanded["safe_window_floor"], 1.0)
        & expanded["auprc_floor_label"].eq("99pct")
    ]
    feasible = part[part["feasibility_flag"]]
    assert len(feasible) == 1
    assert feasible.iloc[0]["lightgbm_weight"] == 1.0


def test_validation_only_selection_rejects_test_metrics():
    assert list(inspect.signature(select_window_aware_candidates).parameters) == [
        "expanded_validation_grid"
    ]
    expanded = expand_window_aware_constraint_grid(_base_grid())
    expanded["test_safe_opportunity_kwh"] = 999.0
    with pytest.raises(ValueError, match="forbidden"):
        select_window_aware_candidates(expanded)


def test_deterministic_tie_breaking_prefers_higher_safe_rate_then_grid_order():
    base = _base_grid().iloc[[1]].copy()
    duplicate = base.copy()
    duplicate["grid_order"] = 9
    duplicate["threshold"] = 0.81
    tied = pd.concat([duplicate, base], ignore_index=True)
    expanded = expand_window_aware_constraint_grid(tied)
    first = select_window_aware_candidates(expanded.sample(frac=1, random_state=1))
    second = select_window_aware_candidates(expanded.sample(frac=1, random_state=2))
    pd.testing.assert_frame_equal(first, second)
    assert first["grid_order"].eq(1).all()


def test_all_declared_constraint_combinations_are_materialized():
    expanded = expand_window_aware_constraint_grid(_base_grid())
    assert len(expanded) == len(_base_grid()) * len(WINDOW_FLOORS) * len(AUPRC_FLOORS)


def test_conflict_severity_calculations():
    y_empty = np.array([[1, 0, 0, 1, 1, 0]], dtype=int)
    recommendation = np.ones_like(y_empty, dtype=bool)
    kwh = np.array([[1, 2, 3, 4, 5, 6]], dtype=float)
    severity = conflict_window_severity_from_arrays(
        y_empty,
        recommendation,
        kwh,
        strategy_key="fixture",
        strategy_label="Fixture",
        evaluation_scope="validation_only",
    ).iloc[0]
    assert severity["occupied_intervals_inside_window"] == 3
    assert severity["occupied_minutes_inside_window"] == 45
    assert severity["maximum_continuous_occupied_duration_minutes"] == 30
    assert severity["conflict_interval_controllable_load_kwh"] == 11.0
    assert np.isclose(severity["percent_of_window_occupied"], 50.0)
    assert severity["conflict_position"] == "beginning|middle|end"


def test_conflict_position_classification():
    result = classify_conflict_position(np.array([1, 0, 0, 1, 0, 1], dtype=bool))
    assert result["conflict_near_beginning"]
    assert result["conflict_near_middle"]
    assert result["conflict_near_end"]
