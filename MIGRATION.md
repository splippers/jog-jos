# MIST → MIST Migration

## What changed
- **MIST** (Mobile Imaging System Toolkit) → **MIST** (Mobile Imaging System Toolkit)
- **MISTMETRY agent** → **WISP** (lightweight telemetry agent name)
- **MISTMETRY dashboard/backend/mobile API** → **MISTMETRY**
- Upstream links corrected to `https://fogproject.org/`

## Compatibility
- `JOG_*` env vars still accepted; `MIST_*` aliases added in `/etc/mist/mist.env` and `/etc/mist/mobile-api.env`.
- `mist-*` commands/paths/services remain; `mist-*` symlinks/aliases added.
- `/api/mist/*` and `/api/mist/*` routes both accepted where implemented.
- CLI: `mist` forwards to `mist` with deprecation message.

## Upgrade notes
1. Pull/update repo, run installer/rebrand apply as appropriate.
2. Update scripts/env to `MIST_*` names; old names are deprecated.
3. Mobile API SSID branding moved to `MISTMETRY`; verify clients.
4. Verify: `mist --help`/shim, `systemctl status mist-*` aliases, `/api/mist/*`, WISP→MISTMETRY reporting.

## Breaking/attention
- Systemd unit filenames still `mist-*` on deployed systems; `mist-*` are symlinks.
- Android package remains `com.mist.imaging.control` for install compatibility; UI branded MISTMETRY.
- Full WISP/MISTMETRY split and repo/file renames may continue in follow-up commits.
