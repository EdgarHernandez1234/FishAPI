def score_water_temp(
    water_temp_c: float,
    ideal_temp_c: float = 18.0,
    tolerance_c: float = 10.0,
) -> int:
    """Score water temperature from 0 to 100."""
    if tolerance_c <= 0:
        raise ValueError("Tolerance must be positive")

    difference = abs(water_temp_c - ideal_temp_c)

    if difference >= tolerance_c:
        return 0

    return round(100 * (1 - difference / tolerance_c))