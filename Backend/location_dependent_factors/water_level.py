def score_water_level(
    level: float,
    ideal_level: float,
    tolerance: float,
) -> int:
    """Score water level relative to a preferred level."""
    if tolerance <= 0:
        raise ValueError("Tolerance must be positive")

    difference = abs(level - ideal_level)

    if difference >= tolerance:
        return 0

    return round(100 * (1 - difference / tolerance))