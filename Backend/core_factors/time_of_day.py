from datetime import datetime, timedelta,date
from zoneinfo import ZoneInfo

from astral import Observer
from astral.sun import sun
from astral import moon



def score_time_of_day(local_time: datetime, sunrise: datetime, sunset: datetime) -> int:
    """Return a 0-100 fishing score based on time of day.

    All three datetimes must be timezone-aware and in the same timezone.
    """
    if sunrise <= local_time <= sunrise + timedelta(hours=2):
        return 100          # morning 
    if sunset - timedelta(hours=3) <= local_time <= sunset:
        return 95           # evening
    return 50 #not a good time


def get_sun_times(latitude: float, longitude: float,
                  tz_name: str = "America/Los_Angeles",
                  now: datetime | None = None):
    """Return (local_time, sunrise, sunset) for a location."""
    tz = ZoneInfo(tz_name)
    local_time = now.astimezone(tz) if now else datetime.now(tz)

    observer = Observer(latitude=latitude, longitude=longitude)
    times = sun(observer, date=local_time.date(), tzinfo=tz)
    return local_time, times["sunrise"], times["sunset"]

phase = moon.phase(date.today())   # 0 to 27.99: 0 = new moon, ~7 = first quarter, ~14 = full, ~21 = last quarter

def score_moon(phase_day: float) -> int:
    """100 at new/full moon, 60 at the quarters."""
    distance = min(phase_day % 14, 14 - phase_day % 14)   # days from nearest new/full moon, 0 to 7
    return round(100 - distance / 7 * 40)