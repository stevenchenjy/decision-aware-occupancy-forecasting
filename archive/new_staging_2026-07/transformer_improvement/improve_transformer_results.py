# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results"
PRED_DIR = ROOT / "predictions"
REPORT_DIR = ROOT / "reports"

HORIZON_STEPS = 96
STABLE_EMPTY_MIN_STEPS = 4
RISK_DELTAS = (0.05, 0.10, 0.20)

BASE_MODEL_COLS = {
    "Historical average": "historical_average_empty_probability",
    "LightGBM": "lightgbm_empty_probability",
    "Random forest": "random_forest_empty_probability",
    "DLinear": "dlinear_empty_probability",
    "Transformer": "transformer_empty_probability",
}


def threshold_grid_values() -> np.ndarray:
    return np.round(np.arange(0.05, 0.9501, 0.025), 3)


def read_prediction_split(split: str) -> pd.DataFrame:
    path = RESULT_DIR / f"forecast_predictions_{split}_all_models.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def reshape_by_anchor(values: np.ndarray) -> np.ndarray:
    if len(values) % HORIZON_STEPS != 0:
        raise ValueError(f"Prediction rows are not divisible by {HORIZON_STEPS}: {len(values)}")
    return np.asarray(values).reshape(-1, HORIZON_STEPS)


def daily_anchor_indices(frame: pd.DataFrame) -> np.ndarray:
    anchor_times = frame["anchor_time"].iloc[::HORIZON_STEPS].astype(str).reset_index(drop=True)
    mask = anchor_times.str.slice(11, 16).eq("00:00").to_numpy()
    if not mask.any():
        mask = np.zeros(len(anchor_times), dtype=bool)
        mask[::HORIZON_STEPS] = True
    return np.flatnonzero(mask)


def load_controllable_kwh(frame: pd.DataFrame) -> np.ndarray:
    processed_path = RESULT_DIR / "processed_lbnl_15min_pacific.csv"
    processed = pd.read_csv(processed_path, usecols=["date_local", "hvac_S", "lig_S"])
    kwh = processed[["hvac_S", "lig_S"]].sum(axis=1).clip(lower=0.0) * 0.25
    load_map = pd.Series(kwh.to_numpy(dtype=float), index=processed["date_local"].astype(str))
    mapped = frame["target_time"].astype(str).map(load_map)
    missing_rate = float(mapped.isna().mean())
    if missing_rate > 0.01:
        print(f"Warning: controllable-load mapping missing rate is {missing_rate:.2%}")
    return mapped.fillna(0.0).to_numpy(dtype=float)


def empty_model_metrics(name: str, y_empty: np.ndarray, p_empty: np.ndarray) -> dict:
    y = np.asarray(y_empty, dtype=int).ravel()
    p = np.clip(np.asarray(p_empty, dtype=float).ravel(), 1e-6, 1.0 - 1e-6)
    pred = (p >= 0.5).astype(int)
    return {
        "model": name,
        "positive_class": "empty",
        "recall_empty": recall_score(y, pred, zero_division=0),
        "precision_empty": precision_score(y, pred, zero_division=0),
        "f1_empty": f1_score(y, pred, zero_division=0),
        "auroc_empty": roc_auc_score(y, p) if len(np.unique(y)) > 1 else np.nan,
        "auprc_empty": average_precision_score(y, p),
        "brier_empty": brier_score_loss(y, p),
        "log_loss_empty": log_loss(y, p) if len(np.unique(y)) > 1 else np.nan,
    }


def stable_empty_mask_from_prob(empty_prob: np.ndarray, threshold: float, min_steps: int) -> np.ndarray:
    high = np.asarray(empty_prob) >= threshold
    stable = np.zeros_like(high, dtype=bool)
    for i, row in enumerate(high):
        padded = np.concatenate([[False], row.astype(bool), [False]])
        changes = np.diff(padded.astype(int))
        starts = np.flatnonzero(changes == 1)
        ends = np.flatnonzero(changes == -1)
        for start, end in zip(starts, ends):
            if end - start >= min_steps:
                stable[i, start:end] = True
    return stable


