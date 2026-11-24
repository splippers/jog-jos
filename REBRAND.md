# HAAR / WISP / HAARMETRY — REBRAND & MIGRATION SPEC
# Formerly: HAAR / HAARMETRY
# Status: APPROVED FOR MIGRATION — DO NOT USE OLD NAMES IN NEW CODE
# Date: 2026-11-24

## 1. THE DECISION — READ THIS FIRST

We are rebranding the entire project. The old names are DEPRECATED.

- HAAR (Mobile Imaging System Toolkit) -> HAAR
- HAARMETRY (telemetry for HAAR) -> WISP (agent) + HAARMETRY (dashboard/backend)
- HAAR repo -> HAAR repo (keep git history, rename in place, do NOT create a new repo)

Reason: HAAR sounded like a personal side-project. HAAR sounds like a product,
fits the FOGProject / fog metaphor, is 4 letters, sticker-friendly, and
searchable. WISP is a tiny bit of haar = perfect for a lightweight telemetry agent.

Do NOT keep "Jonathan's" in any public-facing name, title, description, or banner.
Do NOT keep "HAAR" as an alias, fallback, or easter egg in new code.

## 2. OFFICIAL NAMES & DEFINITIONS

### HAAR — Mobile Imaging System Toolkit
- Pronounced: "haar"
- What it is: The portable, Ubuntu-based laptop imaging system powered by FOGProject.
- Tagline: "Imaging, anywhere."
- Secondary tagline: "Roll in. Image. Roll out."
- Full description: "HAAR is a portable, Ubuntu-based imaging station powered by
  FOGProject. Plug it into any network, boot any machine to PXE, and capture
  or deploy images without needing a server room, a rack, or a permanent install."
- Stack: Ubuntu + FOGProject + PXE + DHCP / TFTP / NFS
- Canonical upstream links:
    - FOGProject: https://fogproject.org/
    - Ubuntu: https://ubuntu.com/

### WISP — Telemetry Agent for HAAR
- Pronounced: "wisp"
- What it is: The lightweight telemetry agent that runs on imaged / managed clients
  and reports back to HAAR.
- Tagline: "Telemetry for HAAR."
- Secondary tagline: "HAAR runs the imaging. WISP watches the machines."
- Full description: "WISP is the lightweight telemetry agent for HAAR. It collects
  host health, imaging status, and system telemetry and drifts it back to HAARMETRY."
- This replaces HAARMETRY entirely as the agent name.

### HAARMETRY — Telemetry Dashboard / Backend
- Pronounced: "haar-met-tree"
- What it is: The dashboard, API, and database where WISP reports land.
  HAARMETRY is NOT an agent. It is the server-side view.
- Tagline: "See what WISP saw."
- Full description: "HAARMETRY is the telemetry store and dashboard for HAAR.
  WISP agents report in, HAARMETRY visualises it."
- Relationship: WISP (agent) -> HAARMETRY (backend/dashboard) -> runs on / alongside HAAR

### The One-Liner For README / About
> HAAR runs the imaging. WISP watches the machines. HAARMETRY shows you what WISP saw.

## 3. BRANDING

- Primary colour (HAAR): Matte Black #1A1A1A, White #FFFFFF, Ubuntu Orange #E95420 accent
- Primary colour (WISP): Deep Navy #0F1426, Cyan #29B6F6 / #35C4F0 accent, White
- Primary colour (HAARMETRY): Same as HAAR, with Cyan accent from WISP to show it bridges both
- Fonts: Bold condensed sans for HAAR / WISP wordmarks. Clean sans for body.
- Logo concept HAAR: HAAR in bold white, "I" can be a network cable / PXE symbol.
  Fog wisp line along the bottom. Orange accent line.
- Logo concept WISP: A single white wisp / wave line ending in a cyan data dot.
  Represents signal + haar + pulse.
- Assets (in repo):
    - assets/branding/haar-splash.png
    - assets/branding/haar-banner.png
    - assets/branding/wisp-icon.png
    - assets/branding/wisp-splash.png
- Banner footer must read: ubuntu + fogproject.org
    - Correct: fogproject.org
    - Incorrect: fogproject.org — DO NOT USE .com ANYWHERE

## 4. RENAME MAP — APPLY GLOBALLY

Opencode: Perform case-sensitive + case-insensitive search/replace across
ALL files except .git/ history, vendor/, node_modules/, and third-party FOGProject
upstream code. Do NOT rename FOGProject itself. FOGProject stays FOGProject.

