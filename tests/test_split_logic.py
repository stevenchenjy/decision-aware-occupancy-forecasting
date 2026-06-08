import pandas as pd

from src.data_preprocessing import chronological_split


def test_chronological_split_respects_order_and_gap():
    index = pd.date_range("2020-01-01", periods=96 * 140, freq="15min", tz="America/Los_Angeles")
    history_steps = 96
    horizon_steps = 96
    gap_steps = 96

    splits = chronological_split(
        index,
        history_steps=history_steps,
        horizon_steps=horizon_steps,
        train_fraction=0.70,
        val_fraction=0.15,
        gap_steps=gap_steps,
    )

    train = splits["train"]
    validation = splits["validation"]
    test = splits["test"]

    assert len(train) > 0
    assert len(validation) > 0
    assert len(test) > 0
    assert train.max() < validation.min()
    assert validation.max() < test.min()

    train_last_target = index[train[-1] + horizon_steps]
    validation_first_history = index[validation[0] - history_steps + 1]
    validation_last_target = index[validation[-1] + horizon_steps]
    test_first_history = index[test[0] - history_steps + 1]

    assert validation_first_history - train_last_target >= pd.Timedelta(minutes=15 * gap_steps)
    assert test_first_history - validation_last_target >= pd.Timedelta(minutes=15 * gap_steps)

