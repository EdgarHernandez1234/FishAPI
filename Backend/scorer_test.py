import pytest
from wind_scorer import score_wind
from sky_scorer import score_sky

def test_ideal_wind_scores_100():
    assert score_wind(8) == 100

def test_strong_wind_scores_low():
    assert score_wind(40) == 0

def test_wind_returns_int():
    assert isinstance(score_wind(15), int)

def test_negative_wind_raises():
    with pytest.raises(ValueError):
        score_wind(-1)

def test_overcast_beats_clear():
    assert score_sky(100) > score_sky(0)

def test_sky_out_of_range_raises():
    with pytest.raises(ValueError):
        score_sky(150)