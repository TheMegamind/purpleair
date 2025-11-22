# custom_components/purpleair_aqi/api.py

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

BASE_URL = "https://api.purpleair.com/v1/sensors"


@dataclass
class PurpleAirConfig:
    api_key: str
    device_search: bool
    search_coords: Tuple[float, float] | None
    search_range: float
    unit: str  # "miles" or "kilometers"
    weighted: bool
    sensor_index: Optional[int]
    read_key: Optional[str]
    conversion: str  # "US EPA", "Woodsmoke", "AQ&U", "LRAPA", "CF=1", "none"
    update_interval: int  # minutes


@dataclass
class PurpleAirResult:
    aqi: int
    category: str
    sites: List[str]
    conversion: str
    weighted: bool


class PurpleAirClient:
    def __init__(self, session: aiohttp.ClientSession, config: PurpleAirConfig) -> None:
        self._session = session
        self._config = config

    async def fetch(self) -> PurpleAirResult:
        pm25_field = self._determine_pm25_field()
        fields = ["name", "confidence", pm25_field]

        # For US EPA conversion we need humidity; we’ll always ask for it to keep the option usable
        fields.append("humidity")

        if self._config.weighted:
            fields += ["latitude", "longitude", "position_rating"]

        params = self._build_query(fields)

        headers = {"X-API-Key": self._config.api_key}

        async with self._session.get(
            BASE_URL, headers=headers, params=params, timeout=30
        ) as resp:
            if resp.status != 200:
                # Simplified error; you can add backoff logic if you want to be fancy
                text = await resp.text()
                raise RuntimeError(f"PurpleAir HTTP {resp.status}: {text}")

            data = await resp.json()

        return self._process_response(data, pm25_field)

    def _determine_pm25_field(self) -> str:
        # mirrors the Groovy logic around avg_period vs conversion; we focus on pm2.5 fields only
        conv = (self._config.conversion or "").lower()
        if conv in ("lrapa", "woodsmoke", "cf=1", "cf=1", "cf=1"):
            return "pm2.5_cf_1"
        # default PurpleAir PM2.5
        return "pm2.5"

    def _build_query(self, fields: List[str]) -> Dict[str, Any]:
        if self._config.device_search and self._config.search_coords:
            lat, lon = self._config.search_coords
            dist2deg = distance2degrees(lat)
            if self._config.unit == "miles":
                lat_deg = self._config.search_range / dist2deg[0]
                lon_deg = self._config.search_range / dist2deg[1]
            else:
                # km → miles
                miles = self._config.search_range / 1.609
                lat_deg = miles / dist2deg[0]
                lon_deg = miles / dist2deg[1]

            return {
                "fields": ",".join(fields),
                "location_type": "0",
                "max_age": 3600,
                "nwlat": lat + lat_deg,
                "nwlng": lon - lon_deg,
                "selat": lat - lat_deg,
                "selng": lon + lon_deg,
            }

        # direct sensor mode
        params: Dict[str, Any] = {
            "fields": ",".join(fields),
        }
        if self._config.sensor_index is not None:
            params["show_only"] = str(self._config.sensor_index)
        if self._config.read_key:
            params["read_key"] = self._config.read_key
        return params

    def _process_response(self, payload: Dict[str, Any], pm25_field: str) -> PurpleAirResult:
        fields = payload.get("fields", [])
        field_index = {name: idx for idx, name in enumerate(fields)}
        data_rows = payload.get("data", [])

        # Filter by confidence >= 90 like driver
        rows = [
            row
            for row in data_rows
            if row[field_index.get("confidence", -1)] is not None
            and int(row[field_index["confidence"]]) >= 90
        ]

        if not rows:
            raise RuntimeError("No valid PurpleAir sensors found in search area")

        sensors: List[Dict[str, Any]] = []

        base_coords = self._config.search_coords

        for row in rows:
            name = row[field_index["name"]]
            confidence = int(row[field_index["confidence"]])
            pm25_raw = float(row[field_index[pm25_field]]) if row[field_index[pm25_field]] is not None else None
            humidity = None
            if "humidity" in field_index and row[field_index["humidity"]] is not None:
                humidity = float(row[field_index["humidity"]])

            if pm25_raw is None:
                # skip sensors with no PM data
                continue

            # Use sensor coords if weighted, otherwise base coords (center)
            if self._config.weighted and "latitude" in field_index and "longitude" in field_index:
                lat = float(row[field_index["latitude"]])
                lon = float(row[field_index["longitude"]])
                coords = (lat, lon)
            else:
                coords = base_coords

            position_rating = -1
            if "position_rating" in field_index and row[field_index["position_rating"]] is not None:
                position_rating = int(row[field_index["position_rating"]])

            pm25_conv = apply_conversion(
                self._config.conversion,
                pm25_raw,
                humidity,
            )

            sensors.append(
                {
                    "site": name,
                    "pm25": pm25_raw,
                    "pm25_conv": pm25_conv,
                    "confidence": confidence,
                    "coords": coords,
                    "position_rating": position_rating,
                }
            )

        if not sensors:
            raise RuntimeError("No sensors with PM2.5 data")

        if self._config.weighted and self._config.device_search and base_coords is not None:
            avg_pm25 = sensor_average_weighted(sensors, "pm25_conv", base_coords)
        else:
            avg_pm25 = sensor_average(sensors, "pm25_conv")

        aqi = get_part_2_5_aqi(avg_pm25)
        category = get_category(aqi)
        sites = sorted(s["site"] for s in sensors)

        return PurpleAirResult(
            aqi=aqi,
            category=category,
            sites=sites,
            conversion=(self._config.conversion or "none"),
            weighted=self._config.weighted,
        )


