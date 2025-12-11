# custom_components/purpleair/sensor.py

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
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([PurpleAirSensor(coordinator, entry)], True)


class PurpleAirSensor(CoordinatorEntity, SensorEntity):
    """Main PurpleAir Sensor."""

    _attr_has_entity_name = True
    _attr_name = "AQI"
    _attr_icon = "mdi:weather-hazy"
    _attr_native_unit_of_measurement = "AQI"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_aqi"

    @property
    def native_value(self) -> int | None:
        result: PurpleAirResult = self.coordinator.data
        return result.aqi if result else None

    @property
    def available(self) -> bool:
        # Mark entity unavailable when API result is missing or errored
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose Hubitat-style attributes as entity attributes."""
        result: PurpleAirResult = self.coordinator.data
        if not result:
            return None

        return {
            "category": result.category,
            "sites": result.sites,
            "conversion": result.conversion,
            "weighted": result.weighted,
            "fetch_time": result.fetch_time,  # Comes from API, not generated each refresh
            "update_interval": result.update_interval,  # Useful for UI visibility
        }
