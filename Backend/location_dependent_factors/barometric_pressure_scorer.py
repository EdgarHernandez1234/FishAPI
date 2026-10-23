def pressure_scorer(change_hpa_3h: float) -> int:
    """Return a 0-100 fishing score for barometric pressure trend.

    change_hpa_3h: change in pressure over the last ~3 hours, in hPa.
                   Negative = falling, positive = rising.

    pretty estimated number give this a lower weight??
    tweak change values based on what we get
    """
    c = change_hpa_3h

    if c <= -6:
        score = 45                      # crashing: stormy, still some activity
    elif c < -3:
        score = 45 + (c + 6) / 3 * 55   # ramp 45 -> 100 as the drop eases
    elif c <= 0:
        score = 100                     # stable or slowly falling: best
    elif c <= 1:
        score = 100 - c * 15            # 100 -> 85
    elif c <= 4:
        score = 85 - (c - 1) / 3 * 35   # 85 -> 50 as it rises faster
    else:
        score = max(40, 50 - (c - 4) * 5)

    return round(score)