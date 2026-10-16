
def score_sky(cloud_cover_pct: float) -> int:
    #returns score for cloud cover percentage (how clear the sky is)
    if not 0<= cloud_cover_pct <= 100:
        raise ValueError("Cloud cover must be between 0 and 100")

    if cloud_cover_pct < 20:
        #clear
        return round(55 + (cloud_cover_pct / 20) * 15)
    if cloud_cover_pct < 60:
        # partly cloudy: ramp 70 -> 90
        return round(70 + ((cloud_cover_pct - 20) / 40) * 20)
    # mostly cloudy to overcast: ramp 90 -> 100
    # best conditions for freshwater fishing
    return round(90 + ((cloud_cover_pct - 60) / 40) * 10)