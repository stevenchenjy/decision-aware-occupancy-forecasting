import numpy as np


def interval_kwh(power_kw, interval_hours=0.25):
    return np.clip(np.asarray(power_kw, dtype=float), 0, None) * interval_hours


def safe_shiftable_load_opportunity(y_empty, recommend_empty, controllable_kwh):
    y_empty = np.asarray(y_empty).astype(bool)
    rec = np.asarray(recommend_empty).astype(bool)
    kwh = np.asarray(controllable_kwh, dtype=float)
    safe = rec & y_empty
    conflict = rec & (~y_empty)
    return {
        "gross_shiftable_load_kwh": float((kwh * rec).sum()),
        "safe_shiftable_load_kwh": float((kwh * safe).sum()),
        "conflict_kwh": float((kwh * conflict).sum()),
        "safe_intervals": int(safe.sum()),
        "conflict_intervals": int(conflict.sum()),
    }


def controllability_scenarios(base_safe_kwh):
    return {
        "Scenario A: 100% selected load controllable": base_safe_kwh,
        "Scenario B: 50% controllable-load assumption": base_safe_kwh * 0.5,
        "Scenario C: 25% controllable-load assumption": base_safe_kwh * 0.25,
    }
