# Lexus Home Assistant Project

Research date: 2026-04-17

Current recommendation: build a private Home Assistant custom integration for Lexus Connected Australia by reverse-engineering the Lexus Connected app/API and reusing patterns from the existing Toyota EU and Toyota NA community integrations.

This repository contains a Home Assistant custom integration under [custom_components/lexus_au](/Users/kyryll/Repos/Lexus/custom_components/lexus_au).

Docs:

- [Project Overview](docs/project-overview.md)
- [Solution Spec](docs/solution-spec.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Protocol Findings (2026-04-18)](docs/protocol-findings-2026-04-18.md)
- [Cross-Region Command Comparison (2026-04-18)](docs/cross-region-command-comparison-2026-04-18.md)
- [Implementation Status (2026-04-18)](docs/implementation-status-2026-04-18.md)
- [GitHub Publishing Checklist](docs/github-publishing-checklist.md)

## Install

### Manual

Copy [custom_components/lexus_au](/Users/kyryll/Repos/Lexus/custom_components/lexus_au) into your Home Assistant config directory under:

```text
custom_components/lexus_au
```

Restart Home Assistant, then add `Lexus Connected AU` from `Settings -> Devices & Services`.

### HACS custom repository

This repo is structured for HACS, but before publishing you must replace the placeholder GitHub values in [custom_components/lexus_au/manifest.json](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/manifest.json). See [GitHub Publishing Checklist](docs/github-publishing-checklist.md).

Why this path:

- It is the only route that can give you native Home Assistant entities and services without adding a new paid middleware layer.
- Existing Toyota/Lexus community work proves the general approach is feasible, but the public integrations I found are region-specific and do not directly target the Australian Lexus Connected backend.
- Lexus Australia officially exposes the same remote capabilities you want in the mobile app, so the missing piece is the integration layer rather than vehicle capability.

Confirmed environment:

- daily phone: iPhone
- interception host: Apple Silicon Mac running the iOS Lexus app
- Home Assistant target: HA OS
- V1 command priority: `lock/unlock`, `engine start/stop`, `hazard flash`

Immediate next step: start the API-capture sprint from the Mac-hosted iOS app, with Android emulator work kept as a fallback if the Mac path proves harder than expected.