def sensor_average(sensors: List[Dict[str, Any]], field: str) -> float:
    values = [float(s[field]) for s in sensors if s.get(field) is not None]
    if not values:
        return 0.0
    return sum(values) / len(values)


def sensor_average_weighted(
    sensors: List[Dict[str, Any]], field: str, origin: Tuple[float, float]
) -> float:
    distances = []
    for s in sensors:
        coords = s.get("coords") or origin
        d = distance(origin, coords)
        distances.append(d if d > 0 else 0.001)  # avoid div/0

    nearest = min(distances)
    weighted_sum = 0.0
    weight_total = 0.0

    for s, d in zip(sensors, distances):
        val = float(s[field])
        position_rating = int(s.get("position_rating", -1))
        weight = nearest / math.sqrt(d) * (position_rating + 1)
        weighted_sum += val * weight
        weight_total += weight

    if weight_total <= 0:
        return 0.0
    return weighted_sum / weight_total


def get_part_2_5_aqi(part_count: float) -> int:
    c = math.floor(10 * part_count) / 10.0
    if 0 <= c < 12.1:
        return aqi_linear(50, 0, 12, 0, c)
    elif 12.1 <= c < 35.5:
        return aqi_linear(100, 51, 35.4, 12.1, c)
    elif 35.5 <= c < 55.5:
        return aqi_linear(150, 101, 55.4, 35.5, c)
    elif 55.5 <= c < 150.5:
        return aqi_linear(200, 151, 150.4, 55.5, c)
    elif 150.5 <= c < 250.5:
        return aqi_linear(300, 201, 250.4, 150.5, c)
    elif 250.5 <= c < 350.5:
        return aqi_linear(400, 301, 350.4, 250.5, c)
    elif 350.5 <= c < 500.5:
        return aqi_linear(500, 401, 500.4, 350.5, c)
    elif c >= 500.5:
        return round(c)
    return -1


def aqi_linear(aqi_high: int, aqi_low: int, conc_high: float, conc_low: float, conc: float) -> int:
    a = ((conc - conc_low) / (conc_high - conc_low)) * (aqi_high - aqi_low) + aqi_low
    return int(round(a))


def get_category(aqi: int) -> str:
    if 0 <= aqi <= 50:
        return "Good"
    if 51 <= aqi <= 100:
        return "Moderate"
    if 101 <= aqi <= 150:
        return "Unhealthy for sensitive groups"
    if 151 <= aqi <= 200:
        return "Unhealthy"
    if 201 <= aqi <= 300:
        return "Very unhealthy"
    if 301 <= aqi <= 500:
        return "Hazardous"
    if aqi > 500:
        return "Extremely hazardous!"
    return "error"


def apply_conversion(conversion: str, pm25: float, rh: Optional[float]) -> float:
    conv = (conversion or "").lower()
    if conv == "us epa" or conv == "us_epa":
        if rh is None:
            # fallback: no humidity, return raw
            return pm25
        return us_epa_conversion(pm25, rh)
    if conv == "woodsmoke":
        return woodsmoke_conversion(pm25)
    if conv in ("aq&u", "aq and u", "aq_and_u", "aq u"):
        return aq_and_u_conversion(pm25)
    if conv == "lrapa":
        return lrapa_conversion(pm25)
    # none / default
    return pm25


def us_epa_conversion(pm: float, rh: float) -> float:
    # Ported from your Groovy; simplified but equivalent.
    if pm < 30:
        c = 0.524 * pm - 0.0862 * rh + 5.75
    elif pm < 50:
        t = pm / 20.0 - 1.5
        c = (0.786 * t + 0.524 * (1 - t)) * pm - 0.0862 * rh + 5.75
    elif pm < 210:
        c = 0.786 * pm - 0.0862 * rh + 5.75
    elif pm < 260:
        t = pm / 50.0 - 4.2
        c = 0.69 * t + 0.786 * (1 - t)
        c = c * pm - 0.0862 * rh * (1 - t)
        c = c + 2.966 * t + 5.75 * (1 - t)
        c = c + 8.84e-4 * (pm ** 2) * t
    else:
        c = 2.966 + 0.69 * pm + 8.84e-4 * (pm ** 2)
    return max(c, 0.0)


def woodsmoke_conversion(pm: float) -> float:
    return 0.55 * pm + 0.53


def aq_and_u_conversion(pm: float) -> float:
    return 0.778 * pm + 2.65


def lrapa_conversion(pm: float) -> float:
    c = 0.5 * pm - 0.66
    return max(c, 0.0)


def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    # Haversine, returns miles
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    aa = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(aa), math.sqrt(1 - aa))
    d_meters = R * c
    d_km = d_meters / 1000.0
    return d_km / 1.609  # miles


def distance2degrees(latitude: float) -> Tuple[float, float]:
    lat_miles_per_degree = 69.172 * math.cos(math.radians(latitude))
    lon_miles_per_degree = 68.972
    return lat_miles_per_degree, lon_miles_per_degree
