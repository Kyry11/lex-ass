"""Common entity helpers for Lexus Connected AU."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import LexusAUCoordinator


class LexusAUEntity(CoordinatorEntity[LexusAUCoordinator]):
    """Base Lexus Connected AU entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: LexusAUCoordinator, unique_key: str) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{unique_key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return Home Assistant device metadata."""
        snapshot = self.coordinator.data
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.client.vin)},
            manufacturer=MANUFACTURER,
            model=snapshot.vehicle.model_name,
            name=snapshot.vehicle.display_name,
            serial_number=self.coordinator.client.vin,
        )
