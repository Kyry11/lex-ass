"""Switch platform for Lexus Connected AU."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Lexus vehicle switch entities."""
    coordinator: LexusAUCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LexusAUVehicleEngineSwitch(coordinator)])


class LexusAUVehicleEngineSwitch(LexusAUEntity, SwitchEntity):
    """Represents the vehicle's remote engine start/stop capability."""

    _attr_translation_key = "vehicle_engine"

    def __init__(self, coordinator: LexusAUCoordinator) -> None:
        """Initialize the vehicle engine switch."""
        super().__init__(coordinator, "vehicle_engine")

    @property
    def is_on(self) -> bool | None:
        """Return engine state from the latest coordinator snapshot."""
        return self.coordinator.data.status.engine_running

    @property
    def icon(self) -> str:
        """Return an icon reflecting the current engine state."""
        if self.is_on is True:
            return "mdi:engine"
        return "mdi:engine-off"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the vehicle engine."""
        await self.coordinator.async_engine_start()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the vehicle engine."""
        await self.coordinator.async_engine_stop()
