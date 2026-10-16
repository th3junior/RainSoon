"""Sensors for RainSoon."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CONDITION,
    ATTR_CURRENT,
    ATTR_DATA_SOURCE,
    ATTR_ELEVATION_M,
    ATTR_FORECAST_STEP_HOURS,
    ATTR_FORECAST_TIME,
    ATTR_HOURLY_FORECAST,
    ATTR_HOURS,
    ATTR_LOOKAHEAD_HOURS,
    ATTR_MAX_PRECIPITATION_IN_WINDOW_MM,
    ATTR_MAX_WIND_IN_WINDOW_KMH,
    ATTR_MESSAGE,
    ATTR_MESSAGE_SHORT,
    ATTR_MINUTES,
    ATTR_PRECIPITATION_MM,
    ATTR_PRECIPITATION_THRESHOLD_MM,
    ATTR_PROBABILITY_THRESHOLD,
    ATTR_TIMEZONE,
    ATTR_TOTAL_PRECIPITATION_IN_WINDOW_MM,
    ATTR_WEATHER_CODE,
    ATTR_ALERT_LEVEL,
    ATTR_HOURS_UNTIL_RAIN,
    ATTR_PRESET,
    CONF_LANGUAGE,
    CONF_LOOKAHEAD_HOURS,
    CONF_PRESET,
    CONF_PRECIPITATION_THRESHOLD_MM,
    CONF_PROBABILITY_THRESHOLD,
    DEFAULT_LOOKAHEAD_HOURS,
    DOMAIN,
    INTEGRATION_VERSION,
)
from .coordinator import RainAlertCoordinator
from .models import RainAlertData
from .rain_logic import RainOutlook
from .i18n import alert_status_label, build_messages, entity_name, normalize_language
from .presets import preset_summary
from .weather_codes import weather_code_description


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RainSoon sensors."""
    coordinator: RainAlertCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RainMinutesSensor(coordinator, entry),
            RainHoursUntilSensor(coordinator, entry),
            RainAlertStatusSensor(coordinator, entry),
            RainProbabilitySensor(coordinator, entry),
            RainMaxProbabilitySensor(coordinator, entry),
            RainNextPrecipSensor(coordinator, entry),
            RainConditionSensor(coordinator, entry),
            RainCurrentConditionSensor(coordinator, entry),
            RainTemperatureSensor(coordinator, entry),
            RainHumiditySensor(coordinator, entry),
            RainWindSensor(coordinator, entry),
            RainCloudCoverSensor(coordinator, entry),
            RainCurrentPrecipSensor(coordinator, entry),
            RainWindowPrecipTotalSensor(coordinator, entry),
            RainWindowPrecipMaxSensor(coordinator, entry),
            RainWindowWindMaxSensor(coordinator, entry),
        ]
    )


