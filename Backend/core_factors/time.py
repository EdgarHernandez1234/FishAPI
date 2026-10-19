def score_time(hour: int) -> int:
    """
    Score time of day for freshwater fishing.
    Hour must be 0-23, using local time.
    """
    if not 0 <= hour <= 23:
        raise ValueError("Hour must be between 0 and 23")

    # Best: early morning (5 AM - 8 AM)
    if 5 <= hour <= 8:
        return 100

    # Good: evening (5 PM - 8 PM)
    if 17 <= hour <= 20:
        return 90

    # Fair: morning and late afternoon
    if 9 <= hour <= 11 or 14 <= hour <= 16:
        return 70

    # Lower: midday
    if 12 <= hour <= 13:
        return 50

    # Lower: nighttime and very early morning
    return 40