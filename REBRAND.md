# Branding and renaming

**Single source of truth:** `brand/brand.env` (shell) and `brand/brand.json` (everything else).
Public names, tagline, licence line and trademark line live there and nowhere else.

- Current working name: **Brume** (telemetry app: **Brumetry**). OS stays **JOS**. These are placeholders: no trademark search or registration has been done.
- **Do not use MIST, MISTMETRY or WISP.** Juniper/HPE hold pending MIST marks in networking software.
- **Internal identifiers stay stable** (`jog`, `jos`, `jogemetry` repo and submodule names, `/etc/jog`, `JOG_*` variables, the Android applicationId). Only the public name changes.
- To rename: edit `brand/brand.*`, replace the wordmark in `branding/`, run `scripts/rebrand-check`.
- Art with the name painted into it (`branding/jogemetry/`) must be regenerated on a rename.

History: the earlier MIST/WISP/MISTMETRY decision is kept in `docs/archive/REBRAND-MIST-2026-11-24.md` for reference only.
