#!/usr/bin/env python3
"""Generate manuscript-only figures from canonical saved outputs.

The script deliberately consumes only canonical CSV artifacts.  It excludes
test-ranked and retrospective exploratory candidates from the main-paper
figures, so every visual statement follows the manuscript's confirmatory
scope.  Run from any working directory:

    python paper/scripts/generate_paper_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "manuscript" / "figures"
POLICY = ROOT / "results" / "canonical_policy_10pct.csv"
UNCERTAINTY = ROOT / "results" / "canonical_uncertainty_summary.csv"

ORDER = ["Historical Average", "LightGBM", "Hybrid Seasonal-GBDT-Transformer"]
LABELS = ["Historical\naverage", "LightGBM", "Primary\nhybrid"]
COLORS = ["#6C7A89", "#E07A28", "#264C7E"]


def load_policy() -> pd.DataFrame:
    frame = pd.read_csv(POLICY, encoding="utf-8-sig").set_index("model")
    missing = set(ORDER).difference(frame.index)
    if missing:
        raise RuntimeError(f"Canonical policy rows missing: {sorted(missing)}")
    chosen = frame.loc[ORDER].copy()
    expected = {
        "Historical Average": (0, 94.623047827),
        "LightGBM": (11, 493.9231551775),
        "Hybrid Seasonal-GBDT-Transformer": (0, 490.1463795264999),
    }
    for model, (conflicts, opportunity) in expected.items():
        row = chosen.loc[model]
        if int(row["conflict_intervals"]) != conflicts or abs(row["safe_opportunity_kwh"] - opportunity) > 1e-6:
            raise RuntimeError(f"Unexpected canonical policy value for {model}")
    return chosen


def policy_figure() -> None:
    policy = load_policy()
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.55), constrained_layout=True)
    x = list(range(len(ORDER)))

    safe = policy["safe_opportunity_kwh"].to_numpy()
    safe_bars = axes[0].bar(x, safe, color=COLORS, width=0.62)
    axes[0].set_ylabel("Offline safe load opportunity (kWh)")
    axes[0].set_ylim(0, 570)
    axes[0].set_xticks(x, LABELS)
    axes[0].grid(axis="y", color="#D9D9D9", linewidth=0.7)
    axes[0].set_axisbelow(True)
    for bar, value, row in zip(safe_bars, safe, policy.itertuples()):
        axes[0].text(
            bar.get_x() + bar.get_width() / 2,
            value + 14,
            f"{value:.1f}\n{row.safe_intervals}/{row.recommended_intervals} intervals",
            ha="center",
            va="bottom",
            fontsize=7.1,
        )

    conflict_pct = 100 * policy["occupancy_conflict_rate"].to_numpy()
    conflict_bars = axes[1].bar(x, conflict_pct, color=COLORS, width=0.62)
    axes[1].set_ylabel("Held-out camera-label-conflict rate (%)")
    axes[1].set_ylim(0, 5.6)
    axes[1].set_xticks(x, LABELS)
    axes[1].grid(axis="y", color="#D9D9D9", linewidth=0.7)
    axes[1].set_axisbelow(True)
    for bar, value, row in zip(conflict_bars, conflict_pct, policy.itertuples()):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            max(value + 0.24, 0.24),
            f"{value:.2f}%\n({row.conflict_intervals} conflicts)",
            ha="center",
            va="bottom",
            fontsize=7.1,
        )

    for axis, letter, title in zip(
        axes,
        ("(a)", "(b)"),
        ("Safe opportunity", "Observed conflict"),
    ):
        axis.set_title(f"{letter} {title}", fontsize=9.5, pad=5)
        axis.tick_params(axis="x", labelsize=7.6)
        axis.tick_params(axis="y", labelsize=7.6)

    fig.savefig(OUT / "fig_policy_comparison.png", dpi=360, bbox_inches="tight")
    plt.close(fig)


def contrast_row(frame: pd.DataFrame, contrast: str, metric: str) -> pd.Series:
    row = frame[(frame["estimate_type"] == "paired_difference") & (frame["model_or_contrast"] == contrast) & (frame["metric"] == metric)]
    if len(row) != 1:
        raise RuntimeError(f"Expected exactly one uncertainty row for {contrast}, {metric}")
    return row.iloc[0]


def uncertainty_figure() -> None:
    frame = pd.read_csv(UNCERTAINTY, encoding="utf-8-sig")
    contrasts = ["Primary minus Historical Average", "Primary minus LightGBM"]
    names = ["Primary - historical", "Primary - LightGBM"]
    auprc = [contrast_row(frame, name, "empty_auprc") for name in contrasts]
    opportunity = [contrast_row(frame, name, "safe_opportunity_kwh") for name in contrasts]

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 2.4), constrained_layout=True)
    for axis, rows, xlabel, digits in (
        (axes[0], auprc, "Paired daily AUPRC difference", 3),
        (axes[1], opportunity, "Paired daily safe-opportunity difference (kWh)", 0),
    ):
        for y, (name, row, color) in enumerate(zip(names, rows, COLORS[0:2])):
            point = float(row["point_estimate"])
            low = float(row["ci95_low"])
            high = float(row["ci95_high"])
            axis.errorbar(
                point,
                y,
                xerr=[[point - low], [high - point]],
                fmt="o",
                color=color,
                capsize=3.5,
                markersize=5.5,
                linewidth=1.4,
            )
            if digits == 3:
                label = f"{point:+.3f} [{low:+.3f}, {high:+.3f}]"
            else:
                label = f"{point:+.0f} [{low:+.0f}, {high:+.0f}]"
            text_x = high + (0.004 if digits == 3 else 23)
            axis.text(text_x, y, label, va="center", fontsize=7.0)
        axis.axvline(0, color="#4C4C4C", linewidth=0.9, linestyle="--")
        axis.set_yticks(range(len(names)), names)
        axis.invert_yaxis()
        axis.set_xlabel(xlabel)
        axis.grid(axis="x", color="#D9D9D9", linewidth=0.7)
        axis.set_axisbelow(True)
        axis.tick_params(labelsize=7.5)
    # Preserve clear right-side padding for interval annotations in a two-column
    # IEEE figure.  The limits intentionally extend beyond the largest interval.
    axes[0].set_xlim(-0.050, 0.075)
    axes[1].set_xlim(-320, 1125)
    axes[0].set_title("(a) Forecast-quality contrast", fontsize=9.5, pad=5)
    axes[1].set_title("(b) Policy-outcome contrast", fontsize=9.5, pad=5)
    fig.savefig(OUT / "fig_paired_uncertainty.png", dpi=360, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    policy_figure()
    uncertainty_figure()
    print("Wrote", OUT / "fig_policy_comparison.png")
    print("Wrote", OUT / "fig_paired_uncertainty.png")


if __name__ == "__main__":
    main()
