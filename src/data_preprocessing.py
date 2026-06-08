from pathlib import Path

import pandas as pd


def read_timeseries(path, raw_timezone="UTC", local_timezone="America/Los_Angeles"):
    """Read a LBNL CSV and convert naive raw timestamps to local time."""
    raw = pd.read_csv(path)
    if "date" not in raw.columns:
        raw = raw.rename(columns={raw.columns[0]: "date"})
    raw = raw.loc[:, [c for c in raw.columns if not str(c).startswith("Unnamed")]]
    dt = pd.to_datetime(raw["date"], errors="coerce")
    raw = raw.loc[dt.notna()].copy()
    dt = dt.loc[dt.notna()]
    raw["date"] = dt.dt.tz_localize(raw_timezone).dt.tz_convert(local_timezone)
    for col in raw.columns:
        if col != "date":
            raw[col] = pd.to_numeric(raw[col], errors="coerce")
    return raw.sort_values("date")


def resample_mean(df, freq="15min"):
    return df.set_index("date").sort_index().resample(freq).mean()


def create_occupancy_frame(data_dir, freq="15min", occupied_count_threshold=0.0):
    occ_raw = read_timeseries(Path(data_dir) / "occ.csv").set_index("date")
    occ_cols = [c for c in occ_raw.columns if c.startswith("occ_")]
    occ_raw["occ_count"] = occ_raw[occ_cols].sum(axis=1, min_count=1)
    occ = pd.DataFrame(
        {
            "occ_count_mean": occ_raw["occ_count"].resample(freq).mean(),
            "occ_count_max": occ_raw["occ_count"].resample(freq).max(),
        }
    )
    occ["occupied"] = (occ["occ_count_max"] > occupied_count_threshold).astype(float)
    occ["empty"] = 1.0 - occ["occupied"]
    return occ.dropna(subset=["occ_count_mean", "occupied"]).sort_index()


def causal_fill(frame, protected_columns):
    """Leakage-safe missing handling: past-only ffill and fixed 0.0 leading fill."""
    out = frame.copy()
    cols = [c for c in out.columns if c not in set(protected_columns)]
    out[cols] = out[cols].ffill().fillna(0.0)
    return out


def chronological_split(index, history_steps=96, horizon_steps=96, train_fraction=0.70, val_fraction=0.15, gap_steps=96):
    anchors = pd.Series(range(history_steps - 1, len(index) - horizon_steps))
    anchors = anchors.to_numpy()
    hist_starts = anchors - history_steps + 1
    target_ends = anchors + horizon_steps
    train_boundary = (index[int(len(index) * train_fraction)] - pd.Timedelta(days=int(index[int(len(index) * train_fraction)].dayofweek))).normalize()
    val_boundary = (index[int(len(index) * (train_fraction + val_fraction))] - pd.Timedelta(days=int(index[int(len(index) * (train_fraction + val_fraction))].dayofweek))).normalize()
    gap = pd.Timedelta(minutes=15 * gap_steps)
    hist_start_times = index.take(hist_starts)
    target_end_times = index.take(target_ends)
    return {
        "train": anchors[target_end_times < train_boundary],
        "validation": anchors[(hist_start_times >= train_boundary + gap) & (target_end_times < val_boundary)],
        "test": anchors[hist_start_times >= val_boundary + gap],
    }
