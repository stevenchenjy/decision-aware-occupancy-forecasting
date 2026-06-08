import numpy as np


def stable_empty_mask(empty_probability, threshold, min_steps):
    high = np.asarray(empty_probability) >= threshold
    if high.ndim == 1:
        high = high.reshape(1, -1)
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


def extract_windows(mask, min_steps):
    mask = np.asarray(mask).astype(bool)
    padded = np.concatenate([[False], mask, [False]])
    changes = np.diff(padded.astype(int))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return [(int(s), int(e)) for s, e in zip(starts, ends) if e - s >= min_steps]


def select_threshold(validation_sweep, risk_delta):
    eligible = validation_sweep[validation_sweep["occupancy_conflict_rate"] <= risk_delta]
    if len(eligible):
        return eligible.sort_values(["safe_shiftable_load_kwh", "empty_recall"], ascending=False).iloc[0]
    return validation_sweep.sort_values(["occupancy_conflict_rate", "safe_shiftable_load_kwh"], ascending=[True, False]).iloc[0]
