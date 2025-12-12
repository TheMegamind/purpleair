# sensor.py (working)

from __future__ import annotations

from typing import Any
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.components.sensor import SensorDeviceClass
from . import DOMAIN
from .api import PurpleAirResult


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up PurpleAir sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        PurpleAirAQISensor(coordinator, entry),
        PurpleAirCategorySensor(coordinator, entry),
        PurpleAirConversionSensor(coordinator, entry),
        PurpleAirSitesSensor(coordinator, entry),
        PurpleAirHealthStatusSensor(coordinator, entry),
        PurpleAirHealthAdvisorySensor(coordinator, entry),
    ]

    async_add_entities(entities, True)


# ════════════════════════════════════════════════════════════════════════
# COMMON MIXIN FOR DEVICE REGISTRATION
# ════════════════════════════════════════════════════════════════════════

class PurpleAirBase:
    """Mixin for device registration."""

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "PurpleAir",
        }


# ════════════════════════════════════════════════════════════════════════
# AQI SENSOR
# ════════════════════════════════════════════════════════════════════════

class PurpleAirAQISensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    """PurpleAir AQI sensor."""

    _attr_has_entity_name = True
    _attr_name = "AQI"
    _attr_icon = "mdi:weather-hazy"
    _attr_native_unit_of_measurement = "AQI"

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_aqi"
        self._update_interval = int(entry.data.get("update_interval", 10))

    @property
    def native_value(self):
        result: PurpleAirResult | None = self.coordinator.data
        return result.aqi if result else None

    @property
    def extra_state_attributes(self):
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


# ════════════════════════════════════════════════════════════════════════
# CATEGORY SENSOR WITH SEVERITY
# ════════════════════════════════════════════════════════════════════════

CATEGORY_MAP = {
    "Good": "info",
    "Moderate": "warning",
    "Unhealthy for Sensitive Groups": "warning",
    "Unhealthy": "critical",
    "Very Unhealthy": "critical",
    "Hazardous": "critical",
}

class PurpleAirCategorySensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    """AQI category sensor with severity mapping."""

    _attr_has_entity_name = True
    _attr_name = "Category"
    _attr_icon = "mdi:eye"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(CATEGORY_MAP.keys())

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
        """Enable Home Assistant built-in color/severity UI."""
        result: PurpleAirResult | None = self.coordinator.data
        if not result:
            return None
        return CATEGORY_MAP.get(result.category)


# ════════════════════════════════════════════════════════════════════════
# CONVERSION METHOD SENSOR
# ════════════════════════════════════════════════════════════════════════

class PurpleAirConversionSensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    """Conversion method sensor."""

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


# ════════════════════════════════════════════════════════════════════════
# SITES SENSOR
# ════════════════════════════════════════════════════════════════════════

class PurpleAirSitesSensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    """Sites used in AQI calculation."""

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


# ════════════════════════════════════════════════════════════════════════
# HEALTH STATUS SENSOR
# ════════════════════════════════════════════════════════════════════════

class PurpleAirHealthStatusSensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    """Indicates if PurpleAir data is online or offline."""

    _attr_has_entity_name = True
    _attr_name = "Health Status"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_health"

    @property
    def native_value(self):
        result: PurpleAirResult | None = self.coordinator.data
        if not result:
            return "offline"
        return "online"


# ════════════════════════════════════════════════════════════════════════
# HEALTH ADVISORY SENSOR
# ════════════════════════════════════════════════════════════════════════

ADVISORIES = {
    "Good": "Air quality is good. Enjoy your day!",
    "Moderate": "Moderate air quality. Sensitive individuals should consider reducing prolonged outdoor exertion.",
    "Unhealthy for Sensitive Groups": "Limit prolonged outdoor exertion if you are sensitive.",
    "Unhealthy": "Air is unhealthy. Consider reducing outdoor activities.",
    "Very Unhealthy": "Health alert: everyone may experience more serious effects.",
    "Hazardous": "Emergency conditions: avoid outdoor activity.",
}

class PurpleAirHealthAdvisorySensor(PurpleAirBase, CoordinatorEntity, SensorEntity):
    """Friendly health advisory based on AQI category."""

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
        return ADVISORIES.get(result.category, "Air quality information unavailable.")
