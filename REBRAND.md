# MIST / WISP / MISTMETRY — REBRAND & MIGRATION SPEC
# Formerly: JOG / JOGEMETRY
# Status: APPROVED FOR MIGRATION — DO NOT USE OLD NAMES IN NEW CODE
# Date: 2026-11-24

## 1. THE DECISION — READ THIS FIRST

We are rebranding the entire project. The old names are DEPRECATED.

- JOG (Jonathan's Opensource Ghost) -> MIST
- JOGEMETRY (telemetry for JOG) -> WISP (agent) + MISTMETRY (dashboard/backend)
- JOG repo -> MIST repo (keep git history, rename in place, do NOT create a new repo)

Reason: JOG sounded like a personal side-project. MIST sounds like a product,
fits the FOGProject / fog metaphor, is 4 letters, sticker-friendly, and
searchable. WISP is a tiny bit of mist = perfect for a lightweight telemetry agent.

Do NOT keep "Jonathan's" in any public-facing name, title, description, or banner.
Do NOT keep "JOG" as an alias, fallback, or easter egg in new code.

## 2. OFFICIAL NAMES & DEFINITIONS

### MIST — Mobile Imaging System Toolkit
- Pronounced: "mist"
- What it is: The portable, Ubuntu-based laptop imaging system powered by FOGProject.
- Tagline: "Imaging, anywhere."
- Secondary tagline: "Roll in. Image. Roll out."
- Full description: "MIST is a portable, Ubuntu-based imaging station powered by
  FOGProject. Plug it into any network, boot any machine to PXE, and capture
  or deploy images without needing a server room, a rack, or a permanent install."
- Stack: Ubuntu + FOGProject + PXE + DHCP / TFTP / NFS
- Canonical upstream links:
    - FOGProject: https://fogproject.org/
    - Ubuntu: https://ubuntu.com/

### WISP — Telemetry Agent for MIST
- Pronounced: "wisp"
- What it is: The lightweight telemetry agent that runs on imaged / managed clients
  and reports back to MIST.
- Tagline: "Telemetry for MIST."
- Secondary tagline: "MIST runs the imaging. WISP watches the machines."
- Full description: "WISP is the lightweight telemetry agent for MIST. It collects
  host health, imaging status, and system telemetry and drifts it back to MISTMETRY."
- This replaces JOGEMETRY entirely as the agent name.

### MISTMETRY — Telemetry Dashboard / Backend
- Pronounced: "mist-met-tree"
- What it is: The dashboard, API, and database where WISP reports land.
  MISTMETRY is NOT an agent. It is the server-side view.
- Tagline: "See what WISP saw."
- Full description: "MISTMETRY is the telemetry store and dashboard for MIST.
  WISP agents report in, MISTMETRY visualises it."
- Relationship: WISP (agent) -> MISTMETRY (backend/dashboard) -> runs on / alongside MIST

### The One-Liner For README / About
> MIST runs the imaging. WISP watches the machines. MISTMETRY shows you what WISP saw.

## 3. BRANDING

- Primary colour (MIST): Matte Black #1A1A1A, White #FFFFFF, Ubuntu Orange #E95420 accent
- Primary colour (WISP): Deep Navy #0F1426, Cyan #29B6F6 / #35C4F0 accent, White
- Primary colour (MISTMETRY): Same as MIST, with Cyan accent from WISP to show it bridges both
- Fonts: Bold condensed sans for MIST / WISP wordmarks. Clean sans for body.
- Logo concept MIST: MIST in bold white, "I" can be a network cable / PXE symbol.
  Fog wisp line along the bottom. Orange accent line.
- Logo concept WISP: A single white wisp / wave line ending in a cyan data dot.
  Represents signal + mist + pulse.
- Assets (in repo):
    - assets/branding/mist-splash.png
    - assets/branding/mist-banner.png
    - assets/branding/wisp-icon.png
    - assets/branding/wisp-splash.png
- Banner footer must read: ubuntu + fogproject.org
    - Correct: fogproject.org
    - Incorrect: fogproject.com — DO NOT USE .com ANYWHERE

## 4. RENAME MAP — APPLY GLOBALLY

Opencode: Perform case-sensitive + case-insensitive search/replace across
ALL files except .git/ history, vendor/, node_modules/, and third-party FOGProject
upstream code. Do NOT rename FOGProject itself. FOGProject stays FOGProject.

| OLD | NEW | NOTES |
| :--- | :--- | :--- |
| JOG | MIST | All caps, titles, docs |
| Jog | Mist | Title case |
| jog | mist | Lowercase, filenames, slugs |
| Jonathan's Opensource Ghost | Mobile Imaging System Toolkit | Full expansion |
| Jonathan's Open Source Ghost | Mobile Imaging System Toolkit | Variant |
| JOGEMETRY | WISP | When referring to the AGENT |
| JOGemetry | Wisp | Title case agent |
| jogemetry | wisp | Lowercase agent |
| jog-emetry | wisp | Hyphen variant |
| JOGEMETRY (dashboard) | MISTMETRY | Only when referring to dashboard/backend |
| jogemetry-dashboard | mistmetry | Dashboard variant |
| jogemetry-server | mistmetry-server | Server variant |
| jogemetry-api | mistmetry-api | API variant |
| jog_agent | wisp_agent | Code identifiers |
| jogAgent | wispAgent | Code identifiers |
| JogAgent | WispAgent | Code identifiers |
| jogTelemetry | wispTelemetry | Code identifiers |
| jog-telemetry | wisp-telemetry | Code identifiers |
| fogproject.com | fogproject.org | Upstream URL correction |
| https://fogproject.com | https://fogproject.org/ | Upstream URL correction |

### CRITICAL DISAMBIGUATION FOR JOGEMETRY
Old code used JOGEMETRY for BOTH agent + dashboard. You MUST split it:
- If the file/class/function runs ON THE CLIENT, collects metrics, sends heartbeat -> rename to WISP
- If the file/class/function runs ON THE SERVER, stores metrics, serves dashboard/API -> rename to MISTMETRY
- If unsure, flag it in MIGRATION_NOTES.md and default to WISP for collectors, MISTMETRY for storage.

## 5. FILE / DIRECTORY RENAMES

Rename directories/files (use `git mv`):

- jog/ -> mist/
- jog-*/ -> mist-*/
- jogemetry/ -> wisp/
- jogemetry-dashboard/ -> mistmetry/
- jogemetry-server/ -> mistmetry-server/
- jogemetry-api/ -> mistmetry-api/
- README-JOG.md -> DELETE, merge into README.md
- docs/jog-* -> docs/mist-*
- assets/jog-* -> assets/branding/mist-* or wisp-*

Proposed final top-level structure:

    /
    ├── README.md                 # MIST overview
    ├── docs/
    │   ├── MIST-SETUP.md
    │   ├── MIST-USAGE.md
    │   ├── WISP-AGENT.md
    │   └── MISTMETRY-DASHBOARD.md
    ├── mist/                     # was jog/ — imaging system code / configs
    ├── wisp/                     # was jogemetry/ agent — client telemetry agent
    ├── mistmetry/                # dashboard + API + DB for telemetry
    ├── assets/
    │   └── branding/
    │       ├── mist-splash.png
    │       ├── mist-banner.png
    │       ├── wisp-icon.png
    │       └── wisp-splash.png
    ├── scripts/
    └── .github/

## 6. CODE RENAMES — SERVICES, PACKAGES, ENV, CONFIG

- systemd services:
    - jog.service -> mist.service
    - jogemetry.service -> wisp.service
    - jogemetry-dashboard.service -> mistmetry.service

- Binaries / CLI:
    - `jog` -> `mist`
    - `jog-cli` -> `mist-cli`
    - `jogemetry` -> `wisp`
    - `jogemetry-collect` -> `wisp-collect`

- Python / Go / JS packages:
    - `jog` -> `mist`
    - `jogemetry` -> `wisp` (agent) / `mistmetry` (backend)
    - `from jog...` -> `from mist...`
    - `import jogemetry` -> `import wisp`

- Docker:
    - `jog:latest` -> `mist:latest`
    - `jogemetry:latest` -> `wisp:latest`
    - `jogemetry-dashboard:latest` -> `mistmetry:latest`
    - container names: `jog-*` -> `mist-*`, `jogemetry-*` -> `wisp-*` / `mistmetry-*`

- Env vars (keep OLD as deprecated alias for 1 release if needed, then remove):
    - JOG_* -> MIST_*
    - JOGEMETRY_* -> WISP_* (agent) or MISTMETRY_* (dashboard)
    - JOG_HOST -> MIST_HOST
    - JOG_PORT -> MIST_PORT
    - JOGEMETRY_ENDPOINT -> WISP_ENDPOINT
    - JOGEMETRY_SERVER -> MISTMETRY_SERVER

- Config files:
    - jog.conf / jog.yaml / jog.json -> mist.conf / mist.yaml / mist.json
    - jogemetry.conf -> wisp.conf
    - jogemetry-dashboard.conf -> mistmetry.conf
    - Config keys: `jog:` -> `mist:`, `jogemetry:` -> `wisp:` / `mistmetry:`

- DB:
    - Database `jog` -> `mist`
    - Database `jogemetry` -> `mistmetry`
    - Tables `jog_*` -> `mist_*`
    - Tables `jogemetry_*` -> `wisp_*` (raw agent events) or `mistmetry_*` (aggregated)

- API routes:
    - /api/jog/* -> /api/mist/*
    - /api/jogemetry/* -> /api/wisp/* (agent ingest) OR /api/mistmetry/* (dashboard queries)
    - Keep a 301 / deprecation shim for /api/jogemetry/* -> /api/wisp/* for one release, log warning.

- Hostnames / mDNS:
    - jog.local -> mist.local
    - jogemetry.local -> wisp.local (agent) / mistmetry.local (dashboard)

## 7. DOCS / UI / STRINGS TO UPDATE

Update in ALL user-facing strings:
- README.md title: "# MIST — Mobile Imaging System Toolkit"
- README.md subtitle: "Imaging, anywhere. Ubuntu + FOGProject, in your bag."
- README.md must link FOGProject as https://fogproject.org/ — never fogproject.com
- Splash screens: MIST splash + WISP splash (see assets/branding/)
- App titles, window titles, CLI --help, --version, man pages
- PXE boot menu: "MIST — Boot to Imaging" (was JOG)
- Web UI header: "MIST" + subhead "MISTMETRY" for telemetry pages
- About dialog: Must list MIST, WISP, MISTMETRY with versions
- Footer: "MIST • WISP • MISTMETRY — Open Source"

Do NOT update:
- FOGProject name, logo, or upstream docs (third-party)
- Ubuntu name/logo (third-party)
- Git commit history (do not rewrite history)

## 8. MIGRATION STEPS FOR OPENCODE — DO IN ORDER

1. Create branch: `git checkout -b rebrand/mist-wisp-mistmetry`
2. Run global search for: JOG, Jog, jog, JOGEMETRY, jogemetry, Jonathan's Opensource Ghost, fogproject.com
   Save results to MIGRATION_NOTES.md before changing anything.
3. Apply rename map in Section 4 + file renames in Section 5 using `git mv`.
4. Split JOGEMETRY -> WISP vs MISTMETRY per Section 4 disambiguation. List every ambiguous file in MIGRATION_NOTES.md.
5. Update env vars, configs, systemd units, Dockerfiles, docker-compose.yml, API routes.
6. Update README.md, docs/, splash screens, banners, icons, PXE menu, CLI help.
7. Fix all upstream links: fogproject.com -> fogproject.org
8. Add deprecation shims: old CLI `jog` -> prints "jog is now mist, use mist" + forwards. Old env vars log deprecation warning once. Keep for 1 release only.
9. Run: lint, unit tests, build, boot test in VM. Fix all broken imports / references.
10. Update .github/workflows, CI badges, links, repo description to MIST.
11. Create MIGRATION.md with: What changed, old -> new table, how to upgrade from JOG to MIST, breaking changes.
12. Commit with message: `feat!: rebrand JOG -> MIST, JOGEMETRY -> WISP / MISTMETRY`
13. Open PR, request review, do NOT merge until PXE boot + WISP heartbeat to MISTMETRY verified.

## 9. VERIFICATION CHECKLIST

- [ ] No `JOG` remains in code/docs/UI except in MIGRATION.md / MIGRATION_NOTES.md historical note + deprecation shims
- [ ] No `JOGEMETRY` remains except in migration docs + shims
- [ ] No `fogproject.com` remains anywhere — only `fogproject.org`
- [ ] `mist --help` works, `wisp --help` works
- [ ] `mist.service` starts, `wisp.service` starts, `mistmetry.service` starts
- [ ] PXE boot menu shows MIST
- [ ] WISP agent reports to MISTMETRY dashboard
- [ ] README shows MIST banner, MIST description, WISP + MISTMETRY section
- [ ] README links FOGProject to https://fogproject.org/
- [ ] Splash screens load: mist-splash.png, wisp-splash.png
- [ ] Docker images build as mist / wisp / mistmetry

## 10. WHAT TO SAY IF USERS ASK

> JOG is now MIST. Same tool, better name. JOGEMETRY is now WISP (agent) + MISTMETRY (dashboard). Update your commands from `jog` to `mist` and `jogemetry` to `wisp`. Powered by FOGProject — https://fogproject.org/