class RainAlertSensor(CoordinatorEntity[RainAlertCoordinator], SensorEntity):
    """Base RainSoon sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-pouring"
    _name_key: str = ""

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._apply_entity_name()

    def _apply_entity_name(self) -> None:
        key = self._name_key or getattr(type(self), "_name_key", "")
        if key:
            self._attr_translation_key = None
            self._attr_name = entity_name(key, self._language())

    @property
    def payload(self) -> RainAlertData | None:
        return self.coordinator.data

    @property
    def outlook(self) -> RainOutlook | None:
        if not self.payload:
            return None
        return self.payload.outlook

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "RainSoon",
            "manufacturer": "RainSoon",
            "model": "Open-Meteo",
            "sw_version": INTEGRATION_VERSION,
            "configuration_url": "https://github.com/th3junior/RainSoon",
        }

    def _language(self) -> str:
        return normalize_language(self._entry.data.get(CONF_LANGUAGE))

    def _alert_messages(self) -> tuple[str, str]:
        """Voice/text summary; always uses current forecast period from config."""
        if not self.outlook:
            return ("", "")
        data = self._entry.data
        lookahead = int(data.get(CONF_LOOKAHEAD_HOURS) or DEFAULT_LOOKAHEAD_HOURS)
        return build_messages(
            self.outlook.minutes_until,
            self.outlook.next_probability,
            self.outlook.rain_expected,
            self._language(),
            lookahead_hours=lookahead,
            max_probability_in_period=self.outlook.max_probability,
            probability_threshold=data.get(CONF_PROBABILITY_THRESHOLD),
        )

    def _config_attributes(self) -> dict:
        data = self._entry.data
        preset = data.get(CONF_PRESET, "recommended")
        lang = self._language()
        return {
            ATTR_LOOKAHEAD_HOURS: data.get(CONF_LOOKAHEAD_HOURS),
            ATTR_PROBABILITY_THRESHOLD: data.get(CONF_PROBABILITY_THRESHOLD),
            ATTR_PRECIPITATION_THRESHOLD_MM: data.get(CONF_PRECIPITATION_THRESHOLD_MM),
            ATTR_PRESET: preset,
            CONF_LANGUAGE: lang,
            "preset_summary": preset_summary(str(preset), lang),
        }


class RainMinutesSensor(RainAlertSensor):
    """Minutes until expected rain."""

    _name_key = "proxima_chuva"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_proxima_chuva"

    @property
    def native_value(self) -> int | None:
        if not self.outlook or not self.outlook.rain_expected:
            return None
        return self.outlook.minutes_until

    @property
    def extra_state_attributes(self) -> dict:
        if not self.outlook:
            return self._config_attributes()
        ft = self.outlook.forecast_time
        minutes = self.outlook.minutes_until or 0
        condition = weather_code_description(self.outlook.weather_code, self._language())
        message, message_short = self._alert_messages()
        attrs = {
            **self._config_attributes(),
            ATTR_RAIN_EXPECTED: self.outlook.rain_expected,
            ATTR_FORECAST_STEP_HOURS: 1,
            ATTR_FORECAST_TIME: ft.isoformat() if ft else None,
            ATTR_HOURS: minutes // 60,
            ATTR_MINUTES: minutes % 60,
            ATTR_PRECIPITATION_MM: self.outlook.precipitation_mm,
            ATTR_WEATHER_CODE: self.outlook.weather_code,
            ATTR_CONDITION: condition,
            ATTR_DATA_SOURCE: self.outlook.data_source,
            ATTR_MESSAGE: message,
            ATTR_MESSAGE_SHORT: message_short,
        }
        if self.outlook.max_probability is not None:
            attrs["max_probability_in_period"] = self.outlook.max_probability
        if self.payload:
            attrs[ATTR_MAX_PRECIPITATION_IN_WINDOW_MM] = (
                self.payload.max_precipitation_in_window_mm
            )
            attrs[ATTR_TOTAL_PRECIPITATION_IN_WINDOW_MM] = (
                self.payload.total_precipitation_in_window_mm
            )
            attrs[ATTR_MAX_WIND_IN_WINDOW_KMH] = self.payload.max_wind_in_window_kmh
            attrs[ATTR_HOURLY_FORECAST] = self.payload.hourly_forecast
            attrs[ATTR_ELEVATION_M] = self.payload.elevation_m
            attrs[ATTR_TIMEZONE] = self.payload.timezone
            attrs[ATTR_ALERT_LEVEL] = self.payload.alert_level
            attrs[ATTR_HOURS_UNTIL_RAIN] = self.payload.hours_until_rain
            cur = self.payload.current
            attrs[ATTR_CURRENT] = {
                "temperature": cur.temperature,
                "humidity": cur.humidity,
                "wind_speed": cur.wind_speed,
                "cloud_cover": cur.cloud_cover,
                "precipitation": cur.precipitation,
                "weather_code": cur.weather_code,
                "condition": weather_code_description(cur.weather_code, self._language()),
            }
        return attrs


class RainHoursUntilSensor(RainAlertSensor):
    """Hours until expected rain (dashboard-friendly)."""

    _name_key = "horas_ate_chuva"
    _attr_native_unit_of_measurement = "h"
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_horas_ate_chuva"

    @property
    def native_value(self) -> float | None:
        if not self.payload or not self.outlook or not self.outlook.rain_expected:
            return None
        return self.payload.hours_until_rain


class RainAlertStatusSensor(RainAlertSensor):
    """Plain-language alert level for dashboards and Alexa."""

    _name_key = "estado_alerta"
    _attr_icon = "mdi:bullhorn-outline"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_estado_alerta"

    @property
    def native_value(self) -> str | None:
        if not self.payload:
            return None
        return alert_status_label(self.payload.alert_level, self._language())


class RainProbabilitySensor(RainAlertSensor):
    """Probability at the next rain window."""

    _name_key = "proxima_probabilidade"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:water-percent"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_proxima_probabilidade"

    @property
    def native_value(self) -> float | None:
        if not self.outlook or not self.outlook.rain_expected:
            return None
        return self.outlook.next_probability


class RainMaxProbabilitySensor(RainAlertSensor):
    """Highest hourly rain chance in the forecast period (ignores alert thresholds)."""

    _name_key = "max_probabilidade"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:chart-line-variant"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_max_probabilidade"

    @property
    def native_value(self) -> float | None:
        if not self.outlook:
            return None
        return self.outlook.max_probability

    @property
    def extra_state_attributes(self) -> dict:
        if not self.outlook:
            return {}
        threshold = self._entry.data.get(CONF_PROBABILITY_THRESHOLD)
        return {
            **self._config_attributes(),
            ATTR_RAIN_EXPECTED: self.outlook.rain_expected,
            "highest_in_period_not_necessarily_alert": True,
            "counts_toward_chuva_prevista": self.outlook.rain_expected,
        }


class RainNextPrecipSensor(RainAlertSensor):
    """Expected mm/h at the next rain hour."""

    _name_key = "precipitacao_proxima_chuva"
    _attr_native_unit_of_measurement = "mm/h"
    _attr_icon = "mdi:weather-pouring"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_precip_proxima"

    @property
    def native_value(self) -> float | None:
        if not self.outlook or not self.outlook.rain_expected:
            return None
        return self.outlook.precipitation_mm


class RainConditionSensor(RainAlertSensor):
    """Human-readable weather at the next rain slot."""

    _name_key = "condicao_proxima_chuva"
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_condicao"

    @property
    def native_value(self) -> str | None:
        if not self.outlook or not self.outlook.rain_expected:
            return None
        return weather_code_description(self.outlook.weather_code, self._language())


class RainCurrentConditionSensor(RainAlertSensor):
    """Human-readable weather right now."""

    _name_key = "condicao_atual"
    _attr_icon = "mdi:weather-partly-cloudy"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_condicao_atual"

    @property
    def native_value(self) -> str | None:
        if not self.payload:
            return None
        return weather_code_description(self.payload.current.weather_code, self._language())


class RainTemperatureSensor(RainAlertSensor):
    """Current temperature from Open-Meteo."""

    _name_key = "temperatura_atual"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = "temperature"
    _attr_icon = "mdi:thermometer"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_temperatura"

    @property
    def native_value(self) -> float | None:
        if not self.payload:
            return None
        return self.payload.current.temperature


class RainHumiditySensor(RainAlertSensor):
    """Current relative humidity."""

    _name_key = "umidade_atual"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = "humidity"
    _attr_icon = "mdi:water-percent"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_umidade"

    @property
    def native_value(self) -> float | None:
        if not self.payload:
            return None
        return self.payload.current.humidity


class RainWindSensor(RainAlertSensor):
    """Current wind speed."""

    _name_key = "vento_atual"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_device_class = "wind_speed"
    _attr_icon = "mdi:weather-windy"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_vento"

    @property
    def native_value(self) -> float | None:
        if not self.payload:
            return None
        return self.payload.current.wind_speed


class RainCloudCoverSensor(RainAlertSensor):
    """Current cloud cover."""

    _name_key = "nuvens_atual"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:cloud"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_nuvens"

    @property
    def native_value(self) -> float | None:
        if not self.payload:
            return None
        return self.payload.current.cloud_cover


class RainCurrentPrecipSensor(RainAlertSensor):
    """Current precipitation intensity."""

    _name_key = "precipitacao_atual"
    _attr_native_unit_of_measurement = "mm/h"
    _attr_icon = "mdi:weather-rainy"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_precip_atual"

    @property
    def native_value(self) -> float | None:
        if not self.payload:
            return None
        return self.payload.current.precipitation


class RainWindowPrecipTotalSensor(RainAlertSensor):
    """Sum of hourly precipitation in the configured window."""

    _name_key = "precipitacao_total_janela"
    _attr_native_unit_of_measurement = "mm"
    _attr_icon = "mdi:weather-rainy"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_precip_total"

    @property
    def native_value(self) -> float | None:
        if not self.payload:
            return None
        return self.payload.total_precipitation_in_window_mm


class RainWindowPrecipMaxSensor(RainAlertSensor):
    """Max hourly precipitation in the configured window."""

    _name_key = "precipitacao_max_janela"
    _attr_native_unit_of_measurement = "mm"
    _attr_icon = "mdi:arrow-collapse-up"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_precip_max"

    @property
    def native_value(self) -> float | None:
        if not self.payload:
            return None
        return self.payload.max_precipitation_in_window_mm


class RainWindowWindMaxSensor(RainAlertSensor):
    """Peak wind speed in the configured window."""

    _name_key = "vento_max_janela"
    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_device_class = "wind_speed"
    _attr_icon = "mdi:weather-windy-variant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_vento_max"

    @property
    def native_value(self) -> float | None:
        if not self.payload:
            return None
        return self.payload.max_wind_in_window_kmh
