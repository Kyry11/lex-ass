"""Lock platform for Lexus Connected AU."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
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
    """Set up Lexus vehicle lock entities."""
    coordinator: LexusAUCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LexusAUVehicleLock(coordinator)])


class LexusAUVehicleLock(LexusAUEntity, LockEntity):
    """Represents the vehicle's remote lock/unlock capability."""

    _attr_translation_key = "vehicle_lock"

    def __init__(self, coordinator: LexusAUCoordinator) -> None:
        """Initialize the vehicle lock entity."""
        super().__init__(coordinator, "vehicle_lock")

    @property
    def is_locked(self) -> bool | None:
        """Return lock state from the latest coordinator snapshot."""
        status = self.coordinator.data.status
        if status.all_doors_locked is not None:
            return status.all_doors_locked
        return status.driver_door_locked

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the vehicle."""
        await self.coordinator.async_lock_doors()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the vehicle."""
        await self.coordinator.async_unlock_doors()
