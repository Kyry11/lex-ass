"""Device tracker entity for Lexus Connected AU."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import LexusAUCoordinator
from .entity import LexusAUEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lexus AU vehicle location tracker."""
    coordinator: LexusAUCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LexusAULocationTracker(coordinator)])


class LexusAULocationTracker(LexusAUEntity, TrackerEntity):
    """Track the vehicle's last known Lexus Connected AU location."""

    _attr_icon = "mdi:car-connected"
    _attr_source_type = SourceType.GPS
    _attr_translation_key = "vehicle_location"

    def __init__(self, coordinator: LexusAUCoordinator) -> None:
        """Initialize the location tracker."""
        super().__init__(coordinator, "vehicle_location")

    @property
    def latitude(self) -> float | None:
        """Return the last known vehicle latitude."""
        return self.coordinator.data.status.latitude

    @property
    def longitude(self) -> float | None:
        """Return the last known vehicle longitude."""
        return self.coordinator.data.status.longitude

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful location metadata."""
        status = self.coordinator.data.status
        attrs: dict[str, Any] = {
            "location_updated_at": status.location_updated_at,
            "last_vehicle_update": status.last_vehicle_update,
        }
        if status.location_display_name:
            attrs["location_display_name"] = status.location_display_name
        return attrs
