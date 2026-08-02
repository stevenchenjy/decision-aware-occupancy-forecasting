#!/usr/bin/env python3
"""Quantify validation-only selection instability from committed saved outputs.

The canonical blend remains selected on all overlapping validation forecasts.
This diagnostic intentionally does *not* read a test export.  It asks whether
near-tied blend and threshold choices change when the 39 non-overlapping
validation policy horizons are perturbed.  Results are descriptive stability
evidence, not a replacement selection rule.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score


# Permit direct execution from the repository root without requiring callers to
# preconfigure PYTHONPATH.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.hybrid_analysis import (
    PRIMARY_MODEL,
    THRESHOLDS,
    controllable_kwh,
    daily_anchor_indices,
    probability_sets,
    reshape_daily,
    select_weights_from_validation,
    stable_empty_mask,
    validate_prediction_frame,
)


DEFAULT_REPS = 1_000
DEFAULT_SEED = 20260801
TOP_BLEND_CANDIDATES = 12


def _threshold_choice(
    probability: np.ndarray, y_empty: np.ndarray, kwh: np.ndarray
) -> tuple[float, float, float, int, int]:
    """Apply the declared validation policy rule without consulting test data."""
    rows: list[tuple[float, float, float, int, int]] = []
    for threshold in THRESHOLDS:
        recommendation = stable_empty_mask(probability, float(threshold), min_steps=4)
        safe = recommendation & np.asarray(y_empty, dtype=bool)
        conflict = recommendation & ~np.asarray(y_empty, dtype=bool)
        recommended = int(recommendation.sum())
        conflict_rate = float(conflict.sum() / recommended) if recommended else 0.0
        safe_opportunity = float((np.asarray(kwh, dtype=float) * safe).sum())
        empty_total = int(np.asarray(y_empty, dtype=bool).sum())
        empty_recall = float(safe.sum() / empty_total) if empty_total else 0.0
        rows.append((float(threshold), conflict_rate, safe_opportunity, recommended, int(safe.sum())))

    eligible = [row for row in rows if row[1] <= 0.10]
    if eligible:
        chosen = max(
            eligible,
            key=lambda row: (row[2], row[4] / max(int(np.asarray(y_empty, dtype=bool).sum()), 1)),
        )
    else:
        chosen = min(rows, key=lambda row: (row[1], -row[2]))
    return chosen


def _append_frequency_rows(
    rows: list[dict],
    counts: pd.Series,
    *,
    analysis: str,
    repetitions: int,
    seed: int,
    candidate_metadata: dict[int, dict] | None = None,
) -> None:
    for key, count in counts.sort_values(ascending=False).items():
        metadata = candidate_metadata.get(int(key), {}) if candidate_metadata else {}
        rows.append(
            {
                "analysis": analysis,
                "selection_scope": "validation_nonoverlapping_midnight_horizons_only",
                "repetitions": repetitions,
                "random_seed": seed,
                "candidate_key": str(key),
                "selection_count": int(count),
                "selection_frequency": float(count / repetitions),
                **metadata,
            }
        )


def run(
    results_dir: Path | str = Path("results"),
    *,
    reps: int = DEFAULT_REPS,
    seed: int = DEFAULT_SEED,
    top_blend_candidates: int = TOP_BLEND_CANDIDATES,
) -> Path:
    results_dir = Path(results_dir)
    validation = pd.read_csv(
        results_dir / "forecast_predictions_validation_all_models.csv", encoding="utf-8-sig"
    )
    processed = pd.read_csv(
        results_dir / "processed_lbnl_15min_pacific.csv", encoding="utf-8-sig"
    )
    validate_prediction_frame(validation, "validation")
    selection, _, primary_search = select_weights_from_validation(validation)
    daily_indices = daily_anchor_indices(validation)
    y_daily = reshape_daily(
        validation["actual_empty_positive"].to_numpy(dtype=int), daily_indices
    )
    kwh_daily = reshape_daily(controllable_kwh(validation, processed), daily_indices)

    component_columns = {
        "historical_average_weight": "historical_average_empty_probability",
        "lightgbm_weight": "lightgbm_empty_probability",
        "transformer_weight": "transformer_empty_probability",
    }
    components_daily = {
        weight: reshape_daily(validation[column].to_numpy(dtype=float), daily_indices)
        for weight, column in component_columns.items()
    }
    top = primary_search.head(top_blend_candidates).reset_index(drop=True).copy()
    probabilities = probability_sets(validation, selection)
    primary_daily = reshape_daily(probabilities[PRIMARY_MODEL], daily_indices)

    rows: list[dict] = []
    best_score = float(primary_search["validation_auprc_empty"].iloc[0])
    for row in primary_search.itertuples(index=False):
        rows.append(
            {
                "analysis": "canonical_full_overlap_blend_grid",
                "selection_scope": "validation_all_overlapping_forecasts",
                "repetitions": 1,
                "random_seed": np.nan,
                "candidate_key": str(int(row.validation_rank)),
                "selection_count": int(bool(row.selected_by_validation)),
                "selection_frequency": float(bool(row.selected_by_validation)),
                "historical_average_weight": float(row.historical_average_weight),
                "lightgbm_weight": float(row.lightgbm_weight),
                "transformer_weight": float(row.transformer_weight),
                "threshold": np.nan,
                "validation_auprc_empty": float(row.validation_auprc_empty),
                "auprc_gap_from_full_overlap_best": best_score - float(row.validation_auprc_empty),
                "candidate_rank_in_full_overlap_grid": int(row.validation_rank),
            }
        )

    blend_metadata = {
        index: {
            "historical_average_weight": float(row.historical_average_weight),
            "lightgbm_weight": float(row.lightgbm_weight),
            "transformer_weight": float(row.transformer_weight),
            "threshold": np.nan,
            "validation_auprc_empty": float(row.validation_auprc_empty),
            "auprc_gap_from_full_overlap_best": best_score - float(row.validation_auprc_empty),
            "candidate_rank_in_full_overlap_grid": int(row.validation_rank),
        }
        for index, row in top.iterrows()
    }
    rng = np.random.default_rng(seed)
    bootstrap_blend_winners: list[int] = []
    for _ in range(reps):
        sample = rng.integers(0, len(daily_indices), size=len(daily_indices))
        y_sample = y_daily[sample].ravel()
        scores = []
        for row in top.itertuples(index=False):
            probability = (
                row.historical_average_weight * components_daily["historical_average_weight"][sample]
                + row.lightgbm_weight * components_daily["lightgbm_weight"][sample]
                + row.transformer_weight * components_daily["transformer_weight"][sample]
            )
            scores.append(float(average_precision_score(y_sample, probability.ravel())))
        bootstrap_blend_winners.append(int(np.argmax(scores)))
    _append_frequency_rows(
        rows,
        pd.Series(bootstrap_blend_winners).value_counts(),
        analysis="daily_block_bootstrap_top12_blend_ranking",
        repetitions=reps,
        seed=seed,
        candidate_metadata=blend_metadata,
    )

    leave_one_out_blend_winners: list[int] = []
    for omitted_day in range(len(daily_indices)):
        keep = np.arange(len(daily_indices)) != omitted_day
        y_sample = y_daily[keep].ravel()
        scores = []
        for row in top.itertuples(index=False):
            probability = (
                row.historical_average_weight * components_daily["historical_average_weight"][keep]
                + row.lightgbm_weight * components_daily["lightgbm_weight"][keep]
                + row.transformer_weight * components_daily["transformer_weight"][keep]
            )
            scores.append(float(average_precision_score(y_sample, probability.ravel())))
        leave_one_out_blend_winners.append(int(np.argmax(scores)))
    _append_frequency_rows(
        rows,
        pd.Series(leave_one_out_blend_winners).value_counts(),
        analysis="leave_one_validation_day_out_top12_blend_ranking",
        repetitions=len(daily_indices),
        seed=seed,
        candidate_metadata=blend_metadata,
    )

    threshold_metadata = {
        index: {"threshold": float(threshold)} for index, threshold in enumerate(THRESHOLDS)
    }
    bootstrap_threshold_winners: list[int] = []
    for _ in range(reps):
        sample = rng.integers(0, len(daily_indices), size=len(daily_indices))
        threshold = _threshold_choice(primary_daily[sample], y_daily[sample], kwh_daily[sample])[0]
        bootstrap_threshold_winners.append(int(np.flatnonzero(np.isclose(THRESHOLDS, threshold))[0]))
    _append_frequency_rows(
        rows,
        pd.Series(bootstrap_threshold_winners).value_counts(),
        analysis="daily_block_bootstrap_primary_threshold",
        repetitions=reps,
        seed=seed,
        candidate_metadata=threshold_metadata,
    )

    leave_one_out_threshold_winners: list[int] = []
    for omitted_day in range(len(daily_indices)):
        keep = np.arange(len(daily_indices)) != omitted_day
        threshold = _threshold_choice(primary_daily[keep], y_daily[keep], kwh_daily[keep])[0]
        leave_one_out_threshold_winners.append(
            int(np.flatnonzero(np.isclose(THRESHOLDS, threshold))[0])
        )
    _append_frequency_rows(
        rows,
        pd.Series(leave_one_out_threshold_winners).value_counts(),
        analysis="leave_one_validation_day_out_primary_threshold",
        repetitions=len(daily_indices),
        seed=seed,
        candidate_metadata=threshold_metadata,
    )

    output = results_dir / "validation_selection_stability.csv"
    pd.DataFrame(rows).to_csv(output, index=False, encoding="utf-8-sig")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run validation-only stability diagnostics from saved outputs."
    )
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--top-blend-candidates", type=int, default=TOP_BLEND_CANDIDATES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = run(
        args.results_dir,
        reps=args.reps,
        seed=args.seed,
        top_blend_candidates=args.top_blend_candidates,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
