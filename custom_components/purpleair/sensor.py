# custom_components/purpleair/sensor.py

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
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

    async_add_entities(
        [
            PurpleAirAQISensor(coordinator, entry),
            PurpleAirCategorySensor(coordinator, entry),
            PurpleAirConversionSensor(coordinator, entry),
            PurpleAirHealthAdvisorySensor(coordinator, entry),
            PurpleAirHealthStatusSensor(coordinator, entry),
            PurpleAirSitesSensor(coordinator, entry),
        ],
        True,
    )


class PurpleAirBase:
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "PurpleAir",
        }


class PurpleAirAQISensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "AQI"
    _attr_icon = "mdi:weather-hazy"
    _attr_native_unit_of_measurement = "AQI"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_aqi"

    @property
    def native_value(self):
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
            "update_interval": int(self.entry.data.get("update_interval", 10)),
        }


CATEGORY_SEVERITY = {
    "Good": "info",
    "Moderate": "warning",
    "Unhealthy for Sensitive Groups": "warning",
    "Unhealthy": "critical",
    "Very Unhealthy": "critical",
    "Hazardous": "critical",
}


class PurpleAirCategorySensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Category"
    _attr_icon = "mdi:eye"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(CATEGORY_SEVERITY.keys())

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_category"

    @property
    def native_value(self):
        result: PurpleAirResult | None = self.coordinator.data
        return result.category if result else None

    @property
    def native_severity(self):
        result: PurpleAirResult | None = self.coordinator.data
        return CATEGORY_SEVERITY.get(result.category) if result else None


class PurpleAirConversionSensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Conversion"
    _attr_icon = "mdi:flask-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_conversion"

    @property
    def native_value(self):
        result: PurpleAirResult | None = self.coordinator.data
        return result.conversion if result else None


class PurpleAirHealthStatusSensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Health Status"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_health"

    @property
    def native_value(self):
        return "online" if self.coordinator.data else "offline"


ADVISORY_TEXT = {
    "Good": "Air quality is good. Enjoy your day!",
    "Moderate": "Moderate air quality. Sensitive individuals should reduce prolonged outdoor exertion.",
    "Unhealthy for Sensitive Groups": "Limit prolonged outdoor exertion if sensitive.",
    "Unhealthy": "Air quality is unhealthy. Reduce outdoor activities.",
    "Very Unhealthy": "Health alert: everyone may experience serious effects.",
    "Hazardous": "Emergency conditions. Avoid outdoor activity.",
}


class PurpleAirHealthAdvisorySensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Health Advisory"
    _attr_icon = "mdi:head-question-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_advisory"

    @property
    def native_value(self):
        result: PurpleAirResult | None = self.coordinator.data
        if not result:
            return "No data available"
        return ADVISORY_TEXT.get(result.category, "Air quality information unavailable.")


class PurpleAirSitesSensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Sites"
    _attr_icon = "mdi:map-marker-multiple-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_sites"

    @property
    def native_value(self):
        result: PurpleAirResult | None = self.coordinator.data
        if not result or not result.sites:
            return None
        return ", ".join(result.sites)
