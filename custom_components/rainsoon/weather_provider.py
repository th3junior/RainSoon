"""Weather provider (Open-Meteo)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import aiohttp


@dataclass
class CurrentConditions:
    """Open-Meteo current block."""

    temperature: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    cloud_cover: float | None = None
    precipitation: float | None = None
    weather_code: int | None = None


@dataclass
class HourlyForecastSlot:
    """Normalized hourly forecast slot."""

    time: datetime
    precipitation_probability: float | None
    precipitation_mm: float | None
    weather_code: int | None
    temperature: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    cloud_cover: float | None = None
    showers_mm: float | None = None
    snowfall_cm: float | None = None


@dataclass
class NormalizedForecast:
    """Provider-agnostic forecast."""

    slots: list[HourlyForecastSlot]
    source: str
    current: CurrentConditions = field(default_factory=CurrentConditions)
    elevation_m: float | None = None
    timezone: str | None = None


class WeatherProvider(ABC):
    """Base weather provider."""

    @abstractmethod
    async def fetch(
        self,
        session: aiohttp.ClientSession,
        latitude: float,
        longitude: float,
        lookahead_hours: int,
    ) -> NormalizedForecast:
        """Fetch and normalize forecast."""


def get_provider() -> WeatherProvider:
    """Return Open-Meteo provider."""
    from .open_meteo import OpenMeteoProvider

    return OpenMeteoProvider()
