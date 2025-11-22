from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

UPDATE_MIN = 1
UPDATE_MAX = 60


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [PurpleAirUpdateIntervalNumber(coordinator, entry)],
        update_before_add=True
    )


class PurpleAirUpdateIntervalNumber(CoordinatorEntity, NumberEntity):
    """Number entity to control the PurpleAir update interval."""

    _attr_name = "PurpleAir Update Interval"
    _attr_unique_id = "purpleair_update_interval"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = UPDATE_MIN
    _attr_native_max_value = UPDATE_MAX
    _attr_native_step = 1

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._value = entry.data.get("update_interval", 10)

    @property
    def native_value(self):
        return self._value

    async def async_set_native_value(self, value: float):
        self._value = int(value)

        data = dict(self.entry.data)
        data["update_interval"] = self._value

        # Update the config entry but WITHOUT restarting the integration
        self.hass.config_entries.async_update_entry(
            self.entry, data=data
        )

        # Now tell coordinator to update polling frequency
        interval_seconds = self._value * 60
        self.coordinator.update_interval = interval_seconds
