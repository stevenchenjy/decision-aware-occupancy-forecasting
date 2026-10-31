"""Small, dependency-free replay of the published saved-output policy scope.

No training, model selection, or claim of prospective availability occurs here.
The browser, notebook, and exported CSV use the same 43 recorded horizons.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = "results/canonical_policy_10pct.csv"
PREDICTION_FILE = "results/forecast_predictions_test_all_models.csv"
LOAD_FILE = "results/processed_lbnl_15min_pacific.csv"
MODELS = {
    "hybrid": ("Selected hybrid", "Hybrid Seasonal-GBDT-Transformer"),
    "historical": ("Historical schedule", "Historical Average"),
    "lightgbm": ("LightGBM", "LightGBM"),
}
THRESHOLDS = [round(0.05 + 0.025 * n, 3) for n in range(37)]
MIN_STEPS = [4, 8, 16]


def stable_mask(scores, threshold, min_steps):
    """Keep whole threshold-passing runs within one horizon, including edges."""
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold must be finite and between zero and one")
    if not isinstance(min_steps, int) or min_steps < 1:
        raise ValueError("Minimum duration must be a positive number of intervals")
    mask = [False] * len(scores)
    start = None
    for i in range(len(scores) + 1):
        high = i < len(scores) and scores[i] >= threshold
        if high and start is None:
            start = i
        if not high and start is not None:
            if i - start >= min_steps:
                mask[start:i] = [True] * (i - start)
            start = None
    return mask


def evaluate(days, model="hybrid", threshold=0.875, min_steps=4):
    """Account once per target interval, without crossing horizon boundaries."""
    if model not in MODELS:
        raise ValueError(f"Unknown model: {model}")
    recommended = conflicts = windows = 0
    opportunity = []
    for day in days:
        labels, loads, scores = day["empty"], day["loadKwh"], day["scores"][model]
        if len(labels) != len(loads) or len(labels) != len(scores):
            raise ValueError("Scores, labels, and loads must be aligned")
        mask = stable_mask(scores, threshold, min_steps)
        recommended += sum(mask)
        conflicts += sum(on and not label for on, label in zip(mask, labels))
        windows += sum(on and (i == 0 or not mask[i - 1]) for i, on in enumerate(mask))
        opportunity.extend(load for on, label, load in zip(mask, labels, loads) if on and label)
    return {
        "recommendedIntervals": recommended,
        "conflictIntervals": conflicts,
        "recommendedWindows": windows,
        "conflictRate": conflicts / recommended if recommended else 0.0,
        "opportunityKwh": math.fsum(opportunity),
    }


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def build_payload(root=ROOT):
    """Select the documented midnight-labelled horizons from canonical exports."""
    policy = {row["model"]: row for row in read_rows(root / POLICY_FILE)}
    loads = {}
    for row in read_rows(root / LOAD_FILE):
        key = row["date_local"]
        if key in loads:
            raise ValueError(f"Duplicate processed timestamp: {key}")
        value = max(float(row["hvac_S"]) + float(row["lig_S"]), 0) * 0.25
        if not math.isfinite(value):
            raise ValueError(f"Non-finite processed load: {key}")
        loads[key] = value

    daily = {}
    for row in read_rows(root / PREDICTION_FILE):
        anchor = row["anchor_time"]
        if anchor[11:16] != "00:00":
            continue
        if row["split"] != "test":
            raise ValueError("Demo inputs must belong to the saved test scope")
        day = daily.setdefault(anchor, {
            "anchor": anchor, "targetTimes": [], "empty": [], "loadKwh": [],
            "scores": {name: [] for name in MODELS},
        })
        if int(row["horizon_step"]) != len(day["empty"]) + 1:
            raise ValueError("Daily rows must contain ordered horizon steps 1..96")
        target = row["target_time"]
        if target not in loads:
            raise ValueError(f"Missing processed load for {target}")
        label = int(row["actual_empty_positive"])
        if label not in (0, 1) or label != 1 - int(row["actual_occupied"]):
            raise ValueError("Invalid or inconsistent Empty label")
        h = float(row["historical_average_empty_probability"])
        l = float(row["lightgbm_empty_probability"])
        t = float(row["transformer_empty_probability"])
        if any(not math.isfinite(v) or v < 0 or v > 1 for v in (h, l, t)):
            raise ValueError("Invalid Empty-class score")
        day["scores"]["historical"].append(h)
        day["scores"]["lightgbm"].append(l)
        day["scores"]["hybrid"].append(min(max(0.15 * h + 0.60 * l + 0.25 * t, 1e-6), 1 - 1e-6))
        day["empty"].append(label)
        day["loadKwh"].append(loads[target])
        day["targetTimes"].append(target)
    days = list(daily.values())
    if len(days) != 43 or any(len(day["empty"]) != 96 for day in days):
        raise ValueError("Expected the 43 complete, non-overlapping 96-interval horizons")
    targets = [time for day in days for time in day["targetTimes"]]
    if len(set(targets)) != 43 * 96:
        raise ValueError("Demo target horizons overlap")

    models = []
    for key, (label, saved_name) in MODELS.items():
        reference = policy[saved_name]
        threshold = float(reference["selected_threshold"])
        metrics = evaluate(days, key, threshold)
        for metric, column in [
            ("recommendedIntervals", "recommended_intervals"),
            ("conflictIntervals", "conflict_intervals"),
            ("recommendedWindows", "recommended_windows"),
            ("opportunityKwh", "safe_opportunity_kwh"),
        ]:
            if not math.isclose(metrics[metric], float(reference[column]), rel_tol=1e-10, abs_tol=1e-7):
                raise ValueError(f"{saved_name}: demo {metric} disagrees with canonical policy table")
        models.append({"id": key, "label": label, "reportedThreshold": threshold, "reportedMetrics": metrics})
    reference_grid = [
        {"model": model, "threshold": threshold, "minSteps": steps,
         **evaluate(days, model, threshold, steps)}
        for model in MODELS for threshold in THRESHOLDS for steps in MIN_STEPS
    ]
    # The initial illustration is selected once using the reported hybrid policy.
    # It does not change the aggregate scope or refit a policy to this test period.
    example = max(range(len(days)), key=lambda i: evaluate([days[i]])["opportunityKwh"])
    return {
        "schemaVersion": 1,
        "scope": "43 saved, non-overlapping test horizons; 4,128 target intervals",
        "intervalMinutes": 15,
        "timeConvention": "Local Pacific labels. A 00:00 anchor uses the completed 00:00-00:15 input bin; targets span 00:15 to the next 00:15.",
        "weights": {"historical": 0.15, "lightgbm": 0.60, "transformer": 0.25},
        "sources": [{"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}
                    for path in [PREDICTION_FILE, LOAD_FILE, POLICY_FILE]],
        "models": models, "thresholds": THRESHOLDS, "minimumSteps": MIN_STEPS,
        "defaultExampleIndex": example, "days": days, "referenceGrid": reference_grid,
    }


def payload_text(payload):
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"
