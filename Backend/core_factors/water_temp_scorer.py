# species: (ideal low °C, ideal high °C, too-cold limit °C, too-hot limit °C)
# PLACEHOLDER values, not researched: check them before relying on them.
SPECIES_RANGES = {
    "bluegill": (21, 29, 10, 35),
}
DEFAULT_SPECIES = "bluegill"


def score_water_temp(temp_c: float, species: str = DEFAULT_SPECIES) -> int:
    """Return a 0-100 score: 100 inside the ideal range, fading to 0 at the limits."""
    low, high, cold, hot = SPECIES_RANGES[species]

    if low <= temp_c <= high:
        return 100
    if temp_c < low:
        return max(0, round(100 * (temp_c - cold) / (low - cold)))
    return max(0, round(100 * (hot - temp_c) / (hot - high)))