import numpy as np
from sklearn.ensemble import RandomForestClassifier

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover
    LGBMClassifier = None


def historical_average_probability(df, train_boundary, positions, slot_col="slot", target_col="occupied"):
    train = df[df.index < train_boundary]
    table = train.groupby(slot_col)[target_col].mean()
    global_mean = float(train[target_col].mean())
    slots = df[slot_col].to_numpy()[positions.ravel()]
    return np.array([table.get(s, global_mean) for s in slots], dtype=np.float32).reshape(positions.shape)


def make_lightgbm(seed=42, n_estimators=320):
    if LGBMClassifier is None:
        raise RuntimeError("lightgbm is not installed")
    return LGBMClassifier(
        n_estimators=n_estimators,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=50,
        colsample_bytree=0.85,
        # LightGBM enables row bagging only when subsample_freq is positive.
        # State the inactive/default behavior explicitly rather than implying
        # that a configured fraction is used.
        subsample=1.0,
        subsample_freq=0,
        reg_lambda=1.0,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
        verbose=-1,
    )


def make_random_forest(seed=42, n_estimators=70):
    return RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=14,
        min_samples_leaf=20,
        max_features="sqrt",
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=seed,
    )
