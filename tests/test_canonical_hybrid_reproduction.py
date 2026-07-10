from pathlib import Path

import numpy as np
import pandas as pd

from src.hybrid_analysis import (
    PRIMARY_MODEL,
    model_metric_row,
    probability_sets,
    select_weights_from_validation,
    validate_split_integrity,
)


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS / name, encoding="utf-8-sig")


def test_canonical_primary_weights_and_test_auprc_reproduce_from_saved_predictions():
    validation = _read("forecast_predictions_validation_all_models.csv")
    test = _read("forecast_predictions_test_all_models.csv")
    validate_split_integrity(validation, test)
    selection, _, primary_search = select_weights_from_validation(validation)
    assert np.isclose(selection.primary_historical_weight, 0.15)
    assert np.isclose(selection.primary_lightgbm_weight, 0.60)
    assert np.isclose(selection.primary_transformer_weight, 0.25)
    assert np.isclose(
        selection.primary_historical_weight
        + selection.primary_lightgbm_weight
        + selection.primary_transformer_weight,
        1.0,
    )
    selected_search = primary_search[primary_search["selected_by_validation"]].iloc[0]
    assert np.isclose(
        selected_search["validation_auprc_empty"],
        primary_search["validation_auprc_empty"].max(),
    )
    probabilities = probability_sets(test, selection)
    reproduced = model_metric_row(
        PRIMARY_MODEL,
        test["actual_empty_positive"].to_numpy(dtype=int),
        probabilities[PRIMARY_MODEL],
    )
    canonical = _read("canonical_model_comparison.csv").set_index("model")
    assert np.isclose(reproduced["empty_auprc"], 0.8513696059906667)
    assert np.isclose(reproduced["empty_auprc"], canonical.loc[PRIMARY_MODEL, "empty_auprc"])


def test_canonical_primary_threshold_is_validation_optimum_and_test_is_evaluation_only():
    sweep = _read("hybrid_risk_opportunity_threshold_sweeps.csv")
    validation = sweep[
        sweep["split"].eq("validation_midnight_daily_forecasts")
        & sweep["model"].eq(PRIMARY_MODEL)
    ]
    eligible = validation[validation["occupancy_conflict_rate"] <= 0.10]
    optimum = eligible.sort_values(
        ["safe_opportunity_kwh", "empty_recall"], ascending=False
    ).iloc[0]
    canonical = _read("canonical_policy_10pct.csv").set_index("model")
    primary = canonical.loc[PRIMARY_MODEL]
    assert np.isclose(primary["selected_threshold"], optimum["selected_threshold"])
    assert np.isclose(primary["validation_conflict_rate"], optimum["occupancy_conflict_rate"])
    assert np.isclose(primary["selected_threshold"], 0.875)
    assert np.isclose(primary["safe_opportunity_kwh"], 490.1464158333333)
    assert primary["conflict_intervals"] == 0
    assert primary["recommended_intervals"] == 259
    assert primary["recommended_windows"] == 14
