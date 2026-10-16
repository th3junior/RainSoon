"""Constants for the RainSoon integration."""

from __future__ import annotations

import json
from pathlib import Path

DOMAIN = "rainsoon"

_MANIFEST = json.loads(
    (Path(__file__).resolve().parent / "manifest.json").read_text(encoding="utf-8")
)
INTEGRATION_VERSION: str = _MANIFEST["version"]

CONF_PROVIDER = "provider"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_USE_HOME = "use_home"
CONF_PRESET = "preset"
CONF_LANGUAGE = "language"
CONF_LOOKAHEAD_HOURS = "lookahead_hours"
CONF_PROBABILITY_THRESHOLD = "probability_threshold"
CONF_PRECIPITATION_THRESHOLD_MM = "precipitation_threshold_mm"
CONF_UPDATE_INTERVAL_MINUTES = "update_interval_minutes"

PROVIDER_OPEN_METEO = "open_meteo"

PRESET_RECOMMENDED = "recommended"
PRESET_HEAVY = "heavy"
PRESET_SENSITIVE = "sensitive"
PRESET_CUSTOM = "custom"

PRESET_CHOICES = [
    PRESET_RECOMMENDED,
    PRESET_HEAVY,
    PRESET_SENSITIVE,
    PRESET_CUSTOM,
]

DEFAULT_LOOKAHEAD_HOURS = 12
MAX_LOOKAHEAD_HOURS = 48
MIN_FETCH_FORECAST_HOURS = 48
DEFAULT_PROBABILITY_THRESHOLD = 50
DEFAULT_PRECIPITATION_THRESHOLD_MM = 0.1
DEFAULT_UPDATE_INTERVAL_MINUTES = 15
MIN_UPDATE_INTERVAL_MINUTES = 5
MAX_UPDATE_INTERVAL_MINUTES = 60

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

ATTR_FORECAST_TIME = "forecast_time"
ATTR_HOURS = "hours"
ATTR_MINUTES = "minutes"
ATTR_PRECIPITATION_MM = "precipitation_mm"
ATTR_WEATHER_CODE = "weather_code"
ATTR_DATA_SOURCE = "data_source"
ATTR_MESSAGE = "message"
ATTR_MESSAGE_SHORT = "message_short"
ATTR_RAIN_EXPECTED = "rain_expected"
ATTR_FORECAST_STEP_HOURS = "forecast_step_hours"
ATTR_LOOKAHEAD_HOURS = "lookahead_hours"
ATTR_PROBABILITY_THRESHOLD = "probability_threshold"
ATTR_PRECIPITATION_THRESHOLD_MM = "precipitation_threshold_mm"
ATTR_CONDITION = "condition"
ATTR_CURRENT = "current"
ATTR_HOURLY_FORECAST = "hourly_forecast"
ATTR_MAX_PRECIPITATION_IN_WINDOW_MM = "max_precipitation_in_window_mm"
ATTR_TOTAL_PRECIPITATION_IN_WINDOW_MM = "total_precipitation_in_window_mm"
ATTR_MAX_WIND_IN_WINDOW_KMH = "max_wind_in_window_kmh"
ATTR_ELEVATION_M = "elevation_m"
ATTR_TIMEZONE = "timezone"
ATTR_ALERT_LEVEL = "alert_level"
ATTR_PRESET = "preset"
ATTR_HOURS_UNTIL_RAIN = "hours_until_rain"
