# Implementation Plan

## Delivery Strategy

Implement this in four layers:

1. Reverse-engineer the Lexus Australia app/backend.
2. Build a standalone Python client with fixtures and tests.
3. Wrap that client in a Home Assistant custom integration.
4. Harden the integration on the real vehicle before deciding whether anything should be shared publicly.

## Phase 0: Confirm Inputs

Goal: remove the few unknowns that materially affect the first sprint.

Confirmed:

- daily phone: iPhone
- you do not want to dedicate the phone to constant integration use
- Home Assistant install type: HA OS
- you are willing to use an emulator if needed
- the iOS Lexus app is already installed on an Apple Silicon Mac, which is the preferred interception host
- V1 command scope: `lock/unlock`, `engine start/stop`, `hazard flash`

Still useful to confirm before implementation:

- whether you control one Lexus account / one vehicle or more than one
- whether the Remote Connect subscription is currently active and all three V1 commands work in the Lexus app today

Output:

- one-page setup note with the actual target environment

## Phase 1: Stand Up The Research Workspace

Goal: prepare tools and reference code before intercepting anything.

Tasks:

- clone or vendor the reference projects locally:
  - `pytoyoda/pytoyoda`
  - `pytoyoda/ha_toyota`
  - `widewing/ha-toyota-na`
- create a local scratch area for:
  - sanitized HTTP captures
  - decoded JSON fixtures
  - endpoint notes
  - replay scripts
- decide whether the repo will contain:
  - a separate client package like `pylexus_au`
  - or an internal client under `custom_components/lexus_au/api`

Recommendation:

- start with an internal client
- split it into a standalone package only after the endpoint model stabilizes

Output:

- repo skeleton and scratch directories

## Phase 2: Reverse-Engineer The Lexus AU API

Goal: identify the auth flow, headers, endpoints, and command semantics used by the Lexus Connected AU app.

### 2.1 Static Analysis

Recommended tools:

- `jadx`
- `apktool`
- `strings`
- `rg`

Tasks:

- inspect the Android APK if available
- extract:
  - base URLs / hostnames
  - certificate pins
  - GraphQL or REST route strings
  - header names
  - app version headers
  - package name and redirect URIs
- compare discovered auth flow with EU `oneapp` and NA patterns

Why Android may still be useful:

- static inspection is easier
- TLS interception work is usually easier than on iOS

Why Mac-first is now preferred for you:

- it avoids repurposing your daily phone
- it lets you inspect the exact app/account behavior you already use
- if the macOS networking path is transparent enough, it reduces setup time

### 2.2 Traffic Interception

Recommended tools:

- `mitmproxy` or HTTP Toolkit
- Burp Suite if you prefer it
- Frida / Objection if certificate pinning blocks passive proxying

Recommended order for your environment:

1. intercept the Apple Silicon Mac traffic from the iOS Lexus app
2. if the app uses pinning or the traffic path is awkward on macOS, switch to Android emulator capture
3. only use a physical iPhone if both of the above are blocked and the value is high enough

Capture these flows:

- app login
- account bootstrap
- vehicle list
- vehicle status refresh
- location request
- door lock
- door unlock
- engine start
- engine stop
- hazard flash
- climate on/off only if it is adjacent to the same command family

For each captured request, record:

- method
- URL/path
- headers
- body schema
- auth token source
- response schema
- success and failure payloads
- whether the command is synchronous or job-based

### 2.3 Endpoint Catalog

Create a sanitized catalog with:

- auth endpoints
- token refresh flow
- vehicle discovery endpoints
- read-state endpoints
- command endpoints
- polling-friendly vs command-only endpoints
- required headers
- inferred brand/region constants

### 2.4 Decision Gate

Proceed if:

- auth can be replayed reliably outside the app
- at least one mutating command can be replayed
- command failure modes are understandable enough to surface in Home Assistant

Fallback if blocked:

- if API replay is blocked by attestation/pinning you cannot practically bypass, pivot to a shortcut bridge or UI automation bridge while continuing research in parallel

Output:

- sanitized endpoint catalog
- sample fixtures
- proof-of-concept replay script

## Phase 3: Build The Python Client

Goal: create a stable Lexus AU client with clean models and replayable tests.

Suggested module layout:

