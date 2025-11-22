
---

# PurpleAir AQI – Home Assistant Integration

Fetches PM2.5-based AQI from nearby PurpleAir sensors, with averaging and PM2.5 conversion options.

---

## ✨ Features

* Automatically finds **public PurpleAir sensors** near a location
* Supports **PM2.5 conversion formulas**:

  * US EPA
  * Woodsmoke
  * AQ&U
  * LRAPA
  * CF=1
  * None
* Uses **averaged AQI** from multiple sensors
* Supports **weighted averaging** (distance + sensor quality)
* Adjustable:

  * Search radius
  * Miles/kilometers
  * Update interval
  * Use of weighted calculations
* Provides three sensor attributes:

  * **aqi** – PM2.5 AQI (converted)
  * **category** – Good / Moderate / Unhealthy, etc.
  * **sites** – List of sensors included in the calculation
* Compatible with **HACS** via Custom Repository
* Minimal configuration required
* Fully asynchronous and efficient

---

## 📦 Installation (HACS – Custom Repository)

1. Open **HACS → Integrations → Custom repositories**
2. Add this URL:

   ```
   https://github.com/TheMegamind/purple_air
   ```
3. Category: **Integration**
4. Install → Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration**
6. Choose **PurpleAir AQI**

---

## ⚙️ Configuration

### Initial Setup Fields

| Setting                  | Description                                |
| ------------------------ | ------------------------------------------ |
| **API Key**              | PurpleAir API key (required)               |
| **Device Search**        | Whether to auto-locate nearby sensors      |
| **Latitude / Longitude** | Center coordinate for search box           |
| **Search Range**         | Radius around the coordinate (0.1–50)      |
| **Unit**                 | Miles or kilometers                        |
| **Weighted**             | Enable distance/quality weighted averaging |
| **Conversion**           | PM2.5 conversion method (See below)        |
| **Update Interval**      | Minutes between sensor refresh             |

If *Device Search* is OFF, you may supply:

* **Sensor Index** (ID of a single PurpleAir sensor)
* **Read Key** (for private sensors only)

### Options (after setup)

Can be edited anytime:

* Search Range
* Unit (miles/km)
* Weighted
* Conversion method
* Update interval

Latitude and longitude remain fixed after initial setup.

---

## 🧪 Entity Provided

| Entity                 | Type   | Description                                |
| ---------------------- | ------ | ------------------------------------------ |
| `sensor.purpleair_aqi` | Sensor | PM2.5 AQI value, category, and sensor list |

---

## 🔧 Example Usage

Send AQI notifications through Pushover:

```yaml
service: notify.pushover
data:
  title: "Air Quality"
  message: >
    Current AQI: {{ states('sensor.purpleair_aqi') }} –
    {{ state_attr('sensor.purpleair_aqi', 'category') }}
```

---

## ⏱ Update Interval

This setting controls how frequently the integration requests new data from the PurpleAir API and updates the sensor values inside Home Assistant.

| Interval                           | What It Means    | Impact                                         |
| ---------------------------------- | ---------------- | ---------------------------------------------- |
| Short (e.g., **1–5 minutes**)      | Frequent updates | More API usage; more current AQI               |
| Moderate (e.g., **10–15 minutes**) | Balanced updates | Recommended for most users                     |
| Long (e.g., **30–60 minutes**)     | Fewer updates    | Lowest API use; slower to react to air changes |

###📌 Recommendation

> For most users, **10 minutes** provides a good balance between responsiveness and API efficiency.

### ⚠ Notes

* Shorter intervals **do not improve sensor accuracy**, only responsiveness.
* If you are monitoring **wildfire smoke or rapid AQI changes**, consider **5–10 minutes**.
* If you have **many PurpleAir sensors** configured, longer intervals help reduce API load.
* The interval only affects **data refresh**, not how often the UI redraws.

---

## 🌫 PM₂.₅ Conversion Formulas Explained


| Formula       | Best For                       | Description / Source                                                                                                                      |
| ------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **US EPA**    | Most users                     | Official U.S. EPA correction for PurpleAir data. Adjusts for humidity and general outdoor conditions. Based on multi-site national study. |
| **Woodsmoke** | Wildfire areas                 | Optimized for particles from wildfire smoke, pellets, and wood burning. Often used in Western U.S.                                        |
| **AQ&U**      | Mountain/valley regions (Utah) | Used by the Utah Dept. of Environmental Quality for inversion-prone areas. Works well in high-elevation, dry climates.                    |
| **LRAPA**     | Very humid climates            | Developed by Lane Regional Air Protection Agency (Oregon). Reduces over-reporting of PM₂.₅ caused by humidity swelling tiny particles.    |
| **CF = 1**    | Indoor sensors                 | A factory “no-correction/wet” value. High-bias outdoors, but suitable indoors (no humidity correction needed).                            |
| **None**      | Raw data use                   | Reports the uncorrected sensor value exactly as measured. Most users shouldn’t choose this. Used for research or custom processing.       |


---

## 🛠 Troubleshooting

* If AQI remains `unknown`, verify your **API key**.
* If no sensors are detected, increase **search_range** in Options.
* For private sensors, ensure **read_key** is correct.

---

## 📄 License

This project is licensed under the MIT License.
See the `LICENSE` file for details.

## Brand Disclaimer

The **PurpleAir** name and logo are trademarks of **PurpleAir, Inc.**  
This project is an independent, community-maintained integration for Home Assistant and is **not affiliated with, endorsed by, or sponsored by PurpleAir, Inc.** in any way.

---
