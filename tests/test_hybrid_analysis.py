import numpy as np
import pandas as pd
import pytest
import inspect

from src.hybrid_analysis import (
    BASE_PROBABILITY_COLUMNS,
    HORIZON_STEPS,
    convex_probability_blend,
    generate_hybrid_artifacts,
    policy_row,
    processed_load_proxy_kwh,
    select_policy_thresholds,
    select_primary_hybrid_weights,
    select_weights_from_validation,
    validate_prediction_frame,
    validate_split_integrity,
)


def test_probability_blend_is_exact_convex_average():
    probabilities = {
        "a": np.array([0.1, 0.6, 0.9]),
        "b": np.array([0.5, 0.2, 0.7]),
    }
    blended = convex_probability_blend(probabilities, {"a": 0.25, "b": 0.75})
    np.testing.assert_allclose(blended, 0.25 * probabilities["a"] + 0.75 * probabilities["b"])


def test_probability_blend_rejects_invalid_weights_and_alignment():
    with pytest.raises(ValueError, match="sum to 1"):
        convex_probability_blend({"a": np.array([0.2])}, {"a": 0.9})
    with pytest.raises(ValueError, match="aligned"):
        convex_probability_blend(
            {"a": np.array([0.2]), "b": np.array([0.2, 0.3])},
            {"a": 0.5, "b": 0.5},
        )


def test_primary_weight_search_returns_validation_maximum_on_declared_grid():
    y = np.array([0, 0, 1, 1, 0, 1])
    historical = np.array([0.2, 0.6, 0.8, 0.7, 0.3, 0.55])
    lightgbm = np.array([0.1, 0.4, 0.9, 0.8, 0.2, 0.7])
    transformer = np.array([0.3, 0.2, 0.6, 0.9, 0.4, 0.8])
    weights, search = select_primary_hybrid_weights(
        y, historical, lightgbm, transformer, step=0.25
    )
    assert len(search) == 15  # simplex combinations for 4 weight units
    assert np.isclose(sum(weights.values()), 1.0)
    chosen = search[search["selected_by_validation"]].iloc[0]
    assert np.isclose(chosen["validation_auprc_empty"], search["validation_auprc_empty"].max())
    assert weights == {
        "Historical Average": chosen["historical_average_weight"],
        "LightGBM": chosen["lightgbm_weight"],
        "Original Transformer": chosen["transformer_weight"],
    }


def _prediction_frame(split: str, anchor: str, target_start: str) -> pd.DataFrame:
    targets = pd.date_range(target_start, periods=HORIZON_STEPS, freq="15min", tz="UTC")
    y_occupied = np.tile([0, 1], HORIZON_STEPS // 2)
    frame = pd.DataFrame(
        {
            "split": split,
            "anchor_time": anchor,
            "target_time": targets.astype(str),
            "horizon_step": np.arange(1, HORIZON_STEPS + 1),
            "actual_occupied": y_occupied,
            "actual_empty_positive": 1 - y_occupied,
        }
    )
    for index, column in enumerate(BASE_PROBABILITY_COLUMNS.values()):
        frame[column] = np.clip(0.15 + 0.1 * index + 0.002 * np.arange(HORIZON_STEPS), 0, 1)
    return frame


def test_split_integrity_accepts_disjoint_chronological_exports():
    validation = _prediction_frame("validation", "2019-01-01 00:00:00+00:00", "2019-01-01 00:15")
    test = _prediction_frame("test", "2019-01-04 00:00:00+00:00", "2019-01-04 00:15")
    validate_split_integrity(validation, test)


def test_split_integrity_rejects_validation_test_target_overlap():
    validation = _prediction_frame("validation", "2019-01-01 00:00:00+00:00", "2019-01-01 00:15")
    test = _prediction_frame("test", "2019-01-01 00:00:00+00:00", "2019-01-01 00:15")
    with pytest.raises(ValueError, match="overlap"):
        validate_split_integrity(validation, test)


def test_prediction_validation_rejects_noncausal_timestamp_offsets():
    frame = _prediction_frame(
        "validation", "2019-01-01 00:00:00+00:00", "2019-01-01 00:15"
    )
    frame.loc[0, "target_time"] = "2019-01-01 00:00:00+00:00"
    with pytest.raises(ValueError, match="target timestamps"):
        validate_prediction_frame(frame, "validation")


def test_fixed_threshold_policy_counts_safe_and_conflict_intervals():
    y_empty = np.array([[1, 1, 0, 0, 1, 1]])
    probability = np.array([[0.9, 0.8, 0.9, 0.9, 0.7, 0.8]])
    kwh = np.ones_like(probability, dtype=float)
    result = policy_row(
        "fixture", y_empty, probability, kwh, threshold=0.75, split="test", min_steps=2
    )
    assert result["recommended_intervals"] == 4
    assert result["safe_intervals"] == 2
    assert result["conflict_intervals"] == 2
    assert np.isclose(result["occupancy_conflict_rate"], 0.5)
    assert np.isclose(result["safe_opportunity_kwh"], 2.0)


def test_processed_load_proxy_is_interval_energy_not_a_control_claim():
    frame = pd.DataFrame(
        {
            "target_time": [
                "2019-01-01 00:15:00+00:00",
                "2019-01-01 00:30:00+00:00",
            ]
        }
    )
    processed = pd.DataFrame(
        {
            "date_local": frame["target_time"],
            "hvac_S": [4.0, 2.0],
            "lig_S": [2.0, 2.0],
        }
    )
    np.testing.assert_allclose(
        processed_load_proxy_kwh(frame, processed),
        np.array([1.5, 1.0]),
    )


def test_selection_interfaces_accept_validation_data_only():
    assert list(inspect.signature(select_weights_from_validation).parameters) == ["validation"]
    assert list(inspect.signature(select_policy_thresholds).parameters) == ["validation_sweep"]


def test_generator_fixes_validation_selections_before_loading_test():
    source = inspect.getsource(generate_hybrid_artifacts)
    selection_position = source.index("selected = select_policy_thresholds(validation_sweep)")
    test_load_position = source.index('forecast_predictions_test_all_models.csv')
    assert selection_position < test_load_position
