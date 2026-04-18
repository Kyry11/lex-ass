"""Sensor entities for Lexus Connected AU."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LexusAUCoordinator
from .entity import LexusAUEntity


@dataclass(frozen=True, kw_only=True)
class LexusAUSensorDescription(SensorEntityDescription):
    """Description of a Lexus AU status sensor."""

    value_attr: str
    unit_attr: str | None = None


SENSORS: tuple[LexusAUSensorDescription, ...] = (
    LexusAUSensorDescription(
        key="last_vehicle_update",
        translation_key="last_vehicle_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_attr="last_vehicle_update",
    ),
    LexusAUSensorDescription(
        key="fuel_level",
        translation_key="fuel_level",
        icon="mdi:gas-station",
        native_unit_of_measurement=PERCENTAGE,
        value_attr="fuel_level",
    ),
    LexusAUSensorDescription(
        key="distance_to_empty",
        translation_key="distance_to_empty",
        icon="mdi:map-marker-distance",
        value_attr="distance_to_empty",
        unit_attr="distance_to_empty_unit",
    ),
    LexusAUSensorDescription(
        key="odometer",
        translation_key="odometer",
        icon="mdi:counter",
        value_attr="odometer",
        unit_attr="odometer_unit",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lexus AU status sensors."""
    coordinator: LexusAUCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        LexusAUSensor(coordinator, description) for description in SENSORS
    )


class LexusAUSensor(LexusAUEntity, SensorEntity):
    """A sensor derived from the current Lexus AU status snapshot."""

    entity_description: LexusAUSensorDescription

    def __init__(
        self,
        coordinator: LexusAUCoordinator,
        description: LexusAUSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        return getattr(self.coordinator.data.status, self.entity_description.value_attr)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return a dynamic unit when the payload provides one."""
        if self.entity_description.unit_attr is None:
            return super().native_unit_of_measurement
        return getattr(self.coordinator.data.status, self.entity_description.unit_attr)
