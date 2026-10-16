"""Config flow for RainSoon (Open-Meteo only)."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    LocationSelector,
    LocationSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_LANGUAGE,
    CONF_LOOKAHEAD_HOURS,
    CONF_PRESET,
    CONF_PRECIPITATION_THRESHOLD_MM,
    CONF_PROBABILITY_THRESHOLD,
    CONF_PROVIDER,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_USE_HOME,
    DEFAULT_LOOKAHEAD_HOURS,
    DEFAULT_PRECIPITATION_THRESHOLD_MM,
    DEFAULT_PROBABILITY_THRESHOLD,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_LOOKAHEAD_HOURS,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_UPDATE_INTERVAL_MINUTES,
    PRESET_CHOICES,
    PRESET_CUSTOM,
    PRESET_RECOMMENDED,
    PROVIDER_OPEN_METEO,
)
from .helpers import normalize_entry_data
from .i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    language_display_labels,
    normalize_language,
    preset_option_labels,
)
from .presets import apply_preset

_LOGGER = logging.getLogger(__name__)


class RainAlertConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RainSoon."""

    VERSION = 3

    def __init__(self) -> None:
        self._data: dict[str, Any] = {CONF_PROVIDER: PROVIDER_OPEN_METEO}

    @staticmethod
    @callback
    def async_migrate_entry(hass, entry: ConfigEntry) -> bool:
        """Migrate older entries to v3 (Open-Meteo only)."""
        if entry.version >= 3:
            data = dict(entry.data)
            if CONF_PRESET not in data or CONF_LANGUAGE not in data:
                data.setdefault(CONF_PRESET, PRESET_RECOMMENDED)
                data.setdefault(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                hass.config_entries.async_update_entry(entry, data=data)
            return True
        data = {
            k: v
            for k, v in entry.data.items()
            if k not in ("api_key",)
        }
        data[CONF_PROVIDER] = PROVIDER_OPEN_METEO
        data.setdefault(CONF_PRESET, PRESET_RECOMMENDED)
        data.setdefault(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        hass.config_entries.async_update_entry(entry, data=data, version=3)
        return True

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Start setup — use HA home or map."""
        return await self.async_step_location(user_input)

    async def _async_create_entry_from_data(self) -> FlowResult:
        errors: dict[str, str] = {}
        try:
            data = normalize_entry_data(self._data)
        except (TypeError, ValueError, KeyError):
            errors["base"] = "invalid_config"
            return await self.async_step_thresholds(errors=errors)

        await self.async_set_unique_id(
            f"{data[CONF_LATITUDE]:.4f}_{data[CONF_LONGITUDE]:.4f}"
        )
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="RainSoon", data=data)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Reconfigure thresholds (same as options, via integration menu)."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        current = dict(entry.data)

        if user_input is not None:
            try:
                new_data = _merge_user_thresholds(current, user_input)
            except (TypeError, ValueError, KeyError):
                errors["base"] = "invalid_config"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=new_data,
                    reason="reconfigure_successful",
                )

        try:
            schema = vol.Schema(_options_schema(current))
        except (TypeError, ValueError, vol.Error) as err:
            _LOGGER.exception("Reconfigure schema error: %s", err)
            errors["base"] = "invalid_config"
            schema = vol.Schema(_thresholds_schema())

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure location."""
        errors: dict[str, str] = {}
        if user_input is not None:
            mode = user_input.get("location_mode", "home")
            if mode != "map":
                lat = self.hass.config.latitude
                lon = self.hass.config.longitude
                if lat is None or lon is None:
                    errors["base"] = "home_location_not_set"
                else:
                    self._data[CONF_USE_HOME] = True
                    self._data[CONF_LATITUDE] = float(lat)
                    self._data[CONF_LONGITUDE] = float(lon)
                    return await self.async_step_language()
            else:
                location = user_input.get("location")
                if not location:
                    errors["base"] = "location_required"
                else:
                    self._data[CONF_USE_HOME] = False
                    self._data[CONF_LATITUDE] = location[CONF_LATITUDE]
                    self._data[CONF_LONGITUDE] = location[CONF_LONGITUDE]
                    return await self.async_step_language()

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(
                {
                    vol.Optional("location_mode", default="home"): SelectSelector(
                        SelectSelectorConfig(
                            options=["home", "map"],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional("location"): LocationSelector(
                        LocationSelectorConfig()
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_language(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose language for messages and condition text."""
        if user_input is not None:
            self._data[CONF_LANGUAGE] = user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
            return await self.async_step_preset()

        return self.async_show_form(
            step_id="language",
            data_schema=vol.Schema(_language_schema()),
        )

    async def async_step_preset(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose an alert profile (most users stop here)."""
        if user_input is not None:
            preset = user_input.get(CONF_PRESET, PRESET_RECOMMENDED)
            self._data[CONF_PRESET] = preset
            if preset != PRESET_CUSTOM:
                self._data.update(apply_preset(preset))
                return await self._async_create_entry_from_data()
            self._data.update(apply_preset(PRESET_CUSTOM))
            return await self.async_step_thresholds()

        lang = normalize_language(self._data.get(CONF_LANGUAGE))
        return self.async_show_form(
            step_id="preset",
            data_schema=vol.Schema(_preset_schema(lang)),
        )

    async def async_step_thresholds(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, str] | None = None,
    ) -> FlowResult:
        """Advanced thresholds for custom profile."""
        errors = errors or {}
        if user_input is not None:
            self._data.update(
                {
                    CONF_PRESET: PRESET_CUSTOM,
                    CONF_LOOKAHEAD_HOURS: user_input[CONF_LOOKAHEAD_HOURS],
                    CONF_PROBABILITY_THRESHOLD: user_input[CONF_PROBABILITY_THRESHOLD],
                    CONF_PRECIPITATION_THRESHOLD_MM: user_input[
                        CONF_PRECIPITATION_THRESHOLD_MM
                    ],
                    CONF_UPDATE_INTERVAL_MINUTES: user_input[
                        CONF_UPDATE_INTERVAL_MINUTES
                    ],
                }
            )
            return await self._async_create_entry_from_data()

        defaults = _schema_defaults(self._data)
        return self.async_show_form(
            step_id="thresholds",
            data_schema=vol.Schema(_thresholds_schema(defaults)),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return RainAlertOptionsFlow()


def _safe_preset(value: Any) -> str:
    if value in PRESET_CHOICES:
        return str(value)
    return PRESET_RECOMMENDED


def _language_select_options() -> list[SelectOptionDict]:
    labels = language_display_labels()
    return [
        SelectOptionDict(value=code, label=labels[code])
        for code in SUPPORTED_LANGUAGES
    ]


def _language_schema(default: str | None = None) -> dict:
    return {
        vol.Optional(CONF_LANGUAGE, default=default or DEFAULT_LANGUAGE): SelectSelector(
            SelectSelectorConfig(
                options=_language_select_options(),
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }


def _language_schema_with_default(current: dict[str, Any]) -> dict:
    return {
        vol.Optional(
            CONF_LANGUAGE,
            default=normalize_language(current.get(CONF_LANGUAGE)),
        ): SelectSelector(
            SelectSelectorConfig(
                options=_language_select_options(),
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }


def _preset_select_options(lang: str) -> list[SelectOptionDict]:
    labels = preset_option_labels(lang)
    return [
        SelectOptionDict(value=key, label=labels[key])
        for key in PRESET_CHOICES
    ]


def _preset_schema(lang: str) -> dict:
    return {
        vol.Optional(CONF_PRESET, default=PRESET_RECOMMENDED): SelectSelector(
            SelectSelectorConfig(
                options=_preset_select_options(lang),
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }


def _merge_user_thresholds(
    current: dict[str, Any], user_input: dict[str, Any]
) -> dict[str, Any]:
    preset = user_input.get(CONF_PRESET, current.get(CONF_PRESET, PRESET_RECOMMENDED))
    if preset != PRESET_CUSTOM:
        merged = {
            **current,
            **apply_preset(preset),
            CONF_PROVIDER: PROVIDER_OPEN_METEO,
        }
    else:
        merged = {
            **current,
            CONF_PROVIDER: PROVIDER_OPEN_METEO,
            CONF_PRESET: PRESET_CUSTOM,
            CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, current.get(CONF_LANGUAGE)),
            CONF_LOOKAHEAD_HOURS: user_input[CONF_LOOKAHEAD_HOURS],
            CONF_PROBABILITY_THRESHOLD: user_input[CONF_PROBABILITY_THRESHOLD],
            CONF_PRECIPITATION_THRESHOLD_MM: user_input[
                CONF_PRECIPITATION_THRESHOLD_MM
            ],
            CONF_UPDATE_INTERVAL_MINUTES: user_input[CONF_UPDATE_INTERVAL_MINUTES],
        }
    merged = {
        **merged,
        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, current.get(CONF_LANGUAGE)),
    }
    return normalize_entry_data(merged)


def _options_schema(current: dict[str, Any]) -> dict:
    lang = normalize_language(current.get(CONF_LANGUAGE))
    return {
        **_language_schema_with_default(current),
        **_preset_schema_with_default(current, lang),
        **_thresholds_schema(current),
    }


def _preset_schema_with_default(current: dict[str, Any], lang: str) -> dict:
    return {
        vol.Optional(
            CONF_PRESET,
            default=_safe_preset(current.get(CONF_PRESET, PRESET_RECOMMENDED)),
        ): SelectSelector(
            SelectSelectorConfig(
                options=_preset_select_options(lang),
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }


def _schema_defaults(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Safe defaults for selector forms (clamped types)."""
    if not raw:
        return {}
    try:
        normalized = normalize_entry_data(raw)
    except (TypeError, ValueError, KeyError):
        return {}
    return {
        CONF_LOOKAHEAD_HOURS: int(normalized[CONF_LOOKAHEAD_HOURS]),
        CONF_PROBABILITY_THRESHOLD: int(
            round(normalized[CONF_PROBABILITY_THRESHOLD])
        ),
        CONF_PRECIPITATION_THRESHOLD_MM: float(
            normalized[CONF_PRECIPITATION_THRESHOLD_MM]
        ),
        CONF_UPDATE_INTERVAL_MINUTES: int(
            normalized[CONF_UPDATE_INTERVAL_MINUTES]
        ),
    }


def _thresholds_schema(defaults: dict[str, Any] | None = None) -> dict:
    """Threshold fields compatible with HA UI selectors."""
    d = _schema_defaults(defaults) if defaults else {}
    return {
        vol.Optional(
            CONF_LOOKAHEAD_HOURS,
            default=d.get(CONF_LOOKAHEAD_HOURS, DEFAULT_LOOKAHEAD_HOURS),
        ): NumberSelector(
            NumberSelectorConfig(
                min=1,
                max=MAX_LOOKAHEAD_HOURS,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(
            CONF_PROBABILITY_THRESHOLD,
            default=d.get(CONF_PROBABILITY_THRESHOLD, DEFAULT_PROBABILITY_THRESHOLD),
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=100,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(
            CONF_PRECIPITATION_THRESHOLD_MM,
            default=d.get(
                CONF_PRECIPITATION_THRESHOLD_MM, DEFAULT_PRECIPITATION_THRESHOLD_MM
            ),
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=50,
                step=0.1,
                mode=NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(
            CONF_UPDATE_INTERVAL_MINUTES,
            default=d.get(
                CONF_UPDATE_INTERVAL_MINUTES, DEFAULT_UPDATE_INTERVAL_MINUTES
            ),
        ): NumberSelector(
            NumberSelectorConfig(
                min=MIN_UPDATE_INTERVAL_MINUTES,
                max=MAX_UPDATE_INTERVAL_MINUTES,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        ),
    }


class RainAlertOptionsFlow(OptionsFlow):
    """Options flow — profile + thresholds."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Update profile or custom thresholds."""
        errors: dict[str, str] = {}
        current = self.config_entry.data

        if user_input is not None:
            try:
                new_data = _merge_user_thresholds(current, user_input)
            except (TypeError, ValueError, KeyError):
                errors["base"] = "invalid_config"
            else:
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})

        try:
            schema = vol.Schema(_options_schema(current))
        except (TypeError, ValueError, vol.Error) as err:
            _LOGGER.exception("Options schema error: %s", err)
            errors["base"] = "invalid_config"
            schema = vol.Schema(_thresholds_schema(current))

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
