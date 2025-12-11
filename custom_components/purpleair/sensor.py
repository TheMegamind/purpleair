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

    entities: list[SensorEntity] = [
        PurpleAirAQISensor(coordinator, entry),
        PurpleAirCategorySensor(coordinator, entry),
    ]

    async_add_entities(entities, True)


class PurpleAirAQISensor(CoordinatorEntity, SensorEntity):
    """Main PurpleAir AQI sensor."""

    _attr_has_entity_name = True
    _attr_name = "AQI"
    _attr_icon = "mdi:weather-hazy"
    _attr_native_unit_of_measurement = "AQI"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_aqi"
        # Store configured update interval (minutes) for attributes
        self._update_interval = int(entry.data.get("update_interval", 10))

    @property
    def native_value(self) -> int | None:
        result: PurpleAirResult | None = self.coordinator.data
        return result.aqi if result is not None else None

    @property
    def available(self) -> bool:
        """Entity is unavailable if no data from API."""
        return self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose additional info similar to Hubitat attributes."""
        result: PurpleAirResult | None = self.coordinator.data
        if result is None:
            return None

        return {
            "category": getattr(result, "category", None),
            "sites": getattr(result, "sites", None),
            "conversion": getattr(result, "conversion", None),
            "weighted": getattr(result, "weighted", None),
            "fetch_time": datetime.now().isoformat(),
            "update_interval": self._update_interval,
        }


class PurpleAirCategorySensor(CoordinatorEntity, SensorEntity):
    """Sensor for the PurpleAir AQI category (Good, Moderate, etc.)."""

    _attr_has_entity_name = True
    _attr_name = "Category"
    _attr_icon = "mdi:eye"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_category"

    @property
    def native_value(self) -> str | None:
        result: PurpleAirResult | None = self.coordinator.data
        return result.category if result is not None else None

    @property
    def available(self) -> bool:
        """Entity is unavailable if no data from API."""
        return self.coordinator.data is not None
