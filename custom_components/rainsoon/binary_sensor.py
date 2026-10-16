"""Binary sensors for RainSoon."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LANGUAGE, DOMAIN, INTEGRATION_VERSION
from .coordinator import RainAlertCoordinator
from .i18n import entity_name, normalize_language


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RainSoon binary sensors."""
    coordinator: RainAlertCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RainExpectedBinarySensor(coordinator, entry),
            RainingNowBinarySensor(coordinator, entry),
        ]
    )


class RainSoonBinary(CoordinatorEntity[RainAlertCoordinator], BinarySensorEntity):
    """Base binary sensor."""

    _attr_has_entity_name = True
    _name_key: str = ""

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._apply_entity_name()

    def _language(self) -> str:
        return normalize_language(self._entry.data.get(CONF_LANGUAGE))

    def _apply_entity_name(self) -> None:
        key = self._name_key or getattr(type(self), "_name_key", "")
        if key:
            self._attr_translation_key = None
            self._attr_name = entity_name(key, self._language())

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


class RainExpectedBinarySensor(RainSoonBinary):
    """Whether rain is expected within configured thresholds."""

    _name_key = "chuva_prevista"
    _attr_icon = "mdi:weather-pouring"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_chuva_prevista"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if not data:
            return None
        return data.outlook.rain_expected


class RainingNowBinarySensor(RainSoonBinary):
    """Whether it is raining at the location right now (Open-Meteo current)."""

    _name_key = "chuva_agora"
    _attr_icon = "mdi:weather-rainy"

    def __init__(
        self, coordinator: RainAlertCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_chuva_agora"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if not data:
            return None
        return data.raining_now
