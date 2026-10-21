from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from astral import Observer
from astral.sun import sun
from timezonefinder import TimezoneFinder

_finder = TimezoneFinder()   # create once, it's slow to build


def score_time_of_day(local_time: datetime, sunrise: datetime, sunset: datetime) -> int:
    """Return a 0-100 fishing score based on time of day.

    All three datetimes must be timezone-aware and in the same timezone.
    """
    if sunrise <= local_time <= sunrise + timedelta(hours=2):
        return 100          # morning 
    if sunset - timedelta(hours=3) <= local_time <= sunset:
        return 95           # evening
    return 50 #not a good time


def get_sun_times(
    latitude: float,
    longitude: float,
    now: datetime | None = None,
):
    """Return local time, sunrise, and sunset for a location."""

    tz_name = _finder.timezone_at(
        lat=latitude,
        lng=longitude,
    )

    if tz_name is None:
        raise ValueError(
            "Could not determine timezone for this location"
        )

    tz = ZoneInfo(tz_name)

    if now is not None:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        local_time = now.astimezone(tz)
    else:
        local_time = datetime.now(tz)

    observer = Observer(
        latitude=latitude,
        longitude=longitude,
    )

    times = sun(
        observer,
        date=local_time.date(),
        tzinfo=tz,
    )

    return local_time, times["sunrise"], times["sunset"]