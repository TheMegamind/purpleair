# custom_components/purpleair_aqi/__init__.py

from __future__ import annotations

from datetime import timedelta
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PurpleAirClient, PurpleAirConfig

DOMAIN = "purpleair_aqi"
PLATFORMS = ["sensor", "number"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up integration (YAML config not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PurpleAir AQI from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = aiohttp.ClientSession()

    conf = entry.data

    device_search = conf.get("device_search", True)
    sensor_index = conf.get("sensor_index")
    read_key = conf.get("read_key")

    coords = None
    if device_search:
        lat = float(conf.get("latitude"))
        lon = float(conf.get("longitude"))
        coords = (lat, lon)

    cfg = PurpleAirConfig(
        api_key=conf["api_key"],
        device_search=device_search,
        search_coords=coords,
        search_range=float(conf.get("search_range", 1.5)),
        unit=conf.get("unit", "miles"),
        weighted=conf.get("weighted", True),
        sensor_index=int(sensor_index) if sensor_index is not None else None,
        read_key=read_key,
        conversion=conf.get("conversion", "US EPA"),
        update_interval=int(conf.get("update_interval", 10)),
    )

    client = PurpleAirClient(session, cfg)

    async def async_update():
        try:
            return await client.fetch()
        except Exception as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="PurpleAir AQI",
        update_method=async_update,
        update_interval=timedelta(minutes=cfg.update_interval),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store references
    hass.data[DOMAIN] = {
        "session": session,
        "coordinator": coordinator,
        "config": cfg,
    }

    # Load ALL platforms (sensor AND number)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload PurpleAir AQI."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    session = hass.data[DOMAIN].pop("session", None)
    if session:
        await session.close()

    if unload_ok:
        hass.data.pop(DOMAIN, None)

    return unload_ok
