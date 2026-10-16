"""Configuration presets for easy setup."""

from __future__ import annotations

from .const import (
    CONF_LOOKAHEAD_HOURS,
    CONF_PRECIPITATION_THRESHOLD_MM,
    CONF_PROBABILITY_THRESHOLD,
    CONF_PRESET,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_LOOKAHEAD_HOURS,
    DEFAULT_PRECIPITATION_THRESHOLD_MM,
    DEFAULT_PROBABILITY_THRESHOLD,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    PRESET_CUSTOM,
    PRESET_HEAVY,
    PRESET_RECOMMENDED,
    PRESET_SENSITIVE,
)

_PRESET_VALUES: dict[str, dict[str, int | float]] = {
    PRESET_RECOMMENDED: {
        CONF_LOOKAHEAD_HOURS: 12,
        CONF_PROBABILITY_THRESHOLD: 50,
        CONF_PRECIPITATION_THRESHOLD_MM: 0.1,
        CONF_UPDATE_INTERVAL_MINUTES: 15,
    },
    PRESET_HEAVY: {
        CONF_LOOKAHEAD_HOURS: 12,
        CONF_PROBABILITY_THRESHOLD: 70,
        CONF_PRECIPITATION_THRESHOLD_MM: 0.5,
        CONF_UPDATE_INTERVAL_MINUTES: 15,
    },
    PRESET_SENSITIVE: {
        CONF_LOOKAHEAD_HOURS: 24,
        CONF_PROBABILITY_THRESHOLD: 40,
        CONF_PRECIPITATION_THRESHOLD_MM: 0.05,
        CONF_UPDATE_INTERVAL_MINUTES: 10,
    },
}


def apply_preset(preset: str) -> dict[str, int | float | str]:
    """Return threshold fields for a named preset."""
    if preset == PRESET_CUSTOM:
        return {
            CONF_LOOKAHEAD_HOURS: DEFAULT_LOOKAHEAD_HOURS,
            CONF_PROBABILITY_THRESHOLD: DEFAULT_PROBABILITY_THRESHOLD,
            CONF_PRECIPITATION_THRESHOLD_MM: DEFAULT_PRECIPITATION_THRESHOLD_MM,
            CONF_UPDATE_INTERVAL_MINUTES: DEFAULT_UPDATE_INTERVAL_MINUTES,
            CONF_PRESET: PRESET_CUSTOM,
        }
    values = _PRESET_VALUES.get(preset, _PRESET_VALUES[PRESET_RECOMMENDED])
    return {**values, CONF_PRESET: preset}


def preset_summary(preset: str, lang: str | None = None) -> str:
    """One-line summary for UI / attributes."""
    from .i18n import preset_custom_label

    v = apply_preset(preset)
    if preset == PRESET_CUSTOM:
        return preset_custom_label(lang or "en")
    return (
        f"{v[CONF_LOOKAHEAD_HOURS]} h · ≥{int(v[CONF_PROBABILITY_THRESHOLD])}% · "
        f"≥{v[CONF_PRECIPITATION_THRESHOLD_MM]} mm/h"
    )
