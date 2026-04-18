# GitHub Publishing Checklist

Use this checklist once you decide the target GitHub repository name.

## Required substitutions

Before publishing or adding the repository to HACS, replace these placeholders in:

- [custom_components/lexus_au/manifest.json](/Users/kyryll/Repos/Lexus/custom_components/lexus_au/manifest.json)

Fields to replace:

- `https://github.com/OWNER/REPO#readme`
- `https://github.com/OWNER/REPO/issues`
- `@OWNER`

## Recommended repository setup

1. Create a GitHub repository with this repo's contents.
2. Push the `main` branch.
3. Update the placeholder values above.
4. Optionally create a first GitHub release matching the integration version.
5. In Home Assistant HACS:
   - add the repo URL as a custom repository
   - choose repository type `Integration`
   - install
   - restart Home Assistant

## Optional improvements

- add a license file
- add local Home Assistant brand assets under `custom_components/lexus_au/brand/`
- add screenshots or example dashboards to the README
- add a changelog or GitHub releases
