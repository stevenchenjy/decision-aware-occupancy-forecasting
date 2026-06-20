#!/usr/bin/env python3
"""Generate presentation-only figures and tables from saved experiment outputs.

This script does not train models, select thresholds, or modify source result CSVs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.recommendation_policy import stable_empty_mask


RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = REPO_ROOT / "figures"
STABLE_FIGURE_PATH = FIGURES_DIR / "stable_window_sensitivity_conflict_and_kwh.png"
TABLE_PATH = RESULTS_DIR / "stable_window_presentation_table.csv"
EXAMPLE_FIGURE_PATH = FIGURES_DIR / "example_day_lightgbm_recommendation.png"
SAME_DAY_FIGURE_PATH = FIGURES_DIR / "lightgbm_vs_historical_same_day_recommendation.png"
SAME_DAY_SUMMARY_PATH = RESULTS_DIR / "lightgbm_vs_historical_same_day_summary.csv"
CAPTION = (
    "Conflict rate alone measures safety; safe kWh measures captured operational opportunity. "
    "Historical Average is the most conservative policy, while LightGBM captures more usable "
    "HVAC-and-lighting opportunity under the selected 10% policy."
)
EXAMPLE_CAPTION = (
    "Example held-out test day showing how LightGBM probabilities are converted into stable "
    "empty-window recommendations. Safe opportunity is counted only when the model recommends "
    "empty, the space is actually empty, and recorded HVAC plus lighting load is present."
)
MODEL_ORDER = ["Historical Average", "LightGBM", "Random Forest", "Transformer", "DLinear"]
MODEL_LABELS = {
    "historical average": "Historical Average",
    "lightgbm": "LightGBM",
    "random forest": "Random Forest",
    "transformer": "Transformer",
    "dlinear": "DLinear",
}
MODEL_COLORS = {
    "Historical Average": "#4C78A8",
    "LightGBM": "#F58518",
    "Random Forest": "#54A24B",
    "Transformer": "#B279A2",
    "DLinear": "#E45756",
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required saved result file is missing: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")


def inspect_test_prediction_file() -> pd.DataFrame:
    """Print the saved prediction schema needed for the same-day comparison."""
    path = RESULTS_DIR / "forecast_predictions_test_all_models.csv"
    predictions = _read_csv(path)
    required = {
        "date/time": "target_time",
        "actual occupancy label": "actual_occupied",
        "LightGBM predicted Empty probability": "lightgbm_empty_probability",
        "Historical Average predicted Empty probability": "historical_average_empty_probability",
    }
    missing = [f"{label} ({column})" for label, column in required.items() if column not in predictions]

    print("Saved test prediction file inspection:")
    print(f"  path: {path.resolve()}")
    print(f"  shape: {predictions.shape}")
    print(f"  columns: {predictions.columns.tolist()}")
    print("  first 5 rows:")
    print(predictions.head().to_string(index=False))
    for label, column in required.items():
        print(f"  {label} column: {column}")
    if missing:
        raise ValueError("Missing required same-day comparison columns: " + ", ".join(missing))
    return predictions


def _display_model_name(value: object) -> str:
    text = str(value).strip()
    return MODEL_LABELS.get(text.casefold(), text)


def _selected_policy_rows(stable: pd.DataFrame) -> pd.DataFrame:
    """Return saved rows for the selected 10% policy without recomputing anything."""
    selected = stable.copy()
    if "risk_delta" in selected.columns:
        selected = selected[np.isclose(pd.to_numeric(selected["risk_delta"]), 0.10)].copy()
    elif "policy" in selected.columns:
        selected = selected[selected["policy"].astype(str).str.contains("10%", regex=False)].copy()
    selected["model"] = selected["model"].map(_display_model_name)
    selected["model"] = pd.Categorical(selected["model"], categories=MODEL_ORDER, ordered=True)
    return selected.sort_values(["model", "min_window_length_hours"])


def generate_stable_window_figure(stable: pd.DataFrame) -> Path:
    plot = _selected_policy_rows(stable)
    if plot.empty:
        raise ValueError("No selected 10% policy rows were found in stable_window_metrics.csv")

    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.8), sharex=True)
    models = [model for model in MODEL_ORDER if model in plot["model"].astype(str).tolist()]

    for model in models:
        part = plot[plot["model"] == model].sort_values("min_window_length_hours")
        emphasis = model in {"Historical Average", "LightGBM"}
        style = dict(
            color=MODEL_COLORS[model],
            marker="o",
            markersize=7 if emphasis else 5,
            linewidth=3.0 if emphasis else 1.8,
            alpha=1.0 if emphasis else 0.78,
            label=model,
        )
        axes[0].plot(
            part["min_window_length_hours"],
            part["test_occupancy_conflict_rate"],
            **style,
        )
        axes[1].plot(
            part["min_window_length_hours"],
            part["safe_shiftable_load_kwh"],
            **style,
        )

    axes[0].set_title("A. Safety")
    axes[0].set_ylabel("Test occupancy conflict rate")
    axes[0].yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    axes[1].set_title("B. Captured opportunity")
    axes[1].set_ylabel("Safe shiftable-load opportunity (kWh)")
    for ax in axes:
        ax.set_xlabel("Minimum empty-window length (hours)")
        ax.set_xticks(sorted(plot["min_window_length_hours"].dropna().unique()))
        ax.legend(title="Model", fontsize=9, title_fontsize=10, frameon=True)
        ax.grid(axis="y", alpha=0.25)

    fig.suptitle("Stable-window sensitivity: safety and captured opportunity", y=0.98)
    fig.text(0.5, 0.025, CAPTION, ha="center", va="bottom", fontsize=9.5, wrap=True)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.83, bottom=0.22, wspace=0.24)
    STABLE_FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(STABLE_FIGURE_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return STABLE_FIGURE_PATH


def generate_presentation_table(stable: pd.DataFrame) -> tuple[Path, pd.DataFrame]:
    selected = _selected_policy_rows(stable)
    selected = selected[selected["model"].isin(["Historical Average", "LightGBM"])].copy()
    selected = selected[selected["min_window_length_hours"].isin([1.0, 2.0, 4.0])]

    source_columns = [
        "model",
        "min_window_length_hours",
        "selected_threshold",
        "test_occupancy_conflict_rate",
        "safe_shiftable_load_kwh",
        "number_of_recommended_windows",
        "number_of_safe_windows",
        "average_window_duration",
    ]
    missing = [column for column in source_columns if column not in selected.columns]
    if missing:
        raise ValueError(f"stable_window_metrics.csv is missing table columns: {missing}")

    table = selected[source_columns].copy().rename(
        columns={
            "min_window_length_hours": "minimum_empty_window_length_hours",
            "safe_shiftable_load_kwh": "safe_shiftable_load_opportunity_kwh",
            "number_of_recommended_windows": "recommended_windows",
            "number_of_safe_windows": "safe_windows",
            "average_window_duration": "average_window_duration_hours",
        }
    )
    table["model"] = table["model"].astype("object")
    table = table.sort_values(["model", "minimum_empty_window_length_hours"], key=lambda col: col.map({"Historical Average": 0, "LightGBM": 1}) if col.name == "model" else col)
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLE_PATH, index=False, encoding="utf-8-sig")
    return TABLE_PATH, table


def find_existing_example_figure() -> list[Path]:
    """Find example/recommendation PNGs, prioritizing exact LightGBM filename matches."""
    matches: set[Path] = set()
    for path in REPO_ROOT.rglob("*.png"):
        if ".git" in path.parts:
            continue
        name = path.name.casefold()
        if (
            name == "example_day_lightgbm_recommendation.png"
            or ("example_day" in name and "lightgbm" in name)
            or "recommendation" in name
            or "example_day" in name
        ):
            matches.add(path.resolve())
    return sorted(
        matches,
        key=lambda path: (
            path.name.casefold() != "example_day_lightgbm_recommendation.png",
            "lightgbm" not in path.name.casefold(),
            path.as_posix(),
        ),
    )


def _count_intervals(mask: np.ndarray) -> int:
    values = np.asarray(mask, dtype=bool)
    return int(np.sum(values & ~np.r_[False, values[:-1]]))


def _shade_mask(ax: plt.Axes, times: pd.Series, mask: np.ndarray, color: str, label: str, alpha: float) -> None:
    first = True
    for timestamp, active in zip(times, mask):
        if active:
            ax.axvspan(
                timestamp,
                timestamp + pd.Timedelta(minutes=15),
                color=color,
                alpha=alpha,
                linewidth=0,
                label=label if first else None,
            )
            first = False


def generate_example_day_figure() -> tuple[Path, dict[str, object]]:
    """Generate the missing example using the first qualifying test-day forecast."""
    predictions = _read_csv(RESULTS_DIR / "forecast_predictions_test_all_models.csv")
    selected = _read_csv(RESULTS_DIR / "selected_threshold_policies.csv")
    loads = _read_csv(RESULTS_DIR / "processed_lbnl_15min_pacific.csv")

    policy = selected[
        selected["model"].astype(str).str.casefold().eq("lightgbm")
        & np.isclose(pd.to_numeric(selected["risk_delta"]), 0.10)
    ]
    if policy.empty:
        raise ValueError("No saved LightGBM selected 10% policy was found")
    threshold = float(policy.iloc[0]["selected_empty_probability_threshold"])

    predictions = predictions.copy()
    predictions["anchor_time"] = pd.to_datetime(predictions["anchor_time"], utc=True).dt.tz_convert("America/Los_Angeles")
    predictions["target_time"] = pd.to_datetime(predictions["target_time"], utc=True).dt.tz_convert("America/Los_Angeles")
    loads = loads.copy()
    loads["target_time"] = pd.to_datetime(loads["date_local"], utc=True).dt.tz_convert("America/Los_Angeles")
    loads["controllable_load_kw"] = loads["hvac_S"].fillna(0).clip(lower=0) + loads["lig_S"].fillna(0).clip(lower=0)
    load_lookup = loads[["target_time", "controllable_load_kw"]].drop_duplicates("target_time")

    daily_anchors = (
        predictions.loc[
            (predictions["anchor_time"].dt.hour == 0) & (predictions["anchor_time"].dt.minute == 0),
            "anchor_time",
        ]
        .drop_duplicates()
        .sort_values()
    )
    chosen: pd.DataFrame | None = None
    for anchor in daily_anchors:
        day = predictions[predictions["anchor_time"] == anchor].sort_values("horizon_step").copy()
        if len(day) < 4:
            continue
        day = day.merge(load_lookup, on="target_time", how="left")
        day["controllable_load_kw"] = day["controllable_load_kw"].fillna(0)
        recommended = stable_empty_mask(day["lightgbm_empty_probability"].to_numpy(), threshold, min_steps=4)[0]
        actual_empty = day["actual_occupied"].to_numpy(dtype=int) == 0
        safe = recommended & actual_empty & (day["controllable_load_kw"].to_numpy() > 0)
        if recommended.any() and float(day.loc[safe, "controllable_load_kw"].sum() * 0.25) > 0:
            day["recommended"] = recommended
            day["actual_empty"] = actual_empty
            day["safe"] = safe
            chosen = day
            break
    if chosen is None:
        raise ValueError("No test day has both a stable LightGBM recommendation and nonzero safe opportunity")

    recommended = chosen["recommended"].to_numpy(dtype=bool)
    actual_empty = chosen["actual_empty"].to_numpy(dtype=bool)
    safe = chosen["safe"].to_numpy(dtype=bool)
    conflict = recommended & ~actual_empty
    times = chosen["target_time"]
    load_kw = chosen["controllable_load_kw"].to_numpy(dtype=float)

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    axes[0].step(times, chosen["lightgbm_empty_probability"], where="post", color=MODEL_COLORS["LightGBM"], linewidth=2, label="LightGBM predicted Empty probability")
    axes[0].axhline(threshold, color="black", linestyle="--", linewidth=1.3, label=f"Selected threshold ({threshold:.2f})")
    _shade_mask(axes[0], times, recommended, "#72B7B2", "Recommended stable empty window", 0.28)
    axes[0].set_ylabel("Empty probability")
    axes[0].set_ylim(-0.02, 1.05)
    axes[0].legend(loc="upper right", fontsize=9)

    axes[1].step(times, actual_empty.astype(int), where="post", color="#4C78A8", linewidth=2, label="Actual Empty label")
    _shade_mask(axes[1], times, safe, "#54A24B", "Safe recommended interval", 0.38)
    _shade_mask(axes[1], times, conflict, "#E45756", "Conflict interval", 0.42)
    axes[1].set_ylabel("Actual Empty")
    axes[1].set_yticks([0, 1], labels=["Occupied", "Empty"])
    axes[1].legend(loc="upper right", fontsize=9)

    axes[2].step(times, load_kw, where="post", color="#7A5195", linewidth=1.8, label="HVAC + lighting load")
    axes[2].fill_between(times, 0, load_kw, where=safe, step="post", color="#54A24B", alpha=0.45, label="Safe opportunity")
    axes[2].set_ylabel("Controllable load (kW)")
    axes[2].set_xlabel("Local time (America/Los_Angeles)")
    axes[2].legend(loc="upper right", fontsize=9)
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=times.dt.tz))

    date_label = times.iloc[0].strftime("%Y-%m-%d")
    fig.suptitle(f"LightGBM stable empty-window recommendations: {date_label}", y=0.985)
    fig.text(0.5, 0.015, EXAMPLE_CAPTION, ha="center", va="bottom", fontsize=9.5, wrap=True)
    fig.subplots_adjust(left=0.1, right=0.98, top=0.93, bottom=0.12, hspace=0.14)
    EXAMPLE_FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(EXAMPLE_FIGURE_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)

    metrics = {
        "chosen_date": date_label,
        "recommended_intervals": _count_intervals(recommended),
        "safe_intervals": _count_intervals(safe),
        "conflict_intervals": _count_intervals(conflict),
        "safe_kwh": float(load_kw[safe].sum() * 0.25),
        "conflict_kwh": float(load_kw[conflict].sum() * 0.25),
    }
    return EXAMPLE_FIGURE_PATH, metrics


def generate_same_day_comparison(predictions: pd.DataFrame) -> tuple[Path, Path, str, str, bool]:
    """Compare saved LightGBM and Historical Average forecasts on one test day."""
    selected = _read_csv(RESULTS_DIR / "selected_threshold_policies.csv")
    selected_10 = selected[np.isclose(pd.to_numeric(selected["risk_delta"]), 0.10)].copy()
    thresholds = {
        _display_model_name(row["model"]): float(row["selected_empty_probability_threshold"])
        for _, row in selected_10.iterrows()
    }
    required_thresholds = [model for model in ["LightGBM", "Historical Average"] if model not in thresholds]
    if required_thresholds:
        raise ValueError(
            "Missing validation-selected 10% threshold(s) for: " + ", ".join(required_thresholds)
        )

    day_predictions = predictions.copy()
    day_predictions["anchor_time"] = pd.to_datetime(
        day_predictions["anchor_time"], utc=True
    ).dt.tz_convert("America/Los_Angeles")
    day_predictions["target_time"] = pd.to_datetime(
        day_predictions["target_time"], utc=True
    ).dt.tz_convert("America/Los_Angeles")

    # A 23:45 anchor's 96 targets cover exactly 00:00--23:45 on one local day.
    daily_anchors = (
        day_predictions.loc[
            (day_predictions["anchor_time"].dt.hour == 23)
            & (day_predictions["anchor_time"].dt.minute == 45),
            "anchor_time",
        ]
        .drop_duplicates()
        .sort_values()
    )
    lightgbm_threshold = thresholds["LightGBM"]
    chosen: pd.DataFrame | None = None
    for anchor in daily_anchors:
        candidate = day_predictions[day_predictions["anchor_time"] == anchor].sort_values(
            "horizon_step"
        )
        if len(candidate) != 96:
            continue
        lightgbm_recommended = stable_empty_mask(
            candidate["lightgbm_empty_probability"].to_numpy(),
            lightgbm_threshold,
            min_steps=4,
        )[0]
        if lightgbm_recommended.any():
            chosen = candidate.copy()
            break
    if chosen is None:
        raise ValueError(
            "No complete held-out test day has four consecutive LightGBM intervals above "
            "the validation-selected 10% threshold"
        )

    selection_rule = (
        "first complete held-out test day whose LightGBM Empty probability is at or above "
        "its validation-selected 10% threshold for at least four consecutive 15-minute intervals"
    )
    chosen_date = chosen["target_time"].iloc[0].strftime("%Y-%m-%d")
    actual_occupied = chosen["actual_occupied"].to_numpy(dtype=int) == 1

    load_available = False
    load_path = RESULTS_DIR / "processed_lbnl_15min_pacific.csv"
    if load_path.exists():
        loads = _read_csv(load_path)
        if {"date_local", "hvac_S", "lig_S"}.issubset(loads.columns):
            loads = loads.copy()
            loads["target_time"] = pd.to_datetime(
                loads["date_local"], utc=True
            ).dt.tz_convert("America/Los_Angeles")
            loads["controllable_load_kw"] = (
                loads["hvac_S"].fillna(0).clip(lower=0)
                + loads["lig_S"].fillna(0).clip(lower=0)
            )
            chosen = chosen.merge(
                loads[["target_time", "controllable_load_kw"]].drop_duplicates("target_time"),
                on="target_time",
                how="left",
            )
            load_available = chosen["controllable_load_kw"].notna().all()

    model_specs = [
        ("LightGBM", "lightgbm_empty_probability", MODEL_COLORS["LightGBM"]),
        (
            "Historical Average",
            "historical_average_empty_probability",
            MODEL_COLORS["Historical Average"],
        ),
    ]
    model_masks: dict[str, dict[str, np.ndarray]] = {}
    summary_rows: list[dict[str, object]] = []
    for model, probability_column, _ in model_specs:
        probability = chosen[probability_column].to_numpy(dtype=float)
        predicted_empty = probability >= thresholds[model]
        recommended = stable_empty_mask(probability, thresholds[model], min_steps=4)[0]
        safe = recommended & ~actual_occupied
        conflict = recommended & actual_occupied
        model_masks[model] = {
            "predicted_empty": predicted_empty,
            "recommended": recommended,
            "safe": safe,
            "conflict": conflict,
        }
        safe_kwh = np.nan
        if load_available:
            load_kw = chosen["controllable_load_kw"].to_numpy(dtype=float)
            safe_kwh = float(load_kw[safe].sum() * 0.25)
        summary_rows.append(
            {
                "chosen_date": chosen_date,
                "model": model,
                "selected_threshold": thresholds[model],
                "number_of_predicted_empty_intervals": int(predicted_empty.sum()),
                "number_of_recommended_stable_intervals": int(recommended.sum()),
                "safe_intervals": int(safe.sum()),
                "conflict_intervals": int(conflict.sum()),
                "conflict_rate": float(conflict.sum() / recommended.sum())
                if recommended.any()
                else 0.0,
                "safe_kwh": safe_kwh,
                "note": (
                    "Recommendations reconstructed from saved probabilities and validation-selected "
                    "10% thresholds; stable windows require >=4 consecutive 15-minute intervals. "
                    "Interval counts are 15-minute intervals."
                ),
            }
        )

    times = chosen["target_time"]
    panel_count = 3 if load_available else 2
    height_ratios = [1.0, 1.0, 0.7] if load_available else [1.0, 1.0]
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(
        panel_count,
        1,
        figsize=(15, 10 if load_available else 7.5),
        sharex=True,
        gridspec_kw={"height_ratios": height_ratios},
    )
    axes = np.atleast_1d(axes)
    legend_handles = [
        Line2D([0], [0], color="black", linewidth=2, label="Predicted Empty probability"),
        Line2D(
            [0],
            [0],
            color="black",
            linestyle="--",
            linewidth=1.3,
            label="Selected Empty threshold",
        ),
        Patch(facecolor="gray", alpha=0.20, label="Actual occupancy"),
        Patch(facecolor="#54A24B", alpha=0.38, label="Recommended safe empty window"),
        Patch(facecolor="#E45756", alpha=0.42, label="Recommended conflict window"),
    ]

    for ax, (model, probability_column, color) in zip(axes[:2], model_specs):
        masks = model_masks[model]
        _shade_mask(ax, times, actual_occupied, "gray", "Actual occupancy", 0.20)
        _shade_mask(
            ax,
            times,
            masks["safe"],
            "#54A24B",
            "Recommended safe empty window",
            0.38,
        )
        _shade_mask(
            ax,
            times,
            masks["conflict"],
            "#E45756",
            "Recommended conflict window",
            0.42,
        )
        ax.step(
            times,
            chosen[probability_column],
            where="post",
            color=color,
            linewidth=2.2,
            label="Predicted Empty probability",
        )
        ax.axhline(
            thresholds[model],
            color="black",
            linestyle="--",
            linewidth=1.3,
            label="Selected Empty threshold",
        )
        ax.set_ylim(-0.02, 1.05)
        ax.set_ylabel("Empty probability")
        ax.set_title(model, loc="left", fontweight="bold")
        ax.legend(handles=legend_handles, loc="upper right", fontsize=8.5, ncol=2)

    if load_available:
        load_kw = chosen["controllable_load_kw"].to_numpy(dtype=float)
        axes[2].step(times, load_kw, where="post", color="#7A5195", linewidth=1.8)
        axes[2].set_ylabel("HVAC + lighting\nload proxy (kW)")
        axes[2].set_title("Recorded controllable-load proxy", loc="left", fontweight="bold")

    axes[-1].set_xlabel("Local time (America/Los_Angeles)")
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=times.dt.tz))
    fig.suptitle(
        "Same-day comparison: conservative schedule baseline vs opportunity-capturing model",
        y=0.985,
    )
    fig.text(
        0.5,
        0.015,
        (
            f"Held-out test date: {chosen_date}. Historical Average follows the regular schedule; "
            "LightGBM identifies additional high-confidence stable empty periods."
        ),
        ha="center",
        va="bottom",
        fontsize=9.5,
    )
    fig.subplots_adjust(left=0.09, right=0.98, top=0.92, bottom=0.10, hspace=0.24)
    SAME_DAY_FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SAME_DAY_FIGURE_PATH, dpi=200, bbox_inches="tight")
    plt.close(fig)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SAME_DAY_SUMMARY_PATH, index=False, encoding="utf-8-sig")
    return SAME_DAY_FIGURE_PATH, SAME_DAY_SUMMARY_PATH, chosen_date, selection_rule, load_available


def main() -> int:
    predictions = inspect_test_prediction_file()
    stable = _read_csv(RESULTS_DIR / "stable_window_metrics.csv")
    figure_path = generate_stable_window_figure(stable)
    table_path, table = generate_presentation_table(stable)
    same_day_path, same_day_summary_path, chosen_date, selection_rule, load_available = (
        generate_same_day_comparison(predictions)
    )

    print("\nStable-window presentation table (selected 10% policy):")
    with pd.option_context("display.max_columns", None, "display.width", 180, "display.float_format", "{:,.4f}".format):
        print(table.to_string(index=False))

    existing_examples = find_existing_example_figure()
    if existing_examples:
        example_path = existing_examples[0]
        example_status = "already existed"
        print(f"\nExisting example-day LightGBM recommendation figure: {example_path}")
    else:
        example_path, metrics = generate_example_day_figure()
        example_status = "newly generated"
        print("\nGenerated example-day LightGBM recommendation figure using the first qualifying test day.")
        for name, value in metrics.items():
            rendered = f"{value:.4f}" if isinstance(value, float) else value
            print(f"  {name.replace('_', ' ')}: {rendered}")

    print("\nOutput paths:")
    print(f"  Stable-window figure: {figure_path.resolve()}")
    print(f"  Presentation table: {table_path.resolve()}")
    print(f"  Same-day comparison figure: {same_day_path.resolve()}")
    print(f"  Same-day comparison summary: {same_day_summary_path.resolve()}")
    print(f"  Same-day chosen date: {chosen_date}")
    print(f"  Same-day selection rule: {selection_rule}")
    print(f"  HVAC + lighting load proxy available: {load_available}")
    print(f"  Example-day figure ({example_status}): {example_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
