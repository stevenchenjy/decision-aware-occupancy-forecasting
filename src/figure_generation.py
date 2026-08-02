"""Regenerate research figures from saved experiment outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve
from matplotlib.lines import Line2D

from src.recommendation_policy import stable_empty_mask


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def _maybe_read_csv(path: Path) -> pd.DataFrame | None:
    return _read_csv(path) if path.exists() else None


def _save_fig(path: Path, dpi: int = 180) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=dpi)
    plt.close()
    return path


def _slugify(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(name)).strip("_")


def _model_name_from_slug(slug: str, model_names: list[str]) -> str:
    lookup = {_slugify(name): name for name in model_names}
    fallback = {
        "historical_average": "Historical average",
        "lightgbm": "LightGBM",
        "random_forest": "Random forest",
        "dlinear": "DLinear",
        "transformer": "Transformer",
    }
    return lookup.get(slug, fallback.get(slug, slug.replace("_", " ").title()))


def _pareto_efficient_frontier(part: pd.DataFrame) -> pd.DataFrame:
    """Return non-dominated points for minimizing conflict and maximizing opportunity."""
    x_col = "occupancy_conflict_rate"
    y_col = "safe_shiftable_load_opportunity_kwh"
    ordered = part.sort_values([x_col, y_col], ascending=[True, False]).copy()
    ordered = ordered.drop_duplicates(subset=[x_col], keep="first")
    previous_best = ordered[y_col].cummax().shift(fill_value=-np.inf)
    frontier = ordered[ordered[y_col] > previous_best].copy()
    frontier["pareto_frontier"] = True
    return frontier


def _prediction_matrices(results_dir: Path, split: str = "test") -> tuple[np.ndarray, dict[str, np.ndarray], pd.DataFrame]:
    pred_path = results_dir / f"forecast_predictions_{split}_all_models.csv"
    pred = _read_csv(pred_path)
    pred = pred.sort_values(["anchor_time", "horizon_step"]).reset_index(drop=True)
    model_metrics = _maybe_read_csv(results_dir / "model_metrics_empty_positive.csv")
    model_names = model_metrics["model"].tolist() if model_metrics is not None else []
    horizon = int(pred["horizon_step"].max())
    anchors = pred[["anchor_time"]].drop_duplicates().reset_index(drop=True)
    y = pred["actual_occupied"].to_numpy(dtype=int).reshape(len(anchors), horizon)
    probabilities: dict[str, np.ndarray] = {}
    for col in pred.columns:
        if not col.endswith("_occupied_probability"):
            continue
        slug = col[: -len("_occupied_probability")]
        model = _model_name_from_slug(slug, model_names)
        probabilities[model] = pred[col].to_numpy(dtype=float).reshape(len(anchors), horizon)
    return y, probabilities, anchors


def _plot_occupancy_profile(results_dir: Path, figures_dir: Path) -> list[Path]:
    df = _maybe_read_csv(results_dir / "processed_lbnl_15min_pacific.csv")
    if df is None or "date_local" not in df:
        return []
    df["date_local"] = pd.to_datetime(df["date_local"], utc=True).dt.tz_convert("America/Los_Angeles")
    df = df.set_index("date_local")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    profile = df.assign(day=df.index.day_name(), hour=df.index.hour).groupby(["day", "hour"])["occupied"].mean().unstack("hour").reindex(day_order)
    plt.figure(figsize=(12, 4.8))
    sns.heatmap(profile, cmap="YlGnBu", vmin=0, vmax=1)
    plt.title("Observed occupancy probability by local Pacific day and hour")
    plt.xlabel("Local hour of day")
    plt.ylabel("")
    return [_save_fig(figures_dir / "occupancy_profile_heatmap_pacific.png")]


def _plot_model_metrics(results_dir: Path, figures_dir: Path) -> list[Path]:
    metrics = _maybe_read_csv(results_dir / "model_metrics_empty_positive.csv")
    if metrics is None:
        return []
    value_vars = [c for c in ["recall_empty", "precision_empty", "f1_empty", "auroc_empty", "auprc_empty"] if c in metrics]
    metric_long = metrics.melt(id_vars="model", value_vars=value_vars, var_name="metric", value_name="value")
    plt.figure(figsize=(12, 5))
    sns.barplot(data=metric_long, x="metric", y="value", hue="model")
    plt.ylim(0, 1)
    plt.xticks(rotation=20)
    plt.title("Model metrics with Empty=1 as positive class")
    plt.legend(loc="lower right", fontsize=8)
    return [_save_fig(figures_dir / "model_metrics_empty_positive.png")]


def _plot_horizon_metrics(results_dir: Path, figures_dir: Path) -> list[Path]:
    paths = []
    bucket = _maybe_read_csv(results_dir / "horizon_bucket_metrics_empty_positive.csv")
    if bucket is not None:
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.barplot(data=bucket, x="horizon_bucket", y="auprc_empty", hue="model", ax=ax)
        ax.set_ylim(0, 1)
        ax.set_title("Empty-positive AUPRC by forecast horizon bucket")
        ax.set_ylabel("Empty-class AUPRC")
        ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0)
        fig.subplots_adjust(right=0.78)
        path = figures_dir / "horizon_bucket_empty_auprc.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=180)
        plt.close(fig)
        paths.append(path)
    return paths


def _plot_sweeps(results_dir: Path, figures_dir: Path) -> list[Path]:
    paths = []
    sweep = _maybe_read_csv(results_dir / "energy_risk_tradeoff_threshold_sweep.csv")
    if sweep is not None:
        selected_thresholds = _maybe_read_csv(results_dir / "selected_threshold_policies.csv")
        selected_test = _maybe_read_csv(results_dir / "threshold_policy_results_test.csv")
        selected = None
        if selected_thresholds is not None and selected_test is not None:
            selected = selected_thresholds[
                [
                    "model",
                    "risk_delta",
                    "selected_empty_probability_threshold",
                    "validation_occupancy_conflict_rate",
                ]
            ].merge(
                selected_test[
                    [
                        "model",
                        "risk_delta",
                        "occupancy_conflict_rate",
                        "safe_shiftable_load_opportunity_kwh",
                    ]
                ],
                on=["model", "risk_delta"],
                how="inner",
            )
            selected = selected.rename(
                columns={
                    "risk_delta": "validation_constraint",
                    "occupancy_conflict_rate": "test_conflict_rate",
                    "safe_shiftable_load_opportunity_kwh": "test_safe_opportunity_kwh",
                }
            )
            selected["test_constraint_result"] = np.where(
                selected["test_conflict_rate"] <= selected["validation_constraint"],
                "pass",
                "test violation",
            )
            selected.to_csv(results_dir / "validation_selected_policy_test_outcomes.csv", index=False, encoding="utf-8-sig")
        pareto_rows = []
        fig, ax = plt.subplots(figsize=(11.5, 6.8))
        palette = dict(zip(sweep["model"].drop_duplicates(), sns.color_palette(n_colors=sweep["model"].nunique())))
        for model, part in sweep.groupby("model"):
            color = palette[model]
            part = part.sort_values(["occupancy_conflict_rate", "safe_shiftable_load_opportunity_kwh"], ascending=[True, False])
            ax.scatter(
                part["occupancy_conflict_rate"],
                part["safe_shiftable_load_opportunity_kwh"],
                s=18,
                alpha=0.22,
                color=color,
                edgecolors="none",
            )
            frontier = _pareto_efficient_frontier(part)
            pareto_rows.append(frontier)
            ax.plot(
                frontier["occupancy_conflict_rate"],
                frontier["safe_shiftable_load_opportunity_kwh"],
                color=color,
                linewidth=2.2,
                label=model,
            )
        for delta, label in [(0.05, "5% empirical conflict cutoff"), (0.10, "10% empirical conflict cutoff"), (0.20, "20% empirical conflict cutoff")]:
            ax.axvline(delta, color="gray", linestyle="--", linewidth=0.9)
            ax.text(delta + 0.003, ax.get_ylim()[1] * 0.96, label, fontsize=8, color="dimgray", rotation=90, va="top")
        ax.set_xlabel("Test occupancy conflict rate")
        ax.set_ylabel("Offline camera-label-empty load-proxy overlap (kWh)")
        ax.set_title("Empirical conflict--opportunity threshold sweep with Pareto frontiers")
        model_handles = [Line2D([0], [0], color=color, linewidth=2.2, label=model) for model, color in palette.items()]
        ax.legend(
            handles=model_handles,
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            borderaxespad=0,
            fontsize=8,
        )
        caption = "Vertical dashed lines show empirical validation conflict cutoffs. Solid lines show Pareto-efficient threshold choices. Transparent points show all tested thresholds."
        fig.text(0.02, 0.025, caption, ha="left", va="bottom", fontsize=8)
        fig.subplots_adjust(right=0.76, bottom=0.18)
        path = figures_dir / "energy_risk_tradeoff_pareto.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=180)
        plt.close(fig)
        paths.append(path)
        if pareto_rows:
            pd.concat(pareto_rows, ignore_index=True).to_csv(results_dir / "energy_risk_pareto_frontier.csv", index=False, encoding="utf-8-sig")
    return paths


def _plot_policy_outputs(results_dir: Path, figures_dir: Path) -> list[Path]:
    policy = _maybe_read_csv(results_dir / "threshold_policy_results_test.csv")
    if policy is None:
        return []
    policy = policy.copy()
    policy["risk_delta_label"] = (policy["risk_delta"] * 100).round().astype(int).astype(str) + "%"
    paths = []
    plt.figure(figsize=(12, 5.5))
    sns.barplot(data=policy, x="risk_delta_label", y="safe_shiftable_load_opportunity_kwh", hue="model")
    plt.title("Offline camera-label-empty load-proxy overlap from validation-selected policies")
    plt.xlabel("Allowed validation conflict rate")
    plt.ylabel("Offline camera-label-empty load-proxy overlap (kWh)")
    plt.legend(fontsize=8)
    paths.append(_save_fig(figures_dir / "threshold_policy_safe_opportunity.png"))

    plt.figure(figsize=(12, 5.5))
    sns.barplot(data=policy, x="risk_delta_label", y="occupancy_conflict_rate", hue="model")
    plt.title("Realized occupancy conflict rate of validation-selected policies")
    plt.xlabel("Allowed validation conflict delta")
    plt.ylabel("Test occupancy conflict rate")
    plt.legend(fontsize=8)
    paths.append(_save_fig(figures_dir / "threshold_policy_occupancy_conflict.png"))

    delta_10 = policy[np.isclose(policy["risk_delta"], 0.10)]
    if len(delta_10):
        plt.figure(figsize=(10, 5))
        sns.barplot(data=delta_10, x="model", y="safe_shiftable_load_opportunity_kwh", color="tab:green")
        plt.xticks(rotation=20, ha="right")
        plt.title("Offline camera-label-empty load-proxy overlap by model, 10% cutoff")
        plt.ylabel("Offline load-proxy overlap (kWh)")
        plt.xlabel("")
        paths.append(_save_fig(figures_dir / "safe_shiftable_load_by_model.png"))
    return paths


def _plot_window_and_sensitivity(results_dir: Path, figures_dir: Path) -> list[Path]:
    paths = []
    window = _maybe_read_csv(results_dir / "continuous_empty_window_policy_results_test.csv")
    if window is not None:
        plot = window[np.isclose(window["risk_delta"], 0.10)].copy()
        if len(plot):
            fig, ax = plt.subplots(figsize=(12, 5.5))
            sns.barplot(data=plot, x="minimum_empty_window_hours", y="window_level_occupancy_conflict_rate", hue="model", ax=ax)
            ax.set_title("Continuous empty-window conflict rate by minimum duration, delta=10% policy")
            ax.set_xlabel("Minimum empty-window duration (hours)")
            ax.set_ylabel("Window-level occupancy conflict rate")
            ax.legend(fontsize=8)
            fig.text(0.02, 0.02, "Missing bars indicate zero conflict, not missing data.", ha="left", va="bottom", fontsize=8)
            fig.subplots_adjust(bottom=0.16)
            path = figures_dir / "continuous_empty_window_conflict_rate.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, dpi=180)
            plt.close(fig)
            paths.append(path)
    stable = _maybe_read_csv(results_dir / "stable_window_metrics.csv")
    if stable is not None:
        plot = stable[np.isclose(stable["risk_delta"], 0.10)].copy() if "risk_delta" in stable else stable
        plt.figure(figsize=(12, 5.5))
        sns.lineplot(data=plot, x="min_window_length_hours", y="test_occupancy_conflict_rate", hue="model", marker="o")
        plt.title("Stable-window sensitivity under selected policies")
        plt.xlabel("Minimum empty-window length (hours)")
        plt.ylabel("Occupancy conflict rate")
        paths.append(_save_fig(figures_dir / "stable_window_sensitivity.png"))
    sensitivity = _maybe_read_csv(results_dir / "energy_sensitivity_analysis.csv")
    if sensitivity is not None:
        plot = sensitivity[np.isclose(sensitivity["risk_delta"], 0.10)].copy()
        y_col = "safe_estimated_opportunity_kwh" if "safe_estimated_opportunity_kwh" in plot else "safe_shiftable_load_kwh"
        plt.figure(figsize=(13, 6))
        sns.barplot(data=plot, x="load_assumption", y=y_col, hue="model")
        plt.title("Hypothetical meter-coefficient sensitivity under 10% cutoff")
        plt.xlabel("Hypothetical meter coefficient scenario")
        plt.ylabel("Offline label-empty proxy overlap (kWh)")
        plt.xticks(rotation=25, ha="right")
        plt.legend(fontsize=8)
        paths.append(_save_fig(figures_dir / "energy_sensitivity_analysis.png"))
    return paths


def _plot_importance(results_dir: Path, figures_dir: Path) -> list[Path]:
    paths = []
    importance = _maybe_read_csv(results_dir / "permutation_importance.csv")
    if importance is None or not len(importance):
        return paths
    top = importance.sort_values("importance", ascending=False).head(18).copy()
    plt.figure(figsize=(11, 6.5))
    sns.barplot(data=top, x="importance", y="feature", color="tab:blue")
    plt.title("LightGBM permutation importance: validation Empty-AUPRC drop")
    plt.xlabel("AUPRC drop after feature permutation")
    plt.ylabel("Feature")
    paths.append(_save_fig(figures_dir / "feature_importance_permutation_empty_auprc.png"))
    return paths


def _plot_curves(results_dir: Path, figures_dir: Path) -> list[Path]:
    try:
        y_occ, probabilities, _ = _prediction_matrices(results_dir, split="test")
    except FileNotFoundError:
        return []
    y_empty_flat = 1 - y_occ.ravel().astype(int)
    paths = []

    reliability_rows = []
    plt.figure(figsize=(8.5, 7))
    plt.plot([0, 1], [0, 1], "--", color="gray", linewidth=1, label="ideal calibrated-probability reference (no calibrator fitted)")
    for name, prob in probabilities.items():
        p_empty = np.clip(1.0 - prob.ravel(), 1e-6, 1 - 1e-6)
        frac_pos, mean_pred = calibration_curve(y_empty_flat, p_empty, n_bins=10, strategy="quantile")
        for bin_id, (mp, fp) in enumerate(zip(mean_pred, frac_pos), start=1):
            reliability_rows.append({"model": name, "positive_class": "empty", "bin": bin_id, "mean_predicted_empty_probability": mp, "observed_empty_fraction": fp})
        plt.plot(mean_pred, frac_pos, marker="o", linewidth=1.5, label=name)
    plt.xlabel("Mean Empty score (uncalibrated)")
    plt.ylabel("Observed empty fraction")
    plt.title("Reliability curve with Empty=1")
    plt.legend(fontsize=8, loc="upper left")
    paths.append(_save_fig(figures_dir / "empty_reliability_curve.png"))
    pd.DataFrame(reliability_rows).to_csv(results_dir / "empty_reliability_curve_points.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(8.5, 7))
    for name, prob in probabilities.items():
        p_empty = np.clip(1.0 - prob.ravel(), 1e-6, 1 - 1e-6)
        precision, recall, _ = precision_recall_curve(y_empty_flat, p_empty)
        ap = average_precision_score(y_empty_flat, p_empty)
        plt.plot(recall, precision, linewidth=1.6, label=f"{name} ({ap:.3f})")
    plt.xlabel("Recall for Empty")
    plt.ylabel("Precision for Empty")
    plt.title("Precision-recall curves with Empty=1")
    plt.legend(fontsize=8, loc="lower left")
    paths.append(_save_fig(figures_dir / "precision_recall_empty_positive.png"))

    plt.figure(figsize=(8.5, 7))
    for name, prob in probabilities.items():
        p_empty = np.clip(1.0 - prob.ravel(), 1e-6, 1 - 1e-6)
        fpr, tpr, _ = roc_curve(y_empty_flat, p_empty)
        auc = roc_auc_score(y_empty_flat, p_empty)
        plt.plot(fpr, tpr, linewidth=1.6, label=f"{name} ({auc:.3f})")
    plt.plot([0, 1], [0, 1], "--", color="gray", linewidth=1)
    plt.xlabel("FPR for Empty class")
    plt.ylabel("TPR for Empty class")
    plt.title("ROC curves with Empty=1")
    plt.legend(fontsize=8, loc="lower right")
    paths.append(_save_fig(figures_dir / "roc_empty_positive.png"))
    return paths


def _plot_confusion(results_dir: Path, figures_dir: Path) -> list[Path]:
    selected = _maybe_read_csv(results_dir / "selected_threshold_policies.csv")
    if selected is None:
        return []
    y_occ, probabilities, anchors = _prediction_matrices(results_dir, split="test")
    anchor_times = pd.to_datetime(anchors["anchor_time"], utc=True).dt.tz_convert("America/Los_Angeles")
    daily_idx = np.flatnonzero((anchor_times.dt.hour == 0) & (anchor_times.dt.minute == 0))
    if len(daily_idx) == 0:
        daily_idx = np.arange(0, len(anchors), y_occ.shape[1])
    rows = []
    for _, sel in selected[np.isclose(selected["risk_delta"], 0.10)].iterrows():
        model = sel["model"]
        if model not in probabilities:
            continue
        threshold = float(sel["selected_empty_probability_threshold"])
        rec = stable_empty_mask(1.0 - probabilities[model][daily_idx], threshold, min_steps=4)
        actual_empty = y_occ[daily_idx] == 0
        rows.append({
            "model": model,
            "true_empty_recommended_empty": int((rec & actual_empty).sum()),
            "true_occupied_recommended_empty": int((rec & ~actual_empty).sum()),
            "true_empty_not_recommended": int((~rec & actual_empty).sum()),
            "true_occupied_not_recommended": int((~rec & ~actual_empty).sum()),
        })
    if not rows:
        return []
    conf = pd.DataFrame(rows).set_index("model")
    fig, axes = plt.subplots(1, len(conf), figsize=(4.2 * len(conf), 3.8), squeeze=False)
    for ax, (model, row) in zip(axes.ravel(), conf.iterrows()):
        matrix = np.array([
            [row["true_empty_recommended_empty"], row["true_empty_not_recommended"]],
            [row["true_occupied_recommended_empty"], row["true_occupied_not_recommended"]],
        ])
        sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax, xticklabels=["Rec empty", "Not rec"], yticklabels=["Actually empty", "Actually occupied"])
        ax.set_title(model)
    fig.suptitle("Delta=10% selected-policy confusion matrices")
    return [_save_fig(figures_dir / "confusion_matrices_empty_selected.png")]


def _plot_ablation(results_dir: Path, figures_dir: Path) -> list[Path]:
    ablation = _maybe_read_csv(results_dir / "ablation_results.csv")
    if ablation is None:
        return []
    plt.figure(figsize=(11, 5.5))
    sns.barplot(data=ablation, x="ablation_group", y="auprc_empty", color="tab:blue")
    plt.ylim(0, 1)
    plt.xticks(rotation=25, ha="right")
    plt.title("LightGBM ablation: Empty-positive AUPRC")
    plt.xlabel("")
    plt.ylabel("Empty AUPRC")
    return [_save_fig(figures_dir / "ablation_empty_auprc.png")]


def _plot_examples(results_dir: Path, figures_dir: Path) -> list[Path]:
    paths = []
    for csv_path in sorted(results_dir.glob("example_*_day.csv")):
        if csv_path.name == "example_case_days.csv":
            continue
        example = _read_csv(csv_path)
        if "date" not in example or "predicted_empty_probability" not in example:
            continue
        label = csv_path.stem.removeprefix("example_")
        example["date"] = pd.to_datetime(example["date"], utc=True).dt.tz_convert("America/Los_Angeles")
        fig, ax = plt.subplots(figsize=(13, 4.8))
        ax.step(example["date"], example["predicted_empty_probability"], where="post", label="Predicted Empty score (legacy column; uncalibrated)")
        if "actual_occupied" in example:
            ax.fill_between(example["date"], 0, example["actual_occupied"], step="post", alpha=0.22, label="actual occupied")
        if "recommend_empty_stable" in example:
            recommended_label_added = False
            for i, is_rec in enumerate(example["recommend_empty_stable"].astype(bool)):
                if is_rec:
                    start = example["date"].iloc[i]
                    ax.axvspan(
                        start,
                        start + pd.Timedelta(minutes=15),
                        color="tab:green",
                        alpha=0.12,
                        label="Recommended empty window" if not recommended_label_added else None,
                    )
                    recommended_label_added = True
        ax.set_ylim(-0.02, 1.05)
        ax.set_title(label.replace("_", " ").title())
        ax.set_ylabel("Empty score / occupancy")
        ax.legend(loc="upper right")
        paths.append(_save_fig(figures_dir / f"example_forecast_{label}.png"))
    return paths


def _write_manifest(results_dir: Path, figures_dir: Path) -> None:
    rows = []
    for folder in [results_dir, figures_dir]:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                rows.append({"folder": folder.as_posix(), "file": path.name, "relative_path": path.as_posix(), "bytes": path.stat().st_size, "modified_time": pd.Timestamp.fromtimestamp(path.stat().st_mtime)})
    pd.DataFrame(rows).sort_values(["folder", "file"]).to_csv(results_dir / "current_run_manifest.csv", index=False, encoding="utf-8-sig")


def generate_all_figures(results_dir: str | Path = "results", figures_dir: str | Path = "figures") -> list[Path]:
    """Regenerate figures from existing result CSV files."""
    results_dir = Path(results_dir)
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    paths: list[Path] = []
    for plotter in [
        _plot_occupancy_profile,
        _plot_model_metrics,
        _plot_horizon_metrics,
        _plot_sweeps,
        _plot_policy_outputs,
        _plot_window_and_sensitivity,
        _plot_importance,
        _plot_curves,
        _plot_confusion,
        _plot_ablation,
        _plot_examples,
    ]:
        paths.extend(plotter(results_dir, figures_dir))
    _write_manifest(results_dir, figures_dir)
    return paths