| OLD | NEW | NOTES |
| :--- | :--- | :--- |
| HAAR | HAAR | All caps, titles, docs |
| Jog | Haar | Title case |
| jog | haar | Lowercase, filenames, slugs |
| Mobile Imaging System Toolkit | Mobile Imaging System Toolkit | Full expansion |
| Mobile Imaging System Toolkit | Mobile Imaging System Toolkit | Variant |
| HAARMETRY | WISP | When referring to the AGENT |
| JOGemetry | Wisp | Title case agent |
| haarmetry | wisp | Lowercase agent |
| jog-emetry | wisp | Hyphen variant |
| HAARMETRY (dashboard) | HAARMETRY | Only when referring to dashboard/backend |
| haarmetry-dashboard | haarmetry | Dashboard variant |
| haarmetry-server | haarmetry-server | Server variant |
| haarmetry-api | haarmetry-api | API variant |
| jog_agent | wisp_agent | Code identifiers |
| jogAgent | wispAgent | Code identifiers |
| JogAgent | WispAgent | Code identifiers |
| jogTelemetry | wispTelemetry | Code identifiers |
| jog-telemetry | wisp-telemetry | Code identifiers |
| fogproject.org | fogproject.org | Upstream URL correction |
| https://fogproject.org | https://fogproject.org/ | Upstream URL correction |

### CRITICAL DISAMBIGUATION FOR HAARMETRY
Old code used HAARMETRY for BOTH agent + dashboard. You MUST split it:
- If the file/class/function runs ON THE CLIENT, collects metrics, sends heartbeat -> rename to WISP
- If the file/class/function runs ON THE SERVER, stores metrics, serves dashboard/API -> rename to HAARMETRY
- If unsure, flag it in MIGRATION_NOTES.md and default to WISP for collectors, HAARMETRY for storage.

## 5. FILE / DIRECTORY RENAMES

Rename directories/files (use `git mv`):

- jog/ -> haar/
- jog-*/ -> haar-*/
- haarmetry/ -> wisp/
- haarmetry-dashboard/ -> haarmetry/
- haarmetry-server/ -> haarmetry-server/
- haarmetry-api/ -> haarmetry-api/
- README-HAAR.md -> DELETE, merge into README.md
- docs/jog-* -> docs/haar-*
- assets/jog-* -> assets/branding/haar-* or wisp-*

Proposed final top-level structure:

    /
    ├── README.md                 # HAAR overview
    ├── docs/
    │   ├── HAAR-SETUP.md
    │   ├── HAAR-USAGE.md
    │   ├── WISP-AGENT.md
    │   └── HAARMETRY-DASHBOARD.md
    ├── haar/                     # was jog/ — imaging system code / configs
    ├── wisp/                     # was haarmetry/ agent — client telemetry agent
    ├── haarmetry/                # dashboard + API + DB for telemetry
    ├── assets/
    │   └── branding/
    │       ├── haar-splash.png
    │       ├── haar-banner.png
    │       ├── wisp-icon.png
    │       └── wisp-splash.png
    ├── scripts/
    └── .github/

## 6. CODE RENAMES — SERVICES, PACKAGES, ENV, CONFIG

- systemd services:
    - jog.service -> haar.service
    - haarmetry.service -> wisp.service
    - haarmetry-dashboard.service -> haarmetry.service

- Binaries / CLI:
    - `jog` -> `haar`
    - `jog-cli` -> `haar-cli`
    - `haarmetry` -> `wisp`
    - `haarmetry-collect` -> `wisp-collect`

- Python / Go / JS packages:
    - `jog` -> `haar`
    - `haarmetry` -> `wisp` (agent) / `haarmetry` (backend)
    - `from jog...` -> `from haar...`
    - `import haarmetry` -> `import wisp`

- Docker:
    - `jog:latest` -> `haar:latest`
    - `haarmetry:latest` -> `wisp:latest`
    - `haarmetry-dashboard:latest` -> `haarmetry:latest`
    - container names: `jog-*` -> `haar-*`, `haarmetry-*` -> `wisp-*` / `haarmetry-*`

- Env vars (keep OLD as deprecated alias for 1 release if needed, then remove):
    - JOG_* -> HAAR_*
    - HAARMETRY_* -> WISP_* (agent) or HAARMETRY_* (dashboard)
    - JOG_HOST -> HAAR_HOST
    - JOG_PORT -> HAAR_PORT
    - HAARMETRY_ENDPOINT -> WISP_ENDPOINT
    - HAARMETRY_SERVER -> HAARMETRY_SERVER

