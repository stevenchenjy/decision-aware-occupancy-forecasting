from src.energy_opportunity import interval_kwh, safe_shiftable_load_opportunity


def test_interval_kwh_clips_negative_power():
    assert interval_kwh([4.0, -2.0, 0.0], interval_hours=0.25).tolist() == [1.0, 0.0, 0.0]


def test_safe_shiftable_load_excludes_conflict_intervals():
    result = safe_shiftable_load_opportunity(
        y_empty=[1, 0, 1, 0],
        recommend_empty=[1, 1, 0, 0],
        controllable_kwh=[2.0, 3.0, 5.0, 7.0],
    )

    assert result["gross_shiftable_load_kwh"] == 5.0
    assert result["safe_shiftable_load_kwh"] == 2.0
    assert result["conflict_kwh"] == 3.0
    assert result["safe_intervals"] == 1
    assert result["conflict_intervals"] == 1


def test_safe_and_conflict_energy_partition_gross_recommended_energy():
    result = safe_shiftable_load_opportunity(
        y_empty=[1, 1, 0, 0],
        recommend_empty=[1, 0, 1, 1],
        controllable_kwh=[1.5, 2.0, 3.0, 4.0],
    )

    assert result["gross_shiftable_load_kwh"] == result["safe_shiftable_load_kwh"] + result["conflict_kwh"]
    assert result["gross_shiftable_load_kwh"] == 8.5
    assert result["safe_shiftable_load_kwh"] == 1.5
    assert result["conflict_kwh"] == 7.0
