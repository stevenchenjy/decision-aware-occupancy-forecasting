import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar


def time_features(index):
    minutes = index.hour * 60 + index.minute
    hour_angle = 2 * np.pi * minutes / (24 * 60)
    dow_angle = 2 * np.pi * index.dayofweek / 7
    month_angle = 2 * np.pi * (index.month - 1) / 12
    holidays = USFederalHolidayCalendar().holidays(index.min().tz_localize(None), index.max().tz_localize(None))
    holiday_dates = set(pd.DatetimeIndex(holidays).date)
    out = pd.DataFrame(index=index)
    out["hour_sin"] = np.sin(hour_angle)
    out["hour_cos"] = np.cos(hour_angle)
    out["day_of_week_sin"] = np.sin(dow_angle)
    out["day_of_week_cos"] = np.cos(dow_angle)
    out["weekend"] = (index.dayofweek >= 5).astype(float)
    out["month_sin"] = np.sin(month_angle)
    out["month_cos"] = np.cos(month_angle)
    out["holiday"] = pd.Series([d in holiday_dates for d in index.date], index=index, dtype=float)
    return out


def future_positions(anchors, horizon_steps):
    return anchors[:, None] + np.arange(1, horizon_steps + 1)[None, :]


def rolling_mean_shifted(arr, anchors, window):
    """Use arr[anchor-window:anchor], excluding current and future values."""
    arr = np.asarray(arr, dtype=np.float64)
    csum = np.concatenate([[0.0], np.cumsum(arr)])
    out = np.full(len(anchors), np.nan, dtype=np.float32)
    valid = anchors - window >= 0
    if valid.any():
        a = anchors[valid]
        out[valid] = ((csum[a] - csum[a - window]) / window).astype(np.float32)
    fill = np.nanmean(out)
    return np.nan_to_num(out, nan=0.0 if not np.isfinite(fill) else fill)


def lag_at_anchors(arr, anchors, lag):
    out = np.full(len(anchors), np.nan, dtype=np.float32)
    valid = anchors - lag >= 0
    if valid.any():
        out[valid] = arr[anchors[valid] - lag]
    fill = np.nanmean(out)
    return np.nan_to_num(out, nan=0.0 if not np.isfinite(fill) else fill)
