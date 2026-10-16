"""Build full RainSoon coordinator payload."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import RainAlertData
from .rain_logic import compute_rain_outlook
from .weather_codes import weather_code_description
from .weather_provider import HourlyForecastSlot, NormalizedForecast


def _slot_time_aware(slot: HourlyForecastSlot, now: datetime) -> datetime:
    t = slot.time
    if t.tzinfo is None:
        return t.replace(tzinfo=now.tzinfo or timezone.utc)
    return t


def build_rain_alert_data(
    forecast: NormalizedForecast,
    *,
    now: datetime,
    lookahead_hours: int,
    probability_threshold: float,
    precipitation_threshold_mm: float,
    language: str,
) -> RainAlertData:
    outlook = compute_rain_outlook(
        forecast,
        now=now,
        lookahead_hours=lookahead_hours,
        probability_threshold=probability_threshold,
        precipitation_threshold_mm=precipitation_threshold_mm,
        language=language,
    )

    window_end = now + timedelta(hours=lookahead_hours)
    precip_values: list[float] = []
    wind_values: list[float] = []
    hourly_rows: list[dict] = []

    for slot in forecast.slots:
        slot_time = _slot_time_aware(slot, now)
        in_window = now <= slot_time <= window_end
        if not in_window:
            continue
        p_mm = slot.precipitation_mm or 0.0
        precip_values.append(p_mm)
        if slot.wind_speed is not None:
            wind_values.append(slot.wind_speed)
        hourly_rows.append(
            {
                "time": slot_time.isoformat(),
                "probability": slot.precipitation_probability,
                "precipitation_mm": slot.precipitation_mm,
                "temperature": slot.temperature,
                "humidity": slot.humidity,
                "wind_speed": slot.wind_speed,
                "cloud_cover": slot.cloud_cover,
                "weather_code": slot.weather_code,
                "condition": weather_code_description(slot.weather_code, language),
            }
        )

    alert_level = "none"
    hours_until: float | None = None
    if outlook.rain_expected and outlook.minutes_until is not None:
        hours_until = round(outlook.minutes_until / 60, 1)
        if outlook.minutes_until <= 60:
            alert_level = "alert"
        elif outlook.minutes_until <= 180:
            alert_level = "watch"
        else:
            alert_level = "info"

    cur = forecast.current
    raining_now = bool(
        (cur.precipitation is not None and cur.precipitation > 0)
        or (cur.weather_code is not None and cur.weather_code >= 51)
    )

    return RainAlertData(
        outlook=outlook,
        current=cur,
        max_precipitation_in_window_mm=max(precip_values) if precip_values else None,
        total_precipitation_in_window_mm=sum(precip_values) if precip_values else None,
        max_wind_in_window_kmh=max(wind_values) if wind_values else None,
        hourly_forecast=hourly_rows,
        elevation_m=forecast.elevation_m,
        timezone=forecast.timezone,
        alert_level=alert_level,
        hours_until_rain=hours_until,
        raining_now=raining_now,
    )
