# (chance of precipitation %, score) anchor points; scores are linearly
# interpolated between them, so there are no sudden cliffs.
_POINTS = [(0, 100), (20, 90), (50, 70), (80, 35), (100, 15)]


def score_precipitation(chance_pct: float) -> int:
    """Return a 0-100 fishing score for chance of precipitation (0-100%)."""
    if chance_pct is None or not 0 <= chance_pct <= 100:
        raise ValueError("Chance of precipitation must be between 0 and 100")

    for (x0, y0), (x1, y1) in zip(_POINTS, _POINTS[1:]):
        if chance_pct <= x1:
            return round(y0 + (chance_pct - x0) / (x1 - x0) * (y1 - y0))