async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    session = aiohttp.ClientSession()
    conf = entry.data

    device_search = conf.get("device_search", True)
    sensor_index = conf.get("sensor_index")
    read_key = conf.get("read_key")

    coords = None
    if device_search:
        coords = (float(conf["latitude"]), float(conf["longitude"]))

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

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "session": session,
        "coordinator": coordinator,
        "config": cfg,
    }

    # LOAD BOTH PLATFORMS
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "number"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "number"])

    session = hass.data[DOMAIN][entry.entry_id].pop("session", None)
    if session:
        await session.close()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
