#sensor.py

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
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
            PurpleAirAQIDeltaSensor(coordinator, entry),
            PurpleAirAQILevelSensor(coordinator, entry),
            PurpleAirCategorySensor(coordinator, entry),
            PurpleAirConversionSensor(coordinator, entry),
            PurpleAirHealthAdvisorySensor(coordinator, entry),
            PurpleAirHealthStatusSensor(coordinator, entry),
            PurpleAirSitesSensor(coordinator, entry),
        ],
        True,
    )


# ────────────────────────────────────────────────────────────────
# Base
# ────────────────────────────────────────────────────────────────
class PurpleAirBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self.entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "PurpleAir",
        }

    @property
    def result(self) -> PurpleAirResult | None:
        return self.coordinator.data


# ────────────────────────────────────────────────────────────────
# AQI — PRIMARY SENSOR (THIS IS THE FIX)
# ────────────────────────────────────────────────────────────────
class PurpleAirAQISensor(PurpleAirBase):
    _attr_name = "AQI"
    _attr_icon = "mdi:weather-hazy"
    _attr_native_unit_of_measurement = "AQI"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_aqi"

    @property
    def native_value(self):
        return self.result.aqi if self.result else None


# ────────────────────────────────────────────────────────────────
# AQI Delta
# ────────────────────────────────────────────────────────────────
class PurpleAirAQIDeltaSensor(PurpleAirBase):
    _attr_name = "AQI Delta"
    _attr_icon = "mdi:vector-difference"
    _attr_native_unit_of_measurement = "AQI"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_aqi_delta"

    @property
    def native_value(self):
        if not self.result:
            return None
        return getattr(self.result, "_aqi_delta", None)


# ────────────────────────────────────────────────────────────────
# AQI Level (1–6)
# ────────────────────────────────────────────────────────────────
CATEGORY_TO_LEVEL = {
    "Good": 1,
    "Moderate": 2,
    "Unhealthy for Sensitive Groups": 3,
    "Unhealthy": 4,
    "Very Unhealthy": 5,
    "Hazardous": 6,
}


class PurpleAirAQILevelSensor(PurpleAirBase):
    _attr_name = "AQI Level"
    _attr_icon = "mdi:numeric"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_aqi_level"

    @property
    def native_value(self):
        if not self.result:
            return None
        level = CATEGORY_TO_LEVEL.get(self.result.category)
        return str(level) if level is not None else None



# ────────────────────────────────────────────────────────────────
# Category
# ────────────────────────────────────────────────────────────────
class PurpleAirCategorySensor(PurpleAirBase):
    _attr_name = "Category"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(CATEGORY_TO_LEVEL.keys())

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_category"

    @property
    def native_value(self):
        return self.result.category if self.result else None


# ────────────────────────────────────────────────────────────────
# Conversion
# ────────────────────────────────────────────────────────────────
class PurpleAirConversionSensor(PurpleAirBase):
    _attr_name = "Conversion"
    _attr_icon = "mdi:flask-outline"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_conversion"

    @property
    def native_value(self):
        return self.result.conversion if self.result else None


# ────────────────────────────────────────────────────────────────
# Health Advisory
# ────────────────────────────────────────────────────────────────
ADVISORY_TEXT = {
    "Good": "Air quality is good. Enjoy your day!",
    "Moderate": "Sensitive individuals should limit prolonged outdoor exertion.",
    "Unhealthy for Sensitive Groups": "Reduce prolonged outdoor exertion if sensitive.",
    "Unhealthy": "Everyone may begin to experience health effects.",
    "Very Unhealthy": "Health alert: avoid outdoor exertion.",
    "Hazardous": "Emergency conditions. Stay indoors.",
}


class PurpleAirHealthAdvisorySensor(PurpleAirBase):
    _attr_name = "Health Advisory"
    _attr_icon = "mdi:head-question-outline"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_health_advisory"

    @property
    def native_value(self):
        if not self.result:
            return None
        return ADVISORY_TEXT.get(self.result.category)


# ────────────────────────────────────────────────────────────────
# Health Status
# ────────────────────────────────────────────────────────────────
class PurpleAirHealthStatusSensor(PurpleAirBase):
    _attr_name = "Health Status"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_health_status"

    @property
    def native_value(self):
        return "online" if self.result else "offline"


# ────────────────────────────────────────────────────────────────
# Sites
# ────────────────────────────────────────────────────────────────
class PurpleAirSitesSensor(PurpleAirBase):
    _attr_name = "Sites"
    _attr_icon = "mdi:map-marker-multiple-outline"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_sites"

    @property
    def native_value(self):
        if not self.result or not self.result.sites:
            return None
        return ", ".join(self.result.sites)
