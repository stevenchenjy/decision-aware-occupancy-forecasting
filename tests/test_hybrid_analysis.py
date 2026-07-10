import numpy as np
import pandas as pd
import pytest

from src.hybrid_analysis import (
    BASE_PROBABILITY_COLUMNS,
    HORIZON_STEPS,
    convex_probability_blend,
    select_primary_hybrid_weights,
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
    validation = _prediction_frame("validation", "2019-01-01 00:00:00+00:00", "2019-01-01")
    test = _prediction_frame("test", "2019-01-04 00:00:00+00:00", "2019-01-04")
    validate_split_integrity(validation, test)


def test_split_integrity_rejects_validation_test_target_overlap():
    validation = _prediction_frame("validation", "2019-01-01 00:00:00+00:00", "2019-01-01")
    test = _prediction_frame("test", "2019-01-01 00:00:00+00:00", "2019-01-01")
    with pytest.raises(ValueError, match="overlap"):
        validate_split_integrity(validation, test)
