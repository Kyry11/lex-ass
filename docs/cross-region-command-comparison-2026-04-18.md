# Cross-Region Command Comparison (2026-04-18)

Goal:

- compare the Lexus Australia protocol captured in [debug-experiments/index.js](/Users/kyryll/Repos/Lexus/debug-experiments/index.js)
- against the public Toyota/Lexus integrations for Europe and North America
- decide which missing AU commands can be inferred safely enough to proceed

## Short Conclusion

The AU implementation clearly belongs to the same Toyota/Lexus "OneApp" family as the EU and modern NA integrations.

That is good enough to make a reasonable implementation assumption for:

- `engine-start`
- `engine-stop`

It is not good enough to make a strong assumption for:

- `hazard flash`

Reason:

- AU already matches the shared modern endpoint family and modern command naming
- but AU also diverges from EU and modern NA by adding `value` fields to door commands
- and "hazard flash" is ambiguous: it may map to `hazard-on` / `hazard-off`, or to a different locator-style command such as `find-vehicle`

## Sources Compared

Your AU capture:

- [debug-experiments/index.js](/Users/kyryll/Repos/Lexus/debug-experiments/index.js)

EU reference:

- [pytoyoda/pytoyoda `const.py`](https://github.com/pytoyoda/pytoyoda/blob/main/pytoyoda/const.py)
- [pytoyoda/pytoyoda `api.py`](https://github.com/pytoyoda/pytoyoda/blob/main/pytoyoda/api.py)
- [pytoyoda/pytoyoda `models/endpoints/command.py`](https://github.com/pytoyoda/pytoyoda/blob/main/pytoyoda/models/endpoints/command.py)
- [pytoyoda/pytoyoda `controller.py`](https://github.com/pytoyoda/pytoyoda/blob/main/pytoyoda/controller.py)

NA reference:

- [widewing/ha-toyota-na `patch_client.py`](https://github.com/widewing/ha-toyota-na/blob/master/custom_components/toyota_na/patch_client.py)
- [widewing/ha-toyota-na `patch_seventeen_cy_plus.py`](https://github.com/widewing/ha-toyota-na/blob/master/custom_components/toyota_na/patch_seventeen_cy_plus.py)
- [widewing/ha-toyota-na `patch_seventeen_cy.py`](https://github.com/widewing/ha-toyota-na/blob/master/custom_components/toyota_na/patch_seventeen_cy.py)

## 1. Auth Pattern Comparison

### AU capture

Observed:

- callback-based auth at `login.lexusdriverslogin.com.au`
- OAuth2 authorization-code flow with PKCE `S256`
- `client_id=oneapp`
- `redirect_uri=com.toyota.oneapp:/oauth2Callback`
- token exchange at `/access_token`
- extra OpenIDM password check after token acquisition

### EU reference

The EU library uses the same overall OneApp pattern:

- callback-based login
- `client_id=oneapp`
- same redirect URI
- same `Authorization: Basic b25lYXBwOm9uZWFwcA==` on token exchange
- OAuth token refresh against the same logical access-token endpoint structure

### Assessment

This is a strong match.

The AU auth stack is not something bespoke to Lexus Australia; it is a regionalized OneApp deployment.

## 2. Status / Refresh Endpoint Comparison

### AU capture

Confirmed:

- `GET /v1/global/remote/status`
- `POST /v1/global/remote/refresh-status`
- `POST /v1/global/remote/command`

### NA modern reference

The NA 17CYPLUS code uses the same modern endpoint family:

- `v1/global/remote/status`
- `v1/global/remote/refresh-status`
- `v1/global/remote/command`

### EU reference

The EU library defines the same endpoint family in `const.py`:

- `/v1/global/remote/status`
- `/v1/global/remote/command`
- climate and electric endpoints in the same namespace

### Assessment

This is another strong match.

Your AU backend is clearly in the same modern API family as the public EU and modern NA integrations.

## 3. Header Pattern Comparison

### AU capture

Common headers include:

- `Authorization: Bearer ...`
- `X-Guid`
- `Vin`
- `X-Api-Key`
- `X-Channel: ONEAPP`
- `X-Appbrand: L`
- `X-Brand: L`
- app version / OS / locale headers

### EU reference

The EU controller also uses:

- `authorization: Bearer ...`
- `x-guid`
- `x-channel: ONEAPP`
- `x-brand`
- `x-appbrand` for Lexus
- `x-appversion`
- `x-region`

### NA modern reference

The NA code also uses:

- `Authorization: Bearer ...`
- `X-GUID`
- `X-CHANNEL: ONEAPP`
- `X-BRAND`
- `X-APPBRAND`
- app version / OS / locale headers

### Assessment

Strong match again.

The header contract is region-specific in values, but not in shape.

## 4. Command Body Comparison

This is the most important section.

### AU capture

Confirmed working:

- `POST /v1/global/remote/command`
- body for lock:
  - `{ "command": "door-lock", "value": 1 }`
- body for unlock:
  - `{ "command": "door-unlock", "value": 2 }`

### EU reference

The EU command model defines these modern string commands:

- `door-lock`
- `door-unlock`
- `engine-start`
- `engine-stop`
- `hazard-on`
- `hazard-off`
- plus other commands like `find-vehicle`, `sound-horn`, `headlight-on`

But the EU model shape is:

- `{ "command": "<string>" }`
- optional `beepCount`

There is no `value` field in the published model.

### NA modern reference

The NA 17CYPLUS code maps commands exactly as modern strings:

- `door-lock`
- `door-unlock`
- `engine-start`
- `engine-stop`
- `hazard-on`
- `hazard-off`

And posts them as:

- `{ "command": "<string>" }`

Again, no `value` field.

### NA older reference

The NA 17CY code uses older symbolic commands with numeric values:

- `DL` with values `1` / `2`
- `RES` with values `1` / `2`
- `HZ` with values `1` / `2`

This is a different naming scheme, but it does establish a useful on/off convention:

- `1` means on / start / lock
- `2` means off / stop / unlock

### Assessment

AU looks like a hybrid:

- modern endpoint family
- modern command names
- older style numeric direction values

That is the key finding.

## 5. Safe Assumptions

## Engine start / stop

Confidence: medium to high

Recommended working assumption:

- `{ "command": "engine-start", "value": 1 }`
- `{ "command": "engine-stop", "value": 2 }`

Why this is reasonable:

- the endpoint matches modern EU/NA
- the command names match modern EU/NA
- the value convention matches older NA conventions exactly
- your confirmed AU door commands already follow the same hybrid rule

Risk:

- low to moderate
- engine commands may require a preliminary status refresh, subscription check, or additional server-side eligibility checks

## Hazard flash

Confidence: low to medium

Candidate assumptions:

- `{ "command": "hazard-on", "value": 1 }`
- `{ "command": "hazard-off", "value": 2 }`

Why this is weaker:

- the open-source projects expose hazards as on/off, not necessarily a single "flash" action
- the EU command model also includes `find-vehicle`, `sound-horn`, `buzzer-warning`, and `headlight-on/off`
- depending on the Lexus AU UI wording, the app's "flash" feature may be implemented as a locator command rather than hazards-on/off

Result:

- not safe enough to commit as the only V1 hazard implementation without one capture

## 6. Recommendation

Proceed without extra capture for:

- auth implementation
- token storage
- vehicle discovery
- status polling
- refresh
- lock / unlock
- an experimental engine start/stop implementation behind an explicit opt-in flag or developer-only service

Do one additional capture before exposing a production `hazard flash` service in Home Assistant.

That gives you the best tradeoff:

- very little extra capture burden
- no guesswork on the most ambiguous command
- continued momentum on the integration

## 7. Practical Project Decision

The next implementation phase can start now.

Suggested scope:

1. build the AU auth + status + lock/unlock client
2. add experimental engine start/stop using the inferred hybrid command shape
3. keep hazard support out of the main service set until one real capture confirms whether AU uses:
   - `hazard-on` / `hazard-off`
   - `find-vehicle`
   - or another command variant
