"""Sensor platform for uHoo Air Quality integration."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import UhooDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

COLOR_DOTS = {
    "green": "🟢",
    "yellow": "🟡",
    "orange": "🟠",
    "red": "🔴",
}


def _color_dot(color: str | None) -> str:
    """Return a unicode dot for a uHoo color string."""
    if not color:
        return "⚪"
    return COLOR_DOTS.get(str(color).lower(), "⚪")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up uHoo sensor entities from a config entry."""
    coordinator: UhooDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for device_idx, device in enumerate(coordinator.data):
        entities.append(UhooLastUpdateSensor(coordinator, device_idx))
        for sensor_key, sensor_cfg in SENSOR_TYPES.items():
            if sensor_key in device["sensors"]:
                entities.append(
                    UhooSensor(coordinator, device_idx, sensor_key, sensor_cfg)
                )
                entities.append(
                    UhooColorSensor(coordinator, device_idx, sensor_key, sensor_cfg)
                )

    async_add_entities(entities)


class UhooSensor(CoordinatorEntity[UhooDataUpdateCoordinator], SensorEntity):
    """Represents a single measurement from a uHoo device."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: UhooDataUpdateCoordinator,
        device_idx: int,
        sensor_key: str,
        sensor_cfg: dict,
    ) -> None:
        super().__init__(coordinator)
        self._device_idx = device_idx
        self._sensor_key = sensor_key

        device = coordinator.data[device_idx]
        serial = device["serialNumber"]

        self._attr_unique_id = f"uhoo_{serial}_{sensor_key}"
        self._attr_name = sensor_cfg["name"]
        self._attr_native_unit_of_measurement = sensor_cfg["unit"]
        self._attr_icon = sensor_cfg.get("icon")

        # Map device_class string → SensorDeviceClass enum (graceful fallback)
        dc_str = sensor_cfg.get("device_class")
        try:
            self._attr_device_class = SensorDeviceClass(dc_str) if dc_str else None
        except ValueError:
            _LOGGER.warning("Unknown device class '%s' for sensor '%s'", dc_str, sensor_key)
            self._attr_device_class = None

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=device["name"],
            manufacturer="uHoo",
            model="uHoo Indoor Air Quality Sensor",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _device(self) -> dict:
        """Return the current device data from the coordinator."""
        return self.coordinator.data[self._device_idx]

    # ------------------------------------------------------------------
    # SensorEntity
    # ------------------------------------------------------------------

    @property
    def native_value(self) -> float | int | None:
        sensor_data = self._device["sensors"].get(self._sensor_key)
        if sensor_data:
            return sensor_data.get("value")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Expose color rating + device metadata for automations."""
        sensor_data = self._device["sensors"].get(self._sensor_key, {})
        color = sensor_data.get("color")
        dot = _color_dot(color)
        device = self._device
        return {
            "color": color,
            "color_dot": dot,
            "color_with_dot": f"{dot} {color}" if color else dot,
            "serial_number": device.get("serialNumber"),
            "last_update_iso": device.get("last_update_iso"),
            "last_update_timestamp": device.get("last_update_timestamp"),
        }


class UhooColorSensor(CoordinatorEntity[UhooDataUpdateCoordinator], SensorEntity):
    """Companion sensor that exposes air-quality color as a colored dot."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:circle"

    def __init__(
        self,
        coordinator: UhooDataUpdateCoordinator,
        device_idx: int,
        sensor_key: str,
        sensor_cfg: dict,
    ) -> None:
        super().__init__(coordinator)
        self._device_idx = device_idx
        self._sensor_key = sensor_key

        device = coordinator.data[device_idx]
        serial = device["serialNumber"]

        self._attr_unique_id = f"uhoo_{serial}_{sensor_key}_color"
        self._attr_name = f"{sensor_cfg['name']} Color"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=device["name"],
            manufacturer="uHoo",
            model="uHoo Indoor Air Quality Sensor",
        )

    @property
    def _device(self) -> dict:
        """Return the current device data from the coordinator."""
        return self.coordinator.data[self._device_idx]

    @property
    def native_value(self) -> str:
        sensor_data = self._device["sensors"].get(self._sensor_key, {})
        color = sensor_data.get("color")
        dot = _color_dot(color)
        if color:
            return f"{dot} {color}"
        return dot

    @property
    def extra_state_attributes(self) -> dict:
        sensor_data = self._device["sensors"].get(self._sensor_key, {})
        color = sensor_data.get("color")
        device = self._device
        return {
            "color": color,
            "color_dot": _color_dot(color),
            "serial_number": device.get("serialNumber"),
            "last_update_iso": device.get("last_update_iso"),
            "last_update_timestamp": device.get("last_update_timestamp"),
        }


class UhooLastUpdateSensor(CoordinatorEntity[UhooDataUpdateCoordinator], SensorEntity):
    """Server timestamp of the last data update for a uHoo device."""

    _attr_has_entity_name = True
    _attr_name = "Last Server Update"
    _attr_icon = "mdi:clock-check-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: UhooDataUpdateCoordinator,
        device_idx: int,
    ) -> None:
        super().__init__(coordinator)
        self._device_idx = device_idx
        device = coordinator.data[device_idx]
        serial = device["serialNumber"]

        self._attr_unique_id = f"uhoo_{serial}_last_update"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=device["name"],
            manufacturer="uHoo",
            model="uHoo Indoor Air Quality Sensor",
        )

    @property
    def _device(self) -> dict:
        """Return the current device data from the coordinator."""
        return self.coordinator.data[self._device_idx]

    @property
    def native_value(self) -> datetime | None:
        ts = self._device.get("last_update_timestamp")
        if isinstance(ts, (int, float)):
            return dt_util.utc_from_timestamp(ts)
        return None

    @property
    def extra_state_attributes(self) -> dict:
        device = self._device
        return {
            "last_update_iso": device.get("last_update_iso"),
            "last_update_timestamp": device.get("last_update_timestamp"),
            "serial_number": device.get("serialNumber"),
        }
