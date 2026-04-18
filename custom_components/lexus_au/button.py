"""Button entities for Lexus Connected AU."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENABLE_EXPERIMENTAL_ENGINE_COMMANDS, DOMAIN
from .coordinator import LexusAUCoordinator
from .entity import LexusAUEntity


@dataclass(frozen=True, kw_only=True)
class LexusAUButtonDescription(ButtonEntityDescription):
    """Description of a Lexus AU action button."""

    method_name: str


BUTTONS: tuple[LexusAUButtonDescription, ...] = (
    LexusAUButtonDescription(
        key="refresh_vehicle",
        translation_key="refresh_vehicle",
        icon="mdi:refresh",
        method_name="async_refresh_vehicle",
    ),
    LexusAUButtonDescription(
        key="lock_doors",
        translation_key="lock_doors",
        icon="mdi:lock",
        method_name="async_lock_doors",
    ),
    LexusAUButtonDescription(
        key="unlock_doors",
        translation_key="unlock_doors",
        icon="mdi:lock-open-variant",
        method_name="async_unlock_doors",
    ),
)

EXPERIMENTAL_ENGINE_BUTTONS: tuple[LexusAUButtonDescription, ...] = (
    LexusAUButtonDescription(
        key="engine_start",
        translation_key="engine_start",
        icon="mdi:engine-outline",
        method_name="async_engine_start",
    ),
    LexusAUButtonDescription(
        key="engine_stop",
        translation_key="engine_stop",
        icon="mdi:engine-off-outline",
        method_name="async_engine_stop",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities from a config entry."""
    coordinator: LexusAUCoordinator = hass.data[DOMAIN][entry.entry_id]
    descriptions = list(BUTTONS)
    if entry.options.get(CONF_ENABLE_EXPERIMENTAL_ENGINE_COMMANDS, False):
        descriptions.extend(EXPERIMENTAL_ENGINE_BUTTONS)

    async_add_entities(LexusAUButton(coordinator, description) for description in descriptions)


class LexusAUButton(LexusAUEntity, ButtonEntity):
    """A button that triggers a Lexus AU remote action."""

    entity_description: LexusAUButtonDescription

    def __init__(
        self,
        coordinator: LexusAUCoordinator,
        description: LexusAUButtonDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        """Execute the configured coordinator action."""
        await getattr(self.coordinator, self.entity_description.method_name)()
