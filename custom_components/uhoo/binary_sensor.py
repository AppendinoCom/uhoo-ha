"""Binary sensor platform for uHoo Air Quality integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES
from .coordinator import UhooDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up uHoo binary sensors from a config entry."""
    coordinator: UhooDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[UhooIsGreenBinarySensor] = []
    for device_idx, device in enumerate(coordinator.data):
        for sensor_key, sensor_cfg in SENSOR_TYPES.items():
            if sensor_key in device["sensors"]:
                entities.append(
                    UhooIsGreenBinarySensor(coordinator, device_idx, sensor_key, sensor_cfg)
                )

    async_add_entities(entities)


class UhooIsGreenBinarySensor(
    CoordinatorEntity[UhooDataUpdateCoordinator],
    BinarySensorEntity,
):
    """Binary helper entity: ON when sensor color is green."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:check-circle-outline"

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

        self._attr_unique_id = f"uhoo_{serial}_{sensor_key}_is_green"
        self._attr_name = f"{sensor_cfg['name']} Is Green"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=device["name"],
            manufacturer="uHoo",
            model="uHoo Indoor Air Quality Sensor",
        )

    @property
    def _device(self) -> dict:
        """Return current device payload from coordinator."""
        return self.coordinator.data[self._device_idx]

    @property
    def is_on(self) -> bool:
        sensor_data = self._device["sensors"].get(self._sensor_key, {})
        return str(sensor_data.get("color", "")).lower() == "green"

    @property
    def extra_state_attributes(self) -> dict:
        sensor_data = self._device["sensors"].get(self._sensor_key, {})
        color = sensor_data.get("color")
        device = self._device
        return {
            "color": color,
            "serial_number": device.get("serialNumber"),
            "last_update_iso": device.get("last_update_iso"),
            "last_update_timestamp": device.get("last_update_timestamp"),
        }
