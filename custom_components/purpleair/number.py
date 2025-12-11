# custom_components/purpleair/number.py

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][entry.entry_id]["config"]

    async_add_entities(
        [
            PurpleAirUpdateIntervalNumber(coordinator, entry, config),
        ]
    )


class PurpleAirUpdateIntervalNumber(CoordinatorEntity, NumberEntity):
    """A number entity controlling update interval."""

    _attr_name = "Update Interval"
    _attr_has_entity_name = True
    _attr_mode = NumberMode.AUTO
    _attr_native_unit_of_measurement = "min"
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1

    def __init__(self, coordinator, entry: ConfigEntry, config):
        super().__init__(coordinator)
        self.entry = entry
        self._config = config
        self._attr_unique_id = f"{entry.entry_id}_update_interval"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "PurpleAir",
        }

    @property
    def native_value(self) -> int:
        return self._config.update_interval

    async def async_set_native_value(self, value: float) -> None:
        """Set polling interval dynamically."""
        self._config.update_interval = int(value)

        # Update HA config entry so it's persistent
        new_data = {**self.entry.data, "update_interval": int(value)}
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

        # Update coordinator interval
        self.coordinator.update_interval = timedelta(minutes=int(value))

        await self.coordinator.async_request_refresh()
