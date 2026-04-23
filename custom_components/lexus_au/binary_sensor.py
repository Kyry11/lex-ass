"""Binary sensor entities for Lexus Connected AU."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LexusAUCoordinator
from .entity import LexusAUEntity


@dataclass(frozen=True, kw_only=True)
class LexusAUBinarySensorDescription(BinarySensorEntityDescription):
    """Description of a Lexus AU binary sensor."""

    opening_keys: tuple[str, ...]


BINARY_SENSORS: tuple[LexusAUBinarySensorDescription, ...] = (
    LexusAUBinarySensorDescription(
        key="driver_side_door",
        translation_key="driver_side_door",
        device_class=BinarySensorDeviceClass.DOOR,
        opening_keys=("driver_side_door",),
    ),
    LexusAUBinarySensorDescription(
        key="passenger_side_door",
        translation_key="passenger_side_door",
        device_class=BinarySensorDeviceClass.DOOR,
        opening_keys=("passenger_side_door",),
    ),
    LexusAUBinarySensorDescription(
        key="rear_driver_side_door",
        translation_key="rear_driver_side_door",
        device_class=BinarySensorDeviceClass.DOOR,
        opening_keys=("rear_driver_side_door",),
    ),
    LexusAUBinarySensorDescription(
        key="rear_passenger_side_door",
        translation_key="rear_passenger_side_door",
        device_class=BinarySensorDeviceClass.DOOR,
        opening_keys=("rear_passenger_side_door",),
    ),
    LexusAUBinarySensorDescription(
        key="driver_side_window",
        translation_key="driver_side_window",
        device_class=BinarySensorDeviceClass.WINDOW,
        opening_keys=("driver_side_window",),
    ),
    LexusAUBinarySensorDescription(
        key="passenger_side_window",
        translation_key="passenger_side_window",
        device_class=BinarySensorDeviceClass.WINDOW,
        opening_keys=("passenger_side_window",),
    ),
    LexusAUBinarySensorDescription(
        key="rear_driver_side_window",
        translation_key="rear_driver_side_window",
        device_class=BinarySensorDeviceClass.WINDOW,
        opening_keys=("rear_driver_side_window",),
    ),
    LexusAUBinarySensorDescription(
        key="rear_passenger_side_window",
        translation_key="rear_passenger_side_window",
        device_class=BinarySensorDeviceClass.WINDOW,
        opening_keys=("rear_passenger_side_window",),
    ),
    LexusAUBinarySensorDescription(
        key="boot",
        translation_key="boot",
        device_class=BinarySensorDeviceClass.DOOR,
        opening_keys=("hatch", "trunk"),
    ),
    LexusAUBinarySensorDescription(
        key="bonnet",
        translation_key="bonnet",
        device_class=BinarySensorDeviceClass.OPENING,
        opening_keys=("bonnet",),
    ),
    LexusAUBinarySensorDescription(
        key="moonroof",
        translation_key="moonroof",
        device_class=BinarySensorDeviceClass.OPENING,
        opening_keys=("moonroof",),
    ),
)

ENGINE_BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="engine_running",
        translation_key="engine_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:engine-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lexus AU binary sensors."""
    coordinator: LexusAUCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            *(
                LexusAUBinarySensor(coordinator, description)
                for description in BINARY_SENSORS
            ),
            *(
                LexusAUEngineRunningBinarySensor(coordinator, description)
                for description in ENGINE_BINARY_SENSORS
            ),
        ]
    )


class LexusAUBinarySensor(LexusAUEntity, BinarySensorEntity):
    """Binary sensor derived from the current Lexus AU status snapshot."""

    entity_description: LexusAUBinarySensorDescription

    def __init__(
        self,
        coordinator: LexusAUCoordinator,
        description: LexusAUBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true when the opening is open."""
        status = self.coordinator.data.status
        for opening_key in self.entity_description.opening_keys:
            opening_state = status.door_states.get(opening_key)
            if opening_state is None or opening_state.closed is None:
                continue
            return opening_state.closed is False
        return None


class LexusAUEngineRunningBinarySensor(LexusAUEntity, BinarySensorEntity):
    """Binary sensor derived from the current remote engine status."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: LexusAUCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true when remote engine status reports running."""
        return self.coordinator.data.status.engine_running
