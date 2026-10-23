import pytest
from Backend.core_factors.wind_scorer import score_wind
from Backend.core_factors.sky_scorer import score_sky
from Backend.core_factors.time_of_day import score_time
from Backend.core_factors.season import score_season


# --------------------
# WIND TESTS
# --------------------

def test_ideal_wind_scores_100():
    assert score_wind(8) == 100

def test_strong_wind_scores_low():
    assert score_wind(40) == 0

def test_wind_returns_int():
    assert isinstance(score_wind(15), int)

def test_negative_wind_raises():
    with pytest.raises(ValueError):
        score_wind(-1)

@pytest.mark.parametrize("speed", [0, 5, 12, 25, 30])
def test_wind_boundary_values(speed):
    assert 0 <= score_wind(speed) <= 100


# --------------------
# SKY TESTS
# --------------------

def test_overcast_beats_clear():
    assert score_sky(100) > score_sky(0)

def test_sky_returns_int():
    assert isinstance(score_sky(50), int)

def test_sky_out_of_range_raises():
    with pytest.raises(ValueError):
        score_sky(150)

@pytest.mark.parametrize("cloud_cover", [0, 20, 60, 100])
def test_sky_boundary_values(cloud_cover):
    assert 0 <= score_sky(cloud_cover) <= 100


# --------------------
# TIME TESTS
# --------------------

def test_early_morning_scores_100():
    assert score_time(6) == 100

def test_evening_scores_high():
    assert score_time(18) == 90

def test_midday_scores_lower():
    assert score_time(12) == 50

def test_time_returns_int():
    assert isinstance(score_time(10), int)

def test_invalid_time_raises():
    with pytest.raises(ValueError):
        score_time(24)

@pytest.mark.parametrize("hour", [0, 5, 8, 12, 17, 20, 23])
def test_time_boundary_values(hour):
    assert 0 <= score_time(hour) <= 100


# --------------------
# SEASON TESTS
# --------------------

def test_spring_scores_100():
    assert score_season(4) == 100

def test_fall_scores_90():
    assert score_season(10) == 90

def test_winter_scores_60():
    assert score_season(1) == 60

def test_summer_scores_70():
    assert score_season(7) == 70

def test_season_returns_int():
    assert isinstance(score_season(6), int)

def test_invalid_month_raises():
    with pytest.raises(ValueError):
        score_season(13)

@pytest.mark.parametrize("month", range(1, 13))
def test_all_months_return_valid_scores(month):
    score = score_season(month)
    assert isinstance(score, int)
    assert 0 <= score <= 100