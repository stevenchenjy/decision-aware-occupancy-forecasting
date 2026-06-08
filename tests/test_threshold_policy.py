import pandas as pd

from src.recommendation_policy import select_threshold, stable_empty_mask, extract_windows


def test_select_threshold_uses_validation_metrics_only():
    validation_sweep = pd.DataFrame(
        [
            {
                "empty_probability_threshold": 0.50,
                "occupancy_conflict_rate": 0.04,
                "safe_shiftable_load_kwh": 10.0,
                "empty_recall": 0.90,
                "test_occupancy_conflict_rate": 0.99,
            },
            {
                "empty_probability_threshold": 0.80,
                "occupancy_conflict_rate": 0.08,
                "safe_shiftable_load_kwh": 30.0,
                "empty_recall": 0.30,
                "test_occupancy_conflict_rate": 0.01,
            },
            {
                "empty_probability_threshold": 0.95,
                "occupancy_conflict_rate": 0.20,
                "safe_shiftable_load_kwh": 100.0,
                "empty_recall": 1.00,
                "test_occupancy_conflict_rate": 0.00,
            },
        ]
    )

    selected = select_threshold(validation_sweep, risk_delta=0.10)

    assert selected["empty_probability_threshold"] == 0.80
    assert selected["safe_shiftable_load_kwh"] == 30.0


def test_select_threshold_falls_back_to_lowest_conflict():
    validation_sweep = pd.DataFrame(
        [
            {"empty_probability_threshold": 0.50, "occupancy_conflict_rate": 0.30, "safe_shiftable_load_kwh": 50.0, "empty_recall": 0.8},
            {"empty_probability_threshold": 0.90, "occupancy_conflict_rate": 0.20, "safe_shiftable_load_kwh": 10.0, "empty_recall": 0.2},
        ]
    )

    selected = select_threshold(validation_sweep, risk_delta=0.10)

    assert selected["empty_probability_threshold"] == 0.90


def test_select_threshold_breaks_safe_energy_ties_with_empty_recall():
    validation_sweep = pd.DataFrame(
        [
            {"empty_probability_threshold": 0.60, "occupancy_conflict_rate": 0.08, "safe_shiftable_load_kwh": 20.0, "empty_recall": 0.20},
            {"empty_probability_threshold": 0.70, "occupancy_conflict_rate": 0.09, "safe_shiftable_load_kwh": 20.0, "empty_recall": 0.50},
        ]
    )

    selected = select_threshold(validation_sweep, risk_delta=0.10)

    assert selected["empty_probability_threshold"] == 0.70


def test_stable_empty_window_extraction_on_toy_probability_series():
    probs = [[0.90, 0.85, 0.20, 0.95, 0.96, 0.97, 0.10]]

    mask = stable_empty_mask(probs, threshold=0.80, min_steps=2)

    assert mask.tolist() == [[True, True, False, True, True, True, False]]
    assert extract_windows(mask[0], min_steps=2) == [(0, 2), (3, 6)]
