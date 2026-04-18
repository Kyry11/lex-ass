# Solution Spec

## Decision

Build a private Home Assistant custom integration for Lexus Connected Australia.

This is the best fit because it is the only path I found that is:

- technically capable of exposing the full cloud-backed vehicle controls you want
- compatible with your preference for no added recurring cost
- realistic to implement using existing Toyota reverse-engineering work as a reference

## Option Review

| Option | Fit | Cost | Assessment |
| --- | --- | --- | --- |
| Use Toyota EU integration directly (`pytoyoda/ha_toyota`) | Low | Free | Not a direct fit. The project explicitly documents EU-only support, though its architecture and Lexus brand handling are useful references. |
| Use Toyota NA integration directly (`widewing/ha-toyota-na`) | Low | Free | Not a direct fit. It has the command surface you want, but it targets North America. |
| Smartcar | Low | Paid | Not a good fit for Lexus Australia. Smartcar's compatibility pages describe North America and Europe coverage, and the Lexus page references Enform accounts rather than the Australian Lexus Connected platform. |
| Siri Shortcuts bridge via Pushcut | Medium | Free to low cost, depending on usage | Viable only as a stopgap if you use iPhone. It can expose a webhook to run shortcuts, but requires a dedicated always-on iOS device and Pushcut's automation-server constraints. |
| Phone UI automation | Medium-Low | Free to low cost | Technically possible, but brittle. Good only as a fallback if the API is blocked by pinning/attestation and no stable shortcut route exists. |
| Custom Lexus AU cloud integration | High | Free beyond your existing Lexus subscription | Recommended. Most effort up front, best long-term UX inside Home Assistant, and no extra middleware dependency. |

## Existing Open-Source Building Blocks

### Toyota EU references

Useful parts:

- `pytoyoda/pytoyoda` already models a cloud client with token handling, headers, brand selection, and endpoint wrappers.
- `pytoyoda/ha_toyota` already shows a normal Home Assistant custom-integration shape:
  - `config_flow.py`
  - `manifest.json`
  - `DataUpdateCoordinator` setup in `__init__.py`

Important limitation:

- The README says only Europe is supported.

Why it still matters:

- The EU project already includes Toyota/Lexus brand selection logic.
- It is a strong template for auth/session management and entity wiring.

### Toyota NA references

Useful parts:

- `widewing/ha-toyota-na` exposes the kind of command services you want:
  - engine start/stop
  - door lock/unlock
  - hazards on/off
  - manual refresh

Important limitation:

- It is North America-specific and should be treated as a command-surface reference, not a drop-in dependency.

## Proposed Architecture

```text
Home Assistant
  -> custom_components/lexus_au
    -> Lexus AU client library
      -> Lexus Connected AU auth + vehicle APIs
        -> Lexus cloud
          -> vehicle telematics unit (DCM)
            -> car
```

## Home Assistant Design

### Domain

Suggested domain: `lexus_au`

### Entity Model

Expose remote actions as explicit services or buttons first, not as optimistic toggles.

Suggested V1 entities:

- `device_tracker`: vehicle location / last parked location
- `sensor`: fuel, range, odometer, last update, ignition-related state if available
- `binary_sensor`: doors, locks, windows, trunk/boot, hood if exposed
- `button`: refresh, engine start, engine stop, climate start, climate stop, locate/flash if supported
- `lock`: vehicle lock/unlock if state handling is reliable

### Update Model

Use at least two refresh cadences:

- fast coordinator for live status and lock/door/window state
- slow coordinator for trips, service history, and notifications

Recommended behavior:

- manual `refresh` service
- immediate post-command refresh
- conservative default polling to reduce ban/rate-limit risk

### Authentication Model

Expected approach:

- username/password login against Lexus AU auth flow
- capture access token, refresh token, user/vehicle identifiers
- cache session in Home Assistant config-entry storage
- support re-auth when the backend invalidates refresh tokens

### Command Safety

Guard risky commands with clear semantics:

- `lock` / `unlock`
- `engine_start` / `engine_stop`
- `climate_start` / `climate_stop`

Recommended safeguards:

- no silent retries for mutating commands
- capture correlation/request IDs in debug logs
- redact VIN, tokens, email, phone number, and location data in diagnostics

## Preferred Delivery Strategy

### Primary path

Private custom integration, built and tested in your Home Assistant instance.

### Stopgap path

If you use iPhone and want something usable quickly before the API work is done:

- create Lexus Siri Shortcuts for the most useful actions
- trigger them from Home Assistant through Pushcut Automation Server

Why this is not the primary recommendation:

- Lexus requires the mobile device to be unlocked and the app to be logged in for Siri Shortcuts
- Pushcut requires a dedicated always-on iOS device and only processes requests while the Pushcut app is in the foreground
- it is harder to make automations robust because state and command acknowledgement are indirect

## Publication Strategy

Keep V1 private.

Reason:

- unofficial OEM integrations can be fragile
- public distribution carries a higher legal/support burden
- the Mazda Home Assistant takedown is a practical warning that OEMs do sometimes act against community integrations

Once the private integration is stable, you can decide whether to:

- keep it private permanently
- publish only the Home Assistant wrapper, not the reverse-engineering notes
- publish a sanitized client after you are comfortable with the legal/support tradeoff

## Source Notes

- Lexus AU terms confirm remote commands, smartwatch access, and Siri shortcuts:
  https://www.lexus.com.au/smallprint/connected-services-terms
- Lexus AU app/connected-services pages confirm vehicle status, fuel level, and remote-connect features:
  https://www.lexus.com.au/owners/apps/lexus-connected-app
  https://www.lexus.com.au/connectivity
- Smartcar region/brand pages:
  https://smartcar.com/product/compatible-vehicles
  https://smartcar.com/brand/lexus
- Toyota EU references:
  https://github.com/pytoyoda/pytoyoda
  https://github.com/pytoyoda/ha_toyota
- Toyota NA reference:
  https://github.com/widewing/ha-toyota-na
