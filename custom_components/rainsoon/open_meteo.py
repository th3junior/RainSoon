"""Open-Meteo weather provider."""

from __future__ import annotations

from datetime import datetime

import aiohttp

from .const import MIN_FETCH_FORECAST_HOURS, OPEN_METEO_URL, PROVIDER_OPEN_METEO
from .weather_provider import (
    CurrentConditions,
    HourlyForecastSlot,
    NormalizedForecast,
    WeatherProvider,
)

HOURLY_VARS = (
    "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,"
    "rain,showers,snowfall,weather_code,cloud_cover,wind_speed_10m"
)
CURRENT_VARS = (
    "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,"
    "cloud_cover,wind_speed_10m"
)


def forecast_fetch_hours(lookahead_hours: int) -> int:
    """Hours to request from API (always enough for the configured window)."""
    return min(384, max(lookahead_hours + 12, MIN_FETCH_FORECAST_HOURS))


class OpenMeteoProvider(WeatherProvider):
    """Fetch hourly forecast from Open-Meteo."""

    async def fetch(
        self,
        session: aiohttp.ClientSession,
        latitude: float,
        longitude: float,
        lookahead_hours: int,
    ) -> NormalizedForecast:
        fetch_hours = forecast_fetch_hours(lookahead_hours)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": HOURLY_VARS,
            "current": CURRENT_VARS,
            "forecast_hours": fetch_hours,
            "timezone": "auto",
        }
        async with session.get(OPEN_METEO_URL, params=params, timeout=30) as response:
            response.raise_for_status()
            data = await response.json()

        if data.get("error") is True:
            reason = data.get("reason") or "Open-Meteo request failed"
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=400,
                message=str(reason),
            )

        return normalize_open_meteo(data)


def normalize_open_meteo(data: dict) -> NormalizedForecast:
    """Parse Open-Meteo JSON into normalized forecast."""
    hourly = data.get("hourly") or {}
    times: list[str] = hourly.get("time") or []
    probs = hourly.get("precipitation_probability") or []
    precip = hourly.get("precipitation") or []
    rain = hourly.get("rain") or []
    showers = hourly.get("showers") or []
    snowfall = hourly.get("snowfall") or []
    codes = hourly.get("weather_code") or []
    temps = hourly.get("temperature_2m") or []
    humidity = hourly.get("relative_humidity_2m") or []
    wind = hourly.get("wind_speed_10m") or []
    clouds = hourly.get("cloud_cover") or []

    slots: list[HourlyForecastSlot] = []
    for i, time_str in enumerate(times):
        slot_time = datetime.fromisoformat(time_str)
        p_mm = _at(precip, i)
        r_mm = _at(rain, i)
        if p_mm is None and r_mm is not None:
            p_mm = r_mm
        elif p_mm is not None and r_mm is not None:
            p_mm = max(p_mm, r_mm)
        slots.append(
            HourlyForecastSlot(
                time=slot_time,
                precipitation_probability=_at(probs, i),
                precipitation_mm=p_mm,
                weather_code=_at_int(codes, i),
                temperature=_at(temps, i),
                humidity=_at(humidity, i),
                wind_speed=_at(wind, i),
                cloud_cover=_at(clouds, i),
                showers_mm=_at(showers, i),
                snowfall_cm=_at(snowfall, i),
            )
        )

    current_raw = data.get("current") or {}
    current = CurrentConditions(
        temperature=_float_or_none(current_raw.get("temperature_2m")),
        humidity=_float_or_none(current_raw.get("relative_humidity_2m")),
        wind_speed=_float_or_none(current_raw.get("wind_speed_10m")),
        cloud_cover=_float_or_none(current_raw.get("cloud_cover")),
        precipitation=_float_or_none(current_raw.get("precipitation")),
        weather_code=_int_or_none(current_raw.get("weather_code")),
    )

    return NormalizedForecast(
        slots=slots,
        source=PROVIDER_OPEN_METEO,
        current=current,
        elevation_m=_float_or_none(data.get("elevation")),
        timezone=data.get("timezone"),
    )


def _float_or_none(val) -> float | None:
    if val is None:
        return None
    return float(val)


def _int_or_none(val) -> int | None:
    if val is None:
        return None
    return int(val)


def _at(values: list, index: int) -> float | None:
    if index >= len(values):
        return None
    val = values[index]
    if val is None:
        return None
    return float(val)


def _at_int(values: list, index: int) -> int | None:
    if index >= len(values):
        return None
    val = values[index]
    if val is None:
        return None
    return int(val)
