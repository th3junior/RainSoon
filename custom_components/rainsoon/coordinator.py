"""Data update coordinator for RainSoon."""

from __future__ import annotations

from datetime import timedelta
import logging

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_LANGUAGE,
    CONF_LOOKAHEAD_HOURS,
    CONF_PRECIPITATION_THRESHOLD_MM,
    CONF_PROBABILITY_THRESHOLD,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)
from .helpers import normalize_entry_data
from .models import RainAlertData
from .payload import build_rain_alert_data
from .weather_provider import get_provider

_LOGGER = logging.getLogger(__name__)


class RainAlertCoordinator(DataUpdateCoordinator[RainAlertData]):
    """Coordinator fetching Open-Meteo forecast and computing rain outlook."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        update_minutes = entry.data.get(
            CONF_UPDATE_INTERVAL_MINUTES, DEFAULT_UPDATE_INTERVAL_MINUTES
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_minutes),
        )
        self._provider = get_provider()

    async def _async_update_data(self) -> RainAlertData:
        session = async_get_clientsession(self.hass)

        try:
            cfg = normalize_entry_data(self.config_entry.data)
        except (TypeError, ValueError, KeyError) as err:
            raise UpdateFailed(f"Invalid configuration: {err}") from err

        try:
            forecast = await self._provider.fetch(
                session,
                cfg[CONF_LATITUDE],
                cfg[CONF_LONGITUDE],
                cfg[CONF_LOOKAHEAD_HOURS],
            )
        except ClientError as err:
            raise UpdateFailed(f"Network error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

        return build_rain_alert_data(
            forecast,
            now=dt_util.now(),
            lookahead_hours=cfg[CONF_LOOKAHEAD_HOURS],
            probability_threshold=cfg[CONF_PROBABILITY_THRESHOLD],
            precipitation_threshold_mm=cfg[CONF_PRECIPITATION_THRESHOLD_MM],
            language=cfg[CONF_LANGUAGE],
        )
