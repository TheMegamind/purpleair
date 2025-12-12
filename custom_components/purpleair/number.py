from __future__ import annotations
 
from datetime import timedelta

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([PurpleAirUpdateIntervalNumber(coordinator, entry)])


class PurpleAirUpdateIntervalNumber(CoordinatorEntity, NumberEntity):
    """Polling interval control."""

    _attr_has_entity_name = True
    _attr_name = "Update Interval"
    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = "slider"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_update_interval"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "PurpleAir",
        }

    @property
    def native_value(self) -> int:
        return int(self.entry.data.get("update_interval", 10))

    async def async_set_native_value(self, value: float) -> None:
        minutes = int(value)

        new_data = {**self.entry.data, "update_interval": minutes}
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

        self.coordinator.update_interval = timedelta(minutes=minutes)
        await self.coordinator.async_request_refresh()
