# Lexus AU Backend Capability Research

Date: 2026-04-23

Scope: authenticated backend functionality that may be available to the owner of a Lexus Connected AU vehicle but is not yet exposed by this Home Assistant integration.

This is not a recommendation to bypass authorization, access vehicles outside the configured account, or probe unrelated infrastructure. All experiments should stay within the authenticated Lexus account and VIN already configured for this integration.

## Executive Summary

The most valuable missing feature is already in hand: current AU `/v1/global/remote/status` responses include latitude, longitude, and `locationAcquisitionDatetime`. The integration parses those fields today, but does not expose them as a Home Assistant `device_tracker` or location sensors yet.

The second best target is a dedicated location endpoint. The EU Toyota client exposes `/v1/location`, and Lexus AU officially advertises Vehicle Locator. This is likely to return last-known/last-parked position, possibly with a display address, but it should not be treated as true live GPS.

The strongest extra endpoint families to probe next are:

- `/v1/location`
- `/v1/global/remote/engine-status`
- `/v1/global/remote/climate-status`
- `/v1/global/remote/climate-settings`
- `/v1/global/remote/refresh-climate-status`
- `/v1/global/remote/climate-control`
- `/v2/notification/history`
- `/v1/vehiclehealth/status`
- `/v1/trips?from=...&to=...&route=...&summary=...&limit=...&offset=...`
- `/v1/servicehistory/vehicle/summary`

The least likely safe target is Stolen Vehicle Tracking. Lexus AU terms describe that service as a call-centre / police-assisted workflow, not normal owner-facing API functionality.

## What AU Already Proves

Observed and/or implemented AU paths:

| Endpoint | Status | Notes |
| --- | --- | --- |
| `/v2/vehicle/guid` | Confirmed | Vehicle metadata, subscriptions, capability flags, model, image, DCM details. |
| `/v1/global/remote/status` | Confirmed | Door/window/opening status, hazards status, trip A/B, fuel/range/odometer, latitude/longitude, location timestamp. |
| `/v1/global/remote/refresh-status` | Confirmed | Requests a fresh vehicle state upload. |
| `/v1/global/remote/command` | Confirmed | Lock/unlock and hazards are confirmed; other commands are trial/inferred. |
| `/v2/telemetry` | Confirmed | Tire pressure and richer telemetry became available after adding AU vehicle metadata headers. |
| `/v3/telemetry` | Failed | Returned unauthorized in AU; lower priority. |
| `/v1/notification/device/status` | Captured | App-device notification status; likely not useful for HA except diagnostics. |

Current AU status payload already includes:

- `latitude`
- `longitude`
- `locationAcquisitionDatetime`
- `occurrenceDate`
- `vehicleStatus`
- `telemetry`
- `cautionOverallCount`

Implication: Home Assistant location can be added immediately from existing data without a new endpoint.

## Official Feature Clues

Lexus Australia publicly describes:

- Vehicle locator / last known location
- Recent trips
- Drive Pulse
- Guest Driver settings
- Vehicle alerts
- Vehicle diagnostic data and alerts
- Odometer, fuel level, distance to empty
- Remote lock/unlock
- Remote engine start
- Remote climate control
- Remote horn, buzzer, hazards, and headlights on selected models
- Connected Navigation / My Destinations

The terms also say location and trip data may take up to 24 hours or longer to appear in the Lexus app. That matters: even if the backend provides location, it may be stale by design and should be labelled as last-known or last-parked.

The privacy policy explicitly lists collected data categories that are relevant to backend probing:

- diagnostic trouble codes
- dashboard warning indicators
- fuel and fluid levels
- odometer
- engine temperature
- acceleration
- speed
- braking
- door open/close
- engine start/stop
- cornering forces
- latitude and longitude

Those fields are not a guarantee that every value is available through the mobile app API, but they are strong evidence that the backend data model can contain more than we currently expose.

## Cross-Region Endpoint Matrix

| Capability | Endpoint or mechanism seen in EU/NA | AU confidence | Notes |
| --- | --- | --- | --- |
| Last-known location | `/v1/location` | High | Lexus AU advertises Vehicle Locator, and AU status already includes coordinates. Probe first. |
| Location from status | `/v1/global/remote/status` | Confirmed | Already available; expose as `device_tracker`. |
| Real-time location | NA telemetry sometimes has `vehicleLocation`; NA GraphQL status has `location` | Medium-low | More likely last-reported than continuous. Avoid high-frequency polling. |
| Engine running status | `/v1/global/remote/engine-status` | Medium-high | NA 17CYPLUS uses this. Useful for confirming engine start/stop state. |
| Climate status/settings | `/v1/global/remote/climate-status`, `/climate-settings`, `/refresh-climate-status`, `/climate-control` | Medium | Lexus AU advertises remote climate. Your capabilities payload has climate-related flags, but some AC settings flags conflict. Probe read endpoints first. |
| Notifications / alerts | `/v2/notification/history` | Medium-high | Lexus AU advertises vehicle alert notifications. Read-only and safe. |
| Vehicle health / diagnostics | `/v1/vehiclehealth/status` | Medium | Official privacy text mentions DTCs, warnings, engine temperature. Payload shape may vary by region/model. |
| Recent trips | `/v1/trips?...` | Medium-high | Lexus AU advertises Recent Trips and Drive Pulse. Route data may be delayed or subscription-gated. |
| Drive score / behaviour | Included in EU trip payload | Medium | EU model includes scores and behaviour records. Likely linked to Drive Pulse. |
| Service history | `/v1/servicehistory/vehicle/summary` | Medium | Low risk, potentially useful for next service/service records. |
| Guest Driver settings | Unknown | Medium-low | Official feature and AU capability flags exist, but endpoint names are not obvious. Capture needed. |
| My Destinations / send-to-car | Unknown / multimedia endpoints | Low-medium | Officially available, but probably separate navigation/multimedia API surface. Capture needed. |
| Electric charging | `/v1/global/remote/electric/*`, `/v2/electric/*` | Low for RX500h | Useful for BEV/PHEV models, not a priority for RX500h. |
| GraphQL pre-wake/status | NA `oa-api.telematicsct.com/graphql` | Low-medium | NA client uses GraphQL for pre-wake and status refresh. AU may differ and needs capture before use. |
| Stolen Vehicle Tracking | Service workflow, not normal app API | Do not pursue | Terms describe police/call-centre flow and app-service restrictions. |

