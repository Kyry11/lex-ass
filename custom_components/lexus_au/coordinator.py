"""Data coordinator for Lexus Connected AU."""

from __future__ import annotations

from datetime import timedelta
import logging

import httpx
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LexusAUAuthError, LexusAUClient, LexusAURequestError, LexusAUSnapshot
from .const import CONF_REFRESH_INTERVAL_SECONDS, DEFAULT_REFRESH_INTERVAL_SECONDS, DOMAIN

LOGGER = logging.getLogger(__name__)


class LexusAUCoordinator(DataUpdateCoordinator[LexusAUSnapshot]):
    """Coordinate Lexus Australia status polling and commands."""

    def __init__(
        self,
        hass,
        entry: ConfigEntry,
        client: LexusAUClient,
    ) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.client = client
        update_interval = timedelta(
            seconds=entry.options.get(
                CONF_REFRESH_INTERVAL_SECONDS,
                DEFAULT_REFRESH_INTERVAL_SECONDS,
            )
        )
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=update_interval,
            always_update=False,
        )

    async def _async_update_data(self) -> LexusAUSnapshot:
        """Fetch the latest vehicle snapshot."""
        try:
            return await self.client.async_get_snapshot()
        except LexusAUAuthError as err:
            raise ConfigEntryAuthFailed from err
        except (LexusAURequestError, httpx.HTTPError) as err:
            raise UpdateFailed(str(err)) from err

    async def async_refresh_vehicle(self) -> None:
        """Request a fresh upload from the vehicle, then refresh coordinator data."""
        try:
            await self.client.async_refresh_remote_status()
        except LexusAURequestError as err:
            LOGGER.debug("Vehicle refresh request failed: %s", err)
        await self.async_request_refresh()

    async def async_lock_doors(self) -> None:
        """Lock the vehicle and refresh state."""
        await self.client.async_lock_doors()
        await self.async_refresh_vehicle()

    async def async_unlock_doors(self) -> None:
        """Unlock the vehicle and refresh state."""
        await self.client.async_unlock_doors()
        await self.async_refresh_vehicle()

    async def async_engine_start(self) -> None:
        """Start the vehicle engine using the inferred AU command."""
        await self.client.async_start_engine_inferred()
        await self.async_refresh_vehicle()

    async def async_engine_stop(self) -> None:
        """Stop the vehicle engine using the inferred AU command."""
        await self.client.async_stop_engine_inferred()
        await self.async_refresh_vehicle()
