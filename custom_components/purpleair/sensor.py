# custom_components/purpleair/sensor.py

from __future__ import annotations

from typing import Any
from datetime import datetime

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
    """Set up PurpleAir sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        PurpleAirAQISensor(coordinator, entry),
        PurpleAirCategorySensor(coordinator, entry),
    ]

    async_add_entities(entities, True)


# --------------------------------------------------------------------
# AQI SENSOR (MAIN)
# --------------------------------------------------------------------
class PurpleAirAQISensor(CoordinatorEntity, SensorEntity):
    """PurpleAir AQI sensor."""

    _attr_has_entity_name = True
    _attr_name = "AQI"
    _attr_icon = "mdi:weather-hazy"
    _attr_native_unit_of_measurement = "AQI"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_aqi"
        self._update_interval = int(entry.data.get("update_interval", 10))

    # Link to device
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "PurpleAir",
        }

    @property
    def native_value(self) -> int | None:
        result: PurpleAirResult | None = self.coordinator.data
        return result.aqi if result else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        result: PurpleAirResult | None = self.coordinator.data
        if not result:
            return None

        return {
            "category": result.category,
            "sites": result.sites,
            "conversion": result.conversion,
            "weighted": result.weighted,
            "fetch_time": datetime.now().isoformat(),
            "update_interval": self._update_interval,
        }


# --------------------------------------------------------------------
# CATEGORY SENSOR
# --------------------------------------------------------------------
class PurpleAirCategorySensor(CoordinatorEntity, SensorEntity):
    """PurpleAir AQI Category sensor."""

    _attr_has_entity_name = True
    _attr_name = "Category"
    _attr_icon = "mdi:eye"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_category"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "PurpleAir",
        }

    @property
    def native_value(self) -> str | None:
        result: PurpleAirResult | None = self.coordinator.data
        return result.category if result else None
