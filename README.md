```markdown
# PurpleAir AQI for Home Assistant

This custom integration provides a single AQI sensor using PurpleAir data,
including multi-sensor averaging, category reporting, and conversion options.

## Installation (via HACS)
1. In Home Assistant, go to HACS > Integrations > Custom repositories
2. Add this repo:
```

[https://github.com/TheMegamind/purple_air](https://github.com/TheMegamind/purple_air)

```
3. Select category: **Integration**
4. Install **PurpleAir AQI**
5. Restart Home Assistant
6. Go to **Settings → Devices & services → Add Integration**
7. Select **PurpleAir AQI**

## Features
- Converts to EPA, Woodsmoke, AQ&U, LRAPA or CF=1
- Weighted or unweighted multi-sensor averaging
- Only the AQI sensor you care about (no raw sensors, no humidity entities)
```

---

## 🚀 **Adding it to HACS once setup is correct**

In Home Assistant:

1. Open **HACS**
2. Click **Integrations**
3. Click **⋮ (three dots)** → **Custom repositories**
4. Enter:

   ```
   https://github.com/TheMegamind/purple_air
   ```
5. Category: **Integration**
6. Click **Add**
7. Install it!

Once installed, restart HA and add the integration via **Settings → Devices & services**.

---


👉 **Yes Review** or **No Thanks**
