# Project Overview

## Objective

Expose your Lexus RX500h cloud-connected functions inside Home Assistant so you can read vehicle state and trigger remote actions such as lock, unlock, engine start/stop, climate control, and vehicle location.

## Recommended Project Outcome

Create a private Home Assistant custom integration for the Australian Lexus Connected platform.

The integration should:

- authenticate against the same Lexus Connected backend used by the official app
- discover the vehicle linked to your Lexus account
- expose safe read-only entities in Home Assistant
- expose remote commands as explicit Home Assistant services/buttons
- avoid any new recurring third-party cost

## Confirmed Environment

- Daily phone: iPhone
- You do not want to dedicate the daily phone to ongoing automation duties
- Research/interception host: Apple Silicon Mac running the iOS Lexus app
- Optional backup research path: emulator-based interception
- Home Assistant target: HA OS
- V1 priority commands:
  - lock / unlock
  - engine start / stop
  - hazard flash

## Why This Is Needed

There is no official Lexus Australia Home Assistant integration, and the existing open-source Toyota integrations I found are region-specific:

- Toyota EU: `pytoyoda/ha_toyota`
- Toyota NA: `widewing/ha-toyota-na`

Those projects are still valuable because they show the general architecture, auth/session handling patterns, and Home Assistant entity model needed for a working solution.

## Constraints

- The car is controlled through Lexus cloud services, not a local LAN API.
- The solution only works while your Lexus Connected / Remote Connect entitlement remains active.
- Lexus Australia states Remote Connect is complimentary for 3 years, with paid subscription optional after that period.
- Lexus Australia states some trip and location data can take up to 24 hours or longer to appear in the app.
- Unofficial API integrations can break when Lexus changes the app, auth flow, headers, or endpoints.
- There is some legal/distribution risk with reverse-engineered OEM APIs, so this should start as a private integration rather than a public HACS release.

## In Scope

- Vehicle discovery
- Token-based authentication and refresh
- Read entities:
  - fuel level / range
  - odometer
  - door / lock / window status
  - last update time
  - last known location
  - optional trip / alert history if practical
- Command entities/services:
  - refresh
  - lock / unlock
  - engine start / stop
  - hazard flash
  - climate on / off or preset application if it turns out to be cheap to add after V1 commands are working

## Out Of Scope For V1

- Publishing to HACS
- Multi-region Toyota/Lexus support
- Local CAN bus or OBD-II integrations for remote commands
- Any solution that depends on a permanent paid middleware subscription
- Voice assistant polish before the core HA integration is stable
- Climate control unless it falls out naturally from the same command family as engine start/stop

## Success Criteria

- Home Assistant can authenticate without manual app interaction on every restart.
- The integration creates one Lexus device with stable entities.
- At least these actions work from Home Assistant: refresh, lock, unlock, engine start/stop, hazard flash.
- Command responses are surfaced clearly enough that an automation can tell success from failure.
- The integration remains usable after Home Assistant restarts and Lexus token refreshes.

## Key Risks

- AU backend may differ significantly from EU and NA backends.
- TLS pinning or device attestation may complicate traffic interception.
- Some commands may require extra anti-abuse headers or challenge flows.
- Lexus may change the app/API without notice.
- OEM legal posture may make public distribution unwise.

## Source Notes

- Lexus Australia connected services overview: https://www.lexus.com.au/connectivity
- Lexus Australia connected services terms: https://www.lexus.com.au/smallprint/connected-services-terms
- Lexus Australia app page: https://www.lexus.com.au/owners/apps/lexus-connected-app
- Toyota EU integration: https://github.com/pytoyoda/ha_toyota
- Toyota EU Python client: https://github.com/pytoyoda/pytoyoda
- Toyota NA integration: https://github.com/widewing/ha-toyota-na
- Home Assistant Mazda DMCA precedent: https://community.home-assistant.io/t/removal-of-mazda-connected-services-integration/625885
