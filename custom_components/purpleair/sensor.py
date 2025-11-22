# custom_components/purpleair_aqi/sensor.py

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .api import PurpleAirResult


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([PurpleAirAQISensor(coordinator)], True)


class PurpleAirAQISensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "PurpleAir AQI"
    _attr_icon = "mdi:weather-hazy"
    _attr_native_unit_of_measurement = "AQI"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = "purpleair_aqi"

    @property
    def native_value(self) -> int | None:
        result: PurpleAirResult = self.coordinator.data
        return result.aqi if result else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        result: PurpleAirResult = self.coordinator.data
        if not result:
            return None
        return {
            "category": result.category,
            "sites": result.sites,
            "conversion": result.conversion,
            "weighted": result.weighted,
        }
