"""Constants for the Lexus Connected AU integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "lexus_au"
NAME = "Lexus Connected AU"
MANUFACTURER = "Lexus"

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.LOCK,
    Platform.SENSOR,
]

CONF_DEVICE_ID = "device_id"
CONF_LEXUS_API_KEY = "lexus_api_key"
CONF_LEXUS_X_API_KEY = "lexus_x_api_key"
CONF_ENABLE_EXPERIMENTAL_ENGINE_COMMANDS = "enable_experimental_engine_commands"
CONF_REFRESH_INTERVAL_SECONDS = "refresh_interval_seconds"
CONF_VIN = "vin"

DEFAULT_REFRESH_INTERVAL_SECONDS = 300
MIN_REFRESH_INTERVAL_SECONDS = 60

COMMAND_CONFIRMATION_TIMEOUT_SECONDS = 20
COMMAND_CONFIRMATION_POLL_INTERVAL_SECONDS = 2
