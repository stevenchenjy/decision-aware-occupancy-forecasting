import pytest

from src.models import make_lightgbm


def test_lightgbm_configuration_disables_row_bagging_explicitly():
    pytest.importorskip("lightgbm")
    model = make_lightgbm()
    params = model.get_params()
    assert params["subsample"] == 1.0
    assert params["subsample_freq"] == 0
    assert params["colsample_bytree"] == 0.85
