# Protocol Findings (2026-04-18)

Source analyzed:

- [debug-experiments/index.js](/Users/kyryll/Repos/Lexus/debug-experiments/index.js)

## Executive Summary

The Lexus Australia backend is replayable outside the app.

The captured script proves:

- the login flow is standard OAuth2/OIDC with PKCE and app-specific pre-auth callbacks
- a bearer token from that flow is accepted by the AU telematics backend
- the telematics backend supports read operations and remote commands over HTTPS
- `door-lock` and `door-unlock` commands are already reproducible

This is enough evidence to proceed with a real client and Home Assistant integration.

## Immediate Security Note

The experiment file currently contains highly sensitive material in plaintext:

- account email
- account password
- VIN
- device identifier
- API keys
- live bearer-session context after execution

Before this repo is shared or synced anywhere, those values should be rotated or removed.

## Discovered Hostnames

Authentication:

- `login.lexusdriverslogin.com.au`
- `openidm.lexusdriverslogin.com.au`

Telematics API:

- `tmca-oneapi.telematicsct.com.au`

## Discovered Auth Flow

### Step 1

POST:

- `https://login.lexusdriverslogin.com.au/json/realms/tmca/authenticate?authIndexType=service&authIndexValue=oneapp`

Result:

- returns `authId`

### Step 2

POST same endpoint with username callback payload.

Result:

- returns next `authId`

### Step 3

POST same endpoint with password callback payload.

Result:

- returns `tokenId`

### Step 4

GET authorize endpoint:

- `https://login.lexusdriverslogin.com.au/oauth2/realms/root/realms/tmca/authorize?...`

Important details:

- `client_id=oneapp`
- `redirect_uri=com.toyota.oneapp:/oauth2Callback`
- `code_challenge_method=S256`
- cookie jar/session from the earlier auth steps is required
- redirect must be handled manually to extract the authorization code from `Location`

### Step 5

POST token exchange:

- `https://login.lexusdriverslogin.com.au/oauth2/realms/root/realms/tmca/access_token`

Important details:

- `Authorization: Basic b25lYXBwOm9uZWFwcA==`
- grant type: authorization code
- PKCE verifier required

Observed result fields:

- `access_token`
- `id_token`
- `refresh_token`

### Step 6

POST OpenIDM password check:

- `https://openidm.lexusdriverslogin.com.au/openidm/endpoint/passwordService?_action=checkPassword`

Important details:

- `Authorization` is the raw access token, not `Bearer ...`
- anonymous OpenIDM headers are required

Status:

- observed in the app flow
- not yet proven necessary for long-term client operation

## Identity Fields

The script derives `sub` from the access token and then uses it as:

- `X-Guid`
- `GUID` in the device registration body
- `guid` in refresh requests

This is an important AU-specific detail because the EU reference implementation often centers around a decoded `uuid`.

## Discovered Telematics Endpoints

### Device registration / status

POST:

- `/v1/notification/device/status`

Observed special case:

- this call includes both `Api_key` and `X-Api-Key`

### Vehicle settings / vehicle discovery

GET:

- `/v2/vehicle/guid`

This likely returns or helps derive vehicle capability metadata.

### Last known remote state

GET:

- `/v1/global/remote/status`

### Force status refresh from vehicle

POST:

- `/v1/global/remote/refresh-status`

Body:

- `guid`
- `vin`
- `deviceId`
- `deviceType`

### Remote command endpoint

POST:

- `/v1/global/remote/command`

Confirmed commands:

- `door-lock` with `value: 1`
- `door-unlock` with `value: 2`

## Common Request Headers

Across telematics requests the following appear important:

- `Authorization: Bearer <access_token>`
- `X-Guid: <sub>`
- `Vin: <vin>` on vehicle-scoped calls
- `X-Api-Key`
- `X-Channel: ONEAPP`
- `X-Appbrand: L`
- `X-Brand: L`
- `X-Osname: iPadOS`
- `X-Osversion`
- `X-Appversion`
- `X-Locale: en-AU`
- `X-Device-Timezone: AEST`
- Lexus mobile `User-Agent`

## Useful Implementation Conclusions

### Good news

- We do not need to guess the AU auth domain anymore.
- We do not need to guess the remote command endpoint anymore.
- We already have enough data to start a real auth client plus lock/unlock support.

### What should be treated as debug noise

- manually setting `Content-Length`
- mixing promise chains and global mutable state
- running through an unauthenticated local Express server
- hardcoded credentials and identifiers

## Gaps Still To Capture

- refresh-token grant flow
- engine start command
- engine stop command
- hazard flash command
- command completion semantics:
  - immediate acknowledgement payload
  - follow-up polling behavior
  - failure payloads
- token expiry behavior
- whether device registration is required on every session or only once per device

## Known Issues In The Current Experiment

### Missing `device_id` in `/register`

The route calls `registerDevice()` without passing the `device_id` argument even though the function signature expects it.

Relevant code:

- [debug-experiments/index.js:369](/Users/kyryll/Repos/Lexus/debug-experiments/index.js:369)
- [debug-experiments/index.js:631](/Users/kyryll/Repos/Lexus/debug-experiments/index.js:631)

### No token refresh support

The script captures `refresh_token` but does not use it.

Relevant code:

- [debug-experiments/index.js:25](/Users/kyryll/Repos/Lexus/debug-experiments/index.js:25)

### Unauthenticated local command surface

The Express routes expose remote vehicle actions with no access control.

Relevant code:

- [debug-experiments/index.js:622](/Users/kyryll/Repos/Lexus/debug-experiments/index.js:622)

## Recommended Next Step

Do not build the Home Assistant integration directly on top of this script.

Instead:

1. extract a small AU client module from the confirmed protocol
2. replace hardcoded secrets with environment variables or a local config file excluded from sync
3. capture `engine start/stop` and `hazard flash`
4. capture the refresh-token exchange
5. only then wrap the client in `custom_components/lexus_au`
