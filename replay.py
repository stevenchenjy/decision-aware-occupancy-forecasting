#!/usr/bin/env python3
"""Replay the saved occupancy comparison offline using Python's standard library."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform

from src.demo_analysis import MODELS, evaluate

ROOT = Path(__file__).resolve().parent


def load_records(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    if data.get("schemaVersion") != 1 or len(data.get("days", [])) != 43:
        raise ValueError("Expected schema 1 and 43 saved daily horizons")
    targets = []
    if {model["id"] for model in data["models"]} != set(MODELS):
        raise ValueError("Expected the three documented models")
    for day in data["days"]:
        if any(len(day[key]) != 96 for key in ["targetTimes", "empty", "loadKwh"]):
            raise ValueError("Expected 96 aligned intervals in each horizon")
        if any(label not in (0, 1) for label in day["empty"]):
            raise ValueError("Camera labels must be zero or one")
        if any(not math.isfinite(load) or load < 0 for load in day["loadKwh"]):
            raise ValueError("Processed loads must be finite and non-negative")
        for model in MODELS:
            scores = day["scores"][model]
            if len(scores) != 96 or any(not math.isfinite(score) or not 0 <= score <= 1 for score in scores):
                raise ValueError("Expected 96 finite scores per model")
        targets.extend(day["targetTimes"])
    if len(set(targets)) != 4128:
        raise ValueError("Saved daily targets must not overlap")
    return data, hashlib.sha256(raw).hexdigest()


def compare(data, model="all", threshold=None, min_hours=1):
    if min_hours not in (1, 2, 4):
        raise ValueError("Minimum window must be one, two, or four hours")
    if model not in (*MODELS, "all"):
        raise ValueError("Unknown model")
    if threshold is not None and (not math.isfinite(threshold) or not 0 <= threshold <= 1):
        raise ValueError("Threshold must be finite and between zero and one")
    if threshold is not None and model == "all":
        raise ValueError("Select one model when exploring a custom threshold")
    rows = []
    for entry in data["models"]:
        if model != "all" and entry["id"] != model:
            continue
        selected = entry["reportedThreshold"] if threshold is None else threshold
        reported = min_hours == 1 and math.isclose(selected, entry["reportedThreshold"], rel_tol=0, abs_tol=1e-12)
        result = evaluate(data["days"], entry["id"], selected, min_hours * 4)
        if reported:
            for key, expected in entry["reportedMetrics"].items():
                if not math.isclose(result[key], expected, rel_tol=1e-10, abs_tol=1e-7):
                    raise ValueError(f"The reported {entry['id']} {key} does not reconcile")
        rows.append({"model": entry["id"], "threshold": selected, "minimum_window_hours": min_hours,
                     "analysis_status": "reported_fixed_policy" if reported else "exploratory_replay",
                     "reconciled_with_reported_metrics": reported, **result})
    return rows


def verify_kit(root):
    """Check every distributed input when running an extracted release kit."""
    manifest_path = root / "kit-manifest.json"
    if not manifest_path.exists():
        return {"software_version": "working-tree", "source_commit": None, "kit_integrity_checked": False}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if root.resolve() not in path.parents or not path.is_file():
            raise ValueError("Invalid or missing kit manifest file")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Kit file hash does not match: {name}")
    return {"software_version": manifest["release_tag"], "source_commit": manifest["source_commit"],
            "kit_integrity_checked": True}


def receipt(data, data_hash, rows, version):
    return {
        "receipt_schema": 1, "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "stevenchenjy/decision-aware-occupancy-forecasting", **version,
        "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(), "os": platform.system()},
        "data_sha256": data_hash, "source_export_hashes": data["sources"],
        "scope": {"daily_horizons": 43, "unique_target_intervals": 4128}, "observed_results": rows,
        "interpretation": "This is a locally generated saved-output replay receipt. It is not an endorsement, independent validation, proof of authorship, or evidence of energy savings. No data were sent by this command.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["all", *MODELS], default="all")
    parser.add_argument("--threshold", type=float, help="Custom score threshold; requires a single model and is exploratory")
    parser.add_argument("--min-hours", type=int, choices=[1, 2, 4], default=1)
    parser.add_argument("--receipt", type=Path, help="Write an optional JSON result receipt locally")
    parser.add_argument("--csv", type=Path, help="Write the comparison table locally")
    args = parser.parse_args()
    try:
        version = verify_kit(ROOT)
        data, data_hash = load_records(ROOT / "docs/demo/data.json")
        rows = compare(data, args.model, args.threshold, args.min_hours)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
    print("Saved-output replay: 43 non-overlapping horizons; 4,128 target intervals")
    print("Model           Threshold  Hours  Windows  Intervals  Conflicts  Load overlap (kWh)  Status")
    for row in rows:
        print(f"{row['model']:<15} {row['threshold']:>8.3f} {row['minimum_window_hours']:>6} {row['recommendedWindows']:>8} {row['recommendedIntervals']:>10} {row['conflictIntervals']:>10} {row['opportunityKwh']:>19.1f}  {row['analysis_status']}")
    print("Load overlap is not measured energy savings. Changed settings are exploratory.")
    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print("Saved comparison CSV:", args.csv)
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt(data, data_hash, rows, version), indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print("Saved local receipt:", args.receipt)
    print("Nothing was uploaded or reported automatically.")


if __name__ == "__main__":
    main()
