def score_wind(speed_mph: float) -> int:
    """Return a 0-100 fishing score for wind speed in ___."""
    if speed_mph < 0:
        raise ValueError("Wind speed cannot be negative")

    if speed_mph < 5:
        score = 65 + (speed_mph/5) *35
    elif speed_mph <= 12:
        # ideal conditions 
        score = 100
    elif speed_mph <= 25:
        score = 100 - ((speed_mph - 12) / 13) * 80
    else:
        score = max(0,20 - ((speed_mph -25) / 5)*20)

    return round(score)