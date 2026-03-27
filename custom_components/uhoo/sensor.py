"""Sensor platform for uHoo Air Quality integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import UhooDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up uHoo sensor entities from a config entry."""
    coordinator: UhooDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[UhooSensor] = []
    for device_idx, device in enumerate(coordinator.data):
        for sensor_key, sensor_cfg in SENSOR_TYPES.items():
            if sensor_key in device["sensors"]:
                entities.append(
                    UhooSensor(coordinator, device_idx, sensor_key, sensor_cfg)
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
        device = self._device
        return {
            "color": sensor_data.get("color"),
            "serial_number": device.get("serialNumber"),
            "last_update_iso": device.get("last_update_iso"),
            "last_update_timestamp": device.get("last_update_timestamp"),
        }
