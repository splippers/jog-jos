# HAAR → HAAR Migration

## What changed
- **HAAR** (Mobile Imaging System Toolkit) → **HAAR** (Mobile Imaging System Toolkit)
- **HAARMETRY agent** → **WISP** (lightweight telemetry agent name)
- **HAARMETRY dashboard/backend/mobile API** → **HAARMETRY**
- Upstream links corrected to `https://fogproject.org/`

## Compatibility
- `JOG_*` env vars still accepted; `HAAR_*` aliases added in `/etc/haar/haar.env` and `/etc/haar/mobile-api.env`.
- `haar-*` commands/paths/services remain; `haar-*` symlinks/aliases added.
- `/api/haar/*` and `/api/haar/*` routes both accepted where implemented.
- CLI: `haar` forwards to `haar` with deprecation message.

## Upgrade notes
1. Pull/update repo, run installer/rebrand apply as appropriate.
2. Update scripts/env to `HAAR_*` names; old names are deprecated.
3. Mobile API SSID branding moved to `HAARMETRY`; verify clients.
4. Verify: `haar --help`/shim, `systemctl status haar-*` aliases, `/api/haar/*`, WISP→HAARMETRY reporting.

## Breaking/attention
- Systemd unit filenames still `haar-*` on deployed systems; `haar-*` are symlinks.
- Android package remains `com.haar.imaging.control` for install compatibility; UI branded HAARMETRY.
- Full WISP/HAARMETRY split and repo/file renames may continue in follow-up commits.
