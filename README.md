# uHoo Air Quality – Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/AppendinoCom/uhoo-ha.svg)](https://github.com/AppendinoCom/uhoo-ha/releases)

Custom integration for [Home Assistant](https://www.home-assistant.io/) that pulls real-time air quality data from a **uHoo** indoor air quality sensor via the official (reverse-engineered) uHoo mobile API.

---

## Sensors

Each uHoo device exposes the following sensor entities:

| Sensor | Unit | HA Device Class |
|---|---|---|
| Temperature | °C | `temperature` |
| Humidity | % | `humidity` |
| Air Pressure | hPa | `atmospheric_pressure` |
| TVOC | ppb | `volatile_organic_compounds_parts` |
| CO₂ | ppm | `carbon_dioxide` |
| CO | ppm | `carbon_monoxide` |
| Ozone | ppb | `ozone` |
| NO₂ | ppb | `nitrogen_dioxide` |
| PM2.5 | µg/m³ | `pm25` |

Every sensor also exposes these **extra attributes** useful for automations:

| Attribute | Description |
|---|---|
| `color` | uHoo quality rating: `green`, `yellow`, `orange`, `red` |
| `color_dot` | Visual dot for dashboards: `🟢`, `🟡`, `🟠`, `🔴` |
| `color_with_dot` | Combined visual value, for example `🟢 green` |
| `serial_number` | Device serial number |
| `last_update_iso` | ISO 8601 timestamp of last sensor reading |
| `last_update_timestamp` | Unix timestamp of last sensor reading |

The integration also creates companion color entities for each metric.
Example: `sensor.sensorik_vzduchu_temperature_color` with state `🟢 green`.

---

## Requirements

- Home Assistant **2023.3** or newer
- A **uHoo** account with at least one registered device
- The **Android ID** of the Android device that has the uHoo app installed

### Getting your Android ID

```bash
adb shell settings get secure android_id
```

Or check in **Settings → About Phone → Status** on the device.

---

## Installation

### Via HACS (recommended)

1. In Home Assistant, open **HACS → Integrations**.
2. Click the three-dot menu → **Custom repositories**.
3. Add `https://github.com/AppendinoCom/uhoo-ha` as an **Integration**.
4. Search for **uHoo Air Quality** and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/uhoo` folder into your HA `config/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **uHoo Air Quality**.
3. Enter your **Email**, **Password**, and **Android ID**.
4. Click **Submit**. The integration will authenticate against the uHoo API and create all sensor entities automatically.

Data is refreshed every **60 seconds**.

---

## Automation example

```yaml
automation:
  - alias: "Alert when CO₂ is not green"
    trigger:
      - platform: state
        entity_id: sensor.sensorik_vzduchu_co2
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.sensorik_vzduchu_co2', 'color') != 'green' }}"
    action:
      - service: notify.mobile_app
        data:
          message: "CO₂ level: {{ states('sensor.sensorik_vzduchu_co2') }} ppm ({{ state_attr('sensor.sensorik_vzduchu_co2', 'color') }})"
```

---

## Troubleshooting

- **Cannot connect** – Double-check your email, password, and Android ID. The Android ID must match the device that was used to register/log in to the uHoo app.
- **No entities after setup** – Check HA logs (`Settings → System → Logs`) for errors from the `uhoo` integration.
- **Data stops updating** – The integration reauthenticates on every poll. If your password changed, remove and re-add the integration.

---

## License

MIT – see [LICENSE](LICENSE).
