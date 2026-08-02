from pathlib import Path

import pandas as pd

from src.data_preprocessing import causal_fill, post_import_forward_fill, resample_mean


def test_resample_mean_uses_explicit_left_labelled_bins():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2020-01-01 00:00:00+00:00", "2020-01-01 00:10:00+00:00"]
            ),
            "value": [1.0, 3.0],
        }
    )
    result = resample_mean(frame, "15min")
    assert list(result.index) == [pd.Timestamp("2020-01-01 00:00:00+00:00")]
    assert result.loc[pd.Timestamp("2020-01-01 00:00:00+00:00"), "value"] == 2.0


def test_validation_selection_stability_script_does_not_load_test_export():
    source = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "audit_validation_selection_stability.py"
    ).read_text(encoding="utf-8")
    assert "forecast_predictions_test_all_models.csv" not in source
    assert "forecast_predictions_validation_all_models.csv" in source


def test_post_import_forward_fill_preserves_legacy_alias_without_causal_claim():
    frame = pd.DataFrame({"protected": [1.0, 2.0], "sensor": [None, 3.0]})
    expected = post_import_forward_fill(frame, protected_columns={"protected"})
    actual = causal_fill(frame, protected_columns={"protected"})
    pd.testing.assert_frame_equal(actual, expected)
    assert expected["sensor"].tolist() == [0.0, 3.0]
