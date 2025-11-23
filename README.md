
---

# PurpleAir – Home Assistant Custom Integration

Fetches PM2.5-based AQI from nearby PurpleAir sensors, with averaging and PM2.5 conversion options.

---

## ✨ Features

* Automatically finds **public PurpleAir sensors** with a specific distance from a location
* Supports a variety of **PM2.5 conversion formulas**:

  * US EPA
  * Woodsmoke
  * AQ&U
  * LRAPA
  * CF=1
  * None
* Uses **averaged AQI** from multiple sensors
* Supports **weighted averaging** (distance + sensor reliability score)
* Adjustable:

  * Search radius
  * Miles/kilometers
  * Update interval
  * Use of weighted calculations
* Provides three sensor attributes:

  * **aqi** – PM2.5 AQI (converted)
  * **category** – Good / Moderate / Unhealthy, etc.
  * **sites** – List of contributing PurpleAir sensors
* Compatible with **HACS** via Custom Repository
* Minimal configuration required
* Fully asynchronous and efficient

---

### 🟣 Why Use PurpleAir?

PurpleAir sensors provide **hyperlocal, real-time air quality information** directly from devices installed in neighborhoods, rather than centralized government monitoring stations. PurpleAir data is  especially valuable in locations where:

* **Official sensors are too far away** to represent local conditions accurately.
* **Terrain, weather inversions, or microclimates** cause large AQI variations over short distances.
* **Wildfire smoke or pollution events** impact specific areas unevenly, even within a single city.

By sampling from a sensor installed on your own home or nearby monitors, users get **air quality data that reflects the air they are actually breathing**, not regional averages.


### 🔵 Why Average Among Multiple Sensors?

Indoor and outdoor conditions can differ significantly, as can readings between nearby outdoor monitors. Supporting multiple sensors allows PurpleAir AQI to:

* **Improve accuracy through redundancy.** A single sensor may temporarily read high or low due to wind direction, cleaning activity, hardware contamination, or obstruction.
* **Differentiate indoor vs. outdoor conditions**, which is useful for:

  * air purifiers
  * ventilation control
  * windows/doors automation
  * alerts when outdoor air becomes unhealthy
* **Automatically choose or combine the best inputs** instead of trusting a single device that may be impacted by localized conditions.

In short: **multiple sensors = more reliable automation and healthier decisions.**

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
6. Choose **PurpleAir**

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

Latitude and longitude remain fixed after initial setup. Changing the location requires removing and re-adding the integration.

---

## 🧪 Entity Provided

| Entity                 | Type   | Description                                |
| ---------------------- | ------ | ------------------------------------------ |
| `sensor.purpleair` | Sensor | PM2.5 AQI value, category, and sensor list |

---

## 🔧 Example Usage

Send AQI notifications through Pushover:

```yaml
service: notify.pushover
data:
  title: "Air Quality"
  message: >
    Current AQI: {{ states('sensor.purpleair') }} –
    {{ state_attr('sensor.purpleair', 'category') }}
```

---

## ⏱ Update Interval

This setting controls how frequently the integration requests new data from the PurpleAir API and updates the sensor values inside Home Assistant.

| Interval                           | What It Means    | Impact                                         |
| ---------------------------------- | ---------------- | ---------------------------------------------- |
| Short (e.g., **1–5 minutes**)      | Frequent updates | More API usage; more current AQI               |
| Moderate (e.g., **10–15 minutes**) | Balanced updates | Recommended for most users                     |
| Long (e.g., **30–60 minutes**)     | Fewer updates    | Lowest API use; slower to react to air changes |

### 📌 Recommendation

> For most users, **10 minutes** provides a good balance between responsiveness and API efficiency.

### ⚠ Notes

* Shorter intervals **do not improve sensor accuracy**, only responsiveness.
* If you are monitoring **wildfire smoke or rapid AQI changes**, consider **5–10 minutes**.
* If you have **many PurpleAir sensors** configured, longer intervals help reduce API load.
* The interval only affects **data refresh**, not how often the UI redraws.

---

## 🌫 PM₂.₅ Conversion Formulas Explained
*For most outdoor use, **US EPA** is recommended unless you live in a wildfire-heavy region.*


| Formula       | Best For                       | Description / Source                                                                                                                      |
| ------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **US EPA**    | Most users                     | Official U.S. EPA correction for PurpleAir data. Adjusts for humidity and general outdoor conditions. Based on multi-site national study. |
| **Woodsmoke** | Wildfire areas                 | Optimized for particles from wildfire smoke, pellets, and wood burning. Often used in Western U.S.                                        |
| **AQ&U**      | Mountain/valley regions (Utah) | Used by the Utah Dept. of Environmental Quality for inversion-prone areas. Works well in high-elevation, dry climates.                    |
| **LRAPA**     | Very humid climates            | Developed by Lane Regional Air Protection Agency (Oregon). Reduces over-reporting of PM₂.₅ caused by humidity swelling tiny particles.    |
| **CF = 1**    | Indoor sensors                 | A factory “no-correction/wet” value. High-bias outdoors, but suitable indoors (no humidity correction needed).                            |
| **None**      | Raw data use                   | Reports the uncorrected sensor value exactly as measured. Most users shouldn’t choose this. Used for research or custom processing.       |


---

### 🔑 API Key Notes
Your API key is stored securely by Home Assistant.  
No YAML or secrets file configuration is required.

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
