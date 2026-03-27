"""Constants for the uHoo Air Quality integration."""

DOMAIN = "uhoo"
DEFAULT_SCAN_INTERVAL = 60  # seconds

AUTH_BASE = "https://auth.uhooinc.com"
API_V2 = "https://api.uhooinc.com/v2"
SALT = "@uhooinc.com"

CONF_ANDROID_ID = "android_id"

# Sensor key → (friendly name, unit, device_class string, icon)
SENSOR_TYPES: dict[str, dict] = {
    "temp": {
        "name": "Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
    },
    "humidity": {
        "name": "Humidity",
        "unit": "%",
        "device_class": "humidity",
        "icon": "mdi:water-percent",
    },
    "pressure": {
        "name": "Air Pressure",
        "unit": "hPa",
        "device_class": "atmospheric_pressure",
        "icon": "mdi:gauge",
    },
    "voc": {
        "name": "TVOC",
        "unit": "ppb",
        "device_class": "volatile_organic_compounds_parts",
        "icon": "mdi:air-filter",
    },
    "co2": {
        "name": "CO2",
        "unit": "ppm",
        "device_class": "carbon_dioxide",
        "icon": "mdi:molecule-co2",
    },
    "co": {
        "name": "CO",
        "unit": "ppm",
        "device_class": "carbon_monoxide",
        "icon": "mdi:molecule-co",
    },
    "ozone": {
        "name": "Ozone",
        "unit": "ppb",
        "device_class": "ozone",
        "icon": "mdi:cloud",
    },
    "no2": {
        "name": "NO2",
        "unit": "ppb",
        "device_class": "nitrogen_dioxide",
        "icon": "mdi:smog",
    },
    "dust": {
        "name": "PM2.5",
        "unit": "µg/m³",
        "device_class": "pm25",
        "icon": "mdi:dots-circle",
    },
}
