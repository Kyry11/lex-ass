# Implementation Status (2026-04-18)

## Added Code

Custom integration scaffold:

- [custom_components/lexus_au/manifest.json](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/manifest.json)
- [custom_components/lexus_au/config_flow.py](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/config_flow.py)
- [custom_components/lexus_au/coordinator.py](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/coordinator.py)
- [custom_components/lexus_au/button.py](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/button.py)
- [custom_components/lexus_au/lock.py](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/lock.py)
- [custom_components/lexus_au/sensor.py](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/sensor.py)

Reusable AU client:

- [custom_components/lexus_au/api/client.py](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/api/client.py)
- [custom_components/lexus_au/api/models.py](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/api/models.py)
- [custom_components/lexus_au/api/const.py](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/api/const.py)

Configuration behavior:

- account credentials, VIN, and app API keys are entered through the Home Assistant config flow
- API keys are no longer hardcoded in the repository

## Implemented With High Confidence

- callback login flow
- PKCE token exchange
- inferred refresh-token grant with full-login fallback
- device registration
- remote status fetch
- remote status refresh
- vehicle lock
- vehicle unlock
- Home Assistant config flow
- Home Assistant manual refresh button
- Home Assistant vehicle lock entity
- Home Assistant status sensors:
  - fuel level
  - distance to empty
  - odometer
  - last vehicle update

## Implemented As Explicitly Experimental

- engine start button
- engine stop button

Current assumption:

- AU uses modern OneApp command names with old-style numeric values
- start: `engine-start` + `value: 1`
- stop: `engine-stop` + `value: 2`

These buttons are hidden behind the integration option:

- `enable_experimental_engine_commands`

## Not Implemented Yet

- hazard flash
- binary sensors for each door/window/opening
- engine status entity
- richer vehicle discovery from `/v2/vehicle/guid`
- diagnostics export
- tests that replay captured sanitized fixtures

## Why Hazard Flash Is Still Missing

The command naming is still ambiguous across regions.

It may be one of:

- `hazard-on` / `hazard-off`
- `find-vehicle`
- another locator-style command

That is the one remaining command family where an AU capture is still justified.

## Practical Next Step

To continue implementation without more protocol work:

1. copy `custom_components/lexus_au` into your HA config directory
2. add the integration in Home Assistant
3. validate login, status, refresh, and lock/unlock
4. only then turn on `enable_experimental_engine_commands`

## Verification Performed

Syntax compilation completed successfully with:

```sh
PYTHONPYCACHEPREFIX=/tmp/lexus-pycache python3 -m compileall custom_components/lexus_au
```