def policy_metrics(
    model: str,
    y_empty: np.ndarray,
    empty_prob: np.ndarray,
    controllable_kwh: np.ndarray,
    threshold: float,
    policy: str,
    split: str,
    risk_delta: float | None = None,
    selection_met_constraint: bool | None = None,
) -> dict:
    rec = stable_empty_mask_from_prob(empty_prob, threshold, STABLE_EMPTY_MIN_STEPS)
    actual_empty = np.asarray(y_empty, dtype=bool)
    actual_occupied = ~actual_empty
    conflict = rec & actual_occupied
    safe = rec & actual_empty
    n_rec = int(rec.sum())
    n_empty = int(actual_empty.sum())
    n_occ = int(actual_occupied.sum())
    safe_kwh = float((controllable_kwh * safe).sum())
    gross_kwh = float((controllable_kwh * rec).sum())
    row = {
        "split": split,
        "model": model,
        "policy": policy,
        "risk_delta": risk_delta,
        "empty_probability_threshold": threshold,
        "stable_empty_min_steps": STABLE_EMPTY_MIN_STEPS,
        "daily_anchor_count": int(len(y_empty)),
        "recommendation_rate": float(rec.mean()) if rec.size else 0.0,
        "recommendation_count": n_rec,
        "occupancy_conflict_count": int(conflict.sum()),
        "occupancy_conflict_rate": float(conflict.sum() / n_rec) if n_rec else 0.0,
        "standard_fpr_occupied_denominator": float(conflict.sum() / n_occ) if n_occ else 0.0,
        "missed_opportunity_rate": float(((~rec) & actual_empty).sum() / n_empty) if n_empty else 0.0,
        "empty_window_precision": float(safe.sum() / n_rec) if n_rec else 0.0,
        "empty_window_recall": float(safe.sum() / n_empty) if n_empty else 0.0,
        "gross_shiftable_load_kwh": gross_kwh,
        "safe_shiftable_load_opportunity_kwh": safe_kwh,
        "kwh_per_day": safe_kwh / max(len(y_empty), 1),
        "selection_met_constraint": selection_met_constraint,
    }
    return row


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "(empty)"
    text = frame.copy()
    for col in text.columns:
        if pd.api.types.is_float_dtype(text[col]):
            text[col] = text[col].map(lambda x: "" if pd.isna(x) else f"{x:.4f}")
        else:
            text[col] = text[col].astype(str)
    headers = list(text.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in text.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in headers) + " |")
    return "\n".join(lines)


