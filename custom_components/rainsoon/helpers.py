"""Shared helpers."""

from __future__ import annotations

from typing import Any

from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_LOOKAHEAD_HOURS,
    CONF_LANGUAGE,
    CONF_PRESET,
    CONF_PRECIPITATION_THRESHOLD_MM,
    CONF_PROBABILITY_THRESHOLD,
    CONF_PROVIDER,
    CONF_UPDATE_INTERVAL_MINUTES,
    PRESET_RECOMMENDED,
    PROVIDER_OPEN_METEO,
)


def normalize_entry_data(data: dict[str, Any]) -> dict[str, Any]:
    """Coerce config entry fields to correct types."""
    out = dict(data)
    out.setdefault(CONF_PROVIDER, PROVIDER_OPEN_METEO)
    out[CONF_LOOKAHEAD_HOURS] = int(float(out[CONF_LOOKAHEAD_HOURS]))
    out[CONF_PROBABILITY_THRESHOLD] = float(out[CONF_PROBABILITY_THRESHOLD])
    out[CONF_PRECIPITATION_THRESHOLD_MM] = float(out[CONF_PRECIPITATION_THRESHOLD_MM])
    out[CONF_UPDATE_INTERVAL_MINUTES] = int(float(out[CONF_UPDATE_INTERVAL_MINUTES]))
    out[CONF_LATITUDE] = float(out[CONF_LATITUDE])
    out[CONF_LONGITUDE] = float(out[CONF_LONGITUDE])
    out.setdefault(CONF_PRESET, PRESET_RECOMMENDED)
    from .i18n import normalize_language

    out[CONF_LANGUAGE] = normalize_language(out.get(CONF_LANGUAGE))
    return out
