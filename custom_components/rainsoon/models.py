"""Data models for RainSoon coordinator."""

from __future__ import annotations

from dataclasses import dataclass, field

from .rain_logic import RainOutlook
from .weather_provider import CurrentConditions


@dataclass
class RainAlertData:
    """Full coordinator payload."""

    outlook: RainOutlook
    current: CurrentConditions
    max_precipitation_in_window_mm: float | None
    total_precipitation_in_window_mm: float | None
    max_wind_in_window_kmh: float | None
    hourly_forecast: list[dict] = field(default_factory=list)
    elevation_m: float | None = None
    timezone: str | None = None
    alert_level: str = "none"
    hours_until_rain: float | None = None
    raining_now: bool = False