def select_thresholds(
    model: str,
    y_empty_daily: np.ndarray,
    p_empty_daily: np.ndarray,
    kwh_daily: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sweep_rows = []
    for threshold in threshold_grid_values():
        sweep_rows.append(
            policy_metrics(
                model=model,
                y_empty=y_empty_daily,
                empty_prob=p_empty_daily,
                controllable_kwh=kwh_daily,
                threshold=float(threshold),
                policy="validation_threshold_sweep",
                split="validation_daily",
            )
        )
    sweep = pd.DataFrame(sweep_rows)
    selected = []
    for delta in RISK_DELTAS:
        eligible = sweep[sweep["occupancy_conflict_rate"] <= delta]
        met = not eligible.empty
        if met:
            chosen = eligible.sort_values(
                ["safe_shiftable_load_opportunity_kwh", "empty_window_recall"],
                ascending=False,
            ).iloc[0]
            note = f"max safe opportunity subject to occupancy conflict <= {delta:.0%} on validation"
        else:
            chosen = sweep.sort_values(["occupancy_conflict_rate", "missed_opportunity_rate"]).iloc[0]
            note = f"no validation threshold met occupancy conflict <= {delta:.0%}; lowest-conflict fallback"
        selected.append(
            {
                "model": model,
                "risk_delta": delta,
                "selected_empty_probability_threshold": float(chosen["empty_probability_threshold"]),
                "validation_occupancy_conflict_rate": float(chosen["occupancy_conflict_rate"]),
                "validation_safe_shiftable_load_opportunity_kwh": float(
                    chosen["safe_shiftable_load_opportunity_kwh"]
                ),
                "selection_met_constraint": bool(met),
                "selection_note": note,
            }
        )
    return sweep, pd.DataFrame(selected)


def weighted_probability(frame: pd.DataFrame, weights: dict[str, float]) -> np.ndarray:
    out = np.zeros(len(frame), dtype=float)
    for model_key, weight in weights.items():
        out += float(weight) * frame[BASE_MODEL_COLS[model_key]].to_numpy(dtype=float)
    return np.clip(out, 1e-6, 1.0 - 1e-6)


def find_best_seasonal_transformer_weight(val: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    y_val = val["actual_empty_positive"].to_numpy(dtype=int)
    rows = []
    best_alpha = 0.0
    best_score = -np.inf
    t = val[BASE_MODEL_COLS["Transformer"]].to_numpy(dtype=float)
    h = val[BASE_MODEL_COLS["Historical average"]].to_numpy(dtype=float)
    for alpha in np.linspace(0.0, 1.0, 101):
        p = alpha * t + (1.0 - alpha) * h
        score = average_precision_score(y_val, p)
        rows.append(
            {
                "candidate": "Seasonal-Transformer blend",
                "transformer_weight": alpha,
                "historical_average_weight": 1.0 - alpha,
                "validation_auprc_empty": score,
            }
        )
        if score > best_score:
            best_score = score
            best_alpha = float(alpha)
    return best_alpha, pd.DataFrame(rows)


def build_candidate_probabilities(val: pd.DataFrame, test: pd.DataFrame) -> tuple[dict, dict, pd.DataFrame]:
    alpha, alpha_search = find_best_seasonal_transformer_weight(val)
    seasonal_weights = {
        "Historical average": 1.0 - alpha,
        "Transformer": alpha,
    }

    candidates = {
        "Transformer": {"Transformer": 1.0},
        "Historical average": {"Historical average": 1.0},
        "LightGBM": {"LightGBM": 1.0},
        "Seasonal-Transformer blend": seasonal_weights,
        "Hybrid Seasonal-GBDT-Transformer": {
            "Historical average": 0.15,
            "LightGBM": 0.60,
            "Transformer": 0.25,
        },
        "Hybrid balanced tree-deep": {
            "Historical average": 0.20,
            "LightGBM": 0.50,
            "Random forest": 0.10,
            "Transformer": 0.20,
        },
        "Hybrid tree-seasonal": {
            "Historical average": 0.25,
            "LightGBM": 0.55,
            "Random forest": 0.20,
        },
    }

    val_probs = {name: weighted_probability(val, weights) for name, weights in candidates.items()}
    test_probs = {name: weighted_probability(test, weights) for name, weights in candidates.items()}

    y_val = val["actual_empty_positive"].to_numpy(dtype=int)
    y_test = test["actual_empty_positive"].to_numpy(dtype=int)
    rows = []
    for name, weights in candidates.items():
        row = {
            "candidate": name,
            "weights": "; ".join(f"{k}={v:.2f}" for k, v in weights.items()),
            "validation_auprc_empty": average_precision_score(y_val, val_probs[name]),
            "test_auprc_empty": average_precision_score(y_test, test_probs[name]),
        }
        rows.append(row)
    candidate_scores = pd.DataFrame(rows).sort_values("validation_auprc_empty", ascending=False)
    alpha_search.to_csv(RESULT_DIR / "improved_transformer_alpha_search.csv", index=False, encoding="utf-8-sig")
    return val_probs, test_probs, candidate_scores


def write_assignment_report(
    candidate_scores: pd.DataFrame,
    metrics_df: pd.DataFrame,
    policy_df: pd.DataFrame,
    selected_df: pd.DataFrame,
) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    baseline = metrics_df[metrics_df["model"].eq("Transformer")].iloc[0]
    seasonal = metrics_df[metrics_df["model"].eq("Seasonal-Transformer blend")].iloc[0]
    primary_model = str(candidate_scores.iloc[0]["candidate"])
    primary = metrics_df[metrics_df["model"].eq(primary_model)].iloc[0]
    best_test = metrics_df.iloc[0]

    def pct(x: float) -> str:
        return f"{100.0 * x:.2f}%"

    delta10 = policy_df[policy_df["policy"].eq("risk_delta_10%")].copy()
    delta10 = delta10.sort_values("safe_shiftable_load_opportunity_kwh", ascending=False)
    primary_delta10 = delta10[delta10["model"].eq(primary_model)].iloc[0]
    best_test_delta10 = delta10[delta10["model"].eq(best_test["model"])].iloc[0]
    seasonal_delta10 = delta10[delta10["model"].eq("Seasonal-Transformer blend")].iloc[0]
    transformer_delta10 = delta10[delta10["model"].eq("Transformer")].iloc[0]

    top_candidates = dataframe_to_markdown(candidate_scores)
    model_metrics = metrics_df[
        [
            "model",
            "auprc_empty",
            "auroc_empty",
            "f1_empty",
            "brier_empty",
            "log_loss_empty",
        ]
    ]
    model_metrics = dataframe_to_markdown(model_metrics)
    policy_metrics = delta10[
        [
            "model",
            "empty_probability_threshold",
            "occupancy_conflict_rate",
            "safe_shiftable_load_opportunity_kwh",
            "kwh_per_day",
            "recommendation_count",
        ]
    ]
    policy_metrics = dataframe_to_markdown(policy_metrics)

    report = f"""# Transformer 改进实验与作业说明材料

## 1. 问题诊断

原 notebook 中 Transformer 的测试集 Empty AUPRC 为 {baseline['auprc_empty']:.4f}，低于 Historical average、LightGBM 和 Random forest。训练日志显示 Transformer 的训练损失持续下降，但验证损失在第 2-4 轮后开始反弹，说明该数据集下纯序列 Transformer 容易过拟合；同时占用行为具有强日周期和周周期，简单历史周期先验本身已经很强。

## 2. 改进思路

本次快速改进采用“季节先验 + 判别模型 + Transformer”的轻量融合结构：

1. **Seasonal-Transformer blend**：用验证集搜索 Transformer 与历史周期先验的线性融合权重，只使用验证集选权，测试集不参与调参。
2. **Hybrid Seasonal-GBDT-Transformer**：在 Seasonal-Transformer 的基础上加入 LightGBM 的非线性表格特征表达，固定权重为 `Historical average=0.15, LightGBM=0.60, Transformer=0.25`。这个结构保留 Transformer 的多步时序信息，同时用季节先验稳定周期模式，用 GBDT 捕获小样本传感器/日历特征的非线性关系。
3. **Hybrid balanced tree-deep**：作为补充消融，加入少量 Random forest 并降低 LightGBM 权重，用于检验树模型集成是否还能进一步改善排序能力。
4. **训练策略解释**：原 Transformer 已出现早停前过拟合，因此本轮不继续堆深模型，而是采用验证集调权的集成正则化，相当于对 Transformer 输出做先验校准和模型平均。

## 3. 验证集选权结果

{top_candidates}

## 4. 模型级测试对比

{model_metrics}

相对原 Transformer，Seasonal-Transformer blend 的 Empty AUPRC 从 {baseline['auprc_empty']:.4f} 提升到 {seasonal['auprc_empty']:.4f}，提升 {seasonal['auprc_empty'] - baseline['auprc_empty']:.4f}。按验证集 AUPRC 选择的主方案为 **{primary_model}**，测试 AUPRC 为 {primary['auprc_empty']:.4f}；测试集中最高的补充候选为 **{best_test['model']}**，AUPRC 为 {best_test['auprc_empty']:.4f}。后者可作为消融结果展示，但严格模型选择应以验证集排序为准。

## 5. 10% 风险约束推荐对比

{policy_metrics}

在 10% 验证集风险约束下，原 Transformer 的测试安全可调负荷机会为 {transformer_delta10['safe_shiftable_load_opportunity_kwh']:.1f} kWh；Seasonal-Transformer blend 提升到 {seasonal_delta10['safe_shiftable_load_opportunity_kwh']:.1f} kWh；验证集选出的主方案 **{primary_model}** 达到 {primary_delta10['safe_shiftable_load_opportunity_kwh']:.1f} kWh，测试占用冲突率为 {pct(primary_delta10['occupancy_conflict_rate'])}。测试 AUPRC 最高的补充候选 **{best_test['model']}** 在同一 10% 约束下为 {best_test_delta10['safe_shiftable_load_opportunity_kwh']:.1f} kWh，冲突率为 {pct(best_test_delta10['occupancy_conflict_rate'])}。

## 6. 可写入作业的创新点

- **面向建筑占用预测的周期先验融合**：不是直接替换 Transformer，而是把强日周期/周周期先验作为可解释基线，与 Transformer 输出进行验证集校准。
- **小数据稳健化策略**：针对 Transformer 过拟合，引入模型平均和先验校准，降低单个深度模型在短时间跨度数据上的方差。
- **风险约束目标一致**：模型选择不仅看 AUPRC，还继续沿用 notebook 中的“最大化安全可调负荷机会，同时限制占用冲突率”的业务指标。
- **不使用未来传感器或负荷泄漏**：融合只使用已有模型的合法预测输出；HVAC/lighting 仍只用于机会评估，不作为预测输入。

## 7. 文件输出

- `results/improved_transformer_candidate_scores.csv`
- `results/improved_transformer_model_metrics.csv`
- `results/improved_transformer_selected_thresholds.csv`
- `results/improved_transformer_policy_results_test.csv`
- `predictions/hybrid_transformer_test_predictions.csv`
"""
    (REPORT_DIR / "transformer_improvement_assignment_notes.md").write_text(report, encoding="utf-8")


def main() -> None:
    RESULT_DIR.mkdir(exist_ok=True)
    PRED_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)

    val = read_prediction_split("validation")
    test = read_prediction_split("test")

    val_probs, test_probs, candidate_scores = build_candidate_probabilities(val, test)
    candidate_scores.to_csv(
        RESULT_DIR / "improved_transformer_candidate_scores.csv",
        index=False,
        encoding="utf-8-sig",
    )

    y_val = val["actual_empty_positive"].to_numpy(dtype=int)
    y_test = test["actual_empty_positive"].to_numpy(dtype=int)

    metric_rows = []
    for name, p in test_probs.items():
        metric_rows.append(empty_model_metrics(name, y_test, p))
    metrics_df = pd.DataFrame(metric_rows).sort_values("auprc_empty", ascending=False)
    metrics_df.to_csv(
        RESULT_DIR / "improved_transformer_model_metrics.csv",
        index=False,
        encoding="utf-8-sig",
    )

    val_y_daily = reshape_by_anchor(y_val)[daily_anchor_indices(val)]
    test_y_daily = reshape_by_anchor(y_test)[daily_anchor_indices(test)]
    val_kwh_daily = reshape_by_anchor(load_controllable_kwh(val))[daily_anchor_indices(val)]
    test_kwh_daily = reshape_by_anchor(load_controllable_kwh(test))[daily_anchor_indices(test)]

    selected_rows = []
    validation_sweep_rows = []
    policy_rows = []
    for name in test_probs.keys():
        val_daily = reshape_by_anchor(val_probs[name])[daily_anchor_indices(val)]
        test_daily = reshape_by_anchor(test_probs[name])[daily_anchor_indices(test)]
        sweep, selected = select_thresholds(name, val_y_daily, val_daily, val_kwh_daily)
        validation_sweep_rows.append(sweep)
        selected_rows.append(selected)
        for _, row in selected.iterrows():
            delta = float(row["risk_delta"])
            threshold = float(row["selected_empty_probability_threshold"])
            policy_rows.append(
                policy_metrics(
                    model=name,
                    y_empty=test_y_daily,
                    empty_prob=test_daily,
                    controllable_kwh=test_kwh_daily,
                    threshold=threshold,
                    policy=f"risk_delta_{delta:.0%}",
                    split="test_daily",
                    risk_delta=delta,
                    selection_met_constraint=bool(row["selection_met_constraint"]),
                )
            )

    validation_sweep_df = pd.concat(validation_sweep_rows, ignore_index=True)
    selected_df = pd.concat(selected_rows, ignore_index=True)
    policy_df = pd.DataFrame(policy_rows)

    validation_sweep_df.to_csv(
        RESULT_DIR / "improved_transformer_threshold_sweep_validation_daily.csv",
        index=False,
        encoding="utf-8-sig",
    )
    selected_df.to_csv(
        RESULT_DIR / "improved_transformer_selected_thresholds.csv",
        index=False,
        encoding="utf-8-sig",
    )
    policy_df.to_csv(
        RESULT_DIR / "improved_transformer_policy_results_test.csv",
        index=False,
        encoding="utf-8-sig",
    )

    out_pred = pd.DataFrame(
        {
            "split": "test",
            "anchor_time": test["anchor_time"],
            "target_time": test["target_time"],
            "horizon_step": test["horizon_step"],
            "actual_empty_positive": y_test,
            "transformer_empty_probability": test_probs["Transformer"],
            "seasonal_transformer_empty_probability": test_probs["Seasonal-Transformer blend"],
            "hybrid_transformer_empty_probability": test_probs["Hybrid Seasonal-GBDT-Transformer"],
            "hybrid_balanced_tree_deep_empty_probability": test_probs["Hybrid balanced tree-deep"],
            "hybrid_tree_seasonal_empty_probability": test_probs["Hybrid tree-seasonal"],
        }
    )
    out_pred.to_csv(PRED_DIR / "hybrid_transformer_test_predictions.csv", index=False, encoding="utf-8-sig")

    write_assignment_report(candidate_scores, metrics_df, policy_df, selected_df)

    print("Improved Transformer experiment complete.")
    print("Top model metrics:")
    print(metrics_df[["model", "auprc_empty", "f1_empty", "brier_empty"]].to_string(index=False))
    print("10% risk policy:")
    print(
        policy_df[policy_df["policy"].eq("risk_delta_10%")][
            [
                "model",
                "empty_probability_threshold",
                "occupancy_conflict_rate",
                "safe_shiftable_load_opportunity_kwh",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
