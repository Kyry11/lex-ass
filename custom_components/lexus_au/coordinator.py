"""Data coordinator for Lexus Connected AU."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from time import monotonic
from typing import Callable

import httpx
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LexusAUAuthError, LexusAUClient, LexusAURequestError, LexusAUSnapshot
from .const import (
    COMMAND_CONFIRMATION_POLL_INTERVAL_SECONDS,
    COMMAND_CONFIRMATION_TIMEOUT_SECONDS,
    CONF_REFRESH_INTERVAL_SECONDS,
    DEFAULT_REFRESH_INTERVAL_SECONDS,
    DOMAIN,
)

LOGGER = logging.getLogger(__name__)

SnapshotPredicate = Callable[[LexusAUSnapshot], bool]


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
        self._command_confirmation_task: asyncio.Task | None = None
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
        await self._async_request_remote_refresh()
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Cancel outstanding background work."""
        await self._async_cancel_command_confirmation_task()

    async def async_lock_doors(self) -> None:
        """Lock the vehicle and confirm the updated state."""
        await self.client.async_lock_doors()
        await self._async_begin_command_confirmation(
            command_name="door lock",
            predicate=_snapshot_is_locked,
        )

    async def async_unlock_doors(self) -> None:
        """Unlock the vehicle and confirm the updated state."""
        await self.client.async_unlock_doors()
        await self._async_begin_command_confirmation(
            command_name="door unlock",
            predicate=_snapshot_is_unlocked,
        )

    async def async_engine_start(self) -> None:
        """Start the vehicle engine using the inferred AU command."""
        await self.client.async_start_engine_inferred()
        await self._async_begin_command_confirmation(
            command_name="engine start",
            predicate=lambda snapshot: snapshot.status.engine_running is True,
        )

    async def async_engine_stop(self) -> None:
        """Stop the vehicle engine using the inferred AU command."""
        await self.client.async_stop_engine_inferred()
        await self._async_begin_command_confirmation(
            command_name="engine stop",
            predicate=lambda snapshot: snapshot.status.engine_running is False,
        )

    async def async_flash_hazards(self) -> None:
        """Flash hazards using the confirmed command sequence."""
        await self.client.async_flash_hazards()
        await self.async_refresh_vehicle()

    async def _async_request_remote_refresh(self) -> None:
        """Request that the vehicle upload fresh state."""
        try:
            await self.client.async_refresh_remote_status()
        except LexusAURequestError as err:
            LOGGER.debug("Vehicle refresh request failed: %s", err)

    async def _async_begin_command_confirmation(
        self,
        *,
        command_name: str,
        predicate: SnapshotPredicate,
    ) -> None:
        """Run an immediate refresh, then keep polling briefly until the state matches."""
        await self._async_cancel_command_confirmation_task()
        await self.async_refresh_vehicle()

        if self.data is not None and predicate(self.data):
            LOGGER.debug("%s confirmed on immediate refresh", command_name)
            return

        LOGGER.debug(
            "Starting command confirmation polling for %s every %ss for up to %ss",
            command_name,
            COMMAND_CONFIRMATION_POLL_INTERVAL_SECONDS,
            COMMAND_CONFIRMATION_TIMEOUT_SECONDS,
        )
        self._command_confirmation_task = self.hass.async_create_task(
            self._async_command_confirmation_loop(
                command_name=command_name,
                predicate=predicate,
            )
        )

    async def _async_command_confirmation_loop(
        self,
        *,
        command_name: str,
        predicate: SnapshotPredicate,
    ) -> None:
        """Perform short-lived faster polling while waiting for a command result."""
        deadline = monotonic() + COMMAND_CONFIRMATION_TIMEOUT_SECONDS
        try:
            while monotonic() < deadline:
                await asyncio.sleep(COMMAND_CONFIRMATION_POLL_INTERVAL_SECONDS)
                await self.async_refresh_vehicle()

                if self.data is not None and predicate(self.data):
                    LOGGER.debug("%s confirmed during command confirmation polling", command_name)
                    return

            LOGGER.debug("%s confirmation polling timed out", command_name)
        except asyncio.CancelledError:
            LOGGER.debug("%s confirmation polling cancelled", command_name)
            raise
        except (LexusAURequestError, httpx.HTTPError, UpdateFailed) as err:
            LOGGER.debug("%s confirmation polling failed: %s", command_name, err)
        finally:
            if self._command_confirmation_task is asyncio.current_task():
                self._command_confirmation_task = None

    async def _async_cancel_command_confirmation_task(self) -> None:
        """Cancel any existing command-confirmation poller."""
        task = self._command_confirmation_task
        if task is None:
            return

        self._command_confirmation_task = None
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def _snapshot_is_locked(snapshot: LexusAUSnapshot) -> bool:
    """Return true when the current snapshot shows the vehicle locked."""
    status = snapshot.status
    return status.all_doors_locked is True or status.driver_door_locked is True


def _snapshot_is_unlocked(snapshot: LexusAUSnapshot) -> bool:
    """Return true when the current snapshot shows the vehicle unlocked."""
    status = snapshot.status
    if status.all_doors_locked is not None:
        return status.all_doors_locked is False
    return status.driver_door_locked is False