```text
lexus_au/
  auth.py
  client.py
  models.py
  commands.py
  exceptions.py
  redact.py
```

Capabilities for V1:

- login
- token refresh
- vehicle discovery
- fetch current status
- fetch location
- lock / unlock
- engine start / stop
- hazard flash
- manual refresh

Recommended implementation details:

- `httpx` async client
- typed response models
- one central request method
- redaction helpers for logs/fixtures
- backoff on transient 5xx or timeout failures
- no blind retries on mutating commands

Tests:

- fixture-based unit tests for parsing
- mocked integration tests for auth/session refresh
- one or two opt-in live tests you can run manually against your own account

Output:

- working client library with fixtures and tests

## Phase 4: Build The Home Assistant Integration

Goal: expose the Lexus AU client cleanly inside Home Assistant.

Suggested layout:

```text
custom_components/lexus_au/
  __init__.py
  manifest.json
  const.py
  config_flow.py
  coordinator.py
  entity.py
  sensor.py
  binary_sensor.py
  device_tracker.py
  lock.py
  button.py
  services.yaml
  strings.json
```

Implementation details:

- `config_flow.py` for username/password and optional brand/region debug settings
- `DataUpdateCoordinator` for periodic refresh
- separate coordinator or throttled tasks for slow data like trips/history
- Home Assistant services for mutating commands
- diagnostics support with aggressive redaction

Recommended V1 Home Assistant surface:

- sensors: odometer, fuel level/range, last update
- binary sensors: doors, locks, windows, hood/trunk if available
- device tracker: location
- lock: vehicle lock state if the API supports reliable lock-state refresh
- buttons/services:
  - refresh
  - engine start
  - engine stop
  - hazard flash
  - optional climate commands only if they are trivial once the core command path is working

Important design choice:

- do not model engine/climate as optimistic `switch` entities until you confirm the AU API returns timely and trustworthy command status

Output:

- installable custom integration in your HA instance

## Phase 5: Real-Car Validation

Goal: validate behavior against the actual RX500h safely.

Test matrix:

- login after Home Assistant restart
- token refresh after idle period
- lock from Home Assistant
- unlock from Home Assistant
- engine start when the car is in a valid state
- engine stop
- hazard flash
- refresh after command
- stale/timeout behavior when the car has poor coverage

Safety rules:

- test mutating commands with the car parked in a safe open area
- do not automate engine start until command semantics are fully understood
- add a cooldown to prevent repeated lock/start commands from automations

Output:

- validated command matrix with known limitations

## Phase 6: Hardening

Goal: make the integration maintainable.

Tasks:

- improve error messages and re-auth flow
- add structured diagnostics
- add command cooldowns and duplicate-command suppression
- document known Lexus backend quirks
- optionally add notification entities/history if the API makes them cheap to fetch

Optional later work:

- trip history entities
- dashboards
- Assist / voice integration
- geofence-based automations
- multi-vehicle support

## Practical Timeline

Realistic first-pass effort if the API is replayable:

- Phase 0-2: 1 to 3 focused sessions
- Phase 3: 1 to 2 sessions
- Phase 4: 1 to 2 sessions
- Phase 5-6: 1 to 2 sessions

If TLS pinning or attestation is heavy, the reverse-engineering phase becomes the dominant effort.

## First Sprint Recommendation

Do this first:

1. Confirm phone platform and Home Assistant environment.
2. Intercept the Apple Silicon Mac traffic from the Lexus iOS app.
3. Capture one successful status request and one successful `lock` or `unlock` command.
4. Replay both outside the app.
5. Capture and replay `engine start/stop` and `hazard flash`.
6. Only then start the Home Assistant component.

That sequence avoids spending time on Home Assistant scaffolding before you know the AU backend is scriptable.

## Source Notes

- Lexus AU app/features:
  https://www.lexus.com.au/owners/apps/lexus-connected-app
- Lexus AU connected-services terms:
  https://www.lexus.com.au/smallprint/connected-services-terms
- Toyota EU Home Assistant integration:
  https://github.com/pytoyoda/ha_toyota
- Toyota EU Python client:
  https://github.com/pytoyoda/pytoyoda
- Toyota NA Home Assistant integration:
  https://github.com/widewing/ha-toyota-na
- Pushcut Automation Server docs:
  https://www.pushcut.io/support/automation-server
