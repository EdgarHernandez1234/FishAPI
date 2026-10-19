def score_season(month: int) -> int:
    """
    Score the season for freshwater fishing in California.
    Month must be 1-12.
    """
    if not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12")

    # Spring: warming water and increased fish activity
    if month in (3, 4, 5):
        return 100

    # Fall: cooling water and increased feeding activity
    if month in (9, 10, 11):
        return 90

    # Winter: activity may be lower
    if month in (12, 1, 2):
        return 60

    # Summer: warm water can reduce activity,
    # especially during hot afternoons
    return 70