# Branding and renaming

**Single source of truth:** `brand/brand.env` (shell) and `brand/brand.json` (everything else).
Public names, descriptor, tagline, licence line and trademark line live there and nowhere else.

- **Haar**: the mobile Ubuntu-based imaging system. **Haaremetry**: the Android assistant app. **JOS**: the secure-boot client OS (name kept).
- These are working names. No trademark search or registration has been done; do that before selling anything.
- **Do not use** MIST, MISTMETRY, WISP or Brume. Juniper/HPE hold pending MIST marks in networking software; Brume was a placeholder.
- **Internal identifiers stay stable** (`jog`, `jos`, `jogemetry` repo and submodule names, `/etc/jog`, `JOG_*` variables,
  `C:\ProgramData\JOG`, `JOG-<mac>` host names, the Android applicationId, the hidden WiFi SSID). Only the public name changes.
- To rename again: edit `brand/brand.*`, replace the wordmark in `branding/`, update the retired-names list in
  `scripts/rebrand-check`, run it.
- Art with a name painted into it (`branding/jogemetry/`) must be regenerated on a rename.

History: the earlier MIST/WISP/MISTMETRY decision is kept in `docs/archive/REBRAND-MIST-2026-11-24.md` for reference only.