## Location and Live Tracking

### What we can likely add now

Expose a Home Assistant `device_tracker` from the already-parsed:

- `status.latitude`
- `status.longitude`
- `status.locationAcquisitionDatetime`

This would give normal Home Assistant map/history behavior. It should be labelled as last known vehicle location, not continuous live tracking.

### What to probe next

Probe:

```text
GET /v1/location
```

Expected EU-like shape:

```json
{
  "payload": {
    "lastTimestamp": "...",
    "vehicleLocation": {
      "displayName": "...",
      "latitude": -33.0,
      "longitude": 151.0,
      "locationAcquisitionDatetime": "..."
    },
    "vin": "..."
  }
}
```

If AU supports this, it may provide a display address or cleaner timestamp than `/remote/status`.

### What not to assume

Do not assume a live GPS stream. Lexus AU terms explicitly allow trip/location delays, and the normal app feature is Vehicle Locator / last known location. The backend may upload more frequently after `refresh-status`, but that still does not make it a live tracker.

## Highest-Value Read-Only Probes

Probe these before adding more mutating commands:

| Priority | Method/path | Why |
| --- | --- | --- |
| 1 | `GET /v1/location` | Direct location endpoint; likely useful immediately. |
| 2 | `GET /v1/global/remote/engine-status` | Confirms engine start/stop state and timer. |
| 3 | `GET /v2/notification/history` | Vehicle alerts and notifications. |
| 4 | `GET /v1/vehiclehealth/status` | Diagnostics/warnings, maybe DTCs/engine temperature. |
| 5 | `GET /v1/trips?...` | Recent trips, route, Drive Pulse, speed/behaviour summaries. |
| 6 | `GET /v1/servicehistory/vehicle/summary` | Service records / next service style data. |
| 7 | `GET /v1/global/remote/climate-status` | Safe climate read path. |
| 8 | `GET /v1/global/remote/climate-settings` | Climate capability/settings shape. |
| 9 | `POST /v1/global/remote/refresh-climate-status` | Mutating only in the sense that it asks the car to report climate status. |

Use the same auth/header envelope as the working AU client:

- bearer token
- `X-API-KEY`
- `X-GUID`
- `X-CHANNEL`
- `X-BRAND`
- `X-APPVERSION`
- `X-LOCALE`
- `VIN`
- `x-region`
- `GENERATION`

## Candidate Home Assistant Entities

If probes succeed, likely entities:

| Backend data | HA entity type |
| --- | --- |
| Last-known vehicle location | `device_tracker` |
| Location timestamp | `sensor` |
| Location display name | `sensor` or `device_tracker` attribute |
| Engine running status | `binary_sensor` |
| Remote start timer | `sensor` |
| Climate status | `climate` or `binary_sensor` + sensors first |
| Target temperature | `sensor`, later `climate` |
| Cabin temperature | `sensor` |
| Vehicle alerts | diagnostic sensors or event entities |
| DTC / dashboard warnings | diagnostic sensors |
| Trip summaries | sensors or optional diagnostics attributes |
| Trip route history | not ideal as HA entities; better diagnostics/export first |
| Drive Pulse score | sensor |
| Service history / next service | sensors |

## Recommended Next Implementation Sequence

1. Add `device_tracker` from existing `/remote/status` latitude/longitude.
2. Add a manual debug/probe service that can call a whitelist of read-only candidate endpoints and redact sensitive fields in logs.
3. Probe `/v1/location` and compare its timestamp/shape against `/remote/status`.
4. Probe `/v1/global/remote/engine-status` and add an engine-running binary sensor if it works.
5. Probe notification and health endpoints; add diagnostic entities only if payloads are stable.
6. Probe trips with a small window and `limit=10`; do not store full routes by default because they are location-sensitive and can be large.
7. Probe climate read endpoints before attempting climate control writes.

## Sources

- Lexus AU Connected Services: https://www.lexus.com.au/connectivity
- Lexus AU Connected Services packages: https://www.lexus.com.au/connectivity/packages
- Lexus AU Connected Services Terms: https://www.lexus.com.au/smallprint/connected-services-terms
- Lexus AU Connected Services Privacy Policy: https://www.lexus.com.au/smallprint/connected-services-privacy
- pytoyoda constants and API surface: https://github.com/pytoyoda/pytoyoda/blob/main/pytoyoda/const.py and https://github.com/pytoyoda/pytoyoda/blob/main/pytoyoda/api.py
- pytoyoda endpoint models: https://github.com/pytoyoda/pytoyoda/tree/main/pytoyoda/models/endpoints
- Toyota NA community integration: https://github.com/widewing/ha-toyota-na