- Config files:
    - jog.conf / jog.yaml / jog.json -> haar.conf / haar.yaml / haar.json
    - haarmetry.conf -> wisp.conf
    - haarmetry-dashboard.conf -> haarmetry.conf
    - Config keys: `jog:` -> `haar:`, `haarmetry:` -> `wisp:` / `haarmetry:`

- DB:
    - Database `jog` -> `haar`
    - Database `haarmetry` -> `haarmetry`
    - Tables `jog_*` -> `haar_*`
    - Tables `haarmetry_*` -> `wisp_*` (raw agent events) or `haarmetry_*` (aggregated)

- API routes:
    - /api/jog/* -> /api/haar/*
    - /api/haarmetry/* -> /api/wisp/* (agent ingest) OR /api/haarmetry/* (dashboard queries)
    - Keep a 301 / deprecation shim for /api/haarmetry/* -> /api/wisp/* for one release, log warning.

- Hostnames / mDNS:
    - jog.local -> haar.local
    - haarmetry.local -> wisp.local (agent) / haarmetry.local (dashboard)

## 7. DOCS / UI / STRINGS TO UPDATE

Update in ALL user-facing strings:
- README.md title: "# HAAR — Mobile Imaging System Toolkit"
- README.md subtitle: "Imaging, anywhere. Ubuntu + FOGProject, in your bag."
- README.md must link FOGProject as https://fogproject.org/ — never fogproject.org
- Splash screens: HAAR splash + WISP splash (see assets/branding/)
- App titles, window titles, CLI --help, --version, man pages
- PXE boot menu: "HAAR — Boot to Imaging" (was HAAR)
- Web UI header: "HAAR" + subhead "HAARMETRY" for telemetry pages
- About dialog: Must list HAAR, WISP, HAARMETRY with versions
- Footer: "HAAR • WISP • HAARMETRY — Open Source"

Do NOT update:
- FOGProject name, logo, or upstream docs (third-party)
- Ubuntu name/logo (third-party)
- Git commit history (do not rewrite history)

## 8. MIGRATION STEPS FOR OPENCODE — DO IN ORDER

1. Create branch: `git checkout -b rebrand/haar-wisp-haarmetry`
2. Run global search for: HAAR, Jog, jog, HAARMETRY, haarmetry, Mobile Imaging System Toolkit, fogproject.org
   Save results to MIGRATION_NOTES.md before changing anything.
3. Apply rename map in Section 4 + file renames in Section 5 using `git mv`.
4. Split HAARMETRY -> WISP vs HAARMETRY per Section 4 disambiguation. List every ambiguous file in MIGRATION_NOTES.md.
5. Update env vars, configs, systemd units, Dockerfiles, docker-compose.yml, API routes.
6. Update README.md, docs/, splash screens, banners, icons, PXE menu, CLI help.
7. Fix all upstream links: fogproject.org -> fogproject.org
8. Add deprecation shims: old CLI `jog` -> prints "jog is now haar, use haar" + forwards. Old env vars log deprecation warning once. Keep for 1 release only.
9. Run: lint, unit tests, build, boot test in VM. Fix all broken imports / references.
10. Update .github/workflows, CI badges, links, repo description to HAAR.
11. Create MIGRATION.md with: What changed, old -> new table, how to upgrade from HAAR to HAAR, breaking changes.
12. Commit with message: `feat!: rebrand HAAR -> HAAR, HAARMETRY -> WISP / HAARMETRY`
13. Open PR, request review, do NOT merge until PXE boot + WISP heartbeat to HAARMETRY verified.

## 9. VERIFICATION CHECKLIST

- [ ] No `HAAR` remains in code/docs/UI except in MIGRATION.md / MIGRATION_NOTES.md historical note + deprecation shims
- [ ] No `HAARMETRY` remains except in migration docs + shims
- [ ] No `fogproject.org` remains anywhere — only `fogproject.org`
- [ ] `haar --help` works, `wisp --help` works
- [ ] `haar.service` starts, `wisp.service` starts, `haarmetry.service` starts
- [ ] PXE boot menu shows HAAR
- [ ] WISP agent reports to HAARMETRY dashboard
- [ ] README shows HAAR banner, HAAR description, WISP + HAARMETRY section
- [ ] README links FOGProject to https://fogproject.org/
- [ ] Splash screens load: haar-splash.png, wisp-splash.png
- [ ] Docker images build as haar / wisp / haarmetry

## 10. WHAT TO SAY IF USERS ASK

> HAAR is now HAAR. Same tool, better name. HAARMETRY is now WISP (agent) + HAARMETRY (dashboard). Update your commands from `jog` to `haar` and `haarmetry` to `wisp`. Powered by FOGProject — https://fogproject.org/
